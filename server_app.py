from flask import Flask, jsonify, request
import os
import subprocess
import json
import time
import signal

FACT_IP="http://192.168.30.177"
FACT_PORT="5000"

def send_signal_recursive(parent_pid, signal_to_send):
    pgrep_process = subprocess.Popen(["pgrep", "-P", str(parent_pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    child_pids_bytes, _ = pgrep_process.communicate()
    child_pids_str = child_pids_bytes.decode('utf-8').strip()
    child_pids = child_pids_str.split()
    for child_pid in child_pids:
        send_signal_recursive(int(child_pid), signal_to_send)
    os.kill(parent_pid, signal_to_send)

def find_next_run(directory):
    pattern = "run_"
    run = ""

    if os.path.isdir(directory):
        subdirs = [subdir for subdir in os.listdir(directory) if subdir.startswith(pattern) and os.path.isdir(os.path.join(directory, subdir))]

        if subdirs:
            max_subdir = max([int(subdir[len(pattern):]) for subdir in subdirs])
            run = f"{pattern}{max_subdir + 1}"
        else:
            run = f"{pattern}0"
    else:
        run = f"{pattern}0"

    return run

def firmwareId2scratchId(firmwareId):
    directory="FirmAE/scratch/firmafl/"
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return None

    for subdir_name in os.listdir(directory):
        subdir_path = os.path.join(directory, subdir_name)

        if os.path.isdir(subdir_path) and os.path.isfile(os.path.join(subdir_path, "name")):
            with open(os.path.join(subdir_path, "name"), 'r') as file:
                file_content = file.read().strip()

            if file_content == firmwareId:
                return subdir_name 

    return None


app = Flask(__name__)

@app.route('/')
def hello():
    return 'FuzzPlanner!', 200

@app.route('/firmwares')
def firmwares():
    directory_path = "firmwares"

    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        files = os.listdir(directory_path)
        firmware_files = [file for file in files if os.path.isfile(os.path.join(directory_path, file))]
        firmware_dict = {"firmwares": firmware_files}
    else:
        response_data = {
            "status": "error",
            "message": "The 'firmwares' directory does not exist."
        }

        return jsonify(response_data), 500

    return jsonify(firmware_dict), 200

@app.route('/runs')
def runs():
    firmwareId = request.args.get('firmwareId', default=None)

    directory_path = "analysis/results/%s/dynamic_analysis/" % firmwareId

    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        dirs = os.listdir(directory_path)
        run_dirs = [dir for dir in dirs if os.path.isdir(os.path.join(directory_path, dir))]
        response_dict = {"firmwareId" : firmwareId, "runs" : run_dirs}
    else:
        response_dict = {"firmwareId" : firmwareId, "runs" : []}

    return jsonify(response_dict), 200

@app.route('/data')
def data():
    firmwareId = request.args.get('firmwareId', default=None)
    runId = request.args.get('runId', default=None)
    type = request.args.get('type', default=None)

    if (type == "interactions" or type == "processes" or type == "data_channels"):
        json_file_path = "analysis/results/%s/dynamic_analysis/%s/data/%s.json" % (firmwareId, runId, type)
    elif (type == "executable_files"):
        json_file_path = "analysis/results/%s/static_analysis/data/executable_files.json" % (firmwareId)
    else:
        response_data = {
            "status": "error",
            "message": "Invalid requested data 'type'."
        }

        return jsonify(response_data), 400        

    try:
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        response_data = {
            "status": "error",
            "message": f"Error: The file '{json_file_path}' does not exist."
        }

        return jsonify(response_data), 500      
    except json.JSONDecodeError as e:
        response_data = {
            "status": "error",
            "message": f"Error: Failed to parse JSON data from '{json_file_path}': {e}."
        }

        return jsonify(response_data), 500      
    except Exception as e:
        response_data = {
            "status": "error",
            "message": f"An unexpected error occurred: {e}"
        }

        return jsonify(response_data), 500      

    json_data = json.dumps(data, indent=4)

    return json_data, 200

@app.route('/emulate', methods=['POST'])
def emulate():
    firmwareId = request.args.get('firmwareId', default=None)
    
    if not os.path.exists("firmwares/"+firmwareId):
        response_data = {
            "status": "error",
            "message": "Firmware file %s does not exist." % firmwareId
        }

        return jsonify(response_data), 500            

    emu_dir_path="backend_runtime/emulation/%s"%firmwareId
    if not os.path.exists(emu_dir_path):
        os.makedirs(emu_dir_path)

    if os.path.exists(emu_dir_path+"/status"):
        with open(emu_dir_path+"/status", "r") as status_file:
            content = status_file.read().strip()

            if "analyzing" in content:
                response_data = {
                    "status": "error",
                    "message": f"{firmwareId} is being analyzed by another process."
                }
                return jsonify(response_data), 400

            if not content == "stopped":
                with open("%s/pid"%emu_dir_path, 'r') as pid_file:
                    pid = int(pid_file.read())
                    send_signal_recursive(pid, signal.SIGINT)

    command = "export EXECUTION_MODE=0; export POSTGRESQL_IP=127.0.0.1; \
                sudo service postgresql restart; ./FirmAFL/flush_interface.sh; \
                ./docker_start.sh -r firmwares/%s" % (firmwareId)

    try:
        with open(emu_dir_path+"/status", "w") as status_file:
            status_file.write("booting")
        with open(os.devnull, "w") as f:
            process = subprocess.Popen(command, shell=True, stdout=f, stderr=f)
        with open(emu_dir_path+"/pid", "w") as status_file:
            status_file.write(str(process.pid))    
    except Exception as e:
        response_data = {
            "status": "error",
            "message": "Server could not start emulation. %s" % e
        }

        return jsonify(response_data), 500

    return 'OK', 200

@app.route('/pause_emulation', methods=['POST'])
def pause_emulation():
    firmwareId = request.args.get('firmwareId', default=None)
    factUid = request.args.get('factUid', default=None)
    emu_dir_path="backend_runtime/emulation/%s"%firmwareId

    try:
        with open("%s/pid"%emu_dir_path, 'r') as pid_file:
            pid = int(pid_file.read())
    except Exception as e:
        response_data = {
            "status": "error",
            "message": f"{firmwareId} emulation has not been started."
        }

        return jsonify(response_data), 400

    if os.path.exists(emu_dir_path+"/status"):
        with open(emu_dir_path+"/status", "r") as status_file:
            content = status_file.read().strip()
            
            if content == "paused" or content == "paused_analyzing":
                response_data = {
                    "status": "error",
                    "message": f"{firmwareId} emulation has already been paused."
                }
                return jsonify(response_data), 400
            
            elif content == "booting":
                response_data = {
                    "status": "error",
                    "message": f"{firmwareId} is still booting."
                }
                return jsonify(response_data), 400
            
            elif content == "running_select":
                response_data = {
                    "status": "error",
                    "message": f"'select' operation on {firmwareId} is being processed."
                }
                return jsonify(response_data), 400

            elif content == "stopped" or content == "stopped_analyzing":
                response_data = {
                    "status": "error",
                    "message": f"{firmwareId} emulation has been stopped."
                }
                return jsonify(response_data), 400

            else:
                if content != "running":
                    assert(False)

    try:
        send_signal_recursive(pid, signal.SIGTSTP)
        with open(emu_dir_path+"/status", "w") as status_file:
            status_file.write("paused")
        time.sleep(1)
    except Exception as e:
        response_data = {
            "status": "error",
            "message": f"Error sending SIGTSTP signal to PID {pid}: {e}"
        }

        return jsonify(response_data), 500

    source_code="firmwares/source_code/%s"%firmwareId
    outdir="analysis/results/%s/dynamic_analysis/%s"%(firmwareId,find_next_run("analysis/results/%s/dynamic_analysis/"%firmwareId))
    workdir="FirmAE/scratch/firmafl/%s"%firmwareId2scratchId(firmwareId)

    command = "python3 analysis/analysis.py %s %s %s/%s/debug/full_system_syscall.log %s/%s/image_backup %s %s %s %s; \
                cp %s/user_interactions.pcap %s" \
                %(firmwareId, outdir, os.getcwd(), workdir, os.getcwd(), workdir, 
                  source_code, str(FACT_IP), str(FACT_PORT), factUid, workdir, outdir)

    try:
        with open(emu_dir_path+"/status", "w") as status_file:
            status_file.write("paused_analyzing")
        with open(os.devnull, "w") as f:
            process = subprocess.Popen(command, shell=True, stdout=f, stderr=f)
    except Exception as e:
        response_data = {
            "status": "error",
            "message": "Server could not analyze emulation data. %s" % e
        }

        return jsonify(response_data), 500
    
    return 'OK', 200

@app.route('/resume_emulation', methods=['POST'])
def resume_emulation():
    firmwareId = request.args.get('firmwareId', default=None)
    emu_dir_path="backend_runtime/emulation/%s"%firmwareId

    try:
        with open("%s/pid"%emu_dir_path, 'r') as pid_file:
            pid = int(pid_file.read())
    except Exception as e:
        response_data = {
            "status": "error",
            "message": f"{firmwareId} emulation has not been started."
        }

        return jsonify(response_data), 400

    if os.path.exists(emu_dir_path+"/status"):
        with open(emu_dir_path+"/status", "r") as status_file:
            content = status_file.read().strip()

            if content == "running":
                response_data = {
                    "status": "error",
                    "message": f"{firmwareId} emulation has not been paused."
                }
                return jsonify(response_data), 400

            elif content == "booting":
                response_data = {
                    "status": "error",
                    "message": f"{firmwareId} is still booting."
                }
                return jsonify(response_data), 400
            
            elif content == "running_select":
                response_data = {
                    "status": "error",
                    "message": f"'select' operation on {firmwareId} is being processed."
                }
                return jsonify(response_data), 400

            elif content == "stopped":
                response_data = {
                    "status": "error",
                    "message": f"{firmwareId} emulation has been stopped."
                }
                return jsonify(response_data), 400
            
            elif "analyzing" in content:
                response_data = {
                    "status": "error",
                    "message": f"{firmwareId} is being analyzed by another process."
                }
                return jsonify(response_data), 400

            else:
                if content != "paused":
                    assert(False)

    try:
        send_signal_recursive(pid, signal.SIGCONT)
        with open(emu_dir_path+"/status", "w") as status_file:
            status_file.write("running")
        time.sleep(1)
    except Exception as e:
        response_data = {
            "status": "error",
            "message": f"Error sending SIGTSTP signal to PID {pid}: {e}"
        }

        return jsonify(response_data), 500

    return 'OK', 200

@app.route('/stop_emulation', methods=['POST'])
def stop_emulation():
    firmwareId = request.args.get('firmwareId', default=None)
    factUid = request.args.get('factUid', default=None)
    emu_dir_path="backend_runtime/emulation/%s"%firmwareId

    try:
        with open("%s/pid"%emu_dir_path, 'r') as pid_file:
            pid = int(pid_file.read())
    except Exception as e:
        response_data = {
            "status": "error",
            "message": f"{firmwareId} emulation has not been started."
        }

        return jsonify(response_data), 400

    if os.path.exists(emu_dir_path+"/status"):
        with open(emu_dir_path+"/status", "r") as status_file:
            content = status_file.read().strip()

            if content == "stopped" or content == "stopped_analyzing":
                response_data = {
                    "status": "error",
                    "message": f"{firmwareId} emulation has already been stopped."
                }
                return jsonify(response_data), 400
            
            elif content == "booting":
                response_data = {
                    "status": "error",
                    "message": f"{firmwareId} is still booting."
                }
                return jsonify(response_data), 400
            
            elif content == "running_select":
                response_data = {
                    "status": "error",
                    "message": f"'select' operation on {firmwareId} is being processed."
                }
                return jsonify(response_data), 400

            elif "paused_analyzing" in content:
                response_data = {
                    "status": "error",
                    "message": f"{firmwareId} is being analyzed by another process."
                }
                return jsonify(response_data), 400

            else:
                if content != "paused" and content != "running":
                    assert(False)

    try:
        send_signal_recursive(pid, signal.SIGINT)
        with open(emu_dir_path+"/status", "w") as status_file:
            status_file.write("stopped")
        time.sleep(1)
    except Exception as e:
        response_data = {
            "status": "error",
            "message": f"Error sending SIGINT signal to PID {pid}: {e}"
        }

        return jsonify(response_data), 500

    source_code="firmwares/source_code/%s"%firmwareId
    outdir="analysis/results/%s/dynamic_analysis/%s"%(firmwareId,find_next_run("analysis/results/%s/dynamic_analysis/"%firmwareId))
    workdir="FirmAE/scratch/firmafl/%s"%firmwareId2scratchId(firmwareId)

    command = "python3 analysis/analysis.py %s %s %s/%s/debug/full_system_syscall.log %s/%s/image_backup %s %s %s %s; \
                cp %s/user_interactions.pcap %s" \
                %(firmwareId, outdir, os.getcwd(), workdir, os.getcwd(), workdir, 
                  source_code, str(FACT_IP), str(FACT_PORT), factUid, workdir, outdir)

    try:
        with open(emu_dir_path+"/status", "w") as status_file:
            status_file.write("stopped_analyzing")
        with open(os.devnull, "w") as f:
            process = subprocess.Popen(command, shell=True, stdout=f, stderr=f)
    except Exception as e:
        response_data = {
            "status": "error",
            "message": "Server could not analyze emulation data. %s" % e
        }

        return jsonify(response_data), 500

    return 'OK', 200

@app.route('/select', methods=['POST'])
def select():
    try:
        firmwareId = request.args.get('firmwareId')
        runId = request.args.get('runId')
        request_data = request.json
        select_data = request_data.get("select", [])
        
        exec_data_pairs = []
        for item in select_data:
            executable_id = item.get("executable_id")
            data_channel_id = item.get("data_channel_id")
            exec_data_pairs.append({"executable_id": executable_id, "data_channel_id": data_channel_id})

        exec_data_json = json.dumps(exec_data_pairs)
        os.environ["EXEC_DATA_PAIRS"] = exec_data_json
    
    except Exception as e:
        response_data = {
            "status": "error",
            "message": "Bad request. %s" % e
        }

        return jsonify(response_data), 400

    emu_dir_path="backend_runtime/emulation/%s"%firmwareId
    if not os.path.exists(emu_dir_path):
        os.makedirs(emu_dir_path)

    if os.path.exists(emu_dir_path+"/status"):
        with open(emu_dir_path+"/status", "r") as status_file:
            content = status_file.read().strip()

            if not content == "stopped":
                with open("%s/pid"%emu_dir_path, 'r') as pid_file:
                    pid = int(pid_file.read())
                    send_signal_recursive(pid, signal.SIGINT)
    
    if not os.path.exists("analysis/results/%s/dynamic_analysis/%s"%(firmwareId, runId)):
        response_data = {
            "status": "error",
            "message": f"({firmwareId}, {runId}) not found."
        }

        return jsonify(response_data), 400

    command = "export EXECUTION_MODE=1; export POSTGRESQL_IP=127.0.0.1; sudo service postgresql restart; \
            ./FirmAFL/flush_interface.sh; export RUN=%s; \
            ./docker_start.sh -r firmwares/%s" % (runId, firmwareId)

    try:
        with open(os.devnull, "w") as f:
            process = subprocess.Popen(command, shell=True, env=os.environ, stdout=f, stderr=f)
        with open(emu_dir_path+"/status", "w") as status_file:
            status_file.write("booting")
        with open(emu_dir_path+"/pid", "w") as status_file:
            status_file.write(str(process.pid))      
    except Exception as e:
        response_data = {
            "status": "error",
            "message": "Server could not process request. %s" % e
        }

        return jsonify(response_data), 500

    return 'OK', 200

@app.route('/execute', methods=['POST'])
def execute():
    try:
        firmwareId = request.args.get('firmwareId')
        runId = request.args.get('runId')
        request_data = request.json
        experiments_data = request_data.get("experiments", [])    
        experiments_data_json = json.dumps(experiments_data)
        os.environ["EXPERIMENTS_DATA"] = experiments_data_json
    
    except Exception as e:
        response_data = {
            "status": "error",
            "message": "Bad request. %s" % e
        }

        return jsonify(response_data), 400

    if not os.path.exists("analysis/results/%s/dynamic_analysis/%s"%(firmwareId, runId)):
        response_data = {
            "status": "error",
            "message": f"({firmwareId}, {runId}) not found."
        }

        return jsonify(response_data), 400

    emu_dir_path="backend_runtime/emulation/%s"%firmwareId
    if not os.path.exists(emu_dir_path):
        os.makedirs(emu_dir_path)

    if os.path.exists(emu_dir_path+"/status"):
        with open(emu_dir_path+"/status", "r") as status_file:
            content = status_file.read().strip()

            if not content == "stopped":
                with open("%s/pid"%emu_dir_path, 'r') as pid_file:
                    pid = int(pid_file.read())
                    send_signal_recursive(pid, signal.SIGINT)

    command = "export EXECUTION_MODE=2; export POSTGRESQL_IP=127.0.0.1; export RUN=%s; \
                ./FirmAFL/flush_interface.sh; sudo service postgresql restart; \
                ./docker_start.sh -f firmwares/%s" % (runId, firmwareId)
    
    try:
        process = subprocess.Popen(command, shell=True, env=os.environ)
        with open(emu_dir_path+"/status", "w") as status_file:
            status_file.write("booting")
        with open(emu_dir_path+"/pid", "w") as status_file:
            status_file.write(str(process.pid))  
    except Exception as e:
        response_data = {
            "status": "error",
            "message": "Server could not start fuzzing session. %s" % e
        }

        return jsonify(response_data), 500
    
    return 'OK', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
    