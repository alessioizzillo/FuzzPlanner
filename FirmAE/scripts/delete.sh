#!/bin/bash

if [ -e ./firmae.config ]; then
    source ./firmae.config
elif [ -e ../firmae.config ]; then
    source ../firmae.config
else
    echo "Error: Could not find 'firmae.config'!"
    exit 1
fi

if [ $# -ne 3 ]; then
    echo "Usage: $0 <image ID> <mode> <psql_ip>"
    echo "This script deletes a whole project"
    exit 1
fi

IID=${1}
MODE=${2}

# Assign abbreviation based on MODE
if [ "${MODE}" == "run" ]; then
    mode_abbr="run"
elif [[ "${MODE}" == *"firmafl"* ]]; then
    suffix=${MODE#*"firmafl"}
    mode_abbr="fa${suffix}"
else
    echo "ERROR: Insert mode!"
    exit 1
fi

PSQL_IP=${3}

if [ "${mode_abbr}" = "" ]; then
    echo "ERROR: Insert mode!"
    exit 1
fi

#Check that no qemu is running:
echo "checking the process table for a running qemu instance ..."
PID=`ps -ef | grep qemu | grep "${IID}" | grep -v grep | awk '{print $2}'`
if ! [ -z $PID ]; then
    echo "killing process ${PID}"
    sudo kill -9 ${PID}
fi

PID1=`ps -ef | grep "${IID}\/run.sh" | grep -v grep | awk '{print $2}'`
if ! [ -z $PID1 ]; then
    echo "killing process ${PID1}"
    sudo kill ${PID1}
fi

#Check that nothing is mounted:
echo "In case the filesystem is mounted, umount it now ..."
sudo ./scripts/umount.sh ${IID} ${MODE}

#Check network config
echo "In case the network is configured, reconfigure it now ..."
for i in {0..4}; do
    sudo ifconfig tap_${mode_abbr}_${IID}_${i} down
    sudo tunctl -d tap_${mode_abbr}_${IID}_${i}
done

#Cleanup database:
echo "Remove the database entries ..."
psql -d firmware_${MODE} -U firmadyne -h $PSQL_IP -p 6666 -t -q -c "DELETE from image WHERE id=${IID};"

#Cleanup filesystem:
echo "Clean up the file system ..."
if [ -f "/tmp/qemu.${IID}*" ]; then
    sudo rm /tmp/qemu.${IID}*
fi

if [ -f ./images/${MODE}/${IID}.tar.gz ]; then
    sudo rm ./images/${MODE}/${IID}.tar.gz
fi

if [ -f ./images/${MODE}/${IID}.kernel ]; then
    sudo rm ./images/${MODE}/${IID}.kernel
fi

if [ -d ./scratch/${MODE}/${IID}/ ]; then
    sudo umount ./scratch/${MODE}/${IID}/dev/null;
    sudo umount ./scratch/${MODE}/${IID}/dev/urandom;
    sudo umount ./scratch/${MODE}/${IID}/equafl_image/dev/null;
    sudo umount ./scratch/${MODE}/${IID}/equafl_image/dev/urandom;
    sudo rm -r ./scratch/${MODE}/${IID}/
fi

echo "Done. Removed project ID ${IID}."
