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
    echo "Usage: umount.sh <image ID> <mode>"
    exit 1
fi
IID=${1}
MODE=${2}

# Assign abbreviation based on MODE

if [ "${MODE}" == "run" ]; then
    mode_abbr="run"
elif [[ "${MODE}" == *"firmafl"* ]]; then
    suffix=${MODE#*"firmafl"}
    mode_abbr="sb${suffix}"
else
    echo "ERROR: Insert mode!"
    exit 1
fi


if check_root; then
    echo "Error: This script requires root privileges!"
    exit 1
fi

echo "----Running----"
WORK_DIR=`get_scratch ${IID} ${mode_abbr}`
IMAGE=`get_fs ${IID} ${mode_abbr}`
IMAGE_DIR=`get_fs_mount ${IID} ${mode_abbr}`

DEVICE=`get_device`

echo "----Unmounting----"
umount "${DEVICE}"

echo "----Disconnecting Device File----"
kpartx -d "${IMAGE}"
losetup -d "${DEVICE}" &>/dev/null
dmsetup remove $(basename "${DEVICE}") &>/dev/null
