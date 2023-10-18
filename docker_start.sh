#!/bin/bash

auto_find_brand() {
    VAR=${1}
    dlink=("dir" "DIR" "DAP" "dap" "DCH" "dch" "DCS" "dcs" "EBR" "ebr" "DGS" "dgs" "DCS" "dcs" "dhp" "DHP" "dns" "DNS" "DSL" "dsl" "DWR" "dwr" "DWL" "dwl" "DVA" "dva")
    netgear=("R6" "r6" "R8" "r8" "R7" "r7" "WN" "wn" "JWN" "jwn" "EX" "ex" "DM" "dm" "DGN" "dgn" "JNR" "jnr" "DST" "dst" "AC" "ac" "Ac" "AX" "ax" \ 
    "RBR" "rbr" "rbs" "RBS" "XR5" "xr5" "SRS" "SRR" "srs" "srr" "WPN" "wpn" "WAC" "wac" "WGT" "wgt" "EVG" "evg" "D78" "WAG" "wag" "WAC" "wac" "GS" "gs" )
    tplink=("ARCHER" "Archer" "archer" "TL" "tl" "TD" "td" "VR" "vr" "EAP" "eap" "RE" "re" "CPE" "cpe" "WBS" "wbs")
    trendnet=("TEW" "tew" "tv-ip" "fw" "FW")

    for TEST in ${dlink[@]}
    do
        if [[ "${VAR}" == *"$TEST"* ]]; then
            echo "dlink"
            return
        fi
    done
    for TEST in ${netgear[@]}
    do
        if [[ "${VAR}" == *"$TEST"* ]]; then
            echo "netgear"
            return
        fi
    done
    for TEST in ${trendnet[@]}
    do
        if [[ "${VAR}" == *"$TEST"* ]]; then
            echo "trendnet"
            return
        fi
    done
    for TEST in ${tplink[@]}
    do
        if [[ "${VAR}" == *"$TEST"* ]]; then
            echo "tplink"
            return
        fi
    done
    
    echo "NotBrandFound"
}


stop() {
    wait
}


pause() {
    wait
}


send_signal_recursive() {
    local parent_pid=$1
    local signal=$2
    local child_pids=$(pgrep -P $parent_pid)
    for child_pid in $child_pids; do
        send_signal_recursive $child_pid $signal
    done
    kill -s $signal $parent_pid;
}


get_dict_types() {
    local dir="$1"
    local dict_types=""
    for file in "$dir"/*.dict; do
        seed_type=$(basename "$file" .dict)
        dict_types+="\"$seed_type\","
    done

    if [ -n "$dict_types" ]; then
        dict_types="${dict_types%,}"
    fi
    echo "$dict_types"
}


start()
{
    export ROOT_DIR=$(pwd)
    RESULTS_DIR=$ROOT_DIR/analysis/results
    
    ./flush_interface.sh > /dev/null 2>&1;

    cd FirmAE;

    if [ ${OPTION} = "-r" ]; then
        if ( ! ./scripts/util.py check_connection _ $PSQL_IP firmafl ); then
            if ( ! ./scripts/util.py check_connection _ $PSQL_IP firmafl ); then
                echo -e "[\033[31m-\033[0m] Docker container failed to connect to the hosts' postgresql!"
                exit 1;
            fi
        fi

        IID=`./scripts/util.py get_iid $FIRMWARE $PSQL_IP firmafl`
        if [[ ${IID} = "" ]] || [[ ! -d scratch/${IID} ]]; then
            echo -e "\033[32m[+]\033[0m\033[32m[+]\033[0m FirmAE: Creating Firmware Scratch Image"
            sudo -E ./run.sh -c ${BRAND} ${FIRMWARE} firmafl $PSQL_IP
            IID=`./scripts/util.py get_iid $FIRMWARE $PSQL_IP firmafl`
        fi

        WORK_DIR=scratch/firmafl/${IID}
        NAME=`cat $WORK_DIR/name`

        if [ -d ${WORK_DIR}/debug ]; then
            sudo rm -r ${WORK_DIR}/debug;
        fi

        export DEBUG=1;

        if [[ ${EXECUTION_MODE} = "0" ]]; then
            # save user interactions
            sudo tcpdump -i any host $(cat ${WORK_DIR}/ip) -w $WORK_DIR/user_interactions.pcap &
            TCPDUMP_PID=$!

            if (egrep -sqi "true" ${WORK_DIR}/web_check); then
                sudo -E ./run.sh -r ${BRAND} $FIRMWARE firmafl $PSQL_IP &
                QEMU_PID=$!
                echo "$$" > "$ROOT_DIR/backend_runtime/emulation/$NAME/pid"
                wait $QEMU_PID
            elif (! egrep -sqi "false" ping); then
                echo "WEB is FALSE and PING IS TRUE" 
                return
            else
                echo "WEB and PING ARE FALSE"
                return
            fi

        elif [[ ${EXECUTION_MODE} = "1" ]]; then
            exec_data_json="$EXEC_DATA_PAIRS"

            if [ -z "$exec_data_json" ]; then
                echo "EXEC_DATA_PAIRS is not set or empty."
                exit 1
            fi

            jq -c '.[]' <<< "$exec_data_json" | while read -r pair; do
                export TARGET_EXECUTABLE=$(echo "$pair" | jq -r '.executable_id')
                export TARGET_CHANNEL=$(echo "$pair" | jq -r '.data_channel_id')

                if (egrep -sqi "true" ${WORK_DIR}/web_check); then
                    sudo -E ./run.sh -r ${BRAND} $FIRMWARE firmafl $PSQL_IP &
                    QEMU_PID=$!

                    while true; do
                        status=$(<"$ROOT_DIR/backend_runtime/emulation/$NAME/status")
                        if [ "$status" = "running_select" ]; then
                            user_interactions_pcap=$ROOT_DIR/analysis/results/$NAME/dynamic_analysis/$RUN/user_interactions.pcap
                            python3 $ROOT_DIR/analysis/replay_packets.py $user_interactions_pcap $(cat ${WORK_DIR}/ip) $WORK_DIR
                            break
                        fi
                        sleep 1;
                    done
                    sleep 5;    # Give it time to process
                    send_signal_recursive $QEMU_PID SIGKILL

                    wait $QEMU_PID

                    engine_features=$(cat "$ROOT_DIR/config/AFL_features.json" | jq -c '.')
                    dict_types=$(get_dict_types "$ROOT_DIR/config/dictionaries")

                    temp_file=$(mktemp)
                    awk -F',' '!seen[$2]++' "$WORK_DIR/debug/forkpoints.log" > "$temp_file"
                    mv "$temp_file" "$WORK_DIR/debug/forkpoints.log"

                    log_list=()
                    while IFS= read -r line; do
                        IFS=',' read -ra elements <<< "$line"
                        
                        if [ "${#elements[@]}" -ge 3 ]; then
                            syscall="${elements[0]}"
                            pc="${elements[1]}"
                            pattern="${elements[2]}"
                            log_list+=('{"syscall":"'"$syscall"'", "pc":"'"$pc"'", "pattern":"'"$pattern"'"}')
                        fi
                    done < "$WORK_DIR/debug/forkpoints.log"

                    parameters="["
                    parameters+="$(IFS=,; echo "${log_list[*]}")"
                    parameters+="]"

                    body="{
                        \"engine_features\": $engine_features,
                        \"dict_types\": [$dict_types],
                        \"analysis\": [
                            {
                                \"executable_id\": \"$TARGET_EXECUTABLE\",
                                \"data_channel_id\": \"$TARGET_CHANNEL\",
                                \"parameters\": $parameters
                            }
                        ]
                    }"

                    body=$(echo "$body" | jq '.')

                    echo "$body"

                    while true; do
                        curl -X POST -H "Content-Type: application/json" --expect100-timeout 1 \
                            -d "$body" "http://localhost:3000/api/select_res?firmwareId=$NAME&runId=$RUN"
                        
                        if [ $? -eq 0 ]; then
                            echo "HTTP POST request was successful."
                            break
                        else
                            echo "HTTP POST request failed. Retrying in 1 seconds..."
                            sleep 1
                        fi
                    done          

                elif (! egrep -sqi "false" ping); then
                    echo "WEB is FALSE and PING IS TRUE" 
                    return
                else
                    echo "WEB and PING ARE FALSE"
                    return
                fi
            done
            echo "stopped" > "$ROOT_DIR/backend_runtime/emulation/$NAME/status"
        fi


    elif [ ${OPTION} = "-f" ]; then
        if ( ! ./scripts/util.py check_connection _ $PSQL_IP firmafl ); then
            if ( ! ./scripts/util.py check_connection _ $PSQL_IP firmafl ); then
                echo -e "[\033[31m-\033[0m] Docker container failed to connect to the hosts' postgresql!"
                exit 1;
            fi
        fi

        IID=`./scripts/util.py get_iid $FIRMWARE $PSQL_IP firmafl`
        if [[ ${IID} = "" ]] || [[ ! -d scratch/${IID} ]]; then
            echo -e "\033[32m[+]\033[0m\033[32m[+]\033[0m FirmAE: Creating Firmware Scratch Image"
            sudo -E ./run.sh -c ${BRAND} ${FIRMWARE} firmafl $PSQL_IP
            IID=`./scripts/util.py get_iid $FIRMWARE $PSQL_IP firmafl`
        fi

        WORK_DIR=scratch/firmafl/${IID}
        NAME=`cat $WORK_DIR/name`

        if [ -d ${WORK_DIR}/debug ]; then
            sudo rm -r ${WORK_DIR}/debug;
        fi

        export DEBUG=1;

        experiments_data_json="$EXPERIMENTS_DATA"

        if [ -z "$experiments_data_json" ]; then
            echo "EXPERIMENTS_DATA is not set or empty."
            exit 1
        fi

        echo "$experiments_data_json" | jq -c '.[]' | while read -r experiment; do
            executableId=$(jq -r '.executableId' <<< "$experiment")
            data_channel_id=$(jq -r '.data_channel_id' <<< "$experiment")
            chosen_dictionary_type=$(jq -r '.chosen_dictionary_type' <<< "$experiment")
            fuzzing_timeout=$(jq -r '.fuzzing_timeout' <<< "$experiment")
            child_timeout=$(jq -r '.child_timeout' <<< "$experiment")
            pc=$(jq -r '.chosen_parameters.pc' <<< "$experiment")
            syscall=$(jq -r '.chosen_parameters.syscall' <<< "$experiment")
            
            export TARGET_EXECUTABLE="$executableId"
            export TARGET_CHANNEL="$data_channel_id"
            export TARGET_PC="$pc"
            export TARGET_SYSCALL="$syscall"
            
            dictionary="$ROOT_DIR/config/dictionaries/$chosen_dictionary_type.dict"
            
            echo "export TARGET_EXECUTABLE=\"$executableId\""
            echo "export TARGET_CHANNEL=\"$data_channel_id\""
            echo "export TARGET_PC=\"$pc\""
            echo "export TARGET_SYSCALL=\"$syscall\""
            
            jq -c '.set_engine_features[]' <<< "$experiment" | while read -r feature; do
                name=$(jq -r '.name' <<< "$feature")
                type=$(jq -r '.type' <<< "$feature")
                value=$(jq -r '.value' <<< "$feature")

                if [ ${type} = "boolean" ]; then
                    export $name
                    echo "export $name"
                else
                    export $name=$value
                    echo "export $name=$value"
                fi
            done

            export FUZZ=1;

            # Bind mount to /dev/null, /dev/urandom, /proc/cpuinfo and /proc/stat
            mkdir ${WORK_DIR}/dev > /dev/null 2>&1;
            touch ${WORK_DIR}/dev/null > /dev/null 2>&1;
            mount --bind /dev/null ${WORK_DIR}/dev/null > /dev/null 2>&1;
            touch ${WORK_DIR}/dev/urandom > /dev/null 2>&1;
            mount --bind /dev/urandom ${WORK_DIR}/dev/urandom > /dev/null 2>&1;
            mkdir ${WORK_DIR}/proc_host > /dev/null 2>&1;
            touch ${WORK_DIR}/proc_host/stat > /dev/null 2>&1;
            mount --bind /proc/stat ${WORK_DIR}/proc_host/stat > /dev/null 2>&1;  

            # First check on the firmware correctness for fuzzing
            # NORMAL Case where PING is TRUE, WEB is TRUE.
            echo "${WORK_DIR}/web_check"
            cat "${WORK_DIR}/web_check"
            if (egrep -sqi "true" ${WORK_DIR}/web_check); then
                # We have to wait that the firmware is up. Then we can start
                echo -e "\033[33m[*]\033[0m Starting emulation of the firmware..."

            elif (! egrep -sqi "false" ping); then
                # Case where PING is TRUE, WEB is FALSE. Type of fuzzing?
                echo "WEB is FALSE and PING IS TRUE - What type of fuzzing we do? At the moment exiting" 
                return

            else   
                # Case where both WEB and PING are False. Type of fuzzing?
                echo "WEB and PING ARE FALSE - What type of fuzzing we do? At the moment exiting"
                return
            fi
            
            # First I start qemu-system mode of the firmware and put it in background
            echo "sudo -E ./run.sh -f ${BRAND} $FIRMWARE firmafl $PSQL_IP 2>&1 > ${WORK_DIR}/run_emulation.log &"
            sudo -E ./run.sh -r ${BRAND} $FIRMWARE firmafl $PSQL_IP 2>&1 > ${WORK_DIR}/run_emulation.log &
            QEMU_PID=$!

            # Loop until the file content matches the expected value
            while true; do
                status=$(<"$ROOT_DIR/backend_runtime/emulation/$NAME/status")
                if [ "$status" = "running_execute" ]; then
                    user_interactions_pcap=$ROOT_DIR/analysis/results/$NAME/dynamic_analysis/$RUN/user_interactions.pcap
                    python3 $ROOT_DIR/analysis/replay_packets.py $user_interactions_pcap $(cat ${WORK_DIR}/ip) $WORK_DIR
                    break
                fi
                sleep 1;
            done
            
            # Enter to the WorkFolder to start the fuzzer
            cd ${WORK_DIR}

            while [[ ! $(wc -l < mapping_table | xargs) -gt 20 ]]
            do
                sleep 2
            done

            echo -e "\033[32m[+]\033[0m Web server has been reached !"
            
            # Some Web Services may have been already activated without POST request, so we handle this case.
            MAP_TAB_LINES=$(wc -l < mapping_table | xargs)
            if [ ${MAP_TAB_LINES} -gt 20 ]; then
                echo -e "\033[32m[+]\033[0m The Mapping Table of the binary program has been configured successfully!"

            else
                echo -e "\033[31m[-]\033[0m Mapping Table is not configured! Without configuration you will have problems later...we are stopping here. See the README to know more"
                exit
            fi

            echo ""
            echo -e "\033[32m[+]\033[0m All set..Now we can start the fuzzer"
            output_dir=$ROOT_DIR/fuzzing_results/$NAME/outputs
            cp $dictionary keywords
            AFL="./afl-fuzz -m none -t 800000+ -Q -i inputs -o outputs -x keywords"

            if [ ! -d "$ROOT_DIR/fuzzing_results/$NAME" ]; then
                mkdir -p "$ROOT_DIR/fuzzing_results/$NAME"
            fi

            if [[ -f "service" ]]; then
                TARGET_PROGRAM_PATH=$(cat service)
            else
                echo -e "\033[31m[-]\033[0m The target program has not been specified!"
                exit 
            fi
            echo -e "\033[32m[->]\033[0m $AFL $TARGET_PROGRAM_PATH"
            echo -e "\033[32m[->]\033[0m To change it go to FirmAE/scratch/firmafl/<ID>/fuzz_line"
            sleep 3

            # The fuzzer cannot start with an already existing /outputs folder so we removes it
            if [ -e outputs ]; then
                sudo rm -r outputs;
            fi

            # Some configuration lines of the fuzzer
            echo core | sudo tee /proc/sys/kernel/core_pattern;
            export AFL_SKIP_CPUFREQ=1;

            TARGET_PROGRAM_PATH=${TARGET_PROGRAM_PATH%%[[:space:]]*}
            TARGET_PROGRAM_PATH="${TARGET_PROGRAM_PATH:1}"

            if [ -f run_count ]; then
                count=$(cat run_count)
                count=$((count+1))
                echo $count > run_count
            else
                echo 0 > run_count
            fi

            CPU_TO_BIND=$(sed -n 's/Cpus_allowed_list:\t\([0-9]*\).*/\1/p' /proc/self/status)
            export FUZZING_TIMEOUT=$fuzzing_timeout
            export CHILD_TIMEOUT=$child_timeout

            chroot . ${AFL} -b $CPU_TO_BIND ${TARGET_PROGRAM_PATH} @@

            sudo chmod 777 -R outputs
            sudo chmod 777 -R outputs

            cp -R outputs $output_dir           
            echo -e "\033[32m[+]\033[0m\033[32m[+]\033[0m Ending Fuzzing Session - Check the result on the outputs directory!"
            send_signal_recursive $QEMU_PID SIGKILL
        done

        echo "stopped" > "$ROOT_DIR/backend_runtime/emulation/$NAME/status"


    elif [ ${OPTION} = "-d" ]; then
        if ( ! ./scripts/util.py check_connection _ $PSQL_IP firmafl ); then
            if ( ! ./scripts/util.py check_connection _ $PSQL_IP firmafl ); then
                echo -e "[\033[31m-\033[0m] docker container failed to connect to the hosts' postgresql!"
                exit 1;
            fi
        fi

        IID=`./scripts/util.py get_iid $FIRMWARE $PSQL_IP firmafl`
        if [[ ${IID} = "" ]] || [[ ! -d scratch/${IID} ]]; then
            echo -e "[\033[31m-\033[0m] $FIRMWARE image (IID = $IID) does not exist!"
            echo -e "\n"
        fi

        if [[ ! ${IID} = "" ]] && [[ -d scratch/${IID} ]]; then
            WORK_DIR=scratch/firmafl/${IID}

            if [ -d ${WORK_DIR}/debug ]; then
                sudo rm -r ${WORK_DIR}/debug;
            fi

            echo -e "\033[32m[+]\033[0m\033[32m[+]\033[0m Removing $FIRMWARE image (IID = $IID)"
            echo -e "\n"
        
            export PGPASSWORD="firmadyne"
            sudo -E ./scripts/delete.sh ${IID} ${PSQL_IP} > /dev/null 2>&1;
        fi
    else
        print_usage
        exit 1        
    fi

    exit 0
}

if [[ ${EXECUTION_MODE} = "0" ]]; then
    trap stop SIGINT
    trap pause SIGTSTP
fi

OUTDIR=""
OPTION=${1}
FIRMWARE=$(readlink -f ${2})
PSQL_IP=$POSTGRESQL_IP
BRAND=$(auto_find_brand ${FIRMWARE})
IID=""

# I will be working in FirmAE directory, so I adjust the firmware relative path if needed
firstCharacter=${FIRMWARE:0:1}
if [ ! $firstCharacter = "/" ]; then
    FIRMWARE="../${FIRMWARE}"
fi

start ${FIRMWARE}
