#!/bin/bash

curl -X POST \
     -H "Content-Type: application/json" \
     "http://localhost:4000//select?brandId=dlink&firmwareId=DAP-2330_1.01.tar.gz&runId=run_0&binaryId=/sbin/httpd&dataChannelId=socket(domain:10,type:2,protocol:6)%7Baddr:0.0.0.0;port:80%7D"