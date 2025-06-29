#!/bin/bash

sudo apt-get update
sudo apt-get install -y curl wget tar git ruby python python3 python3-pip bc
sudo python3 -m pip install --upgrade pip
sudo python3 -m pip install coloredlogs scapy "termcolor<3" colorama venn pandas scipy dpkt tabulate
sudo pip3 install -U cryptography

git clone https://github.com/KimiNewt/pyshark.git
cd pyshark/src
sudo python3 setup.py install
cd -

# for docker
sudo apt-get install -y docker.io

sudo apt install -y libpq-dev
python3 -m pip install psycopg2 psycopg2-binary

sudo apt-get install -y busybox-static bash-static fakeroot dmsetup kpartx netcat-openbsd nmap python3-psycopg2 snmp uml-utilities util-linux vlan

sudo apt-get install -y postgresql-client

# for binwalk
wget https://github.com/ReFirmLabs/binwalk/archive/refs/tags/v2.3.3.tar.gz
tar -xf v2.3.3.tar.gz
cd binwalk-2.3.3
sed -i 's/^install_unstuff//g' deps.sh
echo y | ./deps.sh
sudo python3 setup.py install
sudo apt-get install -y mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract fusecram cramfsswap squashfs-tools sleuthkit default-jdk cpio lzop lzma srecord zlib1g-dev liblzma-dev liblzo2-dev unzip
cd - # back to root of project

sudo cp core/unstuff /usr/local/bin/

python3 -m pip install python-lzo cstruct ubi_reader tqdm networkx
sudo apt-get install -y python3-magic openjdk-8-jdk unrar


# for analyzer, initializer
sudo apt-get install -y python3-bs4
python3 -m pip install selenium
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb; sudo apt-get -fy install
rm google-chrome-stable_current_amd64.deb
python3 -m pip install -r ./analyses/routersploit/requirements.txt
cd ./analyses/routersploit && patch -p1 < ../routersploit_patch && cd -

# for qemu
sudo apt-get install -y qemu-system-arm qemu-system-mips qemu-system-x86 qemu-utils

if ! test -e "./analyses/chromedriver"; then
    wget https://chromedriver.storage.googleapis.com/2.38/chromedriver_linux64.zip
    unzip chromedriver_linux64.zip -d ./analyses/
    rm -rf chromedriver_linux64.zip
fi
