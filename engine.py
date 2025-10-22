import os
import sys
import csv
import re
import signal
import shutil
import subprocess
import fcntl
import stat
import time
import argparse
from typing import Optional, List
import pyshark
import json
from datetime import datetime
from FirmAE.scripts.util import check_connection, get_iid
import dpkt
import socket
from collections import defaultdict

FACT_IP = "http://192.168.30.177"
FACT_PORT = "5000"
BASE_DIR = os.getcwd()
TMP_DIR = os.path.join(BASE_DIR, "tmp")
FIRMAE_DIR = os.path.join(BASE_DIR, "FirmAE")
PCAP_DIR = os.path.join(BASE_DIR, "pcap")
TAINT_DIR = os.path.join(BASE_DIR, "taint_analysis")
FIRMWARE_DIR = os.path.join(BASE_DIR, "firmwares")
FIRM_SOURCES_DIR = os.path.join(BASE_DIR, "firm_sources")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
SCHEDULE_CSV = os.path.join(TMP_DIR, "schedule.csv")
LOCK_DIR = TMP_DIR

FULL_PERM = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO

HTTP_METHODS = [b"GET", b"POST", b"PUT", b"DELETE", b"HEAD", b"OPTIONS", b"PATCH", b"TRACE", b"CONNECT"]

def replay_pcap_requests(pcap_path, target_ip, port=80, timeout=5, container_name=None):
    results = []
    request_count = 0

    with open(pcap_path, "rb") as f:
        pcap = dpkt.pcap.Reader(f)
        sessions = defaultdict(list)

        for ts, buf in pcap:
            try:
                eth = dpkt.ethernet.Ethernet(buf)
                if not isinstance(eth.data, dpkt.ip.IP):
                    continue
                ip = eth.data
                if not isinstance(ip.data, dpkt.tcp.TCP):
                    continue
                tcp = ip.data
                if len(tcp.data) == 0:
                    continue

                session_key = (ip.src, tcp.sport, ip.dst, tcp.dport)
                sessions[session_key].append((ts, tcp.seq, bytes(tcp.data)))

            except Exception as e:
                print(f"[DEBUG] Skipping packet due to exception: {e}")
                continue

        total_http_requests = sum(1 for session_key, packets in sessions.items() if packets and any(b''.join([pkt[2] for pkt in packets]).startswith(method) for method in HTTP_METHODS))

        for session_key, packets in sessions.items():
            if not packets:
                continue

            packets.sort(key=lambda x: x[1])
            session_data = b''.join([pkt[2] for pkt in packets])

            if any(session_data.startswith(method) for method in HTTP_METHODS):
                request_count += 1

                if container_name:
                    progress = 0.8 + (0.15 * request_count / total_http_requests)
                    update_progress(container_name, "analyzing", progress, f"Replaying request {request_count}/{total_http_requests}...")

                try:
                    print(f"[*] Replaying HTTP request {request_count}")

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)

                    sock.connect((target_ip, port))

                    sock.send(session_data)

                    response = b""
                    try:
                        while True:
                            chunk = sock.recv(4096)
                            if not chunk:
                                break
                            response += chunk
                    except socket.timeout:
                        pass

                    sock.close()

                    results.append({
                        'request_size': len(session_data),
                        'response_size': len(response),
                        'success': True
                    })

                    print(f"[+] Request {request_count} completed: {len(session_data)} bytes sent, {len(response)} bytes received")

                    time.sleep(0.5)

                except Exception as e:
                    print(f"[!] Error replaying request {request_count}: {e}")
                    results.append({
                        'request_size': len(session_data),
                        'response_size': 0,
                        'success': False,
                        'error': str(e)
                    })

    return results, request_count

def sanitize_data_channel_id(data_channel_id: str) -> str:
    if not data_channel_id:
        return data_channel_id

    sanitized = data_channel_id.replace('/', '_')
    return sanitized

def ensure_runtime_directories():
    directories = [
        os.path.join(TMP_DIR),
        os.path.join(TMP_DIR, "progress"),
        os.path.join(TMP_DIR, "select_analysis"),
        os.path.join(TMP_DIR, "select_analysis", "infos"),
        os.path.join(TMP_DIR, "select_analysis", "results")
    ]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            print(f"Warning: Could not create directory {directory}: {e}", file=sys.stderr)

def update_fuzz_status(container_name: str, status: str):
    status_dir = os.path.join(TMP_DIR, "fuzz_status")

    try:
        os.makedirs(status_dir, exist_ok=True)
    except OSError as e:
        print(f"Warning: Could not create fuzz_status directory {status_dir}: {e}", file=sys.stderr)
        return

    status_file = os.path.join(status_dir, f"{container_name}.json")
    data = {
        "status": status,
        "timestamp": datetime.now().isoformat()
    }

    try:
        with open(status_file, 'w') as f:
            json.dump(data, f, indent=2)
    except (OSError, IOError) as e:
        print(f"Warning: Could not write fuzz_status file {status_file}: {e}", file=sys.stderr)

def update_progress(container_name: str, phase: str, progress: float, message: str, details: dict = None):
    progress_dir = os.path.join(TMP_DIR, "progress")

    try:
        os.makedirs(progress_dir, exist_ok=True)
    except OSError as e:
        print(f"Warning: Could not create progress directory {progress_dir}: {e}", file=sys.stderr)
        return

    progress_file = os.path.join(progress_dir, f"{container_name}.json")
    data = {
        "container_name": container_name,
        "phase": phase,
        "progress": progress,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }

    try:
        with open(progress_file, 'w') as f:
            json.dump(data, f, indent=2)
    except (OSError, IOError) as e:
        print(f"Warning: Could not write progress file {progress_file}: {e}", file=sys.stderr)

    if phase in ["booting", "fuzzing"]:
        update_fuzz_status(container_name, phase)


def give_all_permissions_recursively(path):
    for root, dirs, files in os.walk(path):
        for dir_ in dirs:
            os.chmod(os.path.join(root, dir_), 0o777)
        for file_ in files:
            os.chmod(os.path.join(root, file_), 0o777)
    os.chmod(path, 0o777)

def load_experiment(json_path: str) -> dict:
    if not os.path.exists(json_path):
        print(f"Error: exec-data JSON not found at {json_path}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(json_path, 'r') as jf:
            exp = json.load(jf)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Failed to load/parse {json_path}: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        pass
    
    return exp

def export_env_vars(exp: dict):
    os.environ["TARGET_EXECUTABLE"] = str(exp.get("executableId"))
    os.environ["TARGET_CHANNEL"]    = str(exp.get("data_channel_id"))

    params = exp.get("chosen_parameters", {})
    os.environ["TARGET_PC"]        = str(params.get("pc"))
    os.environ["TARGET_SYSCALL"]   = str(params.get("syscall"))
    os.environ["TARGET_PATTERN"]   = str(params.get("pattern", ""))
    os.environ["IGNORE_ADDR"]      = "1" if exp.get("ignore_addr", False) else "0"

    print(f'export TARGET_EXECUTABLE="{exp.get("executableId")}"')
    print(f'export TARGET_CHANNEL="{exp.get("data_channel_id")}"')
    print(f'export TARGET_PC="{params.get("pc")}"')
    print(f'export TARGET_SYSCALL="{params.get("syscall")}"')
    print(f'export TARGET_PATTERN="{params.get("pattern", "")}"')
    print(f'export IGNORE_ADDR="{1 if exp.get("ignore_addr", False) else 0}"')

    for feature in exp.get("set_engine_features", []):
        name  = feature.get("name")
        ftype = feature.get("type")
        value = feature.get("value")
        if not name or not value or (ftype == "boolean" and value == "false"):
            continue
        if ftype == "boolean" and value == "true":
            os.environ[name] = ""
            print(f'export {name}')
        else:
            os.environ[name] = str(value)
            print(f'export {name}="{value}"')

def prepare_fuzzing_env(work_dir: str, pattern: bytes, out_dir: str):
    for subdir in ["inputs", "outputs"]:
        target = os.path.join(work_dir, subdir)
        print("TARGET TO REMOVE:", target)
        if os.path.exists(target):
            shutil.rmtree(target, ignore_errors=True)
        os.makedirs(target)

    if out_dir:
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir, ignore_errors=True)
        os.makedirs(out_dir)        
    
    seed_path = os.path.join(work_dir, "inputs", "seed")
    with open(seed_path, "wb") as f:
        f.write(pattern)

    mt = os.path.join(work_dir, "mapping_table")
    if os.path.exists(mt):
        os.remove(mt)

def setup_mounts(work_dir: str) -> None:
    dev_dir       = os.path.join(work_dir, "dev")
    proc_host_dir = os.path.join(work_dir, "proc_host")

    os.makedirs(dev_dir, exist_ok=True)
    os.makedirs(proc_host_dir, exist_ok=True)

    def bind(src: str, dest: str):
        """Crea il file dest e poi fa mount --bind src->dest."""
        try:
            open(dest, 'a').close()
        except OSError as e:
            print(f"Warning: cannot create {dest}: {e}", file=sys.stderr)
            return
        subprocess.run(
            ["sudo", "-E", "mount", "--bind", src, dest],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    bind("/dev/null", os.path.join(dev_dir, "null"))

    bind("/dev/urandom", os.path.join(dev_dir, "urandom"))

    stat_path = os.path.join(proc_host_dir, "stat")
    try:
        open(stat_path, 'a').close()
    except OSError as e:
        if e.errno == 22:
            print(f"Warning: cannot create {stat_path} (Invalid argument): {e}", file=sys.stderr)
            return
        else:
            raise
    subprocess.run(
        ["sudo", "-E", "mount", "--bind", "/proc/stat", stat_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

def set_permissions_recursive(path: str) -> None:
    for root, dirs, files in os.walk(path):
        for d in dirs:
            os.chmod(os.path.join(root, d), FULL_PERM)
        for f in files:
            os.chmod(os.path.join(root, f), FULL_PERM)

def lock_file(lock_path: str):
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    f = open(lock_path, 'w')
    fcntl.lockf(f, fcntl.LOCK_EX)
    
    return f

def remove_schedule_entry(csv_path: str, exp_name: Optional[str] = None,
                          container_name: Optional[str] = None) -> None:
    if not os.path.isfile(csv_path):
        return
    
    lock_path = os.path.join(LOCK_DIR, "schedule.lock")
    lock = lock_file(lock_path)
    rows = []
    
    with open(csv_path, newline='') as infile:
        reader = csv.reader(infile)
        header = next(reader, [])
        rows.append(header)
        idx_exp = header.index("exp_name") if "exp_name" in header else -1
        idx_cont = header.index("container_name") if "container_name" in header else -1
        for row in reader:
            if (exp_name and idx_exp >= 0 and row[idx_exp] == exp_name) or \
               (container_name and idx_cont >= 0 and row[idx_cont] == container_name):
                continue
            rows.append(row)
    
    with open(csv_path, 'w', newline='') as outfile:
        csv.writer(outfile).writerows(rows)
    
    lock.close()

def cleanup(work_dir: str) -> None:
    print("[*] Cleanup Procedure...")
    shutil.rmtree(os.path.join(work_dir, "debug"), ignore_errors=True)
    
    for mount in ("dev/null", "dev/urandom", "proc_host/stat"):
        subprocess.run(["sudo", "-E", "umount", f"{work_dir}/{mount}"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    current = os.getpid()
    parents = set()
    pid = current
    
    while pid != 1:
        try:
            ppid = int(subprocess.check_output(["ps", "-p", str(pid), "-o", "ppid=" ]).strip())
            if ppid in (pid, 0):
                break
            parents.add(ppid)
            pid = ppid
        except Exception:
            break
    
    for line in subprocess.check_output(["ps", "-e", "-o", "pid=,comm="]).splitlines():
        try:
            pid_str, cmd = line.decode().strip().split(None, 1)
            pid_i = int(pid_str)
            if pid_i in (1, current) or pid_i in parents:
                continue
            os.kill(pid_i, signal.SIGKILL)
        except Exception:
            pass
    
    subprocess.run(["sudo", "-E", os.path.join(FIRMAE_DIR, "flush_interface.sh")],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def send_signal_recursive(pid: int, sig: int, self_pid: Optional[int] = None) -> None:
    if self_pid is None:
        self_pid = os.getpid()
    
    try:
        children = subprocess.check_output(["pgrep", "-P", str(pid)]).split()
        for c in children:
            send_signal_recursive(int(c), sig, self_pid)
    except subprocess.CalledProcessError:
        pass
    
    if pid != self_pid:
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            pass

def fast_copytree(source, destination):
    os.makedirs(destination, exist_ok=True)
    subprocess.run(["rsync", "-a", "--info=progress2", source + "/", destination], check=True)

def replace_pattern_in_file(file_path, pattern, replacement):
    with open(file_path, 'r') as file:
        content = file.read()

    content = re.sub(pattern, replacement, content)

    with open(file_path, 'w') as file:
        file.write(content)

def copy_image(dst_mode, firmware):
    src_iid = subprocess.check_output(["sudo", "-E", "./scripts/util.py", "get_iid", firmware, "0.0.0.0", "run"]).decode('utf-8').strip()

    if not src_iid or not os.path.exists(os.path.join(FIRMAE_DIR, "scratch", "run", src_iid)):
        return False

    mode = "run"
    source_csv = os.path.join(FIRMAE_DIR, f"firm_db_{mode}.csv")
    dst_csv = os.path.join(FIRMAE_DIR, f"firm_db_{dst_mode}.csv")
    os.makedirs(os.path.dirname(dst_csv), exist_ok=True)

    if not os.path.exists(dst_csv):
        with open(dst_csv, mode='w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['id', 'firmware', 'brand', 'arch', 'result'])

    row_to_copy = None
    with open(source_csv, mode='r', newline='', encoding='utf-8') as src_file:
        reader = csv.reader(src_file)
        next(reader)
        for row in reader:
            if row[0] == src_iid:
                row_to_copy = row
                break

    if not row_to_copy:
        return False

    existing_ids = set()
    existing_id = None
    with open(dst_csv, mode='r', newline='', encoding='utf-8') as dst_file:
        reader = csv.reader(dst_file)
        next(reader, None)
        for row in reader:
            if row[0].isdigit():
                existing_ids.add(int(row[0]))
            if row[1] == os.path.basename(firmware):
                existing_id = row[0]

    dst_iid = existing_id if existing_id else str(max(existing_ids) + 1 if existing_ids else 1)

    row_to_copy[0] = dst_iid
    with open(dst_csv, mode='a', newline='', encoding='utf-8') as dst_file:
        writer = csv.writer(dst_file)
        writer.writerow(row_to_copy)

    source_img = os.path.join(FIRMAE_DIR, "scratch", "run", src_iid)
    dest_img = os.path.join(FIRMAE_DIR, "scratch", dst_mode, dst_iid)

    fast_copytree(source_img, dest_img)

    run_file = os.path.join(dest_img, "run.sh")
    if not os.path.islink(run_file.replace(".sh", "_%s.sh" % dst_mode)):
        os.symlink(run_file, run_file.replace(".sh", "_%s.sh" % dst_mode))

    replace_pattern_in_file(run_file, f'IID={src_iid}', f'IID={dst_iid}')

    if "fuzz" in dst_mode:
        suffix = dst_mode.split("fuzz", 1)[1]
        dst_abbr_mode = f"fu{suffix}"
    elif "select" in dst_mode:
        suffix = dst_mode.split("select", 1)[1]
        dst_abbr_mode = f"se{suffix}"
    elif "pcap_replay" in dst_mode:
        suffix = dst_mode.split("pcap_replay", 1)[1]
        dst_abbr_mode = f"pr{suffix}"
    else:
        assert(0)

    replace_pattern_in_file(run_file, '_run_', f'_{dst_abbr_mode}_')
    replace_pattern_in_file(run_file, f'_{src_iid}', f'_{dst_iid}')
    
    prev_dir = os.getcwd()
    os.chdir(BASE_DIR)
    subprocess.run(["sudo", "-E", "python3", os.path.join(BASE_DIR, "update_executables.py"), dst_mode])
    os.chdir(prev_dir)

    return True

def get_pcap_protocol(pcap_file: str) -> str:
    cap = pyshark.FileCapture(pcap_file)
    layers = [pkt.layers[3].layer_name for pkt in cap if len(pkt.layers) >= 4]
    layers = [l for l in layers if l != "DATA"]
    
    return layers[0] if layers and all(l == layers[0] for l in layers) else ("mixed" if layers else "none")

def get_next_name(dir_path: str, prefix: str) -> str:
    os.makedirs(dir_path, exist_ok=True)
    max_i = -1

    for fname in os.listdir(dir_path):
        m = re.match(rf"{prefix}_(\d+)", fname)
        if m:
            max_i = max(max_i, int(m.group(1)))
    
    return f"{prefix}_{max_i + 1}"

def get_dict_types(directory: str) -> str:
    dict_types = []
    for filename in os.listdir(directory):
        if filename.endswith(".dict"):
            seed_type = os.path.splitext(filename)[0]
            dict_types.append(f'"{seed_type}"')
    
    return ",".join(dict_types)


def check(firmware: str, mode: str) -> str:    
    iid = ""
    subprocess.run(["sudo", "-E", "./flush_interface.sh"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not subprocess.run(["sudo", "-E", "./scripts/util.py", "check_connection", "_", "0.0.0.0", mode], stdout=subprocess.PIPE).returncode == 0:
        if not subprocess.run(["sudo", "-E", "./scripts/util.py", "check_connection", "_", "0.0.0.0", mode], stdout=subprocess.PIPE).returncode == 0:
            print("[\033[31m-\033[0m] docker container failed to connect to the hosts' postgresql!")
            exit(1)

    iid = subprocess.check_output(["sudo", "-E", "./scripts/util.py", "get_iid", firmware, "0.0.0.0", mode]).decode('utf-8').strip()
    result = subprocess.check_output(["sudo", "-E", "./scripts/util.py", "get_result", iid, "0.0.0.0", mode]).decode('utf-8').strip() if iid else ""
    
    if iid == "" or not os.path.exists(os.path.join(FIRMAE_DIR, "scratch", mode, iid)) or result != 'true':
        if any(mode.startswith(m) for m in {"run", "run_capture", "check"}):
            subprocess.run(["sudo", "-E", "./run.sh", "-c", os.path.basename(os.path.dirname(firmware)), os.path.join(FIRMWARE_DIR, firmware), "run", "0.0.0.0"])
        else:
            if not copy_image(mode, firmware):
                print("\033[32m[+]\033[0m\033[32m[+]\033[0m FirmAE: Creating Firmware Scratch Image")
                os.environ["EXECUTION_MODE"] = "0"
                subprocess.run(["sudo", "-E", "./run.sh", "-c", os.path.basename(os.path.dirname(firmware)), os.path.join(FIRMWARE_DIR, firmware), "run", "0.0.0.0"])            
                copy_image(mode, firmware)

    iid = subprocess.check_output(["sudo", "-E", "./scripts/util.py", "get_iid", firmware, "0.0.0.0", mode]).decode('utf-8').strip()

    return iid

def pcap_replay(firmware: str, container_name: str = None, pcap_name: str = None) -> None:
    if not pcap_name:
        print("Error: No PCAP file specified for replay")
        return

    iid = check(firmware, container_name)
    if not iid:
        return

    work_dir = os.path.join(FIRMAE_DIR, "scratch", container_name, iid)
    shutil.rmtree(os.path.join(work_dir, "debug"), ignore_errors=True)
    web_check = os.path.join(work_dir, "web_check")
    if not os.path.isfile(web_check) or "true" not in open(web_check).read():
        return

    if container_name:
        update_progress(container_name, "booting", 0.0, f"Starting PCAP replay analysis for {pcap_name}...")

    brand = os.path.basename(os.path.dirname(firmware))
    firmware_name = os.path.basename(firmware)
    pcap_path = os.path.join(BASE_DIR, "pcap", brand, firmware_name, "http", pcap_name)

    if not os.path.exists(pcap_path):
        print(f"Error: PCAP file not found: {pcap_path}")
        if container_name:
            update_progress(container_name, "error", 0.0, f"PCAP file not found: {pcap_name}")
        return

    if os.path.exists(os.path.join(work_dir, "webserver_ready")):
        os.remove(os.path.join(work_dir, "webserver_ready"))

    shutil.rmtree(os.path.join(work_dir, "debug"), ignore_errors=True)
    os.environ["EXECUTION_MODE"] = "1"

    if container_name:
        update_progress(container_name, "booting", 0.2, f"Starting firmware emulation for PCAP replay...")

    cmd = ["sudo", "-E", "./run.sh", "-r", os.path.basename(os.path.dirname(firmware)), firmware, container_name, "0.0.0.0"]
    process = subprocess.Popen(cmd)
    time_to_wait = float(open(os.path.join(work_dir, "time_web")).read().strip())

    if container_name:
        update_progress(container_name, "booting", 0.4, f"Booting firmware ({int(time_to_wait)}s remaining)...")
        for elapsed in range(int(time_to_wait)):
            time.sleep(1)
            progress = 0.4 + (0.6 * elapsed / time_to_wait)  # 0.4 to 1.0
            remaining = int(time_to_wait - elapsed)
            update_progress(container_name, "booting", progress, f"Booting firmware ({remaining}s remaining)...")
    else:
        time.sleep(time_to_wait)

    qemu_pid = process.pid
    print(f"[*] Booting firmware, wait {int(time_to_wait)} seconds...")

    target_ip = open(os.path.join(work_dir, "ip")).read().strip()
    print(f"[+] Target IP: {target_ip}")

    print("[*] Waiting for web service to be ready...")
    max_retries = 100
    retry_count = 0
    service_ready = False
    web_port = 80

    ports_to_try = [80]

    while retry_count < max_retries and not service_ready:
        for port in ports_to_try:
            try:
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_sock.settimeout(1)
                result = test_sock.connect_ex((target_ip, port))
                test_sock.close()

                if result == 0:
                    service_ready = True
                    web_port = port
                    print(f"[+] Web service is ready on {target_ip}:{port}")
                    break

            except Exception as e:
                continue

        if not service_ready:
            print(f"[*] Web service not ready yet, retrying... ({retry_count + 1}/{max_retries})")
            retry_count += 1
            time.sleep(2)

    if not service_ready:
        print(f"[!] Web service failed to start after {max_retries} attempts")
        print(f"[!] Tried ports: {ports_to_try}")
        if container_name:
            update_progress(container_name, "error", 0.0, "Web service failed to start")
        send_signal_recursive(qemu_pid, signal.SIGINT)
        try:
            os.waitpid(qemu_pid, 0)
        except:
            pass
        return

    print("[+] Web service READY!")
    ready_flag = os.path.join(work_dir, "webserver_ready")
    open(ready_flag, 'w').close()

    if container_name:
        update_progress(container_name, "analyzing", 0.7, "Web service ready, starting PCAP replay...")

    results, request_count = replay_pcap_requests(pcap_path, target_ip, port=web_port, timeout=5, container_name=container_name)

    if request_count == 0:
        print("[!] No HTTP requests found in PCAP file")
        if container_name:
            update_progress(container_name, "error", 0.0, "No HTTP requests found in PCAP file")
        return

    successful_requests = sum(1 for r in results if r['success'])
    print(f"[+] PCAP replay completed: {successful_requests}/{request_count} requests successful")

    if container_name:
        update_progress(container_name, "analyzing", 0.9, f"PCAP replay completed, starting analysis...")

    try:
        print("[*] Running post-replay analysis...")

        combined = f"{brand}/{firmware_name}"
        analysis_dir = os.path.join(TMP_DIR, "analysis", "results", combined, "dynamic_analysis")

        def next_run_folder(base_dir: str) -> str:
            if os.path.isdir(base_dir):
                runs = [d for d in os.listdir(base_dir) if d.startswith("run_")]
                if runs:
                    nums = [int(r.split("_")[1]) for r in runs]
                    return f"run_{max(nums) + 1}"
            return "run_0"

        out = os.path.join(analysis_dir, next_run_folder(analysis_dir))
        os.makedirs(out, exist_ok=True)

        script = os.path.join(BASE_DIR, "scripts", "analysis.py")

        cmd = [
            "python3", script, combined, out,
            os.path.join(work_dir, "full_system_syscall.log"),
            os.path.join(work_dir, "image_backup"),
            os.path.join(FIRM_SOURCES_DIR, combined),
            FACT_IP, FACT_PORT, "None"
        ]

        pcap_dest = os.path.join(out, "user_interaction.pcap")
        if container_name:
            update_progress(container_name, "analyzing", 0.95, "Copying PCAP file to analysis directory...")
        shutil.copy(pcap_path, pcap_dest)

        cmd_str = " ".join(cmd)
        print(f"[*] Analysis command: {cmd_str}")

        subprocess.run(cmd_str, shell=True)
        print("[+] Analysis started")

    except Exception as e:
        print(f"[!] Error starting analysis: {e}")

    if container_name:
        update_progress(container_name, "completed", 1.0, f"PCAP replay and analysis completed: {successful_requests}/{request_count} requests successful")

    send_signal_recursive(qemu_pid, signal.SIGINT)
    try:
        os.waitpid(qemu_pid, 0)
    except:
        pass
    time.sleep(2)

def run(firmware: str, capture: bool, container_name: str = None) -> None:
    iid = check(firmware, "run")

    if not iid:
        return

    work_dir = os.path.join(FIRMAE_DIR, "scratch", "run", iid)
    shutil.rmtree(os.path.join(work_dir, "debug"), ignore_errors=True)
    web_check = os.path.join(work_dir, "web_check")

    if not os.path.isfile(web_check) or "true" not in open(web_check).read():
        return

    if container_name:
        update_progress(container_name, "booting", 0.0, "Preparing emulation environment...")

    if os.path.exists(os.path.join(work_dir, "webserver_ready")):
        os.remove(os.path.join(work_dir, "webserver_ready"))

    shutil.rmtree(os.path.join(work_dir, "debug"), ignore_errors=True)
    os.environ["EXECUTION_MODE"] = "1"

    if capture:
        brand = os.path.basename(os.path.dirname(firmware))
        firmware_name = os.path.basename(firmware)
        pcap_dir = os.path.join(BASE_DIR, "pcap", brand, firmware_name, "http")
        os.environ["ENABLE_PCAP"] = "true"
        os.environ["PCAP_OUTPUT_DIR"] = pcap_dir
        if container_name:
            update_progress(container_name, "booting", 0.2, "Starting firmware emulation with network capture...")
    else:
        os.environ["ENABLE_PCAP"] = "false"
        if container_name:
            update_progress(container_name, "booting", 0.2, "Starting firmware emulation...")

    cmd = ["sudo", "-E", "./run.sh", "-r", os.path.basename(os.path.dirname(firmware)), firmware, "run", "0.0.0.0"]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time_to_wait = float(open(os.path.join(work_dir, "time_web")).read().strip())

    if container_name:
        update_progress(container_name, "booting", 0.4, f"Booting firmware ({int(time_to_wait)}s remaining)...")
        for elapsed in range(int(time_to_wait)):
            time.sleep(1)
            progress = 0.4 + (0.6 * elapsed / time_to_wait)  # 0.4 to 1.0
            remaining = int(time_to_wait - elapsed)
            update_progress(container_name, "booting", progress, f"Booting firmware ({remaining}s remaining)...")
    else:
        time.sleep(time_to_wait)

    print("[+] Web service READY!")
    ready_flag = os.path.join(work_dir, "webserver_ready")
    open(ready_flag, 'w').close()

    if container_name:
        mode_str = "capture mode" if capture else "mode"
        update_progress(container_name, "fuzzing", 1.0, f"Emulation ready in {mode_str}")

    if capture:
        if container_name:
            update_progress(container_name, "fuzzing", 1.0, "Starting packet capture...")
        interface = f"tap_run_{iid}_0"
        target_ip = open(os.path.join(work_dir, "ip")).read().strip()
        pcap_path = os.path.join(work_dir, "user_interaction.pcap")
        
        blacklist_keywords = ".gif .jpg .png .css .js .ico .htm .html"  # Static resources to filter out
        whitelist_keywords = "POST PUT .php .cgi .xml"  # Important request types and endpoints
        try:
            cmd = ["sudo", "-E", "python3", os.path.join(SCRIPTS_DIR, "capture_packets.py"),
                interface, target_ip, pcap_path, blacklist_keywords, whitelist_keywords]
            subprocess.run(cmd, check=True)
        except:
            pass
        if container_name:
            update_progress(container_name, "completed", 1.0, "Packet capture completed")
        os.kill(proc.pid, signal.SIGINT)

    os.waitpid(proc.pid, 0)

    if container_name:
        update_progress(container_name, "completed", 1.0, "Emulation completed")

def select(container_name: str, firmware: str) -> None:
    run_id   = check(firmware, container_name)
    work_dir = os.path.join(FIRMAE_DIR, "scratch", container_name, run_id)
    shutil.rmtree(os.path.join(work_dir, "debug"), ignore_errors=True)
    json_path = os.path.join(TMP_DIR, 'exec_data_pairs.json')

    if not os.path.exists(json_path):
        print(f"Error: exec-data JSON not found at {json_path}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(json_path, 'r') as jf:
            pairs = json.load(jf)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Failed to load/parse {json_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # try:
    #     os.remove(json_path)
    # except OSError as e:
    #     print(f"Warning: could not delete {json_path}: {e}", file=sys.stderr)

    os.environ["EXECUTION_MODE"] = "1"
    os.environ["DEBUG"] = "1"

    for i, pair in enumerate(pairs):
        os.environ["TARGET_EXECUTABLE"] = os.path.basename(pair["executable_id"])
        os.environ["TARGET_CHANNEL"]    = pair["data_channel_id"]
        os.environ["IGNORE_ADDR"]       = "1" if pair.get("ignore_addr", False) else "0"

        container_name = f"select_{i}"

        running_info_path = os.path.join(TMP_DIR, "select_analysis", "infos", f"{container_name}.json")

        if os.path.exists(running_info_path):
            with open(running_info_path, 'r') as f:
                data = json.load(f)

            running_container_name = data.get("container_name")

            if container_name != running_container_name:
                print(f"Skipping: {container_name} is being processed.", file=sys.stderr)
                continue    

        results_path = os.path.join(TMP_DIR, "select_analysis", "results", pair.get("brand_id"), pair.get("firmware_id"), pair.get("executable_id"), sanitize_data_channel_id(pair.get("data_channel_id")), "results.json")

        if os.path.exists(results_path):
            print(f"Skipping: {container_name} has been already processed.", file=sys.stderr)
            continue

        os.makedirs(os.path.dirname(running_info_path), exist_ok=True)
        metadata = {
            "container_name": container_name,
            "brandId": pair.get("brand_id"),
            "firmwareId": pair.get("firmware_id"),
            "runId": pair.get("run_id"),
            "binaryId": os.path.basename(pair.get("executable_id")),
            "dataChannelId": pair.get("data_channel_id")
        }
        
        with open(running_info_path, "w") as f:
            json.dump(metadata, f)

        update_progress(container_name, "booting", 0.0, "Starting VM...")

        cmd = [
            "sudo", "-E", "./run.sh",
            "-r", os.path.basename(os.path.dirname(firmware)),
            firmware, container_name, "0.0.0.0"
        ]
        proc = subprocess.Popen(cmd)
        qemu_pid = proc.pid

        time_file = os.path.join(work_dir, "time_web")
        time_to_wait = float(open(time_file).read().strip())

        update_progress(container_name, "booting", 0.2, f"Booting VM ({int(time_to_wait)}s remaining)...")
        for elapsed in range(int(time_to_wait)):
            time.sleep(1)
            progress = 0.2 + (0.8 * elapsed / time_to_wait)  # 0.2 to 1.0
            remaining = int(time_to_wait - elapsed)
            update_progress(container_name, "booting", progress, f"Booting VM ({remaining}s remaining)...")

        update_progress(container_name, "replaying", 0.0, "VM ready, starting packet replay...")
        print("[+] Web service READY!")

        replay_pcap = os.path.join(
            TMP_DIR, "analysis", "results",
            os.path.basename(os.path.dirname(firmware)),
            os.path.basename(firmware),
            "dynamic_analysis", pair["run_id"],
            "user_interaction.pcap"
        )
        target_ip = open(os.path.join(work_dir, "ip")).read().strip()

        update_progress(container_name, "replaying", 0.0, "Starting packet replay...")
        subprocess.run(
            ["python3", os.path.join(SCRIPTS_DIR, "replay_packets.py"),
             replay_pcap, target_ip, work_dir, container_name],
            check=True
        )

        time.sleep(5)
        send_signal_recursive(qemu_pid, signal.SIGKILL)
        proc.wait()

        update_progress(container_name, "processing", 0.0, "Analyzing execution traces...")
        fork_log = os.path.join(work_dir, "forkpoints.log")
        seen = set()
        entries = []
        
        if os.path.exists(fork_log):
            total_lines = 0
            skipped_empty = 0
            skipped_invalid = 0
            skipped_placeholder = 0
            skipped_duplicate = 0

            for line_num, line in enumerate(open(fork_log), 1):
                total_lines += 1
                line = line.strip()
                if not line:
                    skipped_empty += 1
                    continue

                parts = line.split(",")
                if len(parts) < 3:
                    print(f"Warning: Invalid forkpoint entry at line {line_num}: {line}", file=sys.stderr)
                    skipped_invalid += 1
                    continue

                syscall, pc, pattern = parts[:3]

                syscall = syscall.strip()
                pc = pc.strip()
                pattern = pattern.strip()

                if not syscall or not pc or not pattern:
                    print(f"Warning: Skipping forkpoint with empty data at line {line_num}: syscall='{syscall}', pc='{pc}', pattern='{pattern}'", file=sys.stderr)
                    skipped_invalid += 1
                    continue

                if pattern.lower() == '':
                    print(f"Warning: Skipping forkpoint with placeholder pattern at line {line_num}: '{pattern}'", file=sys.stderr)
                    skipped_placeholder += 1
                    continue

                key = (pc.lower(), pattern.lower())
                if key in seen:
                    skipped_duplicate += 1
                    continue

                seen.add(key)
                entries.append({
                    "syscall": syscall,
                    "pc": pc,
                    "pattern": pattern
                })
            
            out_path = os.path.join(
                TMP_DIR, "select_analysis", "results",
                os.path.basename(os.path.dirname(firmware)),
                os.path.basename(firmware),
                pair["run_id"], os.path.basename(pair["executable_id"]),
                sanitize_data_channel_id(pair["data_channel_id"]), "results.json"
            )
            os.makedirs(os.path.dirname(out_path), exist_ok=True)

            # Create results structure with original data channel ID metadata
            results = {
                "original_data_channel_id": pair["data_channel_id"],
                "sanitized_data_channel_id": sanitize_data_channel_id(pair["data_channel_id"]),
                "entries": entries
            }

            with open(out_path, "w") as outf:
                json.dump(results, outf, indent=2)

            update_progress(container_name, "completed", 1.0, f"Analysis completed: {len(entries)} execution points found")

        if os.path.exists(running_info_path):
            try:
                os.remove(running_info_path)
            except OSError as e:
                print(f"Warning: could not delete {running_info_path}: {e}", file=sys.stderr)

        try:
            progress_file = f"tmp/progress/{container_name}.json"
            if os.path.exists(progress_file):
                os.remove(progress_file)
        except OSError as e:
            print(f"Warning: Could not remove progress file {progress_file}: {e}", file=sys.stderr)

def fuzz(firmware: str, out_dir: str, container_name: str) -> bool:
    run_id   = check(firmware, container_name)
    json_path = os.path.join(TMP_DIR, 'fuzz_pars.json')
    exp = load_experiment(json_path)

    # if os.path.exists(json_path):
    #     try:
    #         os.remove(json_path)
    #     except OSError as e:
    #         print(f"Warning: could not delete {json_path}: {e}", file=sys.stderr)

    export_env_vars(exp)

    iid = str(check(firmware, container_name))
    work_dir = os.path.join(FIRMAE_DIR, "scratch", container_name, iid)
    shutil.rmtree(os.path.join(work_dir, "debug"), ignore_errors=True)

    if "true" not in open(os.path.join(work_dir, "web_check")).read():
        print("Web check failed, skipping fuzz", file=sys.stderr)
        return False

    memf = os.path.join(work_dir, "mem_file")
    if os.path.exists(memf):
        os.remove(memf)
    sleep_duration = float(open(os.path.join(work_dir, "time_web")).read().strip())

    os.environ["EXECUTION_MODE"] = "2"
    os.environ["FUZZ"] = "1"
    # os.environ["DEBUG"] = "1"
    setup_mounts(work_dir)

    status = open("/proc/self/status").read()
    m = re.search(r"Cpus_allowed_list:\s*([0-9]+)", status)
    cpu_to_bind = m.group(1) if m else None
    if cpu_to_bind:
        print("CPU_TO_BIND:", cpu_to_bind)
    else:
        print("Warning: CPU_TO_BIND not found", file=sys.stderr)

    params      = exp.get("chosen_parameters", {})
    pat_str     = params.get("pattern", "")
    pattern     = pat_str.encode('utf-8').decode('unicode_escape').encode('latin1')

    dict_path = os.path.join(BASE_DIR, "config", "dictionaries",
                             f"{exp.get('chosen_dictionary_type')}")

    prepare_fuzzing_env(work_dir, pattern, out_dir)

    exp_info = {
        "brandId": os.path.basename(os.path.dirname(firmware)),
        "firmwareId": os.path.basename(firmware),
        "runId": exp["runId"],
        "executableId": exp["executableId"],
        "dataChannelId": exp["data_channel_id"],
        "syscall": params.get("syscall"),
        "pc": params.get("pc"),
        "pattern": str(pattern)
    }
    os.makedirs(os.path.join(work_dir, "outputs"), exist_ok=True)
    with open(os.path.join(work_dir, "outputs", "exp_info.json"), "w+", encoding="utf-8") as out:
        json.dump(exp_info, out, indent=4, ensure_ascii=False)

    update_progress(container_name, "booting", 0.0, "Starting fuzz experiment...")

    qemu_proc = subprocess.Popen(
        ["sudo","-E","./run.sh",
         "-r", os.path.basename(os.path.dirname(firmware)),
         os.path.join(FIRMWARE_DIR, firmware),
         container_name,"0.0.0.0"]
    )

    time.sleep(5)
    system_pid = None
    try:
        result = subprocess.check_output(
            ["pgrep", "-f", "qemu-system"],
            text=True
        ).strip()

        if result:
            pids = result.split('\n')
            for pid in pids:
                try:
                    cmdline = open(f"/proc/{pid}/cmdline", 'r').read()
                    if "qemu-system" in cmdline and container_name in cmdline:
                        system_pid = pid
                        break
                except:
                    continue

            if not system_pid and pids:
                system_pid = pids[0]
    except subprocess.CalledProcessError:
        pass
    except Exception as e:
        print(f"[-] Error finding QEMU system PID: {e}")

    if system_pid:
        print(f"[+] QEMU system PID: {system_pid}")
        with open(os.path.join(work_dir, "system_pid"), 'w') as f:
            f.write(system_pid)
    else:
        print("[-] Warning: Could not determine QEMU system PID")

    for elapsed in range(int(sleep_duration)):
        time.sleep(1)
        progress = 0.1 + (0.3 * elapsed / sleep_duration)
        remaining = int(sleep_duration - elapsed)
        update_progress(container_name, "booting", progress, f"Booting firmware ({remaining}s remaining)...")
    print("[+] Web service READY!")
    update_progress(container_name, "booting", 0.4, "Firmware ready, configuring mapping table...")

    replay_pcap = os.path.join(
        TMP_DIR, "analysis","results",
        os.path.basename(os.path.dirname(firmware)),
        os.path.basename(firmware),
        "dynamic_analysis",
        exp["runId"],
        "user_interaction.pcap"
    )
    target_ip = open(os.path.join(work_dir, "ip")).read().strip()

    replay_proc = subprocess.Popen([
        "python3", os.path.join(SCRIPTS_DIR, "replay_packets.py"),
        replay_pcap, target_ip, work_dir, container_name
    ])

    subprocess.run(["sudo", "-E", "tee", "/proc/sys/kernel/core_pattern"], input=b"core\n", check=True)

    env = os.environ.copy()
    env["AFL_SKIP_CPUFREQ"] = "1"

    prev_dir = os.getcwd()
    os.chdir(work_dir)

    mapping_path = os.path.join(work_dir, "mapping_table")
    while True:
        try:
            with open(mapping_path) as f:
                line_count = sum(1 for _ in f)
        except FileNotFoundError:
            line_count = 0

        if line_count > 20:
            if replay_proc.poll() is None:
                replay_proc.terminate()
                try:
                    replay_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    replay_proc.kill()
                    replay_proc.wait()
            break

        print("mapping_table not ready...")
        time.sleep(2)

    print("\033[32m[+]\033[0m Web server has been reached !")

    if line_count > 20:
        print("\033[32m[+]\033[0m The Mapping Table of the binary program has been configured successfully!")
        update_progress(container_name, "fuzzing", 0.5, "Mapping table configured, starting fuzzing...")
    else:
        print("\033[31m[-]\033[0m Mapping Table is not configured! Without configuration you will have problems later...we are stopping here. See the README to know more")
        sys.exit(1)

    print()
    print("\033[32m[+]\033[0m All set..Now we can start the fuzzer")
    update_progress(container_name, "fuzzing", 0.7, "Starting AFL fuzzer...")

    shutil.copy(dict_path, "keywords")

    with open(os.path.join(TMP_DIR, "select_analysis", "results", firmware, exp["runId"], exp["executableId"], sanitize_data_channel_id(exp["data_channel_id"]), "results.json"), "r") as f:
        results = json.load(f)
        data = results.get("entries", results) if isinstance(results, dict) else results

    executable_name = os.path.basename(exp['executableId'])
    executable_path = None

    try:
        result = subprocess.run(
            ["chroot", ".", "which", executable_name],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            executable_path = result.stdout.strip()
    except Exception as e:
        print(f"Warning: 'which' command failed: {e}")

    if not executable_path:
        try:
            result = subprocess.run(
                ["find", ".", "-type", "f", "-name", executable_name, "-executable"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                found = result.stdout.strip().split('\n')[0]
                executable_path = found[1:] if found.startswith('./') else ('/' + found if not found.startswith('/') else found)
        except Exception as e:
            print(f"Warning: 'find' command failed: {e}")

    if not executable_path:
        print(f"Warning: Could not locate executable '{executable_name}', using original path")
        executable_path = exp['executableId']

    print(f"Using executable path: {executable_path}")

    # Read system_pid from file
    system_pid_file = os.path.join(work_dir, "system_pid")
    system_pid = None
    if os.path.exists(system_pid_file):
        with open(system_pid_file, 'r') as f:
            system_pid = f.read().strip()
        print(f"[+] Using QEMU system PID: {system_pid}")
    else:
        print("[-] Warning: system_pid file not found")

    command = []
    # command += ["gdb", "--batch", "--ex", "set follow-fork-mode child", "--ex", "run", "--ex", "bt", "--args"]
    command += ["chroot", "."]
    command += ["./afl-fuzz"]
    command += ["-m", "none"]
    command += ["-t", "800000+"]
    command += ["-Q"]
    command += ["-i", "inputs"]
    command += ["-o", "outputs"]
    command += ["-x", "keywords"]
    command += ["-b", cpu_to_bind]
    if system_pid:
        command += ["-s", system_pid]  # Pass system PID to afl-fuzz
    command += [executable_path]
    command += ["@@"]

    ret = 1
    try:
        print(" ".join(command))
        subprocess.run(
            command,
            env=env,
            check=True
        )
        ret = True

        if out_dir:
            if os.path.exists(out_dir):
                shutil.rmtree(out_dir)
            shutil.copytree("outputs", out_dir)
            give_all_permissions_recursively(out_dir)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
        ret = False

    os.chdir(prev_dir)

    update_progress(container_name, "completed", 1.0, "Fuzzing experiment completed")

    return ret

def start(mode, firmware, out_dir, container_name, pcap_name=None) -> None:
    os.environ["NO_PSQL"] = "1"
    
    prev_dir = os.getcwd()
    os.chdir(FIRMAE_DIR)

    if mode == "run":
        run(firmware, False, container_name)
    elif mode == "run_capture":
        run(firmware, True, container_name)
    elif mode == "pcap_replay":
        pcap_replay(firmware, container_name, pcap_name)
    elif mode == "select":
        select(container_name, firmware)
    elif mode == "check":
        check(firmware, "run")
    elif mode == "fuzz":
        fuzz(firmware, out_dir, container_name)
    else:
        assert(False)

    os.chdir(prev_dir)

if __name__ == "__main__":
    os.umask(0o000)

    ensure_runtime_directories()

    try:
        if os.path.exists("tmp/command"):
            os.remove("tmp/command")
    except OSError as e:
        print(f"Warning: Could not remove command file: {e}", file=sys.stderr)
    
    parser = argparse.ArgumentParser(description="Launch script")
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        help="Path to the engine features file"
    )
    parser.add_argument(
        "--firmware",
        type=str,
        required=True,
        help="Path to the engine features file"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for experiment results"
    )
    parser.add_argument(
        "--container_name",
        type=str,
        help="Name of the Docker container to spawn"
    )
    parser.add_argument(
        "--pcap_name",
        type=str,
        help="PCAP file name for replay analysis"
    )

    args = parser.parse_args()

    exp_path = os.path.abspath(args.output) if args.output else None
    container_name = args.container_name if args.container_name else None

    start(args.mode, args.firmware, os.path.abspath(args.output) if args.output else None, 
        args.container_name if args.container_name else None, args.pcap_name if args.pcap_name else None)
