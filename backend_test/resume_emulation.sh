#!/bin/bash

curl -X POST \
     -H "Content-Type: application/json" \
     "http://localhost:4000/resume_emulation?firmwareId=DAP-2330_1.01.tar.gz"