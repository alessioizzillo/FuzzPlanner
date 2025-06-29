import os
import sys
import random
import subprocess
import fcntl
import csv
import re
import docker
from time import sleep
from typing import Dict, List, Optional, Set, Tuple

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
N_CPU_MAX = os.cpu_count() or 1
CPUS_WHITELIST: Optional[List[int]] = None
RUNTIME_TMP = os.path.join(SCRIPT_DIR, 'runtime_tmp')
AFFINITY_FILE = os.path.join(RUNTIME_TMP, 'affinity.dat')
AFFINITY_LOCK = os.path.join(RUNTIME_TMP, 'affinity.lock')
SCHEDULE_LOCK = os.path.join(RUNTIME_TMP, 'schedule.lock')

def usage_and_exit() -> None:
    print("Usage: python3 experiments.py")
    sys.exit(1)

def lock_file(path: str):
    f = open(path, 'w')
    fcntl.lockf(f, fcntl.LOCK_EX)
    return f

def get_running_containers() -> Dict[int, str]:
    mapping: Dict[int, str] = {}
    
    try:
        for c in docker.from_env().containers.list():
            cpus = c.attrs['HostConfig']['CpusetCpus'].split(',')
            for cpu in cpus:
                idx = int(cpu)
                if 0 <= idx < N_CPU_MAX:
                    mapping[idx] = c.name
    except Exception as e:
        print(f"Error fetching containers: {e}")
        sys.exit(1)
    
    return mapping

def read_affinity() -> Dict[int, str]:
    os.makedirs(RUNTIME_TMP, exist_ok=True)

    if not os.path.exists(AFFINITY_FILE):
        return {i: 'none' for i in range(N_CPU_MAX)}
    
    aff: Dict[int, str] = {}
    
    with open(AFFINITY_FILE) as fp:
        for line in fp:
            parts = line.strip().split(',')
            if len(parts) != 2:
                continue
            try:
                idx = int(parts[0])
                aff[idx] = parts[1]
            except ValueError:
                continue
    
    for i in range(N_CPU_MAX):
        aff.setdefault(i, 'none')
    
    return aff

def write_affinity(aff: Dict[int, str]) -> None:
    with open(AFFINITY_FILE, 'w') as fp:
        for idx, owner in aff.items():
            fp.write(f"{idx},{owner}\n")

def get_free_cpus(aff: Dict[int, str], n: int) -> List[int]:
    free = [cpu for cpu, owner in aff.items() if owner == 'none' and (CPUS_WHITELIST is None or cpu in CPUS_WHITELIST)]
    if len(free) < n:
        print(f"Not enough free CPUs: need {n}, have {len(free)}")
        sys.exit(1)
    random.shuffle(free)
    return free[:n]

def get_first_available_name(existing: Set[str], prefix: str) -> str:
    i = 0
    while f"{prefix}_{i}" in existing:
        i += 1
    return f"{prefix}_{i}"


def assign_names(csv_file: str, idx: int, num_cores: int,
                 container_name: str, exp_dir: Optional[str], mode: str) -> Tuple[Optional[str], str]:
    lock = lock_file(AFFINITY_LOCK)
    aff = read_affinity()
    running = get_running_containers()

    for cpu, owner in list(aff.items()):
        if cpu in running and owner != running[cpu]:
            aff[cpu] = running[cpu]
    write_affinity(aff)
    lock.close()

    mode_map, used = parse_affinity(mode)
    existing = mode_map.get(mode, set())

    if container_name.startswith(f"{mode}_"):
        num = int(container_name.split('_')[-1])
        existing.add(num)

    i = 0
    while i in existing or i in used:
        i += 1
    container_name = f"{mode}_{i}"

    exp_name: Optional[str] = None
    if exp_dir:
        os.makedirs(exp_dir, exist_ok=True)
        existing_dirs = {d for d in os.listdir(exp_dir) if d.startswith('exp_')}
        exp_name = '' if mode == 'check' else get_first_available_name(existing_dirs, 'exp')
        os.makedirs(os.path.join(exp_dir, exp_name), exist_ok=True)

    lock = lock_file(SCHEDULE_LOCK)
    rows = list(csv.reader(open(csv_file, newline='')))
    headers = rows[0]
    
    for h in ('status', 'exp_name', 'container_name'):
        if h not in headers:
            headers.append(h)
    i_status = headers.index('status')
    i_exp = headers.index('exp_name')
    i_cont = headers.index('container_name')

    to_stop = []
    for ridx, row in enumerate(rows[1:], start=1):
        row += [''] * (len(headers) - len(row))
        if row[i_cont] == container_name and row[i_status] == 'running':
            to_stop.append(ridx)
    
    row = rows[idx+1]
    row[i_status] = 'running'
    row[i_cont] = container_name
    row[i_exp] = exp_name or ''
    
    for ridx in to_stop:
        rows[ridx][i_status] = 'stopped'
    
    with open(csv_file, 'w', newline='') as fp:
        csv.writer(fp).writerows(rows)
    
    lock.close()
    
    return exp_name, container_name

def clean_param_name(p: str) -> str:
    return re.sub(r"\s*\(.*?\)", "", p).strip()

def parse_schedule(csv_file: str) -> List[Tuple[str, str, str, str, str, str, str]]:
    lock = lock_file(SCHEDULE_LOCK)
    experiments: List[Tuple[str, str, str, str, str, str, str]] = []
    
    with open(csv_file, newline='') as fp:
        reader = csv.reader(fp)
        headers = [clean_param_name(h) for h in next(reader, [])]
        for row in reader:
            data = dict(zip(headers, row))
            experiments.append((
                data.get('status',''), data.get('exp_name',''), data.get('container_name',''),
                data.get('num_cores',''), data.get('mode',''), data.get('firmware',''),
                data.get('experiments_data_path','')
            ))
    
    lock.close()

    return experiments

def run_experiment(log_to_pair: Dict[int,int], pair_to_log: Dict[int,List[int]],
                   mode: str, firmware: str, exp_path: str,
                   cont_name: str, n_cores: int, exp_data_path: str) -> None:
    lock = lock_file(AFFINITY_LOCK)
    aff = read_affinity()
    free = get_free_cpus(aff, n_cores)
    cpu_ids: List[int] = []
    
    for c in free:
        siblings = pair_to_log.get(log_to_pair.get(c,c), [c])
        for s in siblings:
            cpu_ids.append(s)
            aff[s] = cont_name
    write_affinity(aff)
    lock.close()
    
    cmd_file = os.path.join(RUNTIME_TMP, 'command')
    
    with open(cmd_file, 'w') as f:
        f.write(f"python3 start.py --mode {mode} --firmware {firmware} --container_name {cont_name} --output {exp_path} {exp_data_path}")
    
    script = 'run_exp_host' if mode in ('run','run_capture') else 'run_exp_bridge'
    subprocess.check_call(f"./docker.sh {script} {cont_name} {','.join(map(str,cpu_ids))}", shell=True)
    
    while os.path.exists(cmd_file): sleep(1)

def parse_affinity(mode: Optional[str]=None) -> Tuple[Dict[str,Set[int]], Set[int]]:
    lock = lock_file(AFFINITY_LOCK)
    aff = read_affinity()
    running = get_running_containers()
    mode_map: Dict[str, Set[int]] = {}
    used: Set[int] = set()
    
    for idx, owner in aff.items():
        if owner != 'none':
            m = re.match(r"(.+)_(\d+)", owner)
            if m:
                mode_key, num = m.groups()[0], int(m.groups()[1])
                if mode is None or mode_key == mode:
                    mode_map.setdefault(mode_key, set()).add(num)
                    used.add(num)
    lock.close()
    
    return mode_map, used

def ensure_experiment_consistency(csv_file: str, exp_dir: Optional[str]) -> None:
    lock = lock_file(SCHEDULE_LOCK)
    rows = list(csv.reader(open(csv_file, newline='')))
    headers = rows[0] if rows else []
    valid_rows = [headers]
    existing = set(os.listdir(exp_dir)) if exp_dir and os.path.isdir(exp_dir) else set()
    mode_map, used = parse_affinity()

    for row in rows[1:]:
        if len(row) < len(headers): continue
        status, name, cont, *_ = row
        keep = (
            (status and cont and (status!='running' or int(cont.split('_')[-1]) in used))
            or (row[4] in ('check','run','run_capture') and not name)
            or (name in existing)
        )
        if keep: valid_rows.append(row)
    
    with open(csv_file,'w',newline='') as fp:
        csv.writer(fp).writerows(valid_rows)
    
    if exp_dir and os.path.isdir(exp_dir):
        for d in os.listdir(exp_dir):
            p = os.path.join(exp_dir,d)
            if os.path.isdir(p) and not os.listdir(p): os.rmdir(p)
    
    lock.close()

def run_container(schedule_csv: str, log_to_pair: Dict[int,int], pair_to_log: Dict[int,List[int]], exp_dir: Optional[str]) -> bool:
    ensure_experiment_consistency(schedule_csv, exp_dir)
    exps = parse_schedule(schedule_csv)
    
    for idx, (status, name, cont, cores, mode, fw, data_path) in enumerate(exps):
        if status == '':
            exp_name, cont_name = assign_names(schedule_csv, idx, int(cores), cont, exp_dir, mode)
            if (mode not in {'check','run','run_capture'} and exp_name and cont_name) or (mode in {'check','run','run_capture'} and cont_name):
                run_experiment(log_to_pair, pair_to_log, mode, fw, os.path.join(exp_dir,exp_name) if exp_name else '', cont_name, int(cores), data_path)
    
    return True

def get_container_info(firmware: str, schedule_csv: str) -> Tuple[Optional[str], Optional[str]]:
    ensure_experiment_consistency(schedule_csv, None)
    
    if not os.path.isfile(schedule_csv): return None, None
    
    with open(schedule_csv, newline='') as fp:
        for row in csv.DictReader(fp):
            if row.get('mode') in ('run','run_capture') and row.get('firmware')==firmware:
                return row.get('status'), row.get('container_name')
    
    return None, None

def clear_non_running(schedule_csv: str) -> None:
    if not os.path.isfile(schedule_csv): return
    
    ensure_experiment_consistency(schedule_csv, None)
    lock = lock_file(SCHEDULE_LOCK)
    kept = []
    
    for row in csv.reader(open(schedule_csv, newline='')):
        if row and row[0] in ('running','pause') or row and row[0]=='status':
            kept.append(row)
    
    with open(schedule_csv,'w',newline='') as fp:
        csv.writer(fp).writerows(kept)
    
    lock.close()

def update_schedule_status(schedule_csv: str, status: str,
                           exp_name: Optional[str]=None,
                           container_name: Optional[str]=None) -> None:
    if not os.path.isfile(schedule_csv): return
    
    lock = lock_file(SCHEDULE_LOCK)
    rows = list(csv.reader(open(schedule_csv, newline='')))
    headers = rows[0]
    i_stat = headers.index('status')
    i_exp = headers.index('exp_name')
    i_cont = headers.index('container_name')

    if not exp_name and container_name:
        for r in rows[1:]:
            if r[i_cont]==container_name:
                exp_name = r[i_exp]
                break
    
    for r in rows[1:]:
        if (exp_name and r[i_exp]==exp_name) or (not exp_name and container_name and r[i_cont]==container_name):
            r[i_stat]=status
    
    with open(schedule_csv,'w',newline='') as fp:
        csv.writer(fp).writerows(rows)
    
    lock.close()