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

def setup_mounts(work_dir: str) -> None:
    dev_dir = os.path.join(work_dir, "dev")
    proc_host_dir = os.path.join(work_dir, "proc_host")

    os.makedirs(dev_dir, exist_ok=True)
    os.makedirs(proc_host_dir, exist_ok=True)

    # /dev/null
    null_path = os.path.join(dev_dir, "null")
    open(null_path, 'a').close()
    subprocess.run(["sudo", "-E", "mount", "--bind", "/dev/null", null_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # /dev/urandom
    urandom_path = os.path.join(dev_dir, "urandom")
    open(urandom_path, 'a').close()
    subprocess.run(["sudo", "-E", "mount", "--bind", "/dev/urandom", urandom_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # /proc/stat
    stat_dir = os.path.join(proc_host_dir)
    stat_path = os.path.join(stat_dir, "stat")
    open(stat_path, 'a').close()
    subprocess.run(["sudo", "-E", "mount", "--bind", "/proc/stat", stat_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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

def generic_signal_handler(signum, frame) -> None:
    print(f"Received signal {signum}, cleaning up...")
    send_signal_recursive(os.getpid(), signum)
    sys.exit(0)

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

    if "firmafl" in dst_mode:
        suffix = dst_mode.split("firmafl", 1)[1]
        dst_abbr_mode = f"fa{suffix}"

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
    
    shutil.rmtree(os.path.join(work_dir, "debug"), ignore_errors=True)
    os.environ["EXECUTION_MODE"] = "0"
    ready_flag = os.path.join(work_dir, "webserver_ready")
    
    open(ready_flag, 'w').close()
    
    cmd = ["sudo", "-E", "./run.sh", "-r", os.path.basename(os.path.dirname(firmware)), firmware, "run", "0.0.0.0"]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time_to_wait = float(open(os.path.join(work_dir, "time_web")).read().strip())
    time.sleep(time_to_wait)
    
    print("[+] Web service READY!")
    
    if capture:
        interface = f"tap_run_{iid}_0"
        target_ip = open(os.path.join(work_dir, "ip")).read().strip()
        pcap_path = os.path.join(work_dir, "user_interaction.pcap")
        cmd = ["sudo", "-E", "python3", os.path.join(SCRIPTS_DIR, "capture_packets.py"), interface, target_ip, pcap_path]
        subprocess.run(cmd, check=True)
        os.kill(proc.pid, signal.SIGINT)
    
    os.waitpid(proc.pid, 0)

def select(firmware: str) -> None:
    work_dir = os.path.join(FIRMAE_DIR, "scratch", "run", check(firmware, "run"))

    exec_data = os.getenv("EXEC_DATA_PAIRS", "")
    if not exec_data:
        print("EXEC_DATA_PAIRS is not set or empty.", file=sys.stderr)
        sys.exit(1)
    try:
        pairs = json.loads(exec_data)
    except json.JSONDecodeError as e:
        print(f"Failed to parse EXEC_DATA_PAIRS JSON: {e}", file=sys.stderr)
        sys.exit(1)

    os.environ["EXECUTION_MODE"] = "1"
    for pair in pairs:
        os.environ["TARGET_EXECUTABLE"] = pair["executable_id"]
        os.environ["TARGET_CHANNEL"] = pair["data_channel_id"]

        cmd = [
            "sudo", "-E", "./run.sh",
            "-r", os.path.basename(os.path.dirname(firmware)),
            firmware, "run", "0.0.0.0"
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        QEMU_PID = proc.pid
        time_to_wait = float(open(os.path.join(work_dir, "time_web")).read().strip())
        time.sleep(time_to_wait)
        
        print("[+] Web service READY!")

        replay_pcap = os.path.join(
            RUNTIME_TMP, "analysis", "results",
            os.path.basename(os.path.dirname(firmware)),
            os.path.basename(firmware),
            "dynamic_analysis", 
            os.getenv("RUN", ""),
            "user_interaction.pcap"
        )
        target_ip = open(os.path.join(work_dir, "ip")).read().strip()
        subprocess.run([
            "python3", os.path.join(SCRIPTS_DIR, "replay_packets.py"),
            replay_pcap, target_ip, work_dir
        ], check=True)

        time.sleep(5)
        send_signal_recursive(QEMU_PID, signal.SIGKILL)
        proc.wait()

        engine_features = json.loads(open(os.path.join(BASE_DIR, "config", "AFL_features.json")).read())
        dict_types = get_dict_types(os.path.join(BASE_DIR, "config", "dictionaries"))

        fork_log = os.path.join(work_dir, "debug", "forkpoints.log")
        seen = set()
        entries = []
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

        body = {
            "engine_features": engine_features,
            "dict_types": json.loads(f"[{dict_types}]"),
            "analysis": [{
                "executable_id": pair["executable_id"],
                "data_channel_id": pair["data_channel_id"],
                "parameters": entries
            }]
        }
        body_str = json.dumps(body, indent=2)

        with open(os.path.join(RUNTIME_TMP, "analysis", "results", os.path.basename(os.path.dirname(firmware)), os.path.basename(firmware), "dynamic_analysis", os.getenv("RUN", ""),"select_result.json"), "w+") as f:
            f.write(body_str)


def fuzz(firmware: str, out_dir: str) -> None:
    raw = os.getenv("EXPERIMENTS_DATA")
    if not raw:
        print("EXPERIMENTS_DATA is not set or empty.", file=sys.stderr)
        return False
    try:
        experiments = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Failed to parse EXPERIMENTS_DATA as JSON: {e}", file=sys.stderr)
        return False

    for exp in experiments:
        executableId       = exp.get("executableId")
        data_channel_id    = exp.get("data_channel_id")
        chosen_dict_type   = exp.get("chosen_dictionary_type")
        fuzzing_timeout    = exp.get("fuzzing_timeout")
        child_timeout      = exp.get("child_timeout")
        params             = exp.get("chosen_parameters", {})
        pc                 = params.get("pc")
        syscall            = params.get("syscall")
        pattern_str = params.get("pattern", "")
        pattern = pattern_str.encode('utf-8').decode('unicode_escape').encode('latin1')

        os.environ["TARGET_EXECUTABLE"] = str(executableId)
        os.environ["TARGET_CHANNEL"]    = str(data_channel_id)
        os.environ["FUZZING_TIMEOUT"]   = str(fuzzing_timeout)
        os.environ["CHILD_TIMEOUT"]     = str(child_timeout)
        os.environ["TARGET_PC"]         = str(pc)
        os.environ["TARGET_SYSCALL"]    = str(syscall)

        dict_path = os.path.join(BASE_DIR, "config", "dictionaries", f"{chosen_dict_type}.dict")

        print(f'export TARGET_EXECUTABLE="{executableId}"')
        print(f'export TARGET_CHANNEL="{data_channel_id}"')
        print(f'export TARGET_PC="{pc}"')
        print(f'export TARGET_SYSCALL="{syscall}"')

        for feature in exp.get("set_engine_features", []):
            name  = feature.get("name")
            ftype = feature.get("type")
            value = feature.get("value")

            if not name:
                continue

            if ftype == "boolean":
                os.environ[name] = ""
                print(f'export {name}')
            else:
                os.environ[name] = str(value)
                print(f'export {name}="{value}"')

    iid = str(check(firmware, "firmafl"))
    work_dir = os.path.join(FIRMAE_DIR, "scratch", "firmafl", iid)

    if "true" not in open(os.path.join(work_dir, "web_check")).read():
        return
    if os.path.exists(os.path.join(work_dir, "mem_file")):
        os.remove(os.path.join(work_dir, "mem_file"))
    with open(os.path.join(work_dir, "time_web"), 'r') as file:
        sleep = file.read().strip()

    os.environ["EXECUTION_MODE"] = "2"
    os.environ["FUZZ"] = "1"

    setup_mounts(work_dir)

    with open("/proc/self/status") as file:
        status_content = file.read()

    cpu_to_bind = re.search(r"Cpus_allowed_list:\s*([0-9]+)", status_content)

    if cpu_to_bind:
        cpu_to_bind_value = cpu_to_bind.group(1)
        print("CPU_TO_BIND:", cpu_to_bind_value)
    else:
        print("CPU_TO_BIND not found in /proc/self/status")

    if out_dir:
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir, ignore_errors=True)
        
        os.makedirs(out_dir)
    else:
        if os.path.exists(os.path.join(work_dir, "outputs")):
            shutil.rmtree(os.path.join(work_dir, "outputs"), ignore_errors=True)
        
        os.makedirs(os.path.join(work_dir, "outputs"))

    if os.path.exists(os.path.join(work_dir, "inputs")):
        shutil.rmtree(os.path.join(work_dir, "inputs"), ignore_errors=True)
    
    os.makedirs(os.path.join(work_dir, "inputs"))

    seed_path = os.path.join(work_dir, "inputs", "seed")
    with open(seed_path, "wb") as f:
        f.write(pattern)

    if os.path.exists(os.path.join(work_dir, "mapping_table")):
        os.remove(os.path.join(work_dir, "mapping_table"))

    cmd = ["sudo", "-E", "./run.sh", "-r", os.path.basename(os.path.dirname(firmware)), os.path.join(FIRMWARE_DIR, firmware), "firmafl", "0.0.0.0"]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time_to_wait = float(open(os.path.join(work_dir, "time_web")).read().strip())
    time.sleep(time_to_wait)
    
    print("[+] Web service READY!")

    replay_pcap = os.path.join(
        RUNTIME_TMP, "analysis", "results",
        os.path.basename(os.path.dirname(firmware)),
        os.path.basename(firmware),
        "dynamic_analysis", 
        os.getenv("RUN", ""),
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

    command = ["chroot", "."]
    command += ["./afl-fuzz"]
    command += ["-m", "none"]
    command += ["-t", "800000+"]
    command += ["-Q"]
    command += ["-i", "inputs"]
    if out_dir:
        command += ["-o", out_dir]
    else:
        command += ["-o", "outputs"]
    command += ["-x", "keywords"]
    command += ["-b", cpu_to_bind_value]
    command += [executableId]
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
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
        ret = False

    os.chdir(prev_dir)

    return ret

def start(mode, firmware, out_dir, container_name, experiments_data_path) -> None:
    os.environ["NO_PSQL"] = "1"
    
    prev_dir = os.getcwd()
    os.chdir(FIRMAE_DIR)

    if mode == "run":
        run(firmware, False, "0")
    elif mode == "run_capture":
        run(firmware, True, "0")
    elif mode == "select":
        select(firmware)
    elif mode == "check":
        check(firmware, "run")
    elif mode == "fuzz":
        fuzz(firmware, out_dir)
    else:
        assert(False)

    os.chdir(prev_dir)

if __name__ == "__main__":
    os.umask(0o000)

    signal.signal(signal.SIGTSTP, generic_signal_handler)
    signal.signal(signal.SIGCONT, generic_signal_handler)

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
        "--experiments_data_path",
        type=str,
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

    if (args.experiments_data_path):
        experiments_data_path = os.path.abspath(args.experiments_data_path)

    exp_path = os.path.abspath(args.output) if args.output else None
    container_name = args.container_name if args.container_name else None

    start(args.mode, args.firmware, os.path.abspath(args.output) if args.output else None, 
        args.container_name if args.container_name else None,
        args.experiments_data_path if args.experiments_data_path else None)
