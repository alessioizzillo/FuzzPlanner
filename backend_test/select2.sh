#!/bin/bash

curl -X POST \
     -H "Content-Type: application/json" \
     -d @json/select2.json \
     "http://localhost:4000/select?firmwareId=DAP-2330_1.01.tar.gz&runId=run_0"