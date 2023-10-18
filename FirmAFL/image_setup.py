#!/usr/bin/env python3
import sys
import os
import pdb
from pathlib import Path


firm_id = sys.argv[1]
firm_arch = sys.argv[2]
firm_tool = sys.argv[3]
firm_dir = "FirmAE/scratch/%s/%s" % (firm_tool, firm_id)
feed_type = "http"


def config_creation(feed_type):
	fuzz = open(firm_dir+"/fuzz_line", "w")
	fuzz.write("./afl-fuzz -m none -t 800000+ -Q -i inputs -o outputs -x keywords ") 
	fuzz.close()
	print("\033[32m[+]\033[0m Default Fuzz Call: ./afl-fuzz -m none -Q -i inputs -o outputs -x keywords")
	print("\033[32m[+]\033[0m Default Keywords file placed in "+firm_dir+"/keywords")
	print("\033[32m[+]\033[0m Default Seed file placed in "+firm_dir+"/inputs/seed")

	f = open(firm_dir+"/FirmAFL_config", "w")
	f.write("mapping_filename=mapping_table\n") 
	f.write("init_read_pipename=user_cpu_state\n") 
	f.write("write_pipename=full_cpu_state\n") 

	# Web Service of the firmware
	path = Path(firm_dir+"/service")
	if (path.is_file()):
		file_web = open(firm_dir+"/service", "r+")
		web_service = file_web.read()
		file_web.close()
		f.write("program_analysis="+web_service.split("/")[-1]+"\n")
		print("\033[32m[+]\033[0m Program Analysis: "+web_service+" (web service)")
	else:
		f.write("program_analysis=NotRecognized!!\n")
		print("\033[31m[-]\033[0m Program Analysis: Not Recognized! Set it manually or use later option.")
	
	f.write("feed_type=FEED_HTTP\n")
	f.write("id=%s\n"%firm_id)
	f.write("opti=yes")
	
	f.close()	

	return


def chroot_creation(cmd):
	cmd.append("mkdir -p %s/bin" % firm_dir)
	cmd.append("mkdir -p %s/lib" % firm_dir)
	cmd.append("mkdir -p %s/lib64" % firm_dir)
	cmd.append("cp -v /bin/bash %s/bin" % firm_dir)
	cmd.append("list=\"$(ldd /bin/bash | egrep -o '/lib.*\.[0-9]')\" && for i in $list; do cp -v --parents \"$i\" \"%s\"; done" % firm_dir)


def update_keywords():
	if not os.path.exists("%s/image_tmp" % firm_dir):
		os.makedirs("%s/image_tmp" % firm_dir)
	
	os.system("tar -xf FirmAE/images/%s/%s.tar.gz -C %s/image_tmp" % (firm_tool, firm_id, firm_dir))
	keywords = [os.path.join(dp, f).replace("%s/image_tmp/web" % firm_dir, "") for dp, dn, filenames in os.walk("%s/image_tmp/web" % firm_dir) for f in filenames]
	
	fp = open(firm_dir+"/keywords", "a")
	for i in range(len(keywords)):
		fp.write("\nweb_str%d=\"%s\"" % (i, keywords[i]))
	fp.close()
	
	os.system("rm -r %s/image_tmp" % (firm_dir))


cmd = []
dst = firm_dir
dst_input = "%s/inputs/" % firm_dir

# Executables QEMU system mode and user mode
if "mipseb" in firm_arch:   
	sys_src = "FirmAFL/qemu_mode/DECAF_qemu_2.10/mips-softmmu/qemu-system-mips"
	user_src = "FirmAFL/user_mode/mips-linux-user/qemu-mips"
	kernel_src = "FirmAE/binaries/vmlinux.mipseb.4_DECAF"
elif "mipsel" in firm_arch:
	sys_src = "FirmAFL/qemu_mode/DECAF_qemu_2.10/mipsel-softmmu/qemu-system-mipsel"
	user_src = "FirmAFL/user_mode/mipsel-linux-user/qemu-mipsel"
	kernel_src = "FirmAE/binaries/vmlinux.mipsel.4_DECAF"
else:
	sys_src = "FirmAFL/qemu_mode/DECAF_qemu_2.10/arm-softmmu/qemu-system-arm"
	user_src = "FirmAFL/user_mode/arm-linux-user/qemu-arm"
	kernel_src = "FirmAE/binaries/zImage.armel.4_DECAF"

# Fuzzing_Config_File Creation (Default FEED_HTTP for Web Server)
config_creation(feed_type)

# Default Keywords File (Dictionary for AFL)
keywords_src = "FirmAFL/config/keywords"
cmd.append("cp %s %s" %(keywords_src, dst))

afl_src= "FirmAFL/AFL/afl-fuzz"
cmd.append("cp %s %s" %(afl_src, dst))

# Configuration File to make DECAF_VMI works with our kernel
procinfo_src =  "FirmAFL/config/procinfo.ini"  

# Inputs Folder
if not (os.path.isdir(firm_dir+"/inputs")):
	cmd_input = "mkdir %s/inputs" %firm_dir  
	cmd.append(cmd_input)

# Seed File in Inputs/ folder
seed_src = "FirmAFL/config/seed"  

# VGABios binary
vgabios_bin = "FirmAFL/qemu_mode/DECAF_qemu_2.10/pc-bios/vgabios-cirrus.bin"  

# EFI binary
efi_bin =  "FirmAFL/qemu_mode/DECAF_qemu_2.10/pc-bios/efi-e1000.rom"

cmd.append("cp %s %s" %(seed_src, dst_input))
cmd.append("cp %s %s" %(sys_src, dst))
cmd.append("cp %s %s/afl-qemu-trace" %(user_src, dst))
cmd.append("cp %s %s" %(kernel_src, dst))
cmd.append("cp %s %s" %(procinfo_src, dst))
cmd.append("cp %s %s" %(vgabios_bin, dst))
cmd.append("cp %s %s" %(efi_bin, dst))

chroot_creation(cmd)

for i in range(0, len(cmd)):
	os.system(cmd[i])

update_keywords()

