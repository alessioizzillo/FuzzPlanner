#!/usr/bin/env python3
# This script updates the firmware directories in FirmAE/scratch/<mode>/ 
# by copying the necessary AFL and QEMU executables based on architecture.

import sys
import os

if len(sys.argv) < 2:
    print("ERROR: Insert mode!")
    exit(1)

mode = sys.argv[1]
firm_base_dir = "FirmAE/scratch/"

def process_mode(current_mode):
    firm_dir = os.path.join(firm_base_dir, current_mode)
    
    if not os.path.isdir(firm_dir):
        print(f"WARNING: Mode directory {firm_dir} does not exist, skipping.")
        return

    dir_list = os.listdir(firm_dir)
    cmd = []

    for name in dir_list:
        arch_file = os.path.join(firm_dir, name, "architecture")

        if not os.path.exists(arch_file):
            print(f"WARNING: Architecture file not found for {name}, skipping.")
            continue

        with open(arch_file, "r") as file:
            firm_architecture = file.readline().strip()

        target_dir = os.path.join(firm_dir, name)

        cmd.append(f"sudo cp -f FirmAFL/AFL/afl-fuzz {target_dir}/")

        if "mipseb" in firm_architecture:
            cmd.append(f"sudo cp -f FirmAFL/qemu_mode/DECAF_qemu_2.10/mips-softmmu/qemu-system-mips {target_dir}/afl-qemu-system-trace")
            cmd.append(f"sudo cp -f FirmAFL/qemu_mode/DECAF_qemu_2.10/mips-softmmu/qemu-system-mips {target_dir}/")
        elif "mipsel" in firm_architecture:
            cmd.append(f"sudo cp -f FirmAFL/qemu_mode/DECAF_qemu_2.10/mipsel-softmmu/qemu-system-mipsel {target_dir}/afl-qemu-system-trace")
            cmd.append(f"sudo cp -f FirmAFL/qemu_mode/DECAF_qemu_2.10/mipsel-softmmu/qemu-system-mipsel {target_dir}/")
        else:
            cmd.append(f"sudo cp -f FirmAFL/qemu_mode/DECAF_qemu_2.10/arm-softmmu/qemu-system-arm {target_dir}/afl-qemu-system-trace")
            cmd.append(f"sudo cp -f FirmAFL/qemu_mode/DECAF_qemu_2.10/arm-softmmu/qemu-system-arm {target_dir}/")
    for c in cmd:
        os.system(c)

def main():
    if mode == "all":
        for mode_dir in os.listdir(firm_base_dir):
            if os.path.isdir(os.path.join(firm_base_dir, mode_dir)):
                process_mode(mode_dir)
    else:
        process_mode(mode)

if __name__ == "__main__":
    main()
