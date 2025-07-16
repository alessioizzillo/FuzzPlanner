import sys, os
import requests
from pathlib import Path
from tqdm import tqdm
import json, re
import socket
import time
from stats import calculate_border_executables, calculate_interactions_per_kind, generate_processes_graph, generate_binaries_graph, calculate_proprietary_exe, calculate_interesting_border_executables, sort_executables_by_score, calculate_executed_executables_per_kind
from assign_score import assign_score
from views_generator import phase_1A_view_1, phase_1A_view_2, phase_1A_view_3, phase_1B_view_1, phase_1B_view_2, phase_1B_view_3

##################### SETTINGS ######################
firmware_name = None
log_path = None
directory = None
pattern = None
run = None
extracted_firm_path = None
out_dir = None
source_code_path = None

priv_keywords = ["progs.priv"]                    # TO SET. It may be empty ("").
pub_keywords = ["progs.gpl", "apps/public/", "opensource"]      # TO SET. It is always full.

# MIPS_o32
input_syscalls = {'read':'4003', 'readv':'4145', 'recv':'4175', 'recvfrom':'4176', 'recvmsg':'4177', 'recvmmsg':'4335', 'preadv':'4330'}
output_syscalls = {'write':'4004', 'writev':'4146', 'send':'4178', 'sendmsg':'4179', 'sendto':'4180', 'sendfile':'4207', 'sendfile64':'4237', 'sendmmsg':'4343', 'pwritev':'4331', 'splice':'4304', 'tee':'4306'}
dup_syscall = '4041'
dup2_syscall = '4063'
dup3_syscall = '4327'
open_syscall = '4005'
socket_syscall = '4183'
accept_syscall = '4168'
connect_syscall = '4170'
listen_syscall = '4174'
bind_syscall = '4169'
pipe_syscall = '4042'
close_syscall = '4006'
fcntl64_syscall = '4220'
fcntl_syscall = '4055'
#####################################################

######## TEMPORARY DICTIONARIES, LISTS & VARS ########
log = None
open_interactions_dict = {}     # interactions_dict joinable by subsequent reading actors.
sinks_without_sources_dict = {}      # for input/output operations logged in the "wrong" order (due to the scheduler)
interactions_count = 0
proc_fds = {}   # proc_fds = {proc1:{fd1:obj1}, ..}

procs_to_skip = []
#####################################################

################ FINAL DICTIONARIES #################
# Static analysis
executable_files_dict = {}   # executable_files_dict: [ {id: path_binA, is_proprietary: bool, symlink_target: ( null | executable_id ) }, …]
executable_files_path_dict = {}

# Dynamic analysis
processes_dict = {}          # processes_dict: [ { id: PID, parent: PID,  procname: string, executable: executable_id) } ]
data_channels_dict = {}      # data_channels_dict: [ { id: pipe_PID_X_Y_unique, kind: pipe/file/socketTCP/etc, } ]
interactions_dict = {}       # interactions_dict: [ {id : id, channel: channel_id,  sources: [ { id: PID,  }, … ], sinks: [ { id: PID} … ] } ]
#####################################################


def reset_dicts_and_lists():
    global open_interactions_dict
    global sinks_without_sources_dict
    global interactions_count
    global proc_fds
    global processes_dict
    global data_channels_dict
    global interactions_dict

    open_interactions_dict = {}
    sinks_without_sources_dict = {}
    interactions_count = 0
    proc_fds = {}
    processes_dict = {}
    data_channels_dict = {}
    interactions_dict = {}   


def search_dict(dictionary, search_string):
    for key in dictionary:
        if search_string in key or search_string.split(".")[0] in key:
            return dictionary[key]
    return None


def findfiles(path, regex):
    regObj = re.compile(regex)
    res = ""
    for root, dirs, fnames in os.walk(path):
        for fname in fnames:
            if regObj.match(fname):
                res+=os.path.join(root, fname)+"\n"
    return res


def static_analysis():
    global extracted_firm_path
    global source_code_path
    global executable_files_dict
    global executable_files_path_dict

    # List of files
    file_list = [path for path in list(Path(extracted_firm_path).rglob("*")) if (os.path.isfile(path) or os.path.islink(path))]

    bin_name_list = []      # List of the names of the simlinks into the firmware
    sym_name_list = []      # List of the names of the simlinks into the firmware
    bash_script_name_list = []      # List of the names of the bash scripts into the firmware
    sh_script_name_list = []      # List of the names of the shell scripts into the firmware
    php_script_name_list = []      # List of the names of the php scripts into the firmware
    perl_script_name_list = []      # List of the names of the perl scripts into the firmware

    for i in tqdm(range(len(file_list))):
        filepath = file_list[i]
        if os.path.isfile(filepath):
            with open(filepath, "rb") as f:
                type = None
                interpreter = None
                first_bytes = f.read(20)

                if b'\x7fELF' in first_bytes and not os.path.islink(filepath):
                    type = "binary"
                    bin_name_list.append(filepath.name)
                elif os.path.splitext(filepath)[1] == '.php' and not os.path.islink(filepath):
                    type = "script"
                    interpreter = "php"
                    php_script_name_list.append(filepath.name)
                elif (b'#!/bin/sh' in first_bytes or os.path.splitext(filepath)[1] == '.sh') and not os.path.islink(filepath):
                    type = "script"
                    interpreter = "sh"
                    sh_script_name_list.append(filepath.name)
                elif (b'#!/bin/bash"'in first_bytes or os.path.splitext(filepath)[1] == '.sh') and not os.path.islink(filepath):
                    type = "script"
                    interpreter = "bash"
                    bash_script_name_list.append(filepath.name)
                elif b'#!/usr/bin/perl' in first_bytes and not os.path.islink(filepath):
                    type = "script"
                    interpreter = "perl"
                    perl_script_name_list.append(filepath.name)
                else:
                    continue
            
            filepath_name = filepath.name.replace('+','\+')
            matching_files = findfiles(source_code_path, filepath_name)

            if priv_keywords:
                if (sum(matching_files.count(privk) for privk in priv_keywords) >= sum(matching_files.count(pubk) for pubk in pub_keywords)) or "httpd" in filepath_name:
                    executable_files_dict["/"+os.path.relpath(filepath, extracted_firm_path)] = {"type" : type, "interpreter" : interpreter, "is_proprietary" : True, "symlink_target" : None}
                else:
                    executable_files_dict["/"+os.path.relpath(filepath, extracted_firm_path)] = {"type" : type, "interpreter" : interpreter, "is_proprietary" : False, "symlink_target" : None}
            else:
                if (sum(matching_files.count(pubk) for pubk in pub_keywords)) and "httpd" not in filepath_name:
                    executable_files_dict["/"+os.path.relpath(filepath, extracted_firm_path)] = {"type" : type, "interpreter" : interpreter, "is_proprietary" : False, "symlink_target" : None}
                else:
                    executable_files_dict["/"+os.path.relpath(filepath, extracted_firm_path)] = {"type" : type, "interpreter" : interpreter, "is_proprietary" : True, "symlink_target" : None}
            
            executable_files_path_dict[filepath.name] = "/"+os.path.relpath(filepath, extracted_firm_path)

    for i in tqdm(range(len(file_list))):
        filepath = file_list[i]
        if os.path.islink(filepath):
            target = os.readlink(filepath)

            if target[0] != "/":
                sym_name_list.append(filepath.name)
                target = os.readlink(filepath)
                old_cwd = os.getcwd()
                os.chdir(os.path.dirname(filepath))
                target = os.path.abspath(target)
                os.chdir(old_cwd)
                target = "/"+os.path.relpath(target, extracted_firm_path)

            if not os.path.isfile(extracted_firm_path+target):
                continue
            
            if target in executable_files_dict:
                executable_files_dict["/"+os.path.relpath(filepath, extracted_firm_path)] = {"type" : "symlink", "interpreter" : None, "is_proprietary" : executable_files_dict[target]["is_proprietary"], "symlink_target" : target}
            else:    # TO FIX
                print("\nWARNING: target '%s' not found in 'executable_files_dict' (probably there is a symlink of a symlink). '%s' set to 'proprietary = False'"%(target, "/"+os.path.relpath(filepath, extracted_firm_path)))
                executable_files_dict["/"+os.path.relpath(filepath, extracted_firm_path)] = {"type" : "symlink", "interpreter" : None, "is_proprietary" : False, "symlink_target" : target}
            executable_files_path_dict[filepath.name] = "/"+os.path.relpath(filepath, extracted_firm_path)


def open_and_fix_raw_log(log_path):
    global log

    with open(log_path, "rb") as f:
        log = f.read()

    # Identify the position(s) of the invalid byte(s)
    invalid_byte_positions = []
    for i, byte in enumerate(log):
        try:
            bytes([byte]).decode("utf-8")
        except UnicodeDecodeError:
            invalid_byte_positions.append(i)

    # Remove the invalid byte(s)
    log = bytearray(log)
    for position in reversed(invalid_byte_positions):
        del log[position]
    log = log.decode("utf-8")

    log = log.split("\n")[1:-1]
    log = [line.split(",") for line in log]


def dynamic_analysis():
    global executable_files_path_dict
    global open_interactions_dict
    global sinks_without_sources_dict
    global interactions_count
    global proc_fds
    global log
    global procs_to_skip

    for i in tqdm(range(len(log))):
        try:
            err = int(log[i][0])
            ts = int(log[i][1])
            proc_pid = log[i][2]
            proc_par_pid = log[i][3]
            proc_name = log[i][4]
            syscall = log[i][5]
            ret = log[i][6]
            ret2 = log[i][7]
            a0 = log[i][8]
            a1 = log[i][9]
            a2 = log[i][10]
            a3 = log[i][11]
            a4 = log[i][12]
        except:
            print("\nERROR: a malformed line occurred! (line %d: %s)" % (i+2, log[i]))
            exit(1)
        
        if err:
            continue

        if proc_pid in procs_to_skip:
            continue

        if proc_name == "<kernel>":
            continue

        # if log[i][0] == "-1":
        #     continue

        # print("%s (line: %d)!"%(log[i],i+2))

        keys_to_remove = []
        for sink_obj in sinks_without_sources_dict:
            # if sinks_without_sources_dict[sink_obj]["remaining_bytes"] == 0 or sinks_without_sources_dict[sink_obj]["first_ts"]+5 < ts:
            if sinks_without_sources_dict[sink_obj]["remaining_bytes"] == 0:
                if data_channels_dict[sink_obj]["kind"] == "inet_socket" or data_channels_dict[sink_obj]["kind"] == "inet6_socket":
                    sinks_without_sources_dict[sink_obj]["sources"] = []
                data_channels_dict[sink_obj]["used"] = True
                interactions_dict[str(interactions_count)] = {"channel" : sink_obj, "sources" : sinks_without_sources_dict[sink_obj]["sources"], "sinks" : sinks_without_sources_dict[sink_obj]["sinks"]}
                interactions_count += 1
                keys_to_remove.append(sink_obj)
        for key in keys_to_remove:
            del sinks_without_sources_dict[key]

        if (proc_pid not in proc_fds):
            if proc_pid == '1':
                proc_fds[proc_pid] = [proc_name, {'0': 'stdin_%s'%proc_pid, '1': 'stdout_%s'%proc_pid, '2': 'stderr_%s'%proc_pid}]
            else:
                if proc_par_pid in proc_fds:
                    proc_fds[proc_pid] = [proc_name, proc_fds[proc_par_pid][1].copy()]
                else:
                    proc_fds[proc_pid] = [proc_name, {'0': 'stdin_%s'%proc_pid, '1': 'stdout_%s'%proc_pid, '2': 'stderr_%s'%proc_pid}]
                    # print("\nERROR: parent (pid: %s) of the process with pid %s not found (line: %d)!"%(proc_par_pid, proc_pid, i+2))
                    # procs_to_skip.append(proc_pid)
                    # answer = input("Do you want to skip this syscall? (y/n) ")
                    # while(answer != "y" and answer != "n"):
                    #     print()
                    #     answer = input("Do you want to skip this syscall? (y/n) ")
                    # if (answer == "y"):
                    #     continue
                    # else:
                    #     exit(1)

            processes_dict[proc_pid] = {"parent" : proc_par_pid, "procname" : proc_name, "start_time" : ts}
            if proc_name in executable_files_path_dict:
                processes_dict[proc_pid]["executable"] = executable_files_path_dict[proc_name]
            else:
                processes_dict[proc_pid]["executable"] = search_dict(executable_files_path_dict, proc_name)

            if (not processes_dict[proc_pid]["executable"]):
                print("\nSkip pid %s (process name: %s) because it does not match any executable.\n" % (proc_pid, proc_name))
                procs_to_skip.append(proc_pid)
            else:
                if ("firmadyne" in processes_dict[proc_pid]["executable"]):
                    print("\nSkip pid %s (process name: %s) because it belongs to firmadyne.\n" % (proc_pid, proc_name))
                    procs_to_skip.append(proc_pid)

            data_channels_dict['stdin_%s'%proc_pid] = {"kind" : "stdin", "used": False, "listening_pids" : [], "score": 0.0}
        else:
            proc_fds[proc_pid][0] = proc_name
            processes_dict[proc_pid]["procname"] = proc_name
            if proc_name in executable_files_path_dict:
                processes_dict[proc_pid]["executable"] = executable_files_path_dict[proc_name]
            else:
                processes_dict[proc_pid]["executable"] = search_dict(executable_files_path_dict, proc_name)

            if (not processes_dict[proc_pid]["executable"]):
                print("\nSkip pid %s (process name: %s) because it does not match any executable.\n" % (proc_pid, proc_name))
                procs_to_skip.append(proc_pid)
            else:
                if ("firmadyne" in processes_dict[proc_pid]["executable"]):
                    print("\nSkip pid %s (process name: %s) because it belongs to firmadyne.\n" % (proc_pid, proc_name))
                    procs_to_skip.append(proc_pid)

        if syscall == dup_syscall or ((syscall == fcntl64_syscall or syscall == fcntl_syscall) and a1 == '0'):
            try:
                proc_fds[proc_pid][1][ret] = proc_fds[proc_pid][1][a0]
            except:
                print("\nERROR: inconsistence on DUP (line: %d)!"%(i+2))
                print("\nSkip pid %s (process name: %s) because it causes a DUP inconsistence.\n" % (proc_pid, proc_name))
                procs_to_skip.append(proc_pid)

                # answer = input("Do you want to skip this syscall? (y/n) ")
                # while(answer != "y" and answer != "n"):
                #     print()
                #     answer = input("Do you want to skip this syscall? (y/n) ")
                # if (answer == "y"):
                #     continue
                # else:
                #     exit(1)
        
        elif(syscall == dup2_syscall or syscall == dup3_syscall):
            try:
                proc_fds[proc_pid][1][a1] = proc_fds[proc_pid][1][a0]
            except:
                print("\nERROR: inconsistence on DUP2/DUP3 (line: %d)!"%(i+2))
                print("\nSkip pid %s (process name: %s) because it causes a DUP2/DUP3 inconsistence.\n" % (proc_pid, proc_name))
                procs_to_skip.append(proc_pid)
                # answer = input("Do you want to skip this syscall? (y/n) ")
                # while(answer != "y" and answer != "n"):
                #     print()
                #     answer = input("Do you want to skip this syscall? (y/n) ")
                # if (answer == "y"):
                #     continue
                # else:
                #     exit(1)

        elif(syscall == socket_syscall):
            proc_fds[proc_pid][1][ret] = "socket(domain:%s,type:%s,protocol:%s)" % (a0, a1, a2)          

        elif(syscall == bind_syscall or syscall == connect_syscall):
            pattern = r"\{(.+?)\}"
            match = re.search(pattern, proc_fds[proc_pid][1][a0])

            if not match:
                proc_fds[proc_pid][1][a0] += a1
            else:
                proc_fds[proc_pid][1][a0] = re.sub(pattern, a1, proc_fds[proc_pid][1][a0])

            tmp = proc_fds[proc_pid][1][a0]
            if tmp not in data_channels_dict:
                kind = None
                if ("domain:2" in tmp):
                    kind = "inet_socket"
                elif ("domain:10" in tmp):
                    kind = "inet6_socket"
                elif ("domain:16" in tmp):
                    kind = "netlink_socket"
                elif ("domain:17" in tmp):
                    kind = "packet_socket"
                elif ("domain:1" in tmp):
                    kind = "unix_socket"
                else:
                    kind = "unknown_socket" 
                data_channels_dict[proc_fds[proc_pid][1][a0]] = {"kind" : kind, "used" : False, "listening_pids" : [], "score": 0.0}

        elif(syscall == accept_syscall):
            proc_fds[proc_pid][1][ret] = proc_fds[proc_pid][1][a0]

        elif(syscall == listen_syscall):
            if data_channels_dict[proc_fds[proc_pid][1][a0]]["kind"] == "inet_socket" or data_channels_dict[proc_fds[proc_pid][1][a0]]["kind"] == "inet6_socket":
                data_channels_dict[proc_fds[proc_pid][1][a0]]["listening_pids"].append({"time" : ts, "pid" : proc_pid})

        elif(syscall == pipe_syscall):
            proc_fds[proc_pid][1][ret] = 'pipe_%s_%s_%s' % (proc_pid, ret, ret2)
            proc_fds[proc_pid][1][ret2] = 'pipe_%s_%s_%s' % (proc_pid, ret, ret2)
            if proc_fds[proc_pid][1][ret] not in data_channels_dict:
                data_channels_dict[proc_fds[proc_pid][1][ret]] = {"kind" : "pipe", "used": False, "listening_pids" : [], "score": 0.0}    

        elif(syscall == open_syscall):
            kind = None
            if "/sys" in a0 or "/proc" in a0:
                proc_fds[proc_pid][1][ret] = 'virtual_file'+a0
                kind = "virtual_file"
            elif "/dev" in a0:
                proc_fds[proc_pid][1][ret] = 'device'+a0
                kind = "device"
            else:
                proc_fds[proc_pid][1][ret] = 'file'+a0
                kind = "file"
            
            if proc_fds[proc_pid][1][ret] not in data_channels_dict:
                data_channels_dict[proc_fds[proc_pid][1][ret]] = {"kind" : kind, "used": False, "listening_pids" : [], "score": 0.0}  
        
        elif(syscall == close_syscall):
            if ret == 0:
                proc_fds[proc_pid][1].pop(a0)
                for dict_pid in data_channels_dict[proc_fds[proc_pid][1][a0]]["listening_pids"]:
                    if proc_pid == dict_pid["pid"]:
                        data_channels_dict[proc_fds[proc_pid][1][a0]]["listening_pids"].remove(dict_pid)
        
        elif(syscall in input_syscalls.values()):
            if syscall == input_syscalls["recvfrom"] or syscall == input_syscalls["recvmsg"]:
                pattern = r"\{(.+?)\}"
                match = re.search(pattern, proc_fds[proc_pid][1][a0])

                if not match:
                    proc_fds[proc_pid][1][a0] += a4 if syscall == input_syscalls["recvfrom"] else a1
                else:
                    proc_fds[proc_pid][1][a0] = re.sub(pattern, a4 if syscall == input_syscalls["recvfrom"] else a1, proc_fds[proc_pid][1][a0])

                tmp = proc_fds[proc_pid][1][a0]
                if tmp not in data_channels_dict:
                    kind = None
                    if ("domain:2" in tmp):
                        kind = "inet_socket"
                    elif ("domain:10" in tmp):
                        kind = "inet6_socket"
                    elif ("domain:16" in tmp):
                        kind = "netlink_socket"
                    elif ("domain:17" in tmp):
                        kind = "packet_socket"
                    elif ("domain:1" in tmp):
                        kind = "unix_socket"
                    else:
                        kind = "unknown_socket" 
                    data_channels_dict[proc_fds[proc_pid][1][a0]] = {"kind" : kind, "used": False, "listening_pids" : [], "score": 0.0}

                if data_channels_dict[proc_fds[proc_pid][1][a0]]["kind"] == "inet_socket" or data_channels_dict[proc_fds[proc_pid][1][a0]]["kind"] == "inet6_socket":
                    data_channels_dict[proc_fds[proc_pid][1][a0]]["listening_pids"].append({"time" : ts, "pid" : proc_pid})

            obj = proc_fds[proc_pid][1][a0]
            read_bytes = int(ret)
            if obj in open_interactions_dict:
                if read_bytes > 0:
                    if "sinks" not in open_interactions_dict[obj]:
                        open_interactions_dict[obj]["sinks"] = [(ts, proc_pid)]
                    else:
                        if any(proc_pid in t[1] for t in open_interactions_dict[obj]["sinks"]):
                            open_interactions_dict[obj]["sinks"].append((ts, proc_pid))

            else:
                if read_bytes > 0:
                    if obj not in sinks_without_sources_dict:
                        sinks_without_sources_dict[obj] = {"sinks" : [(ts, proc_pid)], "sources" : [], "first_ts" : ts, "remaining_bytes" : read_bytes}
                    else:
                        if any(proc_pid in t[1] for t in sinks_without_sources_dict[obj]["sinks"]):
                            sinks_without_sources_dict[obj]["sinks"].append((ts, proc_pid))
                        sinks_without_sources_dict[obj]["remaining_bytes"]+=read_bytes

        elif(syscall in output_syscalls.values()):
            if syscall == output_syscalls["sendto"] or syscall == output_syscalls["sendmsg"]:
                pattern = r"\{(.+?)\}"
                match = re.search(pattern, proc_fds[proc_pid][1][a0])

                if not match:
                    proc_fds[proc_pid][1][a0] += a4 if syscall == output_syscalls["sendto"] else a1
                else:
                    proc_fds[proc_pid][1][a0] = re.sub(pattern, a4 if syscall == output_syscalls["sendto"] else a1, proc_fds[proc_pid][1][a0])

                tmp = proc_fds[proc_pid][1][a0]
                if tmp not in data_channels_dict:
                    kind = None
                    if ("domain:2" in tmp):
                        kind = "inet_socket"
                    elif ("domain:10" in tmp):
                        kind = "inet6_socket"
                    elif ("domain:16" in tmp):
                        kind = "netlink_socket"
                    elif ("domain:17" in tmp):
                        kind = "packet_socket"
                    elif ("domain:1" in tmp):
                        kind = "unix_socket"
                    else:
                        kind = "unknown_socket" 
                    data_channels_dict[proc_fds[proc_pid][1][a0]] = {"kind" : kind, "used": False, "listening_pids" : [], "score": 0.0}                

            obj = proc_fds[proc_pid][1][a0]

            if "stderr" in obj or "stdout" in obj or data_channels_dict[obj]["kind"] == "inet_socket" or data_channels_dict[obj]["kind"] == "inet6_socket":
                continue

            written_bytes = int(ret)
            # This is not very accurate...
            cont = False
            for sink_obj in sinks_without_sources_dict:
                if sink_obj == obj and sinks_without_sources_dict[sink_obj]["remaining_bytes"] > 0:
                    sinks_without_sources_dict[obj]["sources"].append((ts, proc_pid))
                    sinks_without_sources_dict[sink_obj]["remaining_bytes"]-=written_bytes
                    cont = True
                    break

            if cont:
                continue

            if obj in open_interactions_dict:
                if written_bytes > 0:
                    if "sinks" in open_interactions_dict[obj]:
                        data_channels_dict[obj]["used"] = True
                        interactions_dict[str(interactions_count)] = {"channel" : obj, "sources" : open_interactions_dict[obj]["sources"], "sinks" : open_interactions_dict[obj]["sinks"]}
                        interactions_count += 1
                        open_interactions_dict.pop(obj)
                        open_interactions_dict[obj] = {"sources" : [(ts, proc_pid)]}
                    else:
                        if any(proc_pid in t[1] for t in open_interactions_dict[obj]["sources"]):
                            open_interactions_dict[obj]["sources"].append((ts, proc_pid))
            else:
                if written_bytes > 0:
                    open_interactions_dict[obj] = {"sources" : [(ts, proc_pid)]}

    for obj in sinks_without_sources_dict:
        if "sinks" in sinks_without_sources_dict[obj]:
            data_channels_dict[obj]["used"] = True
            interactions_dict[str(interactions_count)] = {"channel" : obj, "sources" : sinks_without_sources_dict[obj]["sources"], "sinks" : sinks_without_sources_dict[obj]["sinks"]}
            interactions_count += 1

    for obj in open_interactions_dict:
        if "sinks" in open_interactions_dict[obj]:
            data_channels_dict[obj]["used"] = True
            interactions_dict[str(interactions_count)] = {"channel" : obj, "sources" : open_interactions_dict[obj]["sources"], "sinks" : open_interactions_dict[obj]["sinks"]}
            interactions_count += 1


def fix_temp_dictionaries():
    global procs_to_skip
    global processes_dict

    print("Processes to skip:", procs_to_skip)


def post_analysis_checks(out_dir):
    if not os.path.exists(out_dir+"/checks"):
        os.makedirs(out_dir+"/checks")

    err = False
    with open(out_dir+"/checks/post_analysis_checks.log", "a+") as log_file:
        for int_id in interactions_dict:
            if interactions_dict[int_id]["channel"] not in data_channels_dict:
                log_file.write("ERROR: the data channel of the interaction %s (%s) is not in the 'data channels' dict!\n" % (int_id, interactions_dict[int_id]))
                err = True
            else:
                if data_channels_dict[interactions_dict[int_id]["channel"]]["used"] == False:
                    log_file.write("ERROR: the data channel of the interaction %s (%s) is NOT used!\n" % (int_id, interactions_dict[int_id]))
                    err = True
            if len(interactions_dict[int_id]["sources"]) == 0 and len(interactions_dict[int_id]["sinks"]) == 0:
                log_file.write("ERROR: the interaction %s (%s) has sources and sinks empty!\n" % (int_id, interactions_dict[int_id]))
                err = True                

            if data_channels_dict[interactions_dict[int_id]["channel"]]["kind"] == "pipe":
                if len(interactions_dict[int_id]["sources"]) == 0:
                    log_file.write("WARNING: interaction %s (%s) has no source!\n" % (int_id, interactions_dict[int_id]))
                if len(interactions_dict[int_id]["sinks"]) == 0:
                    log_file.write("WARNING: interaction %s (%s) has no sink!\n" % (int_id, interactions_dict[int_id]))
            elif data_channels_dict[interactions_dict[int_id]["channel"]]["kind"] == "unix_socket":
                if len(interactions_dict[int_id]["sources"]) == 0:
                    log_file.write("WARNING: interaction %s (%s) has no source!\n" % (int_id, interactions_dict[int_id]))
                if len(interactions_dict[int_id]["sinks"]) == 0:
                    log_file.write("WARNING: interaction %s (%s) has no sink!\n" % (int_id, interactions_dict[int_id]))
            elif data_channels_dict[interactions_dict[int_id]["channel"]]["kind"] == "inet_socket":
                if any((ts, proc_pid) in interactions_dict[int_id]["sources"] for (ts, proc_pid) in interactions_dict[int_id]["sinks"]):
                    log_file.write("ERROR: some source process of the interaction %s (%s) is a sink process too!\n" % (int_id, interactions_dict[int_id]))
                    err = True                    
            elif data_channels_dict[interactions_dict[int_id]["channel"]]["kind"] == "inet6_socket":
                if any((ts, proc_pid) in interactions_dict[int_id]["sources"] for (ts, proc_pid) in interactions_dict[int_id]["sinks"]):
                    log_file.write("ERROR: some source process of the interaction %s (%s) is a sink process too!\n" % (int_id, interactions_dict[int_id]))
                    err = True


        for proc_pid in processes_dict:
            if processes_dict[proc_pid]["executable"] == None and proc_pid != '0':
                log_file.write("ERROR: process %s (%s) has executable == null!\n" % (proc_pid, processes_dict[proc_pid]))
                err = True

        for channel_id in data_channels_dict:
            if data_channels_dict[channel_id]["score"] == "-1.0":
                log_file.write("ERROR: data channel %s has no score assigned!\n" % (channel_id))
                err = True

        if not err:
            log_file.write("ALL POST-ANALYSIS CHECKS PASSED!\n")


def static_filter_results():
    global executable_files_dict

    keys_to_remove_executable = []
    for executable in executable_files_dict:
        if "firmadyne" in executable:
            keys_to_remove_executable.append(executable)

    for key in keys_to_remove_executable:
        del executable_files_dict[key]


def dynamic_filter_results():
    global executable_files_dict
    global processes_dict
    global data_channels_dict
    global interactions_dict 

    keys_to_remove_int = []
    keys_to_remove_channel = []
    for interaction in interactions_dict:
        data_channel = interactions_dict[interaction]["channel"]
        if ".so" in data_channel or ".ko" in data_channel or "{path:}" in data_channel or "stdin" in data_channel or "stdout" in data_channel or "stderr" in data_channel:
            if interaction not in keys_to_remove_int:
                keys_to_remove_int.append(interaction)
            if data_channel not in keys_to_remove_channel:
                keys_to_remove_channel.append(data_channel)
        if any(t_source[1] == t_sink[1] for t_source in interactions_dict[interaction]["sources"] for t_sink in interactions_dict[interaction]["sinks"]):
            if interaction not in keys_to_remove_int:
                keys_to_remove_int.append(interaction)

    for key in keys_to_remove_int:
        del interactions_dict[key]

    for key in keys_to_remove_channel:
        del data_channels_dict[key]

    keys_to_remove_int = []
    for interaction in interactions_dict:
        data_channel = interactions_dict[interaction]["channel"]
        if data_channels_dict[data_channel]["kind"] == "pipe":
            if not interactions_dict[interaction]["sources"]:
                keys_to_remove_int.append(interaction)

    for key in keys_to_remove_int:
        del interactions_dict[key]

    keys_to_remove_channel = []
    for data_channel in data_channels_dict:
        if "stdin" in data_channel or "stdout" in data_channel or "stderr" in data_channel or "firmadyne" in data_channel:
            keys_to_remove_channel.append(data_channel)

    for key in keys_to_remove_channel:
        del data_channels_dict[key]

    # keys_to_remove_process = []
    # for process in processes_dict:
    #     found = False
    #     for interaction in interactions_dict:
    #         sources = interactions_dict[interaction]["sources"]
    #         sinks = interactions_dict[interaction]["sinks"]
    #         for (ts, source) in sources:
    #             if source == process:
    #                 found = True
    #         for (ts, sink) in sinks:
    #             if sink == process:
    #                 found = True

    #     if not found:
    #         keys_to_remove_process.append(process)

    # for key in keys_to_remove_process:
    #     del processes_dict[key]


def save_static_analysis_results(out_dir):
    global executable_files_dict

    ######## FINAL LISTS #########
    # Static analysis
    executable_files_list = []   # executable_files_dict: [ {id: path_binA, is_proprietary: bool, symlink_target: ( null | executable_id ) }, …]
    ##############################

    if not os.path.exists(out_dir+"/data"):
        os.makedirs(out_dir+"/data")

    for ex in executable_files_dict:
        executable_files_list.append({"id" : ex, "type" : executable_files_dict[ex]["type"], "interpreter" : executable_files_dict[ex]["interpreter"], "is_proprietary" : executable_files_dict[ex]["is_proprietary"], "symlink_target" : executable_files_dict[ex]["symlink_target"], "cves" : [], "cwes" : []})

    with open(out_dir+"/data/executable_files.json", "w") as f:
        f.write(json.dumps(executable_files_list, indent=4))


def save_dynamic_analysis_results(out_dir):
    global processes_dict
    global data_channels_dict
    global interactions_dict   

    ######## FINAL LISTS #########
    # Dynamic analysis
    processes_list = []          # processes_dict: [ { id: PID, parent: PID,  procname: string, executable: executable_id) } ]
    data_channels_list = []      # data_channels_dict: [ { id: pipe_PID_X_Y_unique, kind: pipe/file/socketTCP/etc, } ]
    interactions_list = []       # interactions_dict: [ {id : id, channel: channel_id,  sources: [ { id: PID,  }, … ], sinks: [ { id: PID} … ] } ]
    ##############################

    for proc in processes_dict:
        processes_list.append({"id" : proc, "start_time" : processes_dict[proc]["start_time"], "parent" : processes_dict[proc]["parent"], "procname" : processes_dict[proc]["procname"], "executable" : processes_dict[proc]["executable"]})

    for channel in data_channels_dict:
        data_channels_list.append({"id" : channel, "kind" : data_channels_dict[channel]["kind"], "used" : data_channels_dict[channel]["used"], "listening_pids" : data_channels_dict[channel]["listening_pids"], "score": data_channels_dict[channel]["score"]})

    for interaction in interactions_dict:
        sources = []
        for (ts, source) in interactions_dict[interaction]["sources"]:
            sources.append({"time" : ts, "pid" : source})
        sinks = []
        for (ts, sink) in interactions_dict[interaction]["sinks"]:
            sinks.append({"time" : ts, "pid" : sink})
        interactions_list.append({"id" : interaction, "channel" : interactions_dict[interaction]["channel"], "sources" : sources, "sinks" : sinks})

    if not os.path.exists(out_dir+"/data"):
        os.makedirs(out_dir+"/data")

    with open(out_dir+"/data/processes.json", "w") as f:
        f.write(json.dumps(processes_list, indent=4))

    with open(out_dir+"/data/data_channels.json", "w") as f:
        f.write(json.dumps(data_channels_list, indent=4))

    with open(out_dir+"/data/interactions.json", "w") as f:
        f.write(json.dumps(interactions_list, indent=4))



def fact(executable_json_file, FACT_URL, fact_uid):
    r = requests.get("%s/rest/firmware/%s"%(FACT_URL, fact_uid))
    firmware_json = r.json()

    with open(executable_json_file) as file:
        executable_files = json.load(file)
    executable_files = {item['id']: {key: item[key] for key in item if key != 'id'} for item in executable_files}

    for exec_id in executable_files:
        executable_files[exec_id]["cves"] = []
        executable_files[exec_id]["cwes"] = []

    included_files_uid_list = firmware_json["firmware"]["meta_data"]["included_files"]

    for obj_uid in tqdm(list(included_files_uid_list)):
        r = requests.get("%s/rest/file_object/%s"%(FACT_URL, obj_uid))
        obj_json = r.json()
        if "file_object" in obj_json:
            exec_id = obj_json["file_object"]["meta_data"]["hid"]

            if exec_id in executable_files:
                if "full" in obj_json["file_object"]["analysis"]["cwe_checker"]:
                    cwe_keys = obj_json["file_object"]["analysis"]["cwe_checker"]["full"].keys()
                    cwe_list = []
                    for key in cwe_keys:
                        d = obj_json["file_object"]["analysis"]["cwe_checker"]["full"][key]
                        cwe = {"id" : key, "plugin_version" : d["plugin_version"], "warnings" : d["warnings"]}
                        cwe_list.append(cwe)

                    executable_files[exec_id]["cwes"] = cwe_list

                if "cve_results" in obj_json["file_object"]["analysis"]["cve_lookup"]:
                    cve_keys = list(obj_json["file_object"]["analysis"]["cve_lookup"]["cve_results"].keys())
                    cve_list = []
                    if cve_keys:
                        cve_key_list = list(obj_json["file_object"]["analysis"]["cve_lookup"]["cve_results"][cve_keys[0]].keys())
                
                        for cve in cve_key_list:
                            while True:
                                r = requests.get("https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=%s"%(cve))
                                try:
                                    cve_json = r.json()
                                except:
                                    time.sleep(5)
                                else:
                                    break

                            print(cve)
                            cve_result = cve_json["vulnerabilities"][0]["cve"]
                            cve_list.append(cve_result)
                    
                    executable_files[exec_id]["cves"] = cve_list


    
    executable_files_list = []
    for ex in executable_files:
        executable_files_list.append({"id" : ex, "type" : executable_files[ex]["type"], "interpreter" : executable_files[ex]["interpreter"], "is_proprietary" : executable_files[ex]["is_proprietary"], "symlink_target" : executable_files[ex]["symlink_target"], "cves" : executable_files[ex]["cves"], "cwes" : executable_files[ex]["cwes"]})

    with open(executable_json_file, "w") as f:
        f.write(json.dumps(executable_files_list, indent=4))


if __name__ == "__main__":
    firmware_name = sys.argv[1]
    out_dir = sys.argv[2]
    log_path = sys.argv[3]
    extracted_firm_path = sys.argv[4]
    static_out_dir = out_dir[:out_dir[:out_dir.rfind("/")].rfind("/")]+"/static_analysis"
    source_code_path = sys.argv[5]
    FACT_IP = sys.argv[6]
    FACT_PORT = sys.argv[7]
    factUid = sys.argv[8]

    os.makedirs(out_dir, exist_ok=True)

    if os.path.isdir(static_out_dir):
        print("\nSTATIC ANALYSIS ALREADY DONE!")
        with open(static_out_dir+"/data/executable_files.json") as file:
            executable_files = json.load(file)
            executable_files_dict = {item['id']: {key: item[key] for key in item if key != 'id'} for item in executable_files}
            executable_files_path_dict = {item['id'].split("/")[-1]: item['id'] for item in executable_files}
    else:
        print("\nSTATIC ANALYSIS...")
        static_analysis()

        print("\nFILTER STATIC ANALYSIS RESULTS...")
        static_filter_results()

        print("\nSAVE STATIC ANALYSIS RESULTS...")
        save_static_analysis_results(static_out_dir)

    print("\nOPEN AND FIX RAW LOG...")
    open_and_fix_raw_log(log_path)

    print("\nDYNAMIC ANALYSIS...")
    dynamic_analysis()

    print("\nFIXING RAW LOG...")
    fix_temp_dictionaries()

    print("\nDYNAMIC ANALYSIS (FINAL)...")
    reset_dicts_and_lists()
    dynamic_analysis()

    print("\nFILTER DYNAMIC ANALYSIS RESULTS...")
    dynamic_filter_results()

    print("\nASSIGNING DATA CHANNEL SCORES...")
    assign_score(data_channels_dict)

    print("\nPOST-ANALYSIS CHECKS...")
    post_analysis_checks(out_dir)

    print("\nSAVE DYNAMIC ANALYSIS RESULTS...")
    save_dynamic_analysis_results(out_dir)

    if (factUid != 'None'):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        try:
            sock.connect((FACT_IP, int(FACT_PORT)))
            print("\nADD CVE/CWE DATA TO STATIC ANALYSIS RESULTS...")
            fact(static_out_dir+"/data/executable_files.json", FACT_IP+":"+FACT_PORT, factUid)
        except Exception as e:
            print(f"IP address {FACT_IP} and port {FACT_PORT} are not reachable. Error: {e}")
        finally:
            sock.close()

    print("\nCOMPUTE STATS...")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    executable_files = None
    data_channels = None
    interactions = None
    processes = None

    with open(static_out_dir+"/data/executable_files.json") as file:
        executable_files = json.load(file)
    executable_files = {item['id']: {key: item[key] for key in item if key != 'id'} for item in executable_files}

    with open(out_dir+"/data/data_channels.json") as file:
        data_channels = json.load(file) 
    data_channels = {item['id']: {key: item[key] for key in item if key != 'id'} for item in data_channels}

    with open(out_dir+"/data/interactions.json") as file:
        interactions = json.load(file)
    interactions = {item['id']: {key: item[key] for key in item if key != 'id'} for item in interactions}

    with open(out_dir+"/data/processes.json") as file:
        processes = json.load(file) 
    processes = {item['id']: {key: item[key] for key in item if key != 'id'} for item in processes}

    if not os.path.exists(out_dir+"/stats"):
        os.makedirs(out_dir+"/stats")

    calculate_border_executables(out_dir+'/stats/border_executables.json', interactions, processes, executable_files)

    calculate_interactions_per_kind(out_dir+'/stats/interactions_per_kind.json', data_channels, interactions)

    generate_processes_graph(out_dir+'/stats/graph_processes.graphml', interactions)

    generate_binaries_graph(out_dir+'/stats/graph_binaries.graphml', interactions, processes)

    calculate_proprietary_exe(out_dir+'/stats/proprietary_exec.json', executable_files)

    calculate_executed_executables_per_kind(out_dir+'/stats/executed_executables.json', processes, executable_files)

    lower_bound = 0.0
    calculate_interesting_border_executables(out_dir+'/stats/interesting_border_executables_%s.json' % (str(lower_bound)), interactions, processes, executable_files, data_channels, lower_bound)

    lower_bound = 0.15
    calculate_interesting_border_executables(out_dir+'/stats/interesting_border_executables_%s.json' % (str(lower_bound)), interactions, processes, executable_files, data_channels, lower_bound)

    lower_bound = 0.50
    calculate_interesting_border_executables(out_dir+'/stats/interesting_border_executables_%s.json' % (str(lower_bound)), interactions, processes, executable_files, data_channels, lower_bound)

    print("\nGENERATE VIEWS...")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if not os.path.exists(out_dir+"/views"):
        os.makedirs(out_dir+"/views")
    
    border_executables_dict_view_1 = phase_1A_view_1(out_dir+'/views/phase_1A/view_1', interactions, processes, executable_files, data_channels)

    border_executables_dict_view_2 = phase_1A_view_2(out_dir+'/views/phase_1A/view_2', border_executables_dict_view_1, interactions, processes, data_channels)

    phase_1A_view_3(out_dir+'/views/phase_1A/view_3', border_executables_dict_view_2, executable_files, interactions, processes, data_channels)

    graph = phase_1B_view_1(out_dir+'/views/phase_1B/view_1', interactions, processes, executable_files, data_channels)

    phase_1B_view_2(out_dir+'/views/phase_1B/view_2', graph)

    phase_1B_view_3(out_dir+'/views/phase_1B/view_3', graph, data_channels, processes)

    print("\nCOMPUTE EXTRA STATS...")

    sort_executables_by_score(out_dir+'/stats/sort_executables_by_score.json', graph, executable_files)

    print("\nFINISHED!")

    # Send a PUT request to the frontend
    url = 'http://localhost:3000/api/run'
    params = {'firmwareId': '%s' % firmware_name, 'runId': '%s' % (out_dir.split('/')[-1])}
    headers = {'Content-Type': 'application/json'}

    success = False

    # # Retry the PUT request until it is successful
    # while not success:
    #     try:
    #         response = requests.put(url, params=params, headers=headers)

    #         if response.status_code == 200:
    #             print('PUT request successful.')
    #             success = True
    #         else:
    #             print(f'PUT request failed with status code: {response.status_code}. Retrying...')
    #             time.sleep(1)  # Wait for 5 seconds before retrying
    #     except Exception as e:
    #         print(f'Error: {e}. Retrying...')
    #         time.sleep(1)  # Wait for 1 seconds before retrying
