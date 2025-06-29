#!/bin/bash

if [ -z "$1" ]
    then
        echo "No argument supplied. Type \"build\", \"run\", \"attach\" or \"rm\"."
        exit 1
fi

case $1 in
    build)
        docker build --network=host --tag fuzzplanner .;
        ;;

    run)
    	docker run -dit --privileged --memory="15g" --network host --name FuzzPlanner -v /var/run/docker.sock:/var/run/docker.sock -v /dev:/dev -v $(pwd):/FuzzPlanner fuzzplanner;
        ;;

    run_exp_host)
    	docker run -dit --privileged --cpuset-cpus=$3 --memory="15g" --network host --name $2 --volumes-from FuzzPlanner --mount type=tmpfs,destination=/dev/shm fuzzplanner /bin/bash -c "$(cat runtime_tmp/command)";
        ;;

    run_exp_bridge)
    	docker run -dit --privileged --cpuset-cpus=$3 --memory="15g" --network bridge --name $2 --volumes-from FuzzPlanner --mount type=tmpfs,destination=/dev/shm fuzzplanner /bin/bash -c "$(cat runtime_tmp/command)";
        ;;

    attach)
        docker attach $2 --detach-keys ctrl-a;
        ;;

    rm)
        docker rm --force {$2};
        ;;

    rmi)
        docker rmi --force fuzzplanner;
        ;;
esac
