#!/bin/bash

curl -X POST \
     -H "Content-Type: application/json" \
     -d @json/select.json \
     "http://localhost:4000/select?firmwareId=dlink/DAP-2330_1.01.tar.gz&runId=run_0"