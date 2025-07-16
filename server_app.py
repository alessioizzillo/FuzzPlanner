import os
import csv
import json
import signal
import subprocess
import shutil
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request, Response
from flask_cors import CORS

from scheduler import (
    run_container,
    get_container_info,
    clear_non_running,
    update_schedule_status,
    ensure_experiment_consistency
)

# Configuration constants
BASE_DIR = os.path.join(os.sep, "FuzzPlanner")
FACT_IP = "http://192.168.30.177"
FACT_PORT = "5000"

RUNTIME_TMP = os.path.join(BASE_DIR, "runtime_tmp")
FUZZ_EXP_DIR = os.path.join(RUNTIME_TMP, "fuzz_experiments")
SCHEDULE_CSV = os.path.join(RUNTIME_TMP, "schedule.csv")
SCHEDULE_HEADER = [
    "status",
    "exp_name",
    "container_name",
    "num_cores",
    "mode",
    "firmware"
]

FIRMAE_DIR = os.path.join(BASE_DIR, "FirmAE")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
FIRM_RUN_DB_CSV = os.path.join(FIRMAE_DIR, "firm_db_run.csv")
FIRMWARES_DIR = os.path.join(BASE_DIR, "firmwares_source_code")
SCRATCH_DIR = os.path.join(FIRMAE_DIR, "scratch")
LOGICAL_TO_PAIR = {}
PAIR_TO_LOGICAL = defaultdict(list)

app = Flask(__name__)
CORS(app)

# Utility functions

def nest_results(entries, leaf_fields):
    nested = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
    for entry in entries:
        brand = entry["brandId"]
        firmware = entry["firmwareId"]
        run = entry["runId"]
        binary = entry["binaryId"]

        for field in leaf_fields:
            nested[brand][firmware][run][binary][field] = entry.get(field)
    return nested

def nest_results_2(entries, leaf_fields):
    nested = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
    for entry in entries:
        brand = entry["brandId"]
        firmware = entry["firmwareId"]

        for field in leaf_fields:
            nested[brand][firmware][field] = entry.get(field)
    return nested

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

@app.route("/brands")
def list_brands() -> Response:
    path = os.path.join(BASE_DIR, "firmwares")
    if not os.path.isdir(path):
        return jsonify({"status": "error", "message": f"Directory '{path}' not found"}), 500

    brands = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    return jsonify(brands), 200

@app.route("/firmwares")
def list_firmwares() -> Response:
    brand = request.args.get("brandId")
    if not brand:
        return jsonify({"status": "error", "message": "Missing 'brand' parameter"}), 400

    path = os.path.join(BASE_DIR, "firmwares", brand)
    if not os.path.isdir(path):
        return jsonify({"status": "error", "message": f"Directory '{path}' not found"}), 404

    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    return jsonify({"firmwares": files}), 200

@app.route("/check_firm_img", methods=["GET"])
def check_firmware_image() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")

    if not brand or not firmware:
        return jsonify({"status": "error", "message": "Missing brand or firmwareId"}), 400

    file_path = os.path.join(BASE_DIR, "firmwares", brand, firmware)

    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": f"Firmware '{firmware}' not found under brand '{brand}'"}), 404

    img_res = get_last_img_result(f"{brand}/{firmware}")
    if img_res in ("true", "false"):
        return jsonify({"status": "succeeded" if img_res == "true" else "failed"}), 200
    if is_check_running(f"{brand}/{firmware}"):
        return jsonify({"status": "running"}), 200
    return jsonify({"status": "not_found"}), 200

@app.route("/create_firm_img", methods=["GET"])
def create_firmware_image() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")

    file_path = os.path.join(BASE_DIR, "firmwares", brand, firmware)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": f"Firmware '{os.path.join(brand, firmware)}' not found"}), 404

    append_csv_row(SCHEDULE_CSV, SCHEDULE_HEADER, [""] * 3 + ["1"] + ["check", os.path.join(brand, firmware)])
    success = run_container(SCHEDULE_CSV, LOGICAL_TO_PAIR, PAIR_TO_LOGICAL, None)
    return ("OK", 200) if success else (jsonify({"status": "error", "message": "Image creation failed"}), 400)

@app.route("/runs")
def list_runs() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")

    base = os.path.join(RUNTIME_TMP, "analysis", "results", brand, firmware, "dynamic_analysis")
    runs = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))] if os.path.isdir(base) else []
    return jsonify({"brand": brand, "firmwareId": firmware, "runs": runs}), 200

@app.route("/remove_run", methods=["POST"])
def remove_run() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")
    run_id = request.args.get("runId")

    if not brand or not firmware or not run_id:
        return jsonify({"status": "error", "message": "Missing brand, firmwareId, or runId"}), 400

    base_dynamic_analysis = os.path.join(
        RUNTIME_TMP, "analysis", "results", brand, firmware, "dynamic_analysis", run_id
    )

    select_analyses_path = os.path.join(
        RUNTIME_TMP, "select_analysis", "results", brand, firmware, run_id
    )

    if os.path.exists(select_analyses_path):
        shutil.rmtree(select_analyses_path)

    if not os.path.exists(base_dynamic_analysis):
        return jsonify({
            "status": "error",
            "message": f"Run '{run_id}' not found under brand '{brand}' and firmware '{firmware}'"
        }), 404

    shutil.rmtree(base_dynamic_analysis)

    fuzz_experiments_dir = os.path.join(
        RUNTIME_TMP, "fuzz_experiments", brand, firmware
    )

    if os.path.exists(fuzz_experiments_dir):
        for entry in os.listdir(fuzz_experiments_dir):
            exp_path = os.path.join(fuzz_experiments_dir, entry)
            if not os.path.isdir(exp_path):
                continue

            exp_info_file = os.path.join(exp_path, "exp_info.json")
            if os.path.exists(exp_info_file):
                try:
                    with open(exp_info_file, "r") as f:
                        exp_info = json.load(f)
                    
                    if exp_info.get("runId") == run_id:
                        shutil.rmtree(exp_path)
                        print(f"Removed fuzzing experiment: {exp_path}")
                except (json.JSONDecodeError, OSError) as e:
                    print(f"Warning: Could not read {exp_info_file}: {e}")

    return jsonify({"status": "succeeded"}), 200

@app.route("/data")
def fetch_data() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")
    run_id = request.args.get("runId")
    dtype = request.args.get("type")

    if dtype in ("interactions", "processes", "data_channels"):
        path = os.path.join(RUNTIME_TMP, "analysis", "results", brand, firmware, "dynamic_analysis", run_id, "data", f"{dtype}.json")
    elif dtype == "executable_files":
        path = os.path.join(RUNTIME_TMP, "analysis", "results", brand, firmware, "static_analysis", "data", "executable_files.json")
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
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")
    combined = os.path.join(brand, firmware)

    file_path = os.path.join(BASE_DIR, "firmwares", brand, firmware)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": f"Firmware '{os.path.join(brand, firmware)}' not found"}), 404

    status, cname = get_container_info(combined, SCHEDULE_CSV)
    if (status == "paused"):
        run_id = get_run_id(combined)
        subprocess.run(["docker", "exec", cname, "pkill", "-CONT", "-f", "capture_packets.py"])
        subprocess.run(["docker", "exec", cname, "pkill", "-CONT", "-f", "qemu-system"])
        update_schedule_status(SCHEDULE_CSV, "running", container_name=cname)
        return ("OK", 200)
    else:
        append_csv_row(SCHEDULE_CSV, SCHEDULE_HEADER, [""] * 3 + ["1"] + ["run_capture", os.path.join(brand, firmware)])
        success = run_container(SCHEDULE_CSV, LOGICAL_TO_PAIR, PAIR_TO_LOGICAL, None)

        return ("OK", 200) if success else (jsonify({"status": "error", "message": "Emulation failed"}), 400)

@app.route("/check_run", methods=["GET"])
def check_run() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")
    combined = os.path.join(brand, firmware)

    if not firmware or not brand:
        return jsonify({"status": "error", "message": "Missing brand or firmwareId"}), 400

    run_id = get_run_id(combined)

    status, cname = get_container_info(combined, SCHEDULE_CSV)
    if (status != "running" and status != "paused") or not run_id:
        return jsonify({"status": "not running"}), 200
    else:
        if status == "paused":
            return jsonify({"status": "paused"}), 200
        else:
            listening_file = os.path.join(SCRATCH_DIR, 'run', run_id, 'webserver_ready')
            listening = os.path.exists(listening_file)

            response_data = {"status": "listening" if listening else "booting"}

            if listening:
                ip_file = os.path.join(SCRATCH_DIR, 'run', run_id, 'ip')
                if os.path.exists(ip_file):
                    try:
                        with open(ip_file, 'r') as f:
                            ip = f.read().strip()
                        response_data["ip"] = ip
                    except Exception as e:
                        pass

            return jsonify(response_data), 200

@app.route("/pause_run_capture", methods=["POST"])
def pause_and_analyze() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")
    fact_uid = request.args.get("factUid")
    combined = os.path.join(brand, firmware)

    if not firmware or not brand:
        return jsonify({"status": "error", "message": "Missing brand or firmwareId"}), 400

    run_id = get_run_id(combined)
    status, cname = get_container_info(combined, SCHEDULE_CSV)
    if status != "running" or not run_id:
        return jsonify({"status": "error", "message": f"Not running: {combined}"}), 400

    update_schedule_status(SCHEDULE_CSV, "paused", container_name=cname)
    subprocess.run(["docker", "exec", cname, "pkill", "-SIGSTOP", "-f", "qemu-system"])
    subprocess.run(["docker", "exec", cname, "pkill", "-SIGTSTP", "-f", "capture_packets.py"])

    work = os.path.join(SCRATCH_DIR, 'run', run_id)
    analysis_dir = os.path.join(RUNTIME_TMP, "analysis", "results", combined, "dynamic_analysis")
    out = os.path.join(analysis_dir, next_run_folder(analysis_dir))
    script = os.path.join(os.getcwd(), "scripts", "analysis.py")
    cmd = [
        "python3", script, combined, out,
        os.path.join(work, "debug", "full_system_syscall.log"),
        os.path.join(work, "image_backup"),
        os.path.join(FIRMWARES_DIR, combined),
        FACT_IP, FACT_PORT, fact_uid if fact_uid else "None"
    ]
    print(" ".join(cmd) + f"; cp {os.path.join(work, 'user_interaction.pcap')} {out}")
    cmd_str = " ".join(cmd) + f"; cp {os.path.join(work, 'user_interaction.pcap')} {out}"
    subprocess.Popen(cmd_str, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return jsonify({"status": "paused"}), 200

@app.route("/stop_emulation", methods=["POST"])
def stop_emulation() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")
    fact_uid = request.args.get("factUid")
    combined = os.path.join(brand, firmware)

    run_id = get_run_id(combined)
    print(run_id)
    status, cname = get_container_info(combined, SCHEDULE_CSV)
    if not status or not run_id:
        return jsonify({"status": "error", "message": f"Not running: {combined}"}), 400

    subprocess.run(["docker", "exec", cname, "pkill", "-SIGTERM", "-f", "capture_packets.py"])
    subprocess.run(["docker", "rm", "-f", cname])
    ensure_experiment_consistency(SCHEDULE_CSV)

    if status != "paused":
        print("analyzing...")
        work = os.path.join(SCRATCH_DIR, 'run', run_id)
        analysis_dir = os.path.join(RUNTIME_TMP, "analysis", "results", combined, "dynamic_analysis")
        out = os.path.join(analysis_dir, next_run_folder(analysis_dir))
        script = os.path.join(os.getcwd(), "scripts", "analysis.py")
        cmd = [
            "python3", script, combined, out,
            os.path.join(work, "debug", "full_system_syscall.log"),
            os.path.join(work, "image_backup"),
            os.path.join(FIRMWARES_DIR, combined),
            FACT_IP, FACT_PORT, fact_uid if fact_uid else "None"
        ]
        print(" ".join(cmd) + f"; cp {os.path.join(work, 'user_interaction.pcap')} {out}")
        cmd_str = " ".join(cmd) + f"; cp {os.path.join(work, 'user_interaction.pcap')} {out}"
        subprocess.Popen(cmd_str, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return jsonify({"status": "stopped"}), 200

@app.route('/select', methods=['POST'])
def select() -> Response:
    brandId    = request.args.get('brandId')
    firmwareId = request.args.get('firmwareId')
    runId      = request.args.get('runId')
    binaryId   = request.args.get('binaryId')
    dataChannelId = request.args.get('dataChannelId')

    try:
        exec_data_pairs = [
            {
                "brand_id": brandId,
                "firmware_id": firmwareId,
                "run_id": runId,
                "executable_id": binaryId,
                "data_channel_id": dataChannelId
            }
        ]
    except (TypeError, KeyError) as e:
        return jsonify({"status": "error", "message": f"Invalid select payload: {e}"}), 400

    json_path = os.path.join(RUNTIME_TMP, 'exec_data_pairs.json')
    try:
        with open(json_path, 'w') as jf:
            json.dump(exec_data_pairs, jf, indent=2)
    except OSError as e:
        return jsonify({"status": "error",
                        "message": f"Could not write exec-data file: {e}"}), 500

    append_csv_row(
        SCHEDULE_CSV,
        SCHEDULE_HEADER,
        ["", "", "", "1", "select", os.path.join(brandId, firmwareId)]
    )

    success = run_container(SCHEDULE_CSV, LOGICAL_TO_PAIR, PAIR_TO_LOGICAL, None)
    if not success:
        return jsonify({"status": "error",
                        "message": "Container launch failed"}), 500

    return ("OK", 200)


@app.route('/engine_features', methods=['GET'])
def engine_features() -> Response:
    file_path = os.path.join(CONFIG_DIR, "engine_features.json")

    if not os.path.isfile(file_path):
        return jsonify({
            "error": "Not found",
            "message": f"Config file not found: {file_path}"
        }), 404

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return jsonify({
            "error": "Server error",
            "message": f"Failed to read or parse engine_features.json: {e}"
        }), 500

    return jsonify(data), 200


@app.route('/dictionaries', methods=['GET'])
def list_dictionaries() -> Response:
    dir_path = os.path.join(CONFIG_DIR, "dictionaries")

    if not os.path.isdir(dir_path):
        return jsonify({
            "error": "Not found",
            "message": f"'dictionaries' directory not found: {dir_path}"
        }), 404

    try:
        entries = os.listdir(dir_path)
        files = [
            name for name in entries
            if os.path.isfile(os.path.join(dir_path, name))
        ]
    except OSError as e:
        return jsonify({
            "error": "Server error",
            "message": f"Failed to list dictionaries: {e}"
        }), 500

    return jsonify(files), 200


@app.route('/select_res', methods=['POST'])
def select_res() -> Response:
    brand_id       = request.args.get('brandId')
    firmware_id    = request.args.get('firmwareId')
    run_id         = request.args.get('runId')
    binary_id      = request.args.get('binaryId')
    data_channel_id = request.args.get('dataChannelId')

    if not all([brand_id, firmware_id, run_id, binary_id, data_channel_id]):
        return jsonify({
            "error": "Missing parameter",
            "message": "You must provide brandId, firmwareId, runId, binaryId and dataChannelId"
        }), 400

    file_path = os.path.join(
        RUNTIME_TMP, "select_analysis", "results",
        brand_id, firmware_id,
        run_id, os.path.basename(binary_id),
        data_channel_id, "results.json"
    )

    if not os.path.isfile(file_path):
        return jsonify({
            "error": "Not found",
            "message": f"File not found: {file_path}"
        }), 404

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return jsonify({
            "error": "Server error",
            "message": f"Failed to read or parse results.json: {e}"
        }), 500

    return jsonify(data), 200

@app.route('/select_analyses', methods=['GET'])
def select_analyses() -> Response:
    brand_id_filter = request.args.get("brandId")
    firmware_id_filter = request.args.get("firmwareId")
    run_id_filter = request.args.get("runId")

    running = []
    done = []

    # --- Collect Running ---
    try:
        ensure_experiment_consistency(SCHEDULE_CSV)
        rows = read_csv_rows(SCHEDULE_CSV)

        for row in rows:
            if row["status"].lower() == "running" and row["mode"] == "select":
                container = row["container_name"]
                json_path = os.path.join(RUNTIME_TMP, "select_analysis", "infos", f"{container}.json")
                if not os.path.isfile(json_path):
                    continue

                try:
                    with open(json_path, "r") as f:
                        metadata = json.load(f)

                    if brand_id_filter and metadata.get("brandId") != brand_id_filter:
                        continue
                    if firmware_id_filter and metadata.get("firmwareId") != firmware_id_filter:
                        continue
                    if run_id_filter and metadata.get("runId") != run_id_filter:
                        continue

                    running.append({
                        "brandId": metadata.get("brandId"),
                        "firmwareId": metadata.get("firmwareId"),
                        "runId": metadata.get("runId"),
                        "binaryId": metadata.get("binaryId"),
                        "dataChannelId": metadata.get("dataChannelId")
                    })
                except (json.JSONDecodeError, OSError):
                    continue
    except Exception as e:
        return jsonify({"error": "Failed to process running analyses", "message": str(e)}), 500

    # --- Collect Done ---
    try:
        if brand_id_filter and firmware_id_filter:
            base_dir = os.path.join(
                RUNTIME_TMP, "select_analysis", "results",
                brand_id_filter, firmware_id_filter
            )

            if os.path.isdir(base_dir):
                run_ids = os.listdir(base_dir)

                if run_id_filter:
                    run_ids = [r for r in run_ids if r == run_id_filter]
                
                for run_id in run_ids:
                    binaries_path = os.path.join(base_dir, run_id)
                    if not os.path.isdir(binaries_path):
                        continue

                    binary_ids = os.listdir(binaries_path)
                    for binary_id in binary_ids:
                        data_channels_path = os.path.join(binaries_path, os.path.basename(binary_id))
                        data_channel_ids = os.listdir(data_channels_path)
                        for data_channel_id in data_channel_ids:
                            result_path = os.path.join(binaries_path, binary_id, data_channel_id, "results.json")
                            if os.path.isfile(result_path):
                                done.append({
                                    "brandId": brand_id_filter,
                                    "firmwareId": firmware_id_filter,
                                    "runId": run_id,
                                    "binaryId": binary_id,
                                    "dataChannelId": data_channel_id
                                })
    except Exception as e:
        return jsonify({"error": "Failed to process done analyses", "message": str(e)}), 500

    return jsonify({
        "running": nest_results(running, ["dataChannelId"]),
        "done": nest_results(done, ["dataChannelId"])
    })

@app.route('/fuzz_experiments', methods=['GET'])
def fuzz_experiments() -> Response:
    brand_id_filter    = request.args.get("brandId")
    firmware_id_filter = request.args.get("firmwareId")

    running_exp_names = []
    done               = []
    seen_running       = set()

    ensure_experiment_consistency(SCHEDULE_CSV)
    rows = read_csv_rows(SCHEDULE_CSV)

    for row in rows:
        if row["status"].lower() != "running" or row["mode"] != "fuzz":
            continue

        try:
            brandId, firmwareId = row["firmware"].split("/", 1)
        except ValueError:
            brandId, firmwareId = None, row["firmware"]

        if brand_id_filter and brandId != brand_id_filter:
            continue
        if firmware_id_filter and firmwareId != firmware_id_filter:
            continue

        exp_name = row["exp_name"]
        if exp_name not in seen_running:
            running_exp_names.append(exp_name)
            seen_running.add(exp_name)

    try:
        for exp_name in os.listdir(os.path.join(FUZZ_EXP_DIR, brand_id_filter, firmware_id_filter)):
            if exp_name in seen_running:
                continue
            done.append(exp_name)
    except OSError:
        pass

    return jsonify({
        "running": running_exp_names,
        "done":    done
    })

@app.route('/execute', methods=['POST'])
def execute():
    try:
        brandId    = request.args.get('brandId')
        firmwareId = request.args.get('firmwareId')
        request_data = request.json 
        experiments_data_json = json.dumps(request_data, indent=2)

        os.environ["EXPERIMENTS_DATA"] = experiments_data_json

        os.makedirs(RUNTIME_TMP, exist_ok=True)
        fuzz_pars_path = os.path.join(RUNTIME_TMP, "fuzz_pars.json")
        with open(fuzz_pars_path, "w", encoding="utf-8") as f:
            f.write(experiments_data_json)

    except Exception as e:
        response_data = {
            "status": "error",
            "message": "Bad request. %s" % e
        }
        return jsonify(response_data), 400

    append_csv_row(
        SCHEDULE_CSV,
        SCHEDULE_HEADER,
        ["", "", "", "1", "fuzz", os.path.join(brandId, firmwareId)]
    )

    success = run_container(SCHEDULE_CSV, LOGICAL_TO_PAIR, PAIR_TO_LOGICAL, os.path.join(FUZZ_EXP_DIR, brandId, firmwareId))
    if not success:
        return jsonify({"status": "error",
                        "message": "Container launch failed"}), 500
    
    return jsonify({"status": "OK"}), 200

@app.route('/remove_select', methods=['POST'])
def remove_select() -> Response:
    brand = request.args.get('brandId')
    firmware = request.args.get('firmwareId')
    run_id = request.args.get('runId')
    binary = request.args.get('binaryId')
    data_channel = request.args.get('dataChannelId')

    if not all([brand, firmware, run_id, binary, data_channel]):
        return jsonify({'status': 'error', 'message': 'Missing parameter'}), 400

    path = os.path.join(
        RUNTIME_TMP, 'select_analysis', 'results',
        brand, firmware, run_id, os.path.basename(binary), data_channel
    )
    if not os.path.isdir(path):
        return jsonify({'status': 'error', 'message': f'Path not found: {path}'}), 404

    try:
        shutil.rmtree(path)
        return jsonify({'status': 'succeeded'}), 200
    except OSError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/remove_select_binary', methods=['POST'])
def remove_select_binary() -> Response:
    brand = request.args.get('brandId')
    firmware = request.args.get('firmwareId')
    run_id = request.args.get('runId')
    binary = request.args.get('binaryId')

    if not all([brand, firmware, run_id, binary]):
        return jsonify({'status': 'error', 'message': 'Missing parameter'}), 400

    path = os.path.join(
        RUNTIME_TMP, 'select_analysis', 'results',
        brand, firmware, run_id, os.path.basename(binary)
    )
    if not os.path.isdir(path):
        return jsonify({'status': 'error', 'message': f'Path not found: {path}'}), 404

    try:
        shutil.rmtree(path)
        return jsonify({'status': 'succeeded'}), 200
    except OSError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/remove_experiment', methods=['POST'])
def remove_experiment() -> Response:
    brand = request.args.get('brandId')
    firmware = request.args.get('firmwareId')
    exp_name = request.args.get('expName')

    if not all([brand, firmware, exp_name]):
        return jsonify({'status': 'error', 'message': 'Missing parameter'}), 400

    try:
        rows = read_csv_rows(SCHEDULE_CSV)
        updated_rows = []
        container_to_remove = None

        for r in rows:
            if (
                r['mode'] == 'fuzz'
                and r['exp_name'] == exp_name
                and r['firmware'] == os.path.join(brand, firmware)
            ):
                container_to_remove = r.get('container_name')
            else:
                updated_rows.append(r)

        if container_to_remove:
            try:
                subprocess.run(
                    ["docker", "rm", "-f", container_to_remove],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            except subprocess.CalledProcessError as docker_err:
                print(f"WARNING: Failed to remove container {container_to_remove}: {docker_err}")

        with open(SCHEDULE_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(SCHEDULE_HEADER)
            for r in updated_rows:
                writer.writerow([r[h] for h in SCHEDULE_HEADER])

        exp_dir = os.path.join(FUZZ_EXP_DIR, brand, firmware, exp_name)
        if os.path.isdir(exp_dir):
            shutil.rmtree(exp_dir)

        return jsonify({'status': 'succeeded'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/exp_info', methods=['GET'])
def exp_info() -> Response:
    brand_id = request.args.get("brandId")
    firmware_id = request.args.get("firmwareId")
    exp_name = request.args.get("expName")

    if not all([brand_id, firmware_id, exp_name]):
        return jsonify({
            "error": "Missing parameter",
            "message": "You must provide brandId, firmwareId, and expName"
        }), 400

    def is_running_exp(exp_name: str):
        try:
            with open(SCHEDULE_CSV, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get("exp_name") == exp_name:
                        container_name = row.get("container_name")
                        if row.get("status", "").lower() == "running":
                            return True, row.get("container_name")
                        else:
                            return False, None
                return False, None
        except Exception as e:
            print(f"Error reading schedule file: {e}")
            return False, None

    running, container_name = is_running_exp(exp_name)

    if running:
        combined = os.path.join(brand_id, firmware_id)
        iid = get_run_id(combined)

        exp_dir = os.path.join(
            FIRMAE_DIR,
            "scratch",
            container_name,
            iid,
            "outputs"
        )
    else:
        exp_dir = os.path.join(FUZZ_EXP_DIR, brand_id, firmware_id, exp_name)

    exp_info_path = os.path.join(exp_dir, "exp_info.json")
    fuzzer_stats_path = os.path.join(exp_dir, "fuzzer_stats")

    if not os.path.isdir(exp_dir):
        return jsonify({
            "error": "Not found",
            "message": f"Experiment directory not found: {exp_dir}"
        }), 404
    
    exp_info_data = {}
    if os.path.isfile(exp_info_path):
        try:
            with open(exp_info_path, 'r', encoding='utf-8') as f:
                exp_info_data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            return jsonify({
                "error": "Server error",
                "message": f"Failed to read/parse exp_info.json: {e}"
            }), 500

    allowed_stats = {
        "cycles_done",
        "execs_done",
        "execs_per_sec",
        "paths_total",
        "paths_favored",
        "paths_found",
        "max_depth",
        "cur_path",
        "pending_favs",
        "pending_total",
        "variable_paths",
        "stability",
        "bitmap_cvg",
        "unique_crashes",
        "unique_hangs",
        "last_update",
        "start_time"
    }

    fuzzer_stats_data = {}
    if os.path.isfile(fuzzer_stats_path):
        try:
            with open(fuzzer_stats_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if ':' not in line:
                        continue
                    key, val = line.strip().split(':', 1)
                    key = key.strip()
                    val = val.strip()

                    parsed_val = None
                    if val.isdigit():
                        parsed_val = int(val)
                    else:
                        try:
                            parsed_val = float(val)
                        except ValueError:
                            parsed_val = val

                    if key in allowed_stats:
                        fuzzer_stats_data[key] = parsed_val

            if "last_update" in fuzzer_stats_data and "start_time" in fuzzer_stats_data:
                try:
                    fuzz_seconds = float(fuzzer_stats_data["last_update"]) - float(fuzzer_stats_data["start_time"])
                    if fuzz_seconds < 0:
                        fuzz_seconds = 0

                    fuzz_time_str = f"{fuzz_seconds:.1f} seconds"

                    fuzzer_stats_data["fuzz_time"] = fuzz_time_str
                except (ValueError, TypeError):
                    pass

            fuzzer_stats_data.pop("last_update", None)
            fuzzer_stats_data.pop("start_time", None)

        except OSError as e:
            return jsonify({
                "error": "Server error",
                "message": f"Failed to read fuzzer_stats: {e}"
            }), 500

    merged = {**exp_info_data, **fuzzer_stats_data}
    return jsonify(merged), 200

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
