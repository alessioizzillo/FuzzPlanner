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
from FirmAE.scripts.util import check_connection, get_iid

BASE_DIR = os.getcwd()
RUNTIME_TMP = os.path.join(BASE_DIR, "runtime_tmp")
FIRMAE_DIR = os.path.join(BASE_DIR, "FirmAE")
PCAP_DIR = os.path.join(BASE_DIR, "pcap")
TAINT_DIR = os.path.join(BASE_DIR, "taint_analysis")
FIRMWARE_DIR = os.path.join(BASE_DIR, "firmwares")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
SCHEDULE_CSV = os.path.join(BASE_DIR, "runtime_tmp", "schedule.csv")
LOCK_DIR = os.path.join(BASE_DIR, "runtime_tmp")

FULL_PERM = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO

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

    print(f'export TARGET_EXECUTABLE="{exp.get("executableId")}"')
    print(f'export TARGET_CHANNEL="{exp.get("data_channel_id")}"')
    print(f'export TARGET_PC="{params.get("pc")}"')
    print(f'export TARGET_SYSCALL="{params.get("syscall")}"')

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

    if container_name in dst_mode:
        suffix = dst_mode.split(container_name, 1)[1]
        dst_abbr_mode = f"fu{suffix}"

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

    if iid == "" or not os.path.exists(os.path.join(FIRMAE_DIR, "scratch", mode, iid)):
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

def run(firmware: str, capture: bool) -> None:
    iid = check(firmware, "run")

    if not iid:
        return
    
    work_dir = os.path.join(FIRMAE_DIR, "scratch", "run", iid)
    web_check = os.path.join(work_dir, "web_check")
    
    if not os.path.isfile(web_check) or "true" not in open(web_check).read():
        return

    if os.path.exists(os.path.join(work_dir, "webserver_ready")):
        os.remove(os.path.join(work_dir, "webserver_ready"))

    shutil.rmtree(os.path.join(work_dir, "debug"), ignore_errors=True)
    os.environ["EXECUTION_MODE"] = "0"
    
    cmd = ["sudo", "-E", "./run.sh", "-r", os.path.basename(os.path.dirname(firmware)), firmware, "run", "0.0.0.0"]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time_to_wait = float(open(os.path.join(work_dir, "time_web")).read().strip())
    time.sleep(time_to_wait)
    
    print("[+] Web service READY!")
    ready_flag = os.path.join(work_dir, "webserver_ready")
    open(ready_flag, 'w').close()

    if capture:
        interface = f"tap_run_{iid}_0"
        target_ip = open(os.path.join(work_dir, "ip")).read().strip()
        pcap_path = os.path.join(work_dir, "user_interaction.pcap")
        cmd = ["sudo", "-E", "python3", os.path.join(SCRIPTS_DIR, "capture_packets.py"), interface, target_ip, pcap_path]
        subprocess.run(cmd, check=True)
        os.kill(proc.pid, signal.SIGINT)
    
    os.waitpid(proc.pid, 0)

def select(container_name: str, firmware: str) -> None:
    run_id   = check(firmware, "run")
    work_dir = os.path.join(FIRMAE_DIR, "scratch", "run", run_id)
    json_path = os.path.join(RUNTIME_TMP, 'exec_data_pairs.json')

    if not os.path.exists(json_path):
        print(f"Error: exec-data JSON not found at {json_path}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(json_path, 'r') as jf:
            pairs = json.load(jf)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Failed to load/parse {json_path}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        os.remove(json_path)
    except OSError as e:
        print(f"Warning: could not delete {json_path}: {e}", file=sys.stderr)

    os.environ["EXECUTION_MODE"] = "1"

    for i, pair in enumerate(pairs):
        os.environ["TARGET_EXECUTABLE"] = os.path.basename(pair["executable_id"])
        os.environ["TARGET_CHANNEL"]    = pair["data_channel_id"]

        container_name = f"select_{i}"

        running_info_path = os.path.join(RUNTIME_TMP, "select_analysis", "infos", f"{container_name}.json")

        if os.path.exists(running_info_path):
            with open(running_info_path, 'r') as f:
                data = json.load(f)

            running_container_name = data.get("container_name")

            if container_name != running_container_name:
                print(f"Skipping: {container_name} is being processed.", file=sys.stderr)
                continue    

        results_path = os.path.join(RUNTIME_TMP, "select_analysis", "results", pair.get("brand_id"), pair.get("firmware_id"), pair.get("executable_id"), pair.get("data_channel_id"), "results.json")

        if os.path.exists(results_path):
            print(f"Skipping: {container_name} has been already processed.", file=sys.stderr)
            continue

        os.makedirs(os.path.dirname(running_info_path), exist_ok=True)
        metadata = {
            "container_name": container_name,
            "brandId": pair.get("brand_id"),
            "firmwareId": pair.get("firmware_id"),
            "runId": pair.get("run_id"),
            "binaryId": pair.get("executable_id"),
            "dataChannelId": pair.get("data_channel_id")
        }
        
        with open(running_info_path, "w") as f:
            json.dump(metadata, f)

        cmd = [
            "sudo", "-E", "./run.sh",
            "-r", os.path.basename(os.path.dirname(firmware)),
            firmware, "run", "0.0.0.0"
        ]
        proc = subprocess.Popen(cmd)
        qemu_pid = proc.pid

        time_file = os.path.join(work_dir, "time_web")
        time_to_wait = float(open(time_file).read().strip())
        time.sleep(time_to_wait)
        print("[+] Web service READY!")

        replay_pcap = os.path.join(
            RUNTIME_TMP, "analysis", "results",
            os.path.basename(os.path.dirname(firmware)),
            os.path.basename(firmware),
            "dynamic_analysis", pair["run_id"],
            "user_interaction.pcap"
        )
        target_ip = open(os.path.join(work_dir, "ip")).read().strip()
        subprocess.run(
            ["python3", os.path.join(SCRIPTS_DIR, "replay_packets.py"),
             replay_pcap, target_ip, work_dir],
            check=True
        )

        time.sleep(5)
        send_signal_recursive(qemu_pid, signal.SIGKILL)
        proc.wait()

        fork_log = os.path.join(work_dir, "debug", "forkpoints.log")
        seen = set()
        entries = []
        
        if os.path.exists(fork_log):
            for line in open(fork_log):
                parts = line.strip().split(",")
                if len(parts) < 3:
                    continue
                syscall, pc, pattern = parts[:3]
                key = (pc, pattern)
                if key in seen:
                    continue
                seen.add(key)
                entries.append({"syscall": syscall, "pc": pc, "pattern": pattern})

            out_path = os.path.join(
                RUNTIME_TMP, "select_analysis", "results",
                os.path.basename(os.path.dirname(firmware)),
                os.path.basename(firmware),
                pair["run_id"], os.path.basename(pair["executable_id"]),
                pair["data_channel_id"], "results.json"
            )
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w") as outf:
                json.dump(entries, outf, indent=2)

        try:
            os.remove(running_info_path)
        except OSError as e:
            print(f"Warning: could not delete {running_info_path}: {e}", file=sys.stderr)

def fuzz(firmware: str, out_dir: str, container_name: str) -> bool:
    run_id   = check(firmware, container_name)
    json_path = os.path.join(RUNTIME_TMP, 'fuzz_pars.json')
    exp = load_experiment(json_path)

    try:
        os.remove(json_path)
    except OSError as e:
        print(f"Warning: could not delete {json_path}: {e}", file=sys.stderr)

    export_env_vars(exp)

    iid = str(check(firmware, container_name))
    work_dir = os.path.join(FIRMAE_DIR, "scratch", container_name, iid)

    if "true" not in open(os.path.join(work_dir, "web_check")).read():
        print("Web check failed, skipping fuzz", file=sys.stderr)
        return False

    memf = os.path.join(work_dir, "mem_file")
    if os.path.exists(memf):
        os.remove(memf)
    sleep_duration = float(open(os.path.join(work_dir, "time_web")).read().strip())

    os.environ["EXECUTION_MODE"] = "2"
    os.environ["FUZZ"] = "1"
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

    subprocess.Popen(
        ["sudo","-E","./run.sh",
         "-r", os.path.basename(os.path.dirname(firmware)),
         os.path.join(FIRMWARE_DIR, firmware),
         container_name,"0.0.0.0"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(sleep_duration)
    print("[+] Web service READY!")

    replay_pcap = os.path.join(
        RUNTIME_TMP, "analysis","results",
        os.path.basename(os.path.dirname(firmware)),
        os.path.basename(firmware),
        "dynamic_analysis",
        exp["runId"],
        "user_interaction.pcap"
    )
    target_ip = open(os.path.join(work_dir, "ip")).read().strip()
    subprocess.run([
        "python3", os.path.join(SCRIPTS_DIR, "replay_packets.py"),
        replay_pcap, target_ip, work_dir
    ], check=True)

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
            break
        time.sleep(2)

    print("\033[32m[+]\033[0m Web server has been reached !")

    if line_count > 20:
        print("\033[32m[+]\033[0m The Mapping Table of the binary program has been configured successfully!")
    else:
        print("\033[31m[-]\033[0m Mapping Table is not configured! Without configuration you will have problems later...we are stopping here. See the README to know more")
        sys.exit(1)

    print()
    print("\033[32m[+]\033[0m All set..Now we can start the fuzzer")

    shutil.copy(dict_path, "keywords")

    with open(os.path.join(RUNTIME_TMP, "select_analysis", "results", firmware, exp["runId"], exp["executableId"], exp["data_channel_id"], "results.json"), "r") as f:
        data = json.load(f)

    command = ["chroot", "."]
    command += ["./afl-fuzz"]
    command += ["-m", "none"]
    command += ["-t", "800000+"]
    command += ["-Q"]
    command += ["-i", "inputs"]
    command += ["-o", "outputs"]
    command += ["-x", "keywords"]
    command += ["-b", cpu_to_bind]
    command += [exp["executableId"]]
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

    return ret

def start(mode, firmware, out_dir, container_name) -> None:
    os.environ["NO_PSQL"] = "1"
    
    prev_dir = os.getcwd()
    os.chdir(FIRMAE_DIR)

    if mode == "run":
        run(firmware, False)
    elif mode == "run_capture":
        run(firmware, True)
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

    if os.path.exists("runtime_tmp/command"):
        os.remove("runtime_tmp/command")
    
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

    args = parser.parse_args()

    exp_path = os.path.abspath(args.output) if args.output else None
    container_name = args.container_name if args.container_name else None

    start(args.mode, args.firmware, os.path.abspath(args.output) if args.output else None, 
        args.container_name if args.container_name else None)
