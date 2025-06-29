import json
import networkx as nx

################## HELPERS ####################

def get_executable(processes, pid):
    process = processes.get(pid)
    if process:
        return process.get("executable")
    return None


def is_sublist(sublist, list):
    n = len(sublist)
    m = len(list)

    for i in range(m - n + 1):
        if list[i:i+n] == sublist:
            return True

    return False

###############################################

def calculate_border_executables(out_file, interactions, processes, executable_files):
    border_executables = []
    exec_id_list = []
    for inter_id in interactions:
        if not interactions[inter_id]['sources']:
            for proc_pid in interactions[inter_id]['sinks']:
                if processes[proc_pid['pid']]['executable'] not in border_executables:
                    exec_id = processes[proc_pid['pid']]['executable']
                    if exec_id not in exec_id_list:
                        border_executables.append({"id" : exec_id, "type" : executable_files[exec_id]["type"], "interpreter" : executable_files[exec_id]["interpreter"], "is_proprietary" : executable_files[exec_id]["is_proprietary"], "symlink_target" : executable_files[exec_id]["symlink_target"]})
                        exec_id_list.append(exec_id)

    with open(out_file, "w") as out:
        out.write(json.dumps(border_executables, indent=4))


def calculate_interactions_per_kind(out_file, data_channels, interactions):
    interactions_per_kind = {}

    for interaction in interactions.values():
        channel = interaction["channel"]
        kind = data_channels[channel]["kind"]
        interactions_per_kind[kind] = interactions_per_kind.get(kind, 0) + 1

    with open(out_file, "w") as out:
        out.write(json.dumps(interactions_per_kind, indent=4))


def generate_processes_graph(out_file, interactions):
    G = nx.MultiDiGraph()

    for i in interactions:
        channel = interactions[i]['channel']
        sources = interactions[i]['sources']
        sinks = interactions[i]['sinks']
        
        for source in sources:
            source_pid = source['pid']
            for sink in sinks:
                sink_pid = sink['pid']
                G.add_edge(source_pid, sink_pid, edge_name=channel)

    nx.write_gml(G, out_file)


def generate_binaries_graph(out_file, interactions, processes):
    G = nx.MultiDiGraph()
 
    d = {}
    for pid in processes:
        executable = processes[pid]['executable']
        d[pid] = executable

    for i in interactions:
        channel = interactions[i]['channel']
        sources = interactions[i]['sources']
        sinks = interactions[i]['sinks']
        
        for source in sources:
            source_exe = d[source['pid']]
            for sink in sinks:
                sink_exe = d[sink['pid']]
                edge_data = G.get_edge_data(source_exe, sink_exe)
                if edge_data == None or not any(channel == data['edge_name'] for data in edge_data.values()):                
                    G.add_edge(source_exe, sink_exe, edge_name=channel)

    nx.write_gml(G, out_file)


def calculate_proprietary_exe(out_file, executable_files):
    d = {'proprietary' : 0, 'open_source' : 0}
    for exec_id in executable_files:
        if executable_files[exec_id]['is_proprietary'] == True:
            d['proprietary'] += 1
        else:
            d['open_source'] += 1

    with open(out_file, "w") as out:
        out.write(json.dumps(d, indent=4))


def calculate_interesting_border_executables(out_file, interactions, processes, executable_files, data_channels, lower_bound):
    border_executables = []
    for inter_id in interactions:
        if not interactions[inter_id]['sources'] and float(data_channels[interactions[inter_id]['channel']]["score"]) > lower_bound:
            for proc_pid in interactions[inter_id]['sinks']:
                if processes[proc_pid['pid']]['executable'] not in border_executables:
                    exec_id = processes[proc_pid['pid']]['executable']
                    border_executables.append({"id" : exec_id, "type" : executable_files[exec_id]["type"], "interpreter" : executable_files[exec_id]["interpreter"], "is_proprietary" : executable_files[exec_id]["is_proprietary"], "symlink_target" : executable_files[exec_id]["symlink_target"]})

    with open(out_file, "w") as out:
        out.write(json.dumps(border_executables, indent=4))


def calculate_executed_executables_per_kind(out_file, processes, executable_files):
    proc_dict = {}
    for proc_id in processes:
        if executable_files[processes[proc_id]["executable"]]["type"] not in proc_dict:
            proc_dict[executable_files[processes[proc_id]["executable"]]["type"]] = []

        if processes[proc_id]["executable"] not in proc_dict[executable_files[processes[proc_id]["executable"]]["type"]]:
            proc_dict[executable_files[processes[proc_id]["executable"]]["type"]].append(processes[proc_id]["executable"])

    final_dict = {}
    for kind in proc_dict:
        final_dict[kind] = len(proc_dict[kind])
    
    with open(out_file, "w") as out:
        out.write(json.dumps(final_dict, indent=4))


def sort_executables_by_score(out_file, G, executable_files):
    exec_list = []
    attrs = nx.get_node_attributes(G, "score")

    for exec_id in attrs:
        if exec_id == "<border>":
            continue        
        exec_list.append((attrs[exec_id], {"id" : exec_id, "type" : executable_files[exec_id]["type"], "interpreter" : executable_files[exec_id]["interpreter"], "is_proprietary" : executable_files[exec_id]["is_proprietary"], "symlink_target" : executable_files[exec_id]["symlink_target"]}))

    exec_list = sorted(exec_list, key=lambda x: x[0])

    with open(out_file, "w") as out:
        out.write(json.dumps(exec_list, indent=4))

