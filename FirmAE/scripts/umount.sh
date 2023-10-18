#!/bin/bash

set -e
set -u

if [ -e ./firmae.config ]; then
    source ./firmae.config
elif [ -e ../firmae.config ]; then
    source ../firmae.config
else
    echo "Error: Could not find 'firmae.config'!"
    exit 1
fi

if check_number $1; then
    echo "Usage: umount.sh <image ID> <tool>"
    exit 1
fi
IID=${1}
TOOL=${2}

if check_root; then
    echo "Error: This script requires root privileges!"
    exit 1
fi

echo "----Running----"
WORK_DIR=`get_scratch ${IID} ${TOOL}`
IMAGE=`get_fs ${IID} ${TOOL}`
IMAGE_DIR=`get_fs_mount ${IID} ${TOOL}`

DEVICE=`get_device`

echo "----Unmounting----"
umount "${DEVICE}"

echo "----Disconnecting Device File----"
kpartx -d "${IMAGE}"
losetup -d "${DEVICE}" &>/dev/null
dmsetup remove $(basename "${DEVICE}") &>/dev/null
