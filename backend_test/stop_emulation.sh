#!/bin/bash

curl -X POST \
     -H "Content-Type: application/json" \
     "http://localhost:4000/stop_emulation?firmwareId=dlink/DAP-2330_1.01.tar.gz"