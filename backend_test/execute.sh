#!/bin/bash

curl -X POST \
     -H "Content-Type: application/json" \
     -d @json/execute.json \
     "http://localhost:4000/execute?brandId=dlink&firmwareId=DAP-2330_1.01.tar.gz"