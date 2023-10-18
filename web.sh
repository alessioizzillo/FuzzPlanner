#!/bin/bash
(
    DOCKER_BUILDKIT=1
    DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

    docker network create --subnet=173.17.0.0/24 fuzzplanner_network > /dev/null 2>&1;

    if [[ "$1" == "build-dev" ]]; then
        docker build --target=app-dev --tag=fuzzplanner/web-dev $DIR/webapp
    elif [[ "$1" == "run-dev" ]]; then
        docker run --rm -d -v $DIR/analysis/results:/home/pn/app/src/data --name FuzzPlanner_web-dev --network fuzzplanner_network --ip 173.17.0.3 -p 3000:3000 fuzzplanner/web-dev
    elif [[ "$1" == "build-prod" ]]; then
        docker build --target=app-prod --tag=fuzzplanner/web-prod $DIR/webapp
    elif [[ "$1" == "run-prod" ]]; then
        docker run --rm -d -v $DIR/analysis/results:/home/pn/app/src/data --name FuzzPlanner_web-prod --network fuzzplanner_network --ip 173.17.0.3 -p 3000:3000 fuzzplanner/web-prod
    else
        exit 1
    fi
)
