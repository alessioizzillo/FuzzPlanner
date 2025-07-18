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

if check_number $2; then
    echo "Usage: run.mipseb.sh <image ID>"
    exit 1
fi
MODE=${1}
IID=${2}
QEMU_INIT=${3}

WORK_DIR=`get_scratch ${IID} ${MODE}`
IMAGE=`get_fs ${IID} ${MODE}`
KERNEL=`get_kernel "mipseb" false`
QEMU_MACHINE=`get_qemu_machine "mipseb"`
QEMU_ROOTFS=`get_qemu_disk "mipseb"`

if (${FIRMAE_NET}); then
  QEMU_NETWORK="-device e1000,netdev=net1 -netdev user,id=net1 -device e1000,netdev=net2 -netdev user,id=net2 -device e1000,netdev=net3 -netdev user,id=net3 -device e1000,netdev=net4 -netdev user,id=net4"
else
  QEMU_NETWORK="-device e1000,netdev=net0 -netdev socket,id=net0,listen=:2000 -device e1000,netdev=net1 -netdev socket,id=net1,listen=:2001 -device e1000,netdev=net2 -netdev socket,id=net2,listen=:2002 -device e1000,netdev=net3 -netdev socket,id=net3,listen=:2003"
fi

cd ${WORK_DIR}
qemu-system-mips -m 256 -M ${QEMU_MACHINE} -kernel ${KERNEL} -drive if=ide,format=raw,file=${IMAGE} -append "firmadyne.syscall=1 root=${QEMU_ROOTFS} console=ttyS0 nandsim.parts=64,64,64,64,64,64,64,64,64,64 ${QEMU_INIT} rw debug ignore_loglevel print-fatal-signals=1 FIRMAE_NET=${FIRMAE_NET} FIRMAE_NVRAM=${FIRMAE_NVRAM} FIRMAE_KERNEL=${FIRMAE_KERNEL} FIRMAE_ETC=${FIRMAE_ETC} user_debug=31" -serial file:${WORK_DIR}/qemu.initial.serial.log -serial unix:/tmp/qemu.${IID}.S1,server,nowait -monitor unix:/tmp/qemu.${IID},server,nowait -display none ${QEMU_NETWORK}
cd -