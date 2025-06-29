#!/bin/bash

if [ $# -ne 3 ]; then
    echo $0: Usage: ./test_emulation.sh [iid] [arch]
    exit 1
fi

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

./flush_interface.sh

MODE=${1}
IID=${2}
WORK_DIR=`get_scratch ${IID} ${MODE}`
ARCH=${3}

echo "[*] test emulator"

if [[ ${MODE} = "run" ]]; then
  EXEC_MODE=RUN TAINT=1 FD_DEPENDENCIES_TRACK=1 ${WORK_DIR}/run.sh 1 2>&1 >${WORK_DIR}/emulation.log &
else
  EXEC_MODE=RUN TAINT=1 FD_DEPENDENCIES_TRACK=1 ${WORK_DIR}/run_$MODE.sh 1 2>&1 >${WORK_DIR}/emulation.log &
fi

echo ""

IPS=()
if (egrep -sq true ${WORK_DIR}/isDhcp); then
  IPS+=("127.0.0.1")
  echo true > ${WORK_DIR}/ping
else
  IP_NUM=`cat ${WORK_DIR}/ip_num`
  for (( IDX=0; IDX<${IP_NUM}; IDX++ ))
  do
    IPS+=(`cat ${WORK_DIR}/ip.${IDX}`)
  done
fi

echo -e "[*] Waiting web service... from ${IPS[@]}"
read IP PING_RESULT WEB_RESULT TIME_PING TIME_WEB < <(check_network "${IPS[@]}" false)
echo -e "IP=$IP, PING_RESULT=$PING_RESULT, WEB_RESULT=$WEB_RESULT, TIME_PING=$TIME_PING, TIME_WEB=$TIME_WEB"

if (${PING_RESULT}); then
    echo true > ${WORK_DIR}/ping
    echo ${TIME_PING} > ${WORK_DIR}/time_ping
    echo ${IP} > ${WORK_DIR}/ip
fi
if (${WEB_RESULT}); then
    echo true > ${WORK_DIR}/web_check
    echo ${TIME_WEB} > ${WORK_DIR}/time_web
fi

kill $(ps aux | grep `get_qemu ${ARCH}` | awk '{print $2}') 2> /dev/null | true

sleep 2
