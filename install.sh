#!/bin/bash

echo -e "\033[32m[+]\033[0m\033[32m[+]\033[0m Building docker image..."
docker build --tag fuzzplanner_tmp .;
echo -e "\n"

echo -e "\033[32m[+]\033[0m\033[32m[+]\033[0m Running docker container and installing tool..."
docker run -dit --privileged --memory="15g" --network host --name FuzzPlanner_tmp -v /dev:/dev -v $(pwd):/FuzzPlanner fuzzplanner_tmp /bin/bash -c "./docker_setup.sh";
docker attach FuzzPlanner_tmp;
sudo docker wait FuzzPlanner_tmp;
echo -e "\n"

echo -e "\033[32m[+]\033[0m\033[32m[+]\033[0m Committing docker container..."
sudo docker commit FuzzPlanner_tmp fuzzplanner;
sudo docker stop FuzzPlanner_tmp;
sudo docker rm FuzzPlanner_tmp;
sudo docker rmi fuzzplanner_tmp;
echo -e "\n"

echo -e "\033[32m[+]\033[0m\033[32m[+]\033[0m Done!"