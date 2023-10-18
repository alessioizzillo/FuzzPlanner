#!/bin/bash

echo -e "\033[32m[+]\033[0m\033[32m[+]\033[0m Building and updating tool..."
docker run -dit --rm --privileged --memory="15g" --network bridge --name FuzzPlanner -v /dev:/dev -v $(pwd):/FuzzPlanner fuzzplanner /bin/bash -c "bash";
docker attach FuzzPlanner;
sudo docker wait FuzzPlanner;
echo -e "\n"