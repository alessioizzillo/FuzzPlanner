#!/bin/bash
#
# american fuzzy lop - QEMU build script
# --------------------------------------
#
# Written by Andrew Griffiths <agriffiths@google.com> and
#            Michal Zalewski <lcamtuf@google.com>
#
# Copyright 2015, 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# This script downloads, patches, and builds a version of QEMU with
# minor tweaks to allow non-instrumented binaries to be run under
# afl-fuzz. 
#
# The modifications reside in patches/*. The standalone QEMU binary
# will be written to ../afl-qemu-trace.
#

ARGS=$1;

if [ "$ARGS" = "user" ] || [ "$ARGS" = "all" ]; then

    echo ""
    echo -e "\033[33m[*]\033[0m Starting QEMU User Mode compilation..!"

    echo "================================================="
    echo "AFL binary-only instrumentation QEMU build script"
    echo "================================================="
    echo

    echo -e "\033[33m[*]\033[0m Configuring QEMU (user mode)..."
    echo ""

    cd user_mode || exit 1

    ./configure --target-list=mipsel-linux-user,mips-linux-user,arm-linux-user --static --disable-werror --python=/usr/bin/python

    echo -e "\033[32m[+]\033[0m Configuration complete."

    echo -e "\033[33m[*]\033[0m Attempting to build QEMU (fingers crossed!)....this could take some time"

    make 2>&1 >qemu_user_make.log || exit 1

    echo -e "\033[32m[+]\033[0m Building process successful!"

    cd ..
fi

if [ "$ARGS" = "qemu" ] || [ "$ARGS" = "all" ]; then

    echo ""
    echo -e "\033[33m[*]\033[0m Starting QEMU System Mode compilation..!"

    echo "================================================="
    echo "QEMU System Mode Build script"
    echo "================================================="
    echo

    echo -e "\033[33m[*]\033[0m Configuring QEMU (system mode)..."

    cd qemu_mode/DECAF_qemu_2.10 || exit 1

    ./configure --target-list=mipsel-softmmu,mips-softmmu,arm-softmmu --static --disable-werror --python=/usr/bin/python

    echo -e "\033[32m[+]\033[0m Configuration complete."

    echo -e "\033[33m[*]\033[0m Attempting to build QEMU (fingers crossed!)...this could take some time"

    make 2>&1 >qemu_system_make.log || exit 1

    echo -e "\033[32m[+]\033[0m Building process successful!"

    cd ../..

fi

echo ""
echo -e "\033[32m[+]\033[0m All set, you can now (hopefully) use the -Q mode in afl-fuzz and qemu-system mode in qemu-mode"

exit 0
