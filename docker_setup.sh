#!/bin/bash

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

apt update;
apt install sudo -y;
sudo apt-get install npm -y;
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

