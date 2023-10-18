#!/usr/bin/env python3
import os

firm_dir = "FirmAE/scratch/firmafl/"

def main():
	#Bash lines to update the new executable of user_mode and qemu_mode

	dir_list = os.listdir(firm_dir)

	cmd = []
	for name in dir_list:
		with open(firm_dir+"/"+name+"/architecture", "r") as file:
			firm_architecture = str(file.readline().rstrip())

		if ("mipseb" in firm_architecture):
			cmd.append("sudo cp FirmAFL/qemu_mode/DECAF_qemu_2.10/mips-softmmu/qemu-system-mips "+ firm_dir+name)

		elif ("mipsel" in firm_architecture):
			cmd.append("sudo cp FirmAFL/qemu_mode/DECAF_qemu_2.10/mipsel-softmmu/qemu-system-mipsel "+ firm_dir+name)

		else:
			cmd.append("sudo cp FirmAFL/qemu_mode/DECAF_qemu_2.10/arm-softmmu/qemu-system-arm "+ firm_dir+name)	
	
	for i in range(0, len(cmd)):
		os.system(cmd[i])

if __name__ == "__main__":
    main()