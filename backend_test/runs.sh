#!/bin/bash

curl -X GET \
     -H "Content-Type: application/json" \
     "http://localhost:4000/runs?firmwareId=dlink/DAP-2330_1.01.tar.gz"