import os
import re
import sys
import csv
import json
import signal
import subprocess
import shutil
import hashlib
import time
import glob
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

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
BASE_DIR = os.getcwd()
TMP_DIR = os.path.join(BASE_DIR, "tmp")
FACT_IP = "http://192.168.30.177"
FACT_PORT = "5000"
FUZZ_EXP_DIR = os.path.join(TMP_DIR, "fuzz_experiments")
SCHEDULE_CSV = os.path.join(TMP_DIR, "schedule.csv")
SCHEDULE_HEADER = [
    "status",
    "exp_name",
    "container_name",
    "num_cores",
    "mode",
    "firmware",
    "pcap_name"
]

# Caching utilities
_cache = {}
_cache_ttl = {}
CACHE_DURATION = 1  # 1 second cache

def get_cached_or_compute(key: str, compute_func, ttl: int = CACHE_DURATION):
    now = time.time()
    if key in _cache and now - _cache_ttl.get(key, 0) < ttl:
        return _cache[key]

    result = compute_func()
    _cache[key] = result
    _cache_ttl[key] = now
    return result

def generate_etag_for_files(file_paths: List[str]) -> Tuple[str, float]:
    etag_data = ""
    last_modified = 0

    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                mtime = os.path.getmtime(file_path)
                size = os.path.getsize(file_path)
                etag_data += f"{file_path}:{mtime}:{size}:"
                last_modified = max(last_modified, mtime)
            except OSError:
                continue

    etag = hashlib.md5(etag_data.encode()).hexdigest()
    return etag, last_modified

def check_etag_match(request_etag: Optional[str], current_etag: str) -> bool:
    """Check if client ETag matches current ETag"""
    return request_etag is not None and request_etag == current_etag

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

def sanitize_data_channel_id(data_channel_id: str) -> str:
    if not data_channel_id:
        return data_channel_id

    sanitized = data_channel_id.replace('/', '_').replace('\\', '_')
    return sanitized

def nest_results(entries, leaf_fields):
    nested = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
    for entry in entries:
        brand = entry["brandId"]
        firmware = entry["firmwareId"]
        run = entry["runId"]
        binary = entry["binaryId"]

        if "dataChannelId" in leaf_fields and len(leaf_fields) == 1:
            data_channel_id = entry.get("dataChannelId", "")
            container_name = entry.get("containerName", "")

            if binary not in nested[brand][firmware][run]:
                nested[brand][firmware][run][binary] = {
                    "binaryId": binary,
                    "dataChannelIds": []
                }

            channel_exists = any(
                item["dataChannelId"] == data_channel_id
                for item in nested[brand][firmware][run][binary]["dataChannelIds"]
                if isinstance(item, dict)
            )

            if not channel_exists:
                nested[brand][firmware][run][binary]["dataChannelIds"].append({
                    "dataChannelId": data_channel_id,
                    "containerName": container_name
                })
        else:
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

def ensure_server_directories():
    directories = [
        TMP_DIR,
        os.path.join(TMP_DIR, "progress"),
        os.path.join(TMP_DIR, "fuzz_status"),
        os.path.join(TMP_DIR, "select_analysis"),
        os.path.join(TMP_DIR, "select_analysis", "infos"),
        os.path.join(TMP_DIR, "select_analysis", "results"),
        FUZZ_EXP_DIR
    ]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            print(f"Warning: Could not create directory {directory}: {e}", file=sys.stderr)

def read_csv_rows(path: str) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                print(f"Warning: CSV file {path} has no headers or is empty", file=sys.stderr)
                return []
            return list(reader)
    except (OSError, IOError, TypeError) as e:
        print(f"Warning: Could not read CSV file {path}: {e}", file=sys.stderr)
        return []


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

def cleanup_progress_file_for_container(container_name: str) -> None:
    progress_dir = os.path.join(TMP_DIR, 'progress')
    if not os.path.exists(progress_dir):
        return

    progress_file = os.path.join(progress_dir, f'{container_name}.json')
    if os.path.exists(progress_file):
        try:
            os.remove(progress_file)
            print(f"Removed stale progress file: {progress_file}")
        except OSError as e:
            print(f"Warning: Failed to remove progress file {progress_file}: {e}")

def get_next_name(dir_path: str, prefix: str) -> str:
    os.makedirs(dir_path, exist_ok=True)
    max_i = -1

    for fname in os.listdir(dir_path):
        m = re.match(rf"{prefix}_(\d+)", fname)
        if m:
            max_i = max(max_i, int(m.group(1)))
    
    return f"{prefix}_{max_i + 1}"

def get_run_id(firmware: str) -> Optional[str]:
    if not os.path.exists(FIRM_RUN_DB_CSV):
        return None
    for record in read_csv_rows(FIRM_RUN_DB_CSV):
        if record.get("brand") == os.path.dirname(firmware) and record.get("firmware") == os.path.basename(firmware):
            return record.get("id") or record.get("run_id")
    return None

def get_id(firmware:str, container_name: str) -> Optional[str]:
    db_path = os.path.join(FIRMAE_DIR, f"firm_db_{container_name}.csv")
    if not os.path.exists(db_path):
        return None
    for record in read_csv_rows(db_path):
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

    append_csv_row(SCHEDULE_CSV, SCHEDULE_HEADER, ["", "", "", "1", "check", os.path.join(brand, firmware), ""])
    success = run_container(SCHEDULE_CSV, LOGICAL_TO_PAIR, PAIR_TO_LOGICAL, None)
    return ("OK", 200) if success else (jsonify({"status": "error", "message": "Image creation failed"}), 400)

@app.route("/runs")
def list_runs() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")

    base = os.path.join(TMP_DIR, "analysis", "results", brand, firmware, "dynamic_analysis")
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
        TMP_DIR, "analysis", "results", brand, firmware, "dynamic_analysis", run_id
    )

    select_analyses_path = os.path.join(
        TMP_DIR, "select_analysis", "results", brand, firmware, run_id
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
        TMP_DIR, "fuzz_experiments", brand, firmware
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
        path = os.path.join(TMP_DIR, "analysis", "results", brand, firmware, "dynamic_analysis", run_id, "data", f"{dtype}.json")
    elif dtype == "executable_files":
        path = os.path.join(TMP_DIR, "analysis", "results", brand, firmware, "static_analysis", "data", "executable_files.json")
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
        append_csv_row(SCHEDULE_CSV, SCHEDULE_HEADER, ["", "", "", "1", "run_capture", os.path.join(brand, firmware), ""])
        success = run_container(SCHEDULE_CSV, LOGICAL_TO_PAIR, PAIR_TO_LOGICAL, None)

        if success:
            try:
                with open(SCHEDULE_CSV, newline='') as fp:
                    reader = csv.DictReader(fp)
                    for row in reader:
                        if (row.get('mode') == 'run_capture' and
                            row.get('status') == 'running' and
                            row.get('firmware') == os.path.join(brand, firmware)):
                            container_name = row.get('container_name')
                            if container_name:
                                cleanup_progress_file_for_container(container_name)
                            break
            except Exception as e:
                print(f"Warning: Failed to cleanup progress file: {e}")

        return ("OK", 200) if success else (jsonify({"status": "error", "message": "Emulation failed"}), 400)

def compute_check_run_data(brand: str, firmware: str) -> dict:
    combined = os.path.join(brand, firmware)
    run_id = get_run_id(combined)
    status, cname = get_container_info(combined, SCHEDULE_CSV)

    if (status != "running" and status != "paused") or not run_id:
        return {"status": "not running"}

    if status == "paused":
        return {"status": "paused"}

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

    return response_data

@app.route("/check_run", methods=["GET"])
def check_run() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")

    if not firmware or not brand:
        return jsonify({"status": "error", "message": "Missing brand or firmwareId"}), 400

    cache_key = f"check_run:{brand}:{firmware}"

    combined = os.path.join(brand, firmware)
    run_id = get_run_id(combined)
    files_to_check = [SCHEDULE_CSV]

    if run_id:
        scratch_run_dir = os.path.join(SCRATCH_DIR, 'run', run_id)
        potential_files = [
            os.path.join(scratch_run_dir, 'webserver_ready'),
            os.path.join(scratch_run_dir, 'ip')
        ]
        files_to_check.extend([f for f in potential_files if os.path.exists(f)])

    current_etag, last_modified = generate_etag_for_files(files_to_check)

    client_etag = request.headers.get('If-None-Match')
    if check_etag_match(client_etag, current_etag):
        response = Response('', 304)
        response.headers['ETag'] = current_etag
        return response

    data = get_cached_or_compute(
        cache_key,
        lambda: compute_check_run_data(brand, firmware)
    )

    # Create response with ETag headers
    response = jsonify(data)
    response.headers['ETag'] = current_etag
    if last_modified > 0:
        response.headers['Last-Modified'] = datetime.fromtimestamp(last_modified).strftime('%a, %d %b %Y %H:%M:%S GMT')

    return response

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

    pcap_source = os.path.join(work, 'user_interaction.pcap')
    if os.path.exists(pcap_source):
        pcap_dir = os.path.join(BASE_DIR, "pcap", brand, firmware, "http")
        os.makedirs(pcap_dir, exist_ok=True)
        pcap_dest = os.path.join(pcap_dir, "user_interaction.pcap")
        shutil.copy(pcap_source, pcap_dest)
        print(f"[INFO] PCAP copied to {pcap_dest} - use Analysis button to analyze")
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

    # Remove the row from schedule.csv
    rows = read_csv_rows(SCHEDULE_CSV)
    updated_rows = []
    for r in rows:
        if r.get('container_name') == cname:
            continue
        updated_rows.append(r)

    with open(SCHEDULE_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(SCHEDULE_HEADER)
        for r in updated_rows:
            writer.writerow([r[h] for h in SCHEDULE_HEADER])

    if status != "paused":
        work = os.path.join(SCRATCH_DIR, 'run', run_id)

        pcap_source = os.path.join(work, 'user_interaction.pcap')
        if os.path.exists(pcap_source):
            pcap_dir = os.path.join(BASE_DIR, "pcap", brand, firmware, "http")
            os.makedirs(pcap_dir, exist_ok=True)
            pcap_dest = os.path.join(pcap_dir, get_next_name(pcap_dir, "user_interaction")+".pcap")
            shutil.copy(pcap_source, pcap_dest)
            print(f"[INFO] PCAP copied to {pcap_dest} - use Analysis button to analyze")

    return jsonify({"status": "stopped"}), 200

@app.route('/select', methods=['POST'])
def select() -> Response:
    brandId    = request.args.get('brandId')
    firmwareId = request.args.get('firmwareId')
    runId      = request.args.get('runId')
    binaryId   = request.args.get('binaryId')
    dataChannelId = request.args.get('dataChannelId')
    ignoreAddr = request.args.get('ignoreAddr', '0') == '1'

    try:
        exec_data_pairs = [
            {
                "brand_id": brandId,
                "firmware_id": firmwareId,
                "run_id": runId,
                "executable_id": binaryId,
                "data_channel_id": dataChannelId,
                "ignore_addr": ignoreAddr
            }
        ]
    except (TypeError, KeyError) as e:
        return jsonify({"status": "error", "message": f"Invalid select payload: {e}"}), 400

    json_path = os.path.join(TMP_DIR, 'exec_data_pairs.json')
    try:
        with open(json_path, 'w') as jf:
            json.dump(exec_data_pairs, jf, indent=2)
    except OSError as e:
        return jsonify({"status": "error",
                        "message": f"Could not write exec-data file: {e}"}), 500

    append_csv_row(
        SCHEDULE_CSV,
        SCHEDULE_HEADER,
        ["", "", "", "1", "select", os.path.join(brandId, firmwareId), ""]
    )

    success = run_container(SCHEDULE_CSV, LOGICAL_TO_PAIR, PAIR_TO_LOGICAL, None)
    if not success:
        return jsonify({"status": "error",
                        "message": "Container launch failed"}), 500

    try:
        with open(SCHEDULE_CSV, newline='') as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                if (row.get('mode') == 'select' and
                    row.get('status') == 'running' and
                    row.get('firmware') == os.path.join(brandId, firmwareId)):
                    container_name = row.get('container_name')
                    if container_name:
                        cleanup_progress_file_for_container(container_name)
                    break
    except Exception as e:
        print(f"Warning: Failed to cleanup progress file: {e}")

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
        TMP_DIR, "select_analysis", "results",
        brand_id, firmware_id,
        run_id, os.path.basename(binary_id),
        sanitize_data_channel_id(data_channel_id), "results.json"
    )

    if not os.path.isfile(file_path):
        return jsonify({
            "error": "Not found",
            "message": f"File not found: {file_path}"
        }), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
            if isinstance(results, dict) and "entries" in results:
                data = results["entries"]
            else:
                data = results
    except (OSError, json.JSONDecodeError) as e:
        return jsonify({
            "error": "Server error",
            "message": f"Failed to read or parse results.json: {e}"
        }), 500

    return jsonify(data), 200

def compute_select_analyses_data(brand_id_filter=None, firmware_id_filter=None, run_id_filter=None, binary_id_filter=None):
    running = []
    done = []

    # --- Collect Running ---
    try:
        ensure_experiment_consistency(SCHEDULE_CSV)
        rows = read_csv_rows(SCHEDULE_CSV)

        for row in rows:
            if (not row.get("status") or not row.get("mode") or not row.get("container_name")):
                continue
            if row["status"].lower() == "running" and row["mode"] == "select":
                container = row["container_name"]
                json_path = os.path.join(TMP_DIR, "select_analysis", "infos", f"{container}.json")
                metadata = None

                if os.path.isfile(json_path):
                    try:
                        with open(json_path, "r") as f:
                            metadata = json.load(f)
                    except (json.JSONDecodeError, OSError):
                        pass

                if metadata is None:
                    exec_pairs_path = os.path.join(TMP_DIR, "exec_data_pairs.json")
                    if os.path.isfile(exec_pairs_path):
                        try:
                            with open(exec_pairs_path, "r") as f:
                                exec_pairs = json.load(f)
                            
                            if exec_pairs and len(exec_pairs) > 0:
                                pair = exec_pairs[0]
                                metadata = {
                                    "brandId": pair.get("brand_id"),
                                    "firmwareId": pair.get("firmware_id"),
                                    "runId": pair.get("run_id"),
                                    "binaryId": pair.get("executable_id"),
                                    "dataChannelId": pair.get("data_channel_id")
                                }
                        except (json.JSONDecodeError, OSError) as e:
                            continue

                if metadata is None:
                    continue

                if brand_id_filter and metadata.get("brandId") != brand_id_filter:
                    continue
                if firmware_id_filter and metadata.get("firmwareId") != firmware_id_filter:
                    continue
                if run_id_filter and metadata.get("runId") != run_id_filter:
                    continue
                if binary_id_filter and metadata.get("binaryId") != binary_id_filter:
                    continue

                running.append({
                    "brandId": metadata.get("brandId"),
                    "firmwareId": metadata.get("firmwareId"),
                    "runId": metadata.get("runId"),
                    "binaryId": metadata.get("binaryId"),
                    "dataChannelId": metadata.get("dataChannelId"),
                    "containerName": container
                })
    except Exception as e:
        return jsonify({"error": "Failed to process running analyses", "message": str(e)}), 500

    # --- Collect Done ---
    try:
        if brand_id_filter and firmware_id_filter:
            base_dir = os.path.join(
                TMP_DIR, "select_analysis", "results",
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

                    if binary_id_filter:
                        binary_ids = [b for b in binary_ids if b == binary_id_filter]

                    for binary_id in binary_ids:
                        data_channels_path = os.path.join(binaries_path, os.path.basename(binary_id))
                        if not os.path.isdir(data_channels_path):
                            continue
                        data_channel_ids = os.listdir(data_channels_path)
                        for sanitized_data_channel_id in data_channel_ids:
                            result_path = os.path.join(binaries_path, binary_id, sanitized_data_channel_id, "results.json")
                            if os.path.isfile(result_path):
                                try:
                                    with open(result_path, 'r') as f:
                                        result_data = json.load(f)
                                        if isinstance(result_data, dict) and "original_data_channel_id" in result_data:
                                            original_data_channel_id = result_data["original_data_channel_id"]
                                        else:
                                            original_data_channel_id = sanitized_data_channel_id
                                except (json.JSONDecodeError, OSError):
                                    original_data_channel_id = sanitized_data_channel_id

                                done.append({
                                    "brandId": brand_id_filter,
                                    "firmwareId": firmware_id_filter,
                                    "runId": run_id,
                                    "binaryId": binary_id,
                                    "dataChannelId": original_data_channel_id
                                })
    except Exception as e:
        return jsonify({"error": "Failed to process done analyses", "message": str(e)}), 500

    return {
        "running": nest_results(running, ["dataChannelId"]),
        "done": nest_results(done, ["dataChannelId"])
    }

@app.route('/select_analyses', methods=['GET'])
def select_analyses() -> Response:
    brand_id_filter = request.args.get("brandId")
    firmware_id_filter = request.args.get("firmwareId")
    run_id_filter = request.args.get("runId")
    binary_id_filter = request.args.get("binaryId")

    cache_key = f"select_analyses:{brand_id_filter}:{firmware_id_filter}:{run_id_filter}:{binary_id_filter}"

    files_to_check = [SCHEDULE_CSV]

    info_dir = os.path.join(TMP_DIR, "select_analysis", "infos")
    if os.path.exists(info_dir):
        info_files = glob.glob(os.path.join(info_dir, "*.json"))
        files_to_check.extend(info_files)

    if brand_id_filter and firmware_id_filter and run_id_filter:
        results_dir = os.path.join(TMP_DIR, "select_analysis", "results", brand_id_filter, firmware_id_filter, run_id_filter)
        if binary_id_filter:
            results_dir = os.path.join(results_dir, binary_id_filter)
        if os.path.exists(results_dir):
            results_files = glob.glob(os.path.join(results_dir, "**", "results.json"), recursive=True)
            files_to_check.extend(results_files)

    # Disable ETag caching for select_analyses to ensure fresh data
    data = compute_select_analyses_data(brand_id_filter, firmware_id_filter, run_id_filter, binary_id_filter)

    response = jsonify(data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response

def get_fuzz_status(container_name: str) -> str:
    if not container_name:
        return "unknown"

    status_file = os.path.join(TMP_DIR, "fuzz_status", f"{container_name}.json")

    if not os.path.exists(status_file):
        return "unknown"

    try:
        with open(status_file, 'r') as f:
            status_data = json.load(f)
        return status_data.get("status", "unknown")
    except (OSError, json.JSONDecodeError):
        return "unknown"

def compute_fuzz_experiments_data(brand_id_filter=None, firmware_id_filter=None):
    running_experiments = []
    done               = []
    seen_running       = set()

    ensure_experiment_consistency(SCHEDULE_CSV)
    rows = read_csv_rows(SCHEDULE_CSV)

    for row in rows:
        if (not row.get("status") or not row.get("mode") or not row.get("firmware")):
            continue
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
        container_name = row.get("container_name", "")

        if exp_name not in seen_running:
            status = get_fuzz_status(container_name)

            running_experiments.append({
                "name": exp_name,
                "container_name": container_name,
                "status": status
            })
            seen_running.add(exp_name)

    try:
        for exp_name in os.listdir(os.path.join(FUZZ_EXP_DIR, brand_id_filter, firmware_id_filter)):
            if exp_name in seen_running:
                continue
            done.append(exp_name)
    except OSError:
        pass

    return {
        "running": running_experiments,
        "done":    done
    }

@app.route('/fuzz_experiments', methods=['GET'])
def fuzz_experiments() -> Response:
    brand_id_filter = request.args.get("brandId")
    firmware_id_filter = request.args.get("firmwareId")

    cache_key = f"fuzz_experiments:{brand_id_filter}:{firmware_id_filter}"

    files_to_check = [SCHEDULE_CSV]

    if brand_id_filter and firmware_id_filter:
        exp_dir = os.path.join(FUZZ_EXP_DIR, brand_id_filter, firmware_id_filter)
        if os.path.exists(exp_dir):
            for exp_name in os.listdir(exp_dir):
                exp_path = os.path.join(exp_dir, exp_name)
                if os.path.isdir(exp_path):
                    for root, dirs, files in os.walk(exp_path):
                        for file in files[:10]:  # Limit to avoid too many files
                            files_to_check.append(os.path.join(root, file))

    current_etag, last_modified = generate_etag_for_files(files_to_check)

    client_etag = request.headers.get('If-None-Match')
    if check_etag_match(client_etag, current_etag):
        response = Response('', 304)
        response.headers['ETag'] = current_etag
        return response

    data = get_cached_or_compute(
        cache_key,
        lambda: compute_fuzz_experiments_data(brand_id_filter, firmware_id_filter)
    )

    response = jsonify(data)
    response.headers['ETag'] = current_etag
    if last_modified > 0:
        response.headers['Last-Modified'] = datetime.fromtimestamp(last_modified).strftime('%a, %d %b %Y %H:%M:%S GMT')

    return response

@app.route('/execute', methods=['POST'])
def execute():
    try:
        brandId    = request.args.get('brandId')
        firmwareId = request.args.get('firmwareId')
        request_data = request.json 
        experiments_data_json = json.dumps(request_data, indent=2)

        print(request_data)

        os.environ["EXPERIMENTS_DATA"] = experiments_data_json

        os.makedirs(TMP_DIR, exist_ok=True)
        fuzz_pars_path = os.path.join(TMP_DIR, "fuzz_pars.json")
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
        ["", "", "", "1", "fuzz", os.path.join(brandId, firmwareId), ""]
    )

    success = run_container(SCHEDULE_CSV, LOGICAL_TO_PAIR, PAIR_TO_LOGICAL, os.path.join(FUZZ_EXP_DIR, brandId, firmwareId))
    if not success:
        return jsonify({"status": "error",
                        "message": "Container launch failed"}), 500

    try:
        with open(SCHEDULE_CSV, newline='') as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                if (row.get('mode') == 'fuzz' and
                    row.get('status') == 'running' and
                    row.get('firmware') == os.path.join(brandId, firmwareId)):
                    container_name = row.get('container_name')
                    if container_name:
                        cleanup_progress_file_for_container(container_name)
                    break
    except Exception as e:
        print(f"Warning: Failed to cleanup progress file: {e}")

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
        TMP_DIR, 'select_analysis', 'results',
        brand, firmware, run_id, os.path.basename(binary), sanitize_data_channel_id(data_channel)
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
        TMP_DIR, 'select_analysis', 'results',
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
    combined = os.path.join(brand_id, firmware_id)

    if not all([brand_id, firmware_id, exp_name]):
        return jsonify({
            "error": "Missing parameter",
            "message": "You must provide brandId, firmwareId, and expName"
        }), 400

    def is_running_exp(exp_name: str):
        try:
            with open(SCHEDULE_CSV, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                if reader.fieldnames is None:
                    print(f"Warning: CSV file {SCHEDULE_CSV} has no headers or is empty", file=sys.stderr)
                    return (False, None)

                for row in reader:
                    if row.get("exp_name") == exp_name:
                        container_name = row.get("container_name")
                        if row.get("status", "").lower() == "running":
                            return (True, row.get("container_name"))
                        else:
                            return (False, None)
                return (False, None)
        except Exception as e:
            print(f"Error reading schedule file: {e}")
            return (False, None)
    ret = is_running_exp(exp_name)
    running = ret[0]
    container_name = ret[1]

    if running:
        iid = get_id(combined, container_name)
        if not iid:
            print(f"Warning: Could not get IID for firmware {combined} with container {container_name}", file=sys.stderr)
            return jsonify({
                "error": "Server error",
                "message": f"Could not find experiment ID for running container {container_name}"
            }), 500

        work_dir = os.path.join(
            FIRMAE_DIR,
            "scratch",
            container_name,
            iid
        )
        exp_dir = os.path.join(work_dir, "outputs")
        exp_info_path = os.path.join(work_dir, "outputs", "exp_info.json")
        fuzzer_stats_path = os.path.join(work_dir, "outputs", "fuzzer_stats")
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

@app.route('/select_progress/<container_name>', methods=['GET'])
def get_select_progress(container_name: str) -> Response:
    progress_file = os.path.join(TMP_DIR, "progress", f"{container_name}.json")

    # Generate ETag based on the progress file
    files_to_check = [progress_file] if os.path.exists(progress_file) else []
    current_etag, last_modified = generate_etag_for_files(files_to_check)

    # Check if client ETag matches current ETag
    client_etag = request.headers.get('If-None-Match')
    if check_etag_match(client_etag, current_etag):
        response = Response('', 304)
        response.headers['ETag'] = current_etag
        return response

    if not os.path.exists(progress_file):
        response_data = {
            "phase": "unknown",
            "progress": 0.0,
            "message": "No progress data available"
        }
        response = jsonify(response_data)
        response.headers['ETag'] = current_etag
        return response, 200

    try:
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)
        response = jsonify(progress_data)
        response.headers['ETag'] = current_etag
        return response
    except (OSError, json.JSONDecodeError) as e:
        response_data = {
            "phase": "error",
            "progress": 0.0,
            "message": f"Failed to read progress data: {e}"
        }
        response = jsonify(response_data)
        response.headers['ETag'] = current_etag
        return response, 500

@app.route('/fuzz_progress/<container_name>', methods=['GET'])
def get_fuzz_progress(container_name: str) -> Response:
    """Get progress information for a fuzz experiment container."""
    progress_file = os.path.join(TMP_DIR, "progress", f"{container_name}.json")

    # Generate ETag based on the progress file
    files_to_check = [progress_file] if os.path.exists(progress_file) else []
    current_etag, last_modified = generate_etag_for_files(files_to_check)

    # Check if client ETag matches current ETag
    client_etag = request.headers.get('If-None-Match')
    if check_etag_match(client_etag, current_etag):
        response = Response('', 304)
        response.headers['ETag'] = current_etag
        return response

    if not os.path.exists(progress_file):
        response_data = {
            "phase": "unknown",
            "progress": 0.0,
            "message": "No progress data available"
        }
        response = jsonify(response_data)
        response.headers['ETag'] = current_etag
        return response, 200

    try:
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)
        response = jsonify(progress_data)
        response.headers['ETag'] = current_etag
        return response
    except (OSError, json.JSONDecodeError) as e:
        response_data = {
            "phase": "error",
            "progress": 0.0,
            "message": f"Failed to read progress data: {e}"
        }
        response = jsonify(response_data)
        response.headers['ETag'] = current_etag
        return response, 500

def get_pcap_files(brand: str, firmware: str) -> List[str]:
    pcap_dir = os.path.join(BASE_DIR, "pcap", brand, firmware, "http")
    if not os.path.isdir(pcap_dir):
        return []

    pcap_files = []
    for file in os.listdir(pcap_dir):
        if file.endswith('.pcap') or file.endswith('.pcapng'):
            pcap_files.append(file)

    return sorted(pcap_files)

def save_emulation_pcap(brand: str, firmware: str, run_id: str, pcap_data: bytes) -> bool:
    try:
        pcap_dir = os.path.join(BASE_DIR, "pcap", brand, firmware, "http")
        os.makedirs(pcap_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"emulation_run_{run_id}_{timestamp}.pcap"
        filepath = os.path.join(pcap_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(pcap_data)

        return True
    except Exception as e:
        print(f"Error saving PCAP: {e}")
        return False

@app.route("/pcaps")
def list_pcaps() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")

    if not brand or not firmware:
        return jsonify({"status": "error", "message": "Missing brandId or firmwareId parameter"}), 400

    try:
        pcap_files = get_pcap_files(brand, firmware)
        return jsonify({"brand": brand, "firmwareId": firmware, "pcap": pcap_files}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to list PCAP files: {e}"}), 500


@app.route("/remove_pcap", methods=["POST"])
def remove_pcap() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")
    pcap_name = request.args.get("pcapName")

    if not brand or not firmware or not pcap_name:
        return jsonify({"status": "error", "message": "Missing required parameters"}), 400

    try:
        pcap_path = os.path.join(BASE_DIR, "pcap", brand, firmware, "http", pcap_name)

        if not os.path.exists(pcap_path):
            return jsonify({"status": "error", "message": "PCAP file not found"}), 404

        os.remove(pcap_path)
        return jsonify({"status": "success", "message": f"PCAP file '{pcap_name}' removed successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to remove PCAP file: {e}"}), 500

@app.route("/analyze_pcap", methods=["POST"])
def analyze_pcap() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")
    pcap_name = request.args.get("pcapName")

    if not brand or not firmware or not pcap_name:
        return jsonify({"status": "error", "message": "Missing required parameters"}), 400

    try:
        pcap_path = os.path.join(BASE_DIR, "pcap", brand, firmware, "http", pcap_name)

        if not os.path.exists(pcap_path):
            return jsonify({"status": "error", "message": "PCAP file not found"}), 404

        combined = os.path.join(brand, firmware)

        if os.path.isfile(SCHEDULE_CSV):
            with open(SCHEDULE_CSV, newline='') as fp:
                reader = csv.DictReader(fp)
                for row in reader:
                    if (row.get('mode') == 'pcap_replay' and
                        row.get('firmware') == combined and
                        row.get('status') == 'running'):
                        return jsonify({"status": "error", "message": "PCAP replay already running for this firmware"}), 400

        append_csv_row(SCHEDULE_CSV, SCHEDULE_HEADER, ["", "", "", "1", "pcap_replay", combined, pcap_name])
        success = run_container(SCHEDULE_CSV, LOGICAL_TO_PAIR, PAIR_TO_LOGICAL, None)

        if success:
            container_name = None
            if os.path.isfile(SCHEDULE_CSV):
                with open(SCHEDULE_CSV, newline='') as fp:
                    reader = csv.DictReader(fp)
                    for row in reader:
                        if (row.get('mode') == 'pcap_replay' and
                            row.get('firmware') == combined and
                            row.get('status') == 'running'):
                            container_name = row.get('container_name')
                            break

            if container_name:
                cleanup_progress_file_for_container(container_name)

            return jsonify({
                "status": "success",
                "message": f"Started PCAP replay analysis for {pcap_name}",
                "pcap_name": pcap_name,
                "firmware": combined,
                "container_name": container_name
            }), 200
        else:
            return jsonify({"status": "error", "message": "Failed to start PCAP replay analysis"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to analyze PCAP file: {e}"}), 500

@app.route("/stop_pcap_replay", methods=["POST"])
def stop_pcap_replay() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")
    pcap_name = request.args.get("pcapName")

    if not brand or not firmware or not pcap_name:
        return jsonify({"status": "error", "message": "Missing required parameters"}), 400

    try:
        combined = os.path.join(brand, firmware)
        rows = read_csv_rows(SCHEDULE_CSV)
        updated_rows = []
        container_to_remove = None

        for r in rows:
            if (
                r.get("mode") == "pcap_replay"
                and r.get("pcap_name") == pcap_name
                and r.get("firmware") == combined
            ):
                container_to_remove = r.get("container_name")
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

        return jsonify({"status": "success", "message": f"Stopped PCAP replay analysis for {pcap_name}"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to stop PCAP replay: {e}"}), 500

@app.route("/progress/<container_name>", methods=["GET"])
def get_progress(container_name: str) -> Response:
    progress_file = os.path.join(TMP_DIR, "progress", f"{container_name}.json")

    if not os.path.exists(progress_file):
        return jsonify({"error": "Progress not found"}), 404

    try:
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)
        return jsonify(progress_data), 200
    except (OSError, json.JSONDecodeError) as e:
        return jsonify({"error": f"Failed to read progress: {e}"}), 500

def compute_pcap_replay_progress(brand: str, firmware: str, pcap_name: str) -> dict:
    combined = os.path.join(brand, firmware)

    rows = read_csv_rows(SCHEDULE_CSV)
    for row in rows:
        if (row.get("firmware") == combined and
            row.get("mode") == "pcap_replay" and
            row.get("pcap_name") == pcap_name and
            row.get("status") == "running"):

            container_name = row.get("container_name")
            progress_file = os.path.join(TMP_DIR, "progress", f"{container_name}.json")
            if os.path.exists(progress_file):
                try:
                    with open(progress_file, 'r') as f:
                        progress_data = json.load(f)
                    progress_data["container_name"] = container_name
                    return progress_data
                except (OSError, json.JSONDecodeError):
                    pass

            return {
                "phase": "starting",
                "progress": 0.0,
                "message": "Analysis is starting...",
                "container_name": container_name,
                "timestamp": datetime.now().isoformat()
            }

    return {"status": "not_running"}

@app.route("/pcap_replay_progress", methods=["GET"])
def get_pcap_replay_progress() -> Response:
    brand = request.args.get("brandId")
    firmware = request.args.get("firmwareId")
    pcap_name = request.args.get("pcapName")

    if not brand or not firmware or not pcap_name:
        return jsonify({"status": "error", "message": "Missing brandId, firmwareId, or pcapName parameter"}), 400

    cache_key = f"pcap_replay_progress:{brand}:{firmware}:{pcap_name}"

    combined = os.path.join(brand, firmware)
    files_to_check = [SCHEDULE_CSV]

    rows = read_csv_rows(SCHEDULE_CSV)
    for row in rows:
        if (row.get("firmware") == combined and
            row.get("mode") == "pcap_replay" and
            row.get("pcap_name") == pcap_name and
            row.get("status") == "running"):
            container_name = row.get("container_name")
            if container_name:
                progress_file = os.path.join(TMP_DIR, "progress", f"{container_name}.json")
                if os.path.exists(progress_file):
                    files_to_check.append(progress_file)
            break

    current_etag, last_modified = generate_etag_for_files(files_to_check)

    client_etag = request.headers.get('If-None-Match')
    if check_etag_match(client_etag, current_etag):
        response = Response('', 304)
        response.headers['ETag'] = current_etag
        return response

    data = get_cached_or_compute(
        cache_key,
        lambda: compute_pcap_replay_progress(brand, firmware, pcap_name)
    )

    response = jsonify(data)
    response.headers['ETag'] = current_etag
    if last_modified > 0:
        response.headers['Last-Modified'] = datetime.fromtimestamp(last_modified).strftime('%a, %d %b %Y %H:%M:%S GMT')

    return response


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

    if not os.path.exists("tmp"):
        os.makedirs("tmp")

    with open("tmp/cpu_ids.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["CPU ID", "Physical ID", "Logical ID"])
        for node, core, cpu in rows:
            writer.writerow([node, core, cpu])

    print("Wrote", len(rows), "rows to cpu_ids.csv")

    try:
        with open("tmp/cpu_ids.csv") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                print("Warning: CPU IDs CSV file has no headers or is empty", file=sys.stderr)
            else:
                for row in reader:
                    cpu_id = int(row["CPU ID"])
                    physical_id = int(row["Physical ID"])
                    logical_id = int(row["Logical ID"])
                    pair = (cpu_id, physical_id)

                    LOGICAL_TO_PAIR[logical_id] = pair
                    PAIR_TO_LOGICAL[pair].append(logical_id)
    except (OSError, csv.Error, ValueError, KeyError) as e:
        print(f"Error reading CPU IDs CSV file: {e}", file=sys.stderr)

    ensure_server_directories()
    app.run(host='0.0.0.0', port=4000)