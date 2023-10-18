import json
import os, sys
import glob
import shutil

if __name__ == '__main__':
    config_path = sys.argv[1]
    target_exec = sys.argv[2]
    target_channel = sys.argv[3]
    target_replay_init_syscall_str = sys.argv[4]
    target_replay_injected_syscall_str = sys.argv[5]
    target_replay_pc_str = sys.argv[6]
    dict_path = sys.argv[7]

    out_file = config_path+"/config.json"
    dict_files = glob.glob(os.path.join(dict_path, "*.dict"))
    dict_names = [os.path.splitext(os.path.basename(file))[0] for file in dict_files]

    if 'socket' in target_channel:
        seed_type = 'socket'
    elif 'pipe' in target_channel:
        seed_type = 'pipe'
    elif 'file' in target_channel:
        seed_type = 'file'
    elif 'device' in target_channel:
        seed_type = 'device'
    elif 'virtual_file' in target_channel:
        seed_type = 'virtual_file'
    else:
        seed_type = 'unknown'

    target_dict = None
    for d in dict_names:
        if d in target_exec:
            target_dict = d

    config = {
        'seed_type': seed_type,
        'syscall_init': int(target_replay_init_syscall_str),
        'syscall_injected': int(target_replay_injected_syscall_str),
        'fork_point_address': int(target_replay_pc_str, 16),
        'dictionary_type': target_dict
    }

    with open(out_file, 'w') as f:
        json.dump(config, f, indent=4)

    if target_dict:
        shutil.copy(dict_path+"/"+target_dict+".dict", config_path+"/"+target_dict+".dict")