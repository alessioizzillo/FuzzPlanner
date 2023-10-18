#!/bin/bash

dictionary_types='["http", "dns", "generic"]'

analysis_elements=()


print_usage()
{
    echo "####-USAGE GUIDE-#####"
    echo ""
    echo -e "\033[32m[->]\033[0m Usage: $ sudo ${0} [mode] [firmware]"
    echo ""
    echo "[mode]: use one option at once"
    echo "      -r        Run emulation with qemu-system"
    echo "      -u        Update results with FACT analysis"
    echo "      -d        Delete emulation firmware image"
    echo "      -h        Help"
    echo ""
}


OPTION=${1}
FIRMWARE=${2}

if [ $# -eq 0 ] || [ "$OPTION" = "-h" ]; then 
	print_usage
    exit 1
fi

if [ $# -ne 2 ]; then
    echo -e "\033[31m[-]\033[0m Wrong number of arguments. Please read the USAGE and try again.."
    echo ""
    print_usage ${0}
    exit 1
fi

if (! id | egrep -sqi "root"); then
  echo -e "\033[31m[-]\033[0m This script must run with 'root' privilege"
  exit 1
fi

docker network create --subnet=173.17.0.0/24 fuzzplanner_network > /dev/null 2>&1;
sudo docker rm FuzzPlanner_web-prod --force > /dev/null 2>&1;
sudo ./web.sh build-prod
sudo ./web.sh run-prod

sudo docker rm FuzzPlanner --force > /dev/null 2>&1;
sudo docker run -dit --rm --privileged --memory="15g" --network host --name FuzzPlanner -v /dev:/dev \
    -v $(pwd):/FuzzPlanner fuzzplanner /bin/bash -c "export EXECUTION_MODE=0; export POSTGRESQL_IP=127.0.0.1; \
    sudo service postgresql restart > /dev/null 2>&1; ./FirmAFL/flush_interface.sh > /dev/null 2>&1; \
    ./docker_start.sh $OPTION $FIRMWARE";
sudo docker attach FuzzPlanner --detach-keys ctrl-a;

substring_after_last_slash="${FIRMWARE##*/}"
substring_without_extension="${substring_after_last_slash%.*}"
scratch_dir=$(find FirmAE/scratch/firmafl -type d -exec test -e '{}/name' \; -exec grep -q "$substring_without_extension" '{}/name' \; -print -quit)

# Check if a result was found
if [ -n "$scratch_dir" ]; then
  echo "Scratch dir: $scratch_dir"
else
  echo "No matching subdirectory found."
  exit 1
fi

if [ "$OPTION" = "-r" ]; then
    PORT=4000

    request_data=$(nc -l -p $PORT )
    json_data=$(echo "$request_data" | sed -n '/{/,/}/p')
    pair_list=$(echo "$json_data" | jq -r '.selectingPOSTvizToAnalysis[] | "\(.executable_id), \(.data_channel_id)"')

    while IFS= read -r pair; do
        IFS=',' read -r executable_id data_channel_id <<< "$pair"

        TARGET_EXECUTABLE=$executable_id
        TARGET_CHANNEL=$data_channel_id

        echo "Executable ID: $TARGET_EXECUTABLE"
        echo "Data Channel ID: $TARGET_CHANNEL"

        sudo docker rm FuzzPlanner --force > /dev/null 2>&1;
        sudo docker run -dit --rm --privileged --memory="15g" --network fuzzplanner_network \
            --ip 173.17.0.2 --name FuzzPlanner -v /dev:/dev -v $(pwd):/FuzzPlanner fuzzplanner /bin/bash \
            -c "export EXECUTION_MODE=1; export POSTGRESQL_IP=127.0.0.1; sudo service postgresql restart > /dev/null 2>&1; \
            ./FirmAFL/flush_interface.sh > /dev/null 2>&1; export TARGET_EXECUTABLE='$TARGET_EXECUTABLE'; \
            export TARGET_CHANNEL='$TARGET_CHANNEL'; ./docker_start.sh $OPTION $FIRMWARE";
        sudo docker wait FuzzPlanner

        # docker run -dit --rm --privileged --memory="15g" --network fuzzplanner_network \
        #     --ip 173.17.0.1 --name FuzzPlanner -v /dev:/dev -v $(pwd):/FuzzPlanner fuzzplanner /bin/bash \
        #     -c "export EXECUTION_MODE=2; export FUZZ=1; export POSTGRESQL_IP=172.17.0.1; \
        #     sudo service postgresql restart > /dev/null 2>&1; ./export_env_vars.sh; ./docker_start.sh -f $FIRMWARE" 

        # sudo docker attach FuzzPlanner --detach-keys ctrl-a;

        parameters_list=()

        while IFS= read -r line; do
            syscall=$(echo "$line" | cut -d ',' -f1)
            pc=$(echo "$line" | cut -d ',' -f2)
            pattern=$(echo "$line" | cut -d ',' -f3)
            
            parameter='{
                "syscall": "'"$syscall"'",
                "pc": "'"$pc"'",
                "pattern": "'"$pattern"'"
            }'
            
            parameters_list+=("$parameter")
        done < "$scratch_dir/debug/forkpoints.log"

        analysis_element='{
            "executable_id": "${executable_id}",
            "data_channel_id": "${data_channel_id}",
            "parameters": ['"${parameters_list[$i]}"']
        }'

        analysis_elements+=("$analysis_element")

    done <<< "$pair_list"

    # Combine all components into the final JSON response
    json_response='{
        "selectingRESanalysisToViz": {
            "engine_features": '"$engine_features"',
            "dictionary_types": '"$dictionary_types"',
            "analysis": ['"${analysis_elements[*]}"']
        }
    }'

    echo -n "$json_response"

    # Send the JSON response to localhost on port 3000 using netcat (nc)
    echo -n "$json_response" | nc -q 1 localhost 3000 > /dev/null 2>&1;


#TODO: Test the snippet below
    nc -l -p "$port" > executingPOSTvizToAnalysis.json

    sudo docker run -dit --rm --privileged --memory="15g" --network fuzzplanner_network \
        --ip 173.17.0.1 --name FuzzPlanner -v /dev:/dev -v $(pwd):/FuzzPlanner fuzzplanner /bin/bash \
        -c "export EXECUTION_MODE=2; export FUZZ=1; export POSTGRESQL_IP=172.17.0.1; \
        sudo service postgresql restart > /dev/null 2>&1; ./export_env_vars.sh; ./docker_start.sh -f $FIRMWARE";
    sudo docker attach FuzzPlanner --detach-keys ctrl-a;

fi

echo -e "\033[32m[+]\033[0m\033[32m[+]\033[0m HAVE A GOOD DAY :)"
