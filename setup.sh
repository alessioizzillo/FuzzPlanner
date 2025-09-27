#!/bin/bash

# FuzzPlanner Setup Script
# This script handles the complete Docker-based setup process

function download()
{
  sudo apt-get update;
  export DEBIAN_FRONTEND=noninteractive;
  sudo ln -fs /usr/share/zoneinfo/Europe/Rome /etc/localtime;
  sudo apt-get install tzdata -y;
  
  while read line; do
    echo "************************** Installing $line ***********************"
    sudo apt-get install $line -y;
  done < FirmAFL/packages.txt
}

function setup_docker_environment()
{
  echo "[FuzzPlanner] Building Docker image..."
  ./docker.sh build

  echo "[FuzzPlanner] Starting container to run setup..."
  ./docker.sh run

  echo "[FuzzPlanner] Waiting for container to be ready..."
  sleep 5

  echo "[FuzzPlanner] Running setup inside container..."
  docker exec FuzzPlanner /bin/bash -c "cd /FuzzPlanner && ./setup.sh install"

  echo "[FuzzPlanner] Committing configured container to new image..."
  docker commit FuzzPlanner fuzzplanner

  echo "[FuzzPlanner] Stopping and removing temporary container..."
  docker stop FuzzPlanner
  docker rm FuzzPlanner

  echo ""
  echo "[FuzzPlanner] Setup complete! Use './docker.sh run' to start FuzzPlanner"
  echo ""
  echo "Access the application at:"
  echo "  Frontend: http://localhost:3000"
  echo "  Backend:  http://localhost:4000"

  exit 0
}

if [ "$1" != "install" ]; then
  setup_docker_environment
fi

apt update;
apt install sudo -y;
sudo apt-get install npm tshark rsync -y;
sudo apt-get install jq -y;
npm install --global prettier;

echo -e "***************************Starting installation of FirmAFL packages*********************************";
download

echo -e "***************************Starting installation of FirmAE packages*********************************";
cd FirmAE
./install.sh
cd -

echo -e "***************************Starting installation of Python3 packages*********************************";
pip3 install -q requests;
pip3 install -q scapy;
pip3 install -q flask;
pip3 install -q flask_cors;
pip3 install -q docker;
git clone https://github.com/KimiNewt/pyshark.git
cd pyshark/src
sudo python3 setup.py install
cd -
rm -r pyshark
pip3 install -q gunicorn;

echo -e "***************************Building FirmAFL*********************************";
cd FirmAFL
sudo make;
cd -

echo -e "***************************Setting Postgresql server*********************************";
sudo ./postgres.sh 127.0.0.1;
sudo service postgresql restart;

echo -e "***************************Installing Node.js*********************************";
sudo apt-get update;
sudo apt-get install -y ca-certificates curl gnupg;
sudo mkdir -p /etc/apt/keyrings;
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg;
NODE_MAJOR=20;
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list;
sudo apt-get update;
sudo apt-get install nodejs -y;

echo -e "***************************Installing Next.js*********************************";
cd webapp
npm init -y;
npm install next@latest react@latest react-dom@latest;
cd -

echo -e "***************************FINISHED*********************************";

