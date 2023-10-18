#!/bin/bash

if [ -z "$1" ]
    then
        echo "No argument supplied. Type \"build\", \"run\", \"attach\" or \"rm\"."
        exit 1
fi

case $1 in
    build)
        docker build --tag fuzzplanner .;
        ;;

    run)
    	docker run -dit --privileged --cpuset-cpus $3 --memory="15g" --network bridge --name $2 -v /dev:/dev -v $(pwd):/FuzzPlanner fuzzplanner;
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
