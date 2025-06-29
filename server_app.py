import os
import csv
import json
import signal
import subprocess
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request, Response
from flask_cors import CORS

from scheduler import (
    run_container,
    get_container_info,
    clear_non_running,
    update_schedule_status,
    ensure_experiment_consistency,
)

# Configuration constants
BASE_DIR = os.path.join(os.sep, "FuzzPlanner")
FACT_IP = "http://192.168.30.177"
FACT_PORT = "5000"

RUNTIME_TMP = os.path.join(BASE_DIR, "runtime_tmp")
SCHEDULE_CSV = os.path.join(RUNTIME_TMP, "schedule.csv")
SCHEDULE_HEADER = [
    "status",
    "exp_name",
    "container_name",
    "num_cores",
    "mode",
    "firmware",
    "experiments_data_path",
]

FIRMAE_DIR = os.path.join(BASE_DIR, "FirmAE")
FIRM_RUN_DB_CSV = os.path.join(FIRMAE_DIR, "firm_db_run.csv")
EXPERIMENTS_DIR = os.path.join(RUNTIME_TMP, "experiments")
FIRMWARES_DIR = os.path.join(BASE_DIR, "firmwares_source_code")
SCRATCH_DIR = os.path.join(FIRMAE_DIR, "scratch")
LOGICAL_TO_PAIR = {}
PAIR_TO_LOGICAL = defaultdict(list)

app = Flask(__name__)
CORS(app)

# Utility functions

def read_csv_rows(path: str) -> List[Dict[str, str]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def append_csv_row(path: str, header: List[str], row: List[Any]) -> None:
    write_header = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(header)
        writer.writerow(row)


def get_last_img_result(firmware: str, db_path: str = FIRM_RUN_DB_CSV) -> Optional[str]:
    if not os.path.exists(db_path):
        return None
    for record in read_csv_rows(db_path):
        if record.get("firmware") == os.path.basename(firmware):
            # assume result is in last column
            return list(record.values())[-1]
    return None


def is_check_running(firmware: str, schedule_path: str = SCHEDULE_CSV) -> bool:
    if not os.path.exists(schedule_path):
        return False
    for record in read_csv_rows(schedule_path):
        if record.get("mode") == "check" and record.get("firmware") == firmware and record.get("status") == "running":
            return True
    return False


def send_signal_tree(pid: int, sig: int) -> None:
    try:
        children = subprocess.check_output(["pgrep", "-P", str(pid)]).split()
        for c in children:
            send_signal_tree(int(c), sig)
        os.kill(pid, sig)
    except subprocess.CalledProcessError:
        os.kill(pid, sig)


def next_run_folder(base_dir: str) -> str:
    if os.path.isdir(base_dir):
        runs = [d for d in os.listdir(base_dir) if d.startswith("run_")]
        if runs:
            nums = [int(r.split("_")[1]) for r in runs]
            return f"run_{max(nums) + 1}"
    return "run_0"


def get_run_id(firmware: str) -> Optional[str]:
    if not os.path.exists(FIRM_RUN_DB_CSV):
        return None
    for record in read_csv_rows(FIRM_RUN_DB_CSV):
        if record.get("brand") == os.path.dirname(firmware) and record.get("firmware") == os.path.basename(firmware):
            return record.get("id") or record.get("run_id")
    return None

# Route handlers

@app.route("/")
def index() -> Tuple[str, int]:
    return "FuzzPlanner!", 200

@app.errorhandler(404)
def not_found(e) -> Response:
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404

@app.route("/firmwares")
def list_firmwares() -> Response:
    path = os.path.join(BASE_DIR, "firmwares")
    if not os.path.isdir(path):
        return jsonify({"status": "error", "message": f"Directory '{path}' not found"}), 500
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    return jsonify({"firmwares": files}), 200

@app.route("/check_firm_img", methods=["GET"])
def check_firmware_image() -> Response:
    firmware = request.args.get("firmwareId")
    file_path = os.path.join(BASE_DIR, "firmwares", firmware)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": f"Firmware '{firmware}' not found"}), 404

    img_res = get_last_img_result(firmware)
    if img_res in ("true", "false"):
        return jsonify({"status": "succeeded" if img_res == "true" else "failed"}), 200
    if is_check_running(firmware):
        return jsonify({"status": "running"}), 200
    return jsonify({"status": "not_found"}), 200

@app.route("/create_firm_img", methods=["GET"])
def create_firmware_image() -> Response:
    firmware = request.args.get("firmwareId")
    file_path = os.path.join(BASE_DIR, "firmwares", firmware)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": f"Firmware '{firmware}' not found"}), 404

    append_csv_row(
        SCHEDULE_CSV,
        SCHEDULE_HEADER,
        [""] * 3 + ["check", firmware, ""]
    )
    success = run_container(SCHEDULE_CSV, LOGICAL_TO_PAIR, PAIR_TO_LOGICAL, None)
    return ("OK", 200) if success else (jsonify({"status": "error", "message": "Image creation failed"}), 400)

@app.route("/runs")
def list_runs() -> Response:
    firmware = request.args.get("firmwareId")
    base = os.path.join(RUNTIME_TMP, "analysis", "results", firmware, "dynamic_analysis")
    runs = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))] if os.path.isdir(base) else []
    return jsonify({"firmwareId": firmware, "runs": runs}), 200

@app.route("/data")
def fetch_data() -> Response:
    firmware = request.args.get("firmwareId")
    run_id = request.args.get("runId")
    dtype = request.args.get("type")

    if dtype in ("interactions", "processes", "data_channels"):
        path = os.path.join(RUNTIME_TMP, "analysis", "results", firmware, "dynamic_analysis", run_id, "data", f"{dtype}.json")
    elif dtype == "executable_files":
        path = os.path.join(RUNTIME_TMP, "analysis", "results", firmware, "static_analysis", "data", "executable_files.json")
    else:
        return jsonify({"status": "error", "message": "Invalid data type"}), 400

    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    return Response(json.dumps(data, indent=2), mimetype="application/json"), 200

@app.route("/run", methods=["POST"])
@app.route("/run_capture", methods=["POST"])
def emulate() -> Response:
    capture_flag = request.path.endswith("capture")
    firmware = request.args.get("firmwareId")
    return _emulate(firmware, capture=capture_flag)

@app.route("/check_run", methods=["GET"])
def check_run() -> Response:
    firmware = request.args.get("firmwareId")
    if not firmware:
        return jsonify({"status": "error", "message": "Missing firmwareId"}), 400

    run_id = get_run_id(firmware)
    status, cname = get_container_info(firmware, SCHEDULE_CSV)
    if status != "running" or not run_id:
        return jsonify({"status": "not_running"}), 200

    listening_file = os.path.join(SCRATCH_DIR, 'run', run_id, 'webserver_ready')
    listening = os.path.exists(listening_file)
    return jsonify({"status": "running", "listening": listening, "booting": not listening}), 200

@app.route("/pause_run_capture", methods=["POST"])
def pause_and_analyze() -> Response:
    firmware = request.args.get("firmwareId")
    fact_uid = request.args.get("factUid")
    if not firmware:
        return jsonify({"status": "error", "message": "Missing firmwareId"}), 400

    run_id = get_run_id(firmware)
    status, cname = get_container_info(firmware, SCHEDULE_CSV)
    if status != "running" or not run_id:
        return jsonify({"status": "error", "message": f"Not running: {firmware}"}), 400

    subprocess.run(["docker", "exec", cname, "kill", "-TSTP", "1"]),
    update_schedule_status(SCHEDULE_CSV, "paused", container_name=cname)

    work = os.path.join(SCRATCH_DIR, 'run', run_id)
    analysis_dir = os.path.join(RUNTIME_TMP, "analysis", "results", firmware, "dynamic_analysis")
    out = os.path.join(analysis_dir, next_run_folder(analysis_dir))
    script = os.path.join(os.getcwd(), "scripts", "analysis.py")
    cmd = ["python3", script, firmware, out, os.path.join(work, "debug", "full_system_syscall.log"), os.path.join(work, "image_backup"), os.path.join(FIRMWARES_DIR, firmware), FACT_IP, FACT_PORT, fact_uid]
    cmd_str = " ".join(cmd) + f"; cp {os.path.join(work, 'user_interaction.pcap')} {out}"
    subprocess.Popen(cmd_str, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return jsonify({"status": "paused"}), 200

@app.route("/resume_emulation", methods=["POST"])
def resume_emulation() -> Response:
    firmware = request.args.get("firmwareId")
    run_id = get_run_id(firmware)
    status, cname = get_container_info(firmware, SCHEDULE_CSV)
    if status != "paused" or not run_id:
        return jsonify({"status": "error", "message": f"Not paused: {firmware}"}), 400

    subprocess.run(["docker", "exec", cname, "kill", "-CONT", "1"]),
    update_schedule_status(SCHEDULE_CSV, "running", container_name=cname)
    return jsonify({"status": "resumed"}), 200

@app.route("/stop_emulation", methods=["POST"])
def stop_emulation() -> Response:
    firmware = request.args.get("firmwareId")
    run_id = get_run_id(firmware)
    status, cname = get_container_info(firmware, SCHEDULE_CSV)
    if not status or not run_id:
        return jsonify({"status": "error", "message": f"Not running: {firmware}"}), 400

    subprocess.run(["docker", "rm", "-f", cname])
    ensure_experiment_consistency(SCHEDULE_CSV, None)

    if status != "paused":
        pause_and_analyze()

    return jsonify({"status": "stopped"}), 200

@app.route('/select', methods=['POST'])
def select() -> Response:
    try:
        firmwareId = request.args.get('firmwareId')
        runId = request.args.get('runId')
        request_data = request.json
        select_data = request_data.get("select", [])
        
        exec_data_pairs = []
        for item in select_data:
            executable_id = item.get("executable_id")
            data_channel_id = item.get("data_channel_id")
            exec_data_pairs.append({"executable_id": executable_id, "data_channel_id": data_channel_id})

        exec_data_json = json.dumps(exec_data_pairs)
        os.environ["EXEC_DATA_PAIRS"] = exec_data_json
        print(exec_data_json)

    except Exception as e:
        response_data = {
            "status": "error",
            "message": "Bad request. %s" % e
        }

        return jsonify(response_data), 400

    return ("OK", 200)

@app.route('/execute', methods=['POST'])
def execute():
    try:
        firmwareId = request.args.get('firmwareId')
        runId = request.args.get('runId')
        request_data = request.json
        experiments_data = request_data.get("experiments", [])    
        experiments_data_json = json.dumps(experiments_data)
        os.environ["EXPERIMENTS_DATA"] = experiments_data_json
    
    except Exception as e:
        response_data = {
            "status": "error",
            "message": "Bad request. %s" % e
        }

        return jsonify(response_data), 400

    print(experiments_data_json)
    return ("OK", 200)

if __name__ == '__main__':
    clear_non_running(SCHEDULE_CSV)
    proc = subprocess.run(
        ["lscpu", "-p=NODE,CORE,CPU"],
        capture_output=True,
        text=True,
        check=True
    )

    rows = []
    for line in proc.stdout.splitlines():
        if line.startswith("#"):
            continue
        node, core, cpu = map(int, line.split(","))
        rows.append((node, core, cpu))

    rows.sort(key=lambda x: (x[0], x[1]))

    if not os.path.exists("runtime_tmp"):
        os.makedirs("runtime_tmp")

    with open("runtime_tmp/cpu_ids.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["CPU ID", "Physical ID", "Logical ID"])
        for node, core, cpu in rows:
            writer.writerow([node, core, cpu])

    print("Wrote", len(rows), "rows to cpu_ids.csv")

    with open("runtime_tmp/cpu_ids.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cpu_id = int(row["CPU ID"])
            physical_id = int(row["Physical ID"])
            logical_id = int(row["Logical ID"])
            pair = (cpu_id, physical_id)

            LOGICAL_TO_PAIR[logical_id] = pair
            PAIR_TO_LOGICAL[pair].append(logical_id)

    app.run(host='0.0.0.0', port=4000)
    