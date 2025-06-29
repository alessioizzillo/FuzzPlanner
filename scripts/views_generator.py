import json
import os
import networkx as nx


def phase_1A_view_1(out_dir, interactions, processes, executable_files, data_channels):
    border_executables_dict_view_1 = {}
    for inter_id in interactions:
        if not interactions[inter_id]['sources']:
            for proc_pid in interactions[inter_id]['sinks']:
                exec_id = processes[proc_pid['pid']]['executable']

                if exec_id not in border_executables_dict_view_1:
                    border_executables_dict_view_1[exec_id] = [interactions[inter_id]["channel"]]
                else:
                    border_executables_dict_view_1[exec_id].append(interactions[inter_id]["channel"])

    view_1 = []
    for exec_id in border_executables_dict_view_1:
        executable = {"id" : exec_id, "type" : executable_files[exec_id]["type"], "is_proprietary" : executable_files[exec_id]["is_proprietary"]}
        executable["border_data_channels"] = {}

        for data_channel_id in border_executables_dict_view_1[exec_id]:
            kind = data_channels[data_channel_id]["kind"]
            if kind not in executable["border_data_channels"]:
                executable["border_data_channels"][kind] = {data_channel_id : {"num" : 1, "score" : data_channels[data_channel_id]["score"]}}
            else:
                if data_channel_id not in executable["border_data_channels"][kind]:
                    executable["border_data_channels"][kind][data_channel_id] = {"num" : 1, "score" : data_channels[data_channel_id]["score"]}
                else:
                    executable["border_data_channels"][kind][data_channel_id]["num"] += 1
        
        view_1.append(executable)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(out_dir+"/binaries.json", "w") as out:
        out.write(json.dumps(view_1, indent=4))

    return border_executables_dict_view_1


def phase_1A_view_2(out_dir, border_executables_dict_view_1, interactions, processes, data_channels):
    border_executables_dict_view_2 = {}

    for exec_id in border_executables_dict_view_1:
        dir = exec_id[:exec_id.rfind("/")]
        border_executables_dict_view_2[exec_id] = {"channels" : {}, "client_executables" : [], "server_executables": []}

        for inter_id in interactions:
            data_channel_id = interactions[inter_id]["channel"]

            role = None
            for proc_pid in interactions[inter_id]['sinks']:
                if (exec_id == processes[proc_pid['pid']]['executable']):
                    if data_channel_id not in border_executables_dict_view_2[exec_id]["channels"]:
                        border_executables_dict_view_2[exec_id]["channels"][data_channel_id] = {"ints_as_source" : [], "ints_as_sink" : [], "first_as_sink" : True, "first_as_source" : False, "executables" : [], "processes" : []}

                    border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["ints_as_sink"].append(inter_id)
                    role = "sink"
                    
            for proc_pid in interactions[inter_id]['sources']:
                if (exec_id == processes[proc_pid['pid']]['executable']):
                    if data_channel_id not in border_executables_dict_view_2[exec_id]["channels"]:
                        border_executables_dict_view_2[exec_id]["channels"][data_channel_id] = {"ints_as_source" : [], "ints_as_sink" : [], "first_as_sink" : False, "first_as_source" : True, "executables" : [], "processes" : []}

                    border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["ints_as_source"].append(inter_id)
                    role = "source"

            if role:
                if role == "source":
                    for proc_pid in interactions[inter_id]['sinks']:
                        if processes[proc_pid['pid']]['executable'] not in border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["executables"]:
                            border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["executables"].append(processes[proc_pid['pid']]['executable'])

                        if proc_pid not in border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["processes"]:
                            border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["processes"].append(proc_pid['pid'])

                        if processes[proc_pid['pid']]['executable'] not in border_executables_dict_view_2[exec_id]["server_executables"] and processes[proc_pid['pid']]['executable'] not in border_executables_dict_view_2[exec_id]["client_executables"]:
                            border_executables_dict_view_2[exec_id]["server_executables"].append(processes[proc_pid['pid']]['executable'])
                    
                    for proc_pid in interactions[inter_id]['sources']:
                        if processes[proc_pid['pid']]['executable'] not in border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["executables"]:
                            border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["executables"].append(processes[proc_pid['pid']]['executable'])

                        if proc_pid not in border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["processes"]:
                            border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["processes"].append(proc_pid['pid'])

                else:
                    for proc_pid in interactions[inter_id]['sources']:
                        if processes[proc_pid['pid']]['executable'] not in border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["executables"]:
                            border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["executables"].append(processes[proc_pid['pid']]['executable'])

                        if proc_pid not in border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["processes"]:
                            border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["processes"].append(proc_pid['pid'])

                        if processes[proc_pid['pid']]['executable'] not in border_executables_dict_view_2[exec_id]["server_executables"] and processes[proc_pid['pid']]['executable'] not in border_executables_dict_view_2[exec_id]["client_executables"]:
                            border_executables_dict_view_2[exec_id]["client_executables"].append(processes[proc_pid['pid']]['executable'])

                    for proc_pid in interactions[inter_id]['sinks']:
                        if processes[proc_pid['pid']]['executable'] not in border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["executables"]:
                            border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["executables"].append(processes[proc_pid['pid']]['executable'])

                        if proc_pid not in border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["processes"]:
                            border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["processes"].append(proc_pid['pid'])


        view_2 = {"num_client_executables": len(border_executables_dict_view_2[exec_id]["client_executables"]), "num_server_executables": len(border_executables_dict_view_2[exec_id]["server_executables"]), "data_channels" : []}
        for data_channel_id in border_executables_dict_view_2[exec_id]["channels"]:
            kind = data_channels[data_channel_id]["kind"]
            used = data_channels[data_channel_id]["used"]
            score = data_channels[data_channel_id]["score"]
            num_executables = len(border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["executables"])
            num_processes = len(border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["processes"])
            num_ints_as_source = len(border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["ints_as_source"])
            num_ints_as_sink = len(border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["ints_as_sink"])
            first_as_sink = border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["first_as_sink"]
            first_as_source = border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["first_as_source"]   
            
            is_border = False
            for border_channel_id in border_executables_dict_view_1[exec_id]:
                if data_channel_id == border_channel_id:
                    is_border = True
                    break
        
            data_channel = {"id": data_channel_id, "kind" : kind, "used" : used, "score" : score, "is_border" : is_border, "num_executables" : num_executables, "num_processes" : num_processes, "num_interactions_as_source" : num_ints_as_source, "num_interactions_as_sink" : num_ints_as_sink, "first_as_sink" : first_as_sink, "first_as_source" : first_as_source}

            view_2["data_channels"].append(data_channel)

        if not os.path.exists(out_dir+dir):
            os.makedirs(out_dir+dir)

        with open(out_dir+"/"+exec_id+".json", "w") as out:
            out.write(json.dumps(view_2, indent=4))
    
    return border_executables_dict_view_2




def phase_1A_view_3(out_dir, border_executables_dict_view_2, executable_files, interactions, processes, data_channels):
    for exec_id in border_executables_dict_view_2:
        i = 0
        for data_channel_id in border_executables_dict_view_2[exec_id]["channels"]:
            kind = data_channels[data_channel_id]["kind"]
            used = data_channels[data_channel_id]["used"]
            score = data_channels[data_channel_id]["score"]
            view_3 = {"id": data_channel_id, "kind" : kind, "used" : used, "score" : score, "executables" : []}
            
            execs_ints_as_source_dict = {}
            execs_ints_as_sink_dict = {}
            execs_proc_dict = {}
            first_as_sink = []
            first_as_source = []
            
            # Use the following for statement if you want select, for each channel, just the interactions which include exec_id
            # for interaction_id in border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["ints_as_source"]+border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["ints_as_sink"]:
            
            # Use the following for statement if you want select, for each channel, all the interactions which have used that channel
            for interaction_id in interactions:
                if interactions[interaction_id]["channel"] == data_channel_id:
                    for proc_pid in interactions[interaction_id]['sources']:
                        if processes[proc_pid['pid']]['executable'] not in execs_proc_dict:
                            execs_proc_dict[processes[proc_pid['pid']]['executable']] = [proc_pid['pid']]
                        else:
                            execs_proc_dict[processes[proc_pid['pid']]['executable']].append(proc_pid['pid'])

                        if processes[proc_pid['pid']]['executable'] not in execs_ints_as_source_dict:
                            execs_ints_as_source_dict[processes[proc_pid['pid']]['executable']] = [interaction_id]
                            if processes[proc_pid['pid']]['executable'] not in first_as_source and processes[proc_pid['pid']]['executable'] not in first_as_sink:
                                first_as_source.append(processes[proc_pid['pid']]['executable'])
                        else:
                            execs_ints_as_source_dict[processes[proc_pid['pid']]['executable']].append(interaction_id)
                    for proc_pid in interactions[interaction_id]['sinks']:
                        if processes[proc_pid['pid']]['executable'] not in execs_proc_dict:
                            execs_proc_dict[processes[proc_pid['pid']]['executable']] = [proc_pid['pid']]
                        else:
                            execs_proc_dict[processes[proc_pid['pid']]['executable']].append(proc_pid['pid'])

                        if processes[proc_pid['pid']]['executable'] not in execs_ints_as_sink_dict:
                            execs_ints_as_sink_dict[processes[proc_pid['pid']]['executable']] = [interaction_id]
                            if processes[proc_pid['pid']]['executable'] not in first_as_source and processes[proc_pid['pid']]['executable'] not in first_as_sink:
                                first_as_sink.append(processes[proc_pid['pid']]['executable'])
                        else:
                            execs_ints_as_sink_dict[processes[proc_pid['pid']]['executable']].append(interaction_id)
            
            # Use the following for statement if you want select, for each channel, just the interactions which include exec_id
            # for channel_exec_id in border_executables_dict_view_2[exec_id]["channels"][data_channel_id]["executables"]:

            # Use the following for statement if you want select, for each channel, all the interactions which have used that channel
            for channel_exec_id in execs_proc_dict:    
                num_interactions_as_source = len(execs_ints_as_source_dict[channel_exec_id]) if channel_exec_id in execs_ints_as_source_dict else 0
                num_interactions_as_sink = len(execs_ints_as_sink_dict[channel_exec_id]) if channel_exec_id in execs_ints_as_sink_dict else 0
                first_as_source_bool = True if channel_exec_id in first_as_source else False
                first_as_sink_bool = True if channel_exec_id in first_as_sink else False
                executable = {"id" : channel_exec_id, "type" : executable_files[channel_exec_id]["type"], "is_proprietary" : executable_files[channel_exec_id]["is_proprietary"], "num_interactions_as_source" : num_interactions_as_source, "num_interactions_as_sink" : num_interactions_as_sink, "num_processes" : len(execs_proc_dict[channel_exec_id]), "first_as_source" : first_as_source_bool, "first_as_sink" : first_as_sink_bool}
                view_3["executables"].append(executable)

            if not os.path.exists(out_dir+exec_id):
                os.makedirs(out_dir+exec_id)

            with open(out_dir+"/"+exec_id+"/"+str(i)+".json", "w") as out:
                out.write(json.dumps(view_3, indent=4))
            
            i+=1



def phase_1B_view_1(out_dir, interactions, processes, executable_files, data_channels):
    G = nx.MultiDiGraph()

    for int in interactions:
        channel = interactions[int]["channel"]
        sources = interactions[int]["sources"]
        sinks = interactions[int]["sinks"]
        
        if sources:
            for source in sources:
                source_exe = processes[source["pid"]]["executable"]
                for sink in sinks:
                    sink_exe = processes[sink["pid"]]["executable"]
                    edge_data = G.get_edge_data(source_exe, sink_exe)
                    if edge_data == None or not any(channel == data["edge_name"] for data in edge_data.values()):                
                        G.add_edge(source_exe, sink_exe, edge_name=channel, score=data_channels[channel]["score"], time=sink["time"])
                        if "start_time" not in G.nodes[source_exe]:
                            G.add_node(source_exe, **{"start_time" : processes[source["pid"]]["start_time"]})
                        if "start_time" not in G.nodes[sink_exe]:
                            G.add_node(sink_exe, **{"start_time" : processes[sink["pid"]]["start_time"]})
        else:
            source_exe = "<border>"
            for sink in sinks:
                sink_exe = processes[sink["pid"]]["executable"]
                edge_data = G.get_edge_data(source_exe, sink_exe)
                if edge_data == None or not any(channel == data["edge_name"] for data in edge_data.values()):                
                    G.add_edge(source_exe, sink_exe, edge_name=channel, score=data_channels[channel]["score"])
                    if "start_time" not in G.nodes[sink_exe]:
                        G.add_node(sink_exe, **{"start_time" : processes[sink["pid"]]["start_time"]})

    for channel in data_channels:
        for dict_pid in data_channels[channel]["listening_pids"]:
            pid = dict_pid["pid"]
            exec_id = processes[pid]["executable"]
            if not G.has_node(exec_id):
                start_time = -1
                for proc_id in processes:
                    if processes[proc_id]["executable"] == exec_id:
                        if start_time == -1 or processes[proc_id]["start_time"] < start_time:
                            start_time = processes[proc_id]["start_time"]

                if start_time == -1:
                    assert(False)

                G.add_node(exec_id, **{"start_time" : start_time})

    exec_scores = {}
    exec_proprietary = {}
    for node in G.nodes:
        adjacent_in_edges = G.in_edges(node, data=True)
        score_max = 0.0
        for edge in adjacent_in_edges:
            score = float(edge[2]["score"])
            distance = nx.shortest_path_length(G, node, edge[1])
            score_max += score / (distance+1)

        exec_scores[node] = score_max
        
        if node != "<border>":
            exec_proprietary[node] = executable_files[node]["is_proprietary"]
        else:
            exec_proprietary[node] = "<border>"

    nx.set_node_attributes(G, exec_scores, "score")
    nx.set_node_attributes(G, exec_proprietary, "is_proprietary")

    # if G.has_node("<border>"):
    #     G.remove_node("<border>")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    nx.write_gml(G, out_dir+"/executable_graph.gml")

    return G
    


def phase_1B_view_2(out_dir, graph):
    for exec_id in graph.nodes():
        if exec_id == "<border>":
            continue

        dir = exec_id[:exec_id.rfind("/")]
        subgraph = graph.subgraph(nx.algorithms.dfs_tree(graph, exec_id))

        if not os.path.exists(out_dir+dir):
            os.makedirs(out_dir+dir)
        
        nx.write_gml(subgraph, out_dir+"/"+exec_id+".gml")



def phase_1B_view_3(out_dir, graph, data_channels, processes):
    attrs = nx.get_edge_attributes(graph, "edge_name")

    for channel_id in set(attrs.values()):
        listening = {}
        subgraph = nx.DiGraph()

        subgraph.add_node(channel_id, kind="channel")
        
        list_executables = []

        for source, sink, attributes in graph.edges(data=True):
            edge_name = attributes.get("edge_name")
            
            if edge_name == channel_id:
                subgraph.add_node(source, kind="executable")
                subgraph.add_node(sink, kind="executable")
                listening[source] = False
                listening[sink] = False
                subgraph.add_edge(source, channel_id)
                subgraph.add_edge(channel_id, sink)
                list_executables.append(source)
                list_executables.append(sink)

        for dict_pid in data_channels[channel_id]["listening_pids"]:
            pid = dict_pid["pid"]
            exec_id = processes[pid]["executable"]
            
            if not subgraph.has_node(exec_id):
                subgraph.add_node(exec_id, kind="executable")

            listening[exec_id] = True 
            subgraph.add_edge(channel_id, exec_id)

        nx.set_node_attributes(subgraph, listening, "listening")

        list_executables = list(set(list_executables))

        for exec_id in list_executables:
            if exec_id == "<border>":
                continue

            if not os.path.exists(out_dir+exec_id):
                os.makedirs(out_dir+exec_id)

            pattern = '.gml'
            files = [file for file in os.listdir(out_dir+exec_id) if file.endswith(pattern)]
            n_values = [int(file.split('.')[0]) for file in files]
            max_n = max(n_values) if n_values else 0
            next_n = max_n + 1

            nx.write_gml(subgraph, out_dir+"/"+exec_id+"/"+str(next_n)+".gml")

