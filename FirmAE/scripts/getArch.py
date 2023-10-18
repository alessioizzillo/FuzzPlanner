#!/usr/bin/env python3

import sys
import tarfile
import subprocess
import psycopg2

archMap = {"MIPS64":"mips64", "MIPS":"mips", "ARM64":"arm64", "ARM":"arm", "Intel 80386":"intel", "x86-64":"intel64", "PowerPC":"ppc", "unknown":"unknown"}

endMap = {"LSB":"el", "MSB":"eb"}

def getArch(filetype):
    for arch in archMap:
        if filetype.find(arch) != -1:
            return archMap[arch]
    return None

def getEndian(filetype):
    for endian in endMap:
        if filetype.find(endian) != -1:
            return endMap[endian]
    return None

infile = sys.argv[1]
psql_ip = sys.argv[2]
tool = sys.argv[3]
base = infile[infile.rfind("/") + 1:]
iid = base[:base.find(".")]

tar = tarfile.open(infile, 'r')

infos = []
fileList = []
for info in tar.getmembers():
    if any([info.name.find(binary) != -1 for binary in ["/busybox", "/alphapd", "/boa", "/http", "/hydra", "/helia", "/webs"]]):
        infos.append(info)
    elif any([info.name.find(path) != -1 for path in ["/sbin/", "/bin/"]]):
        infos.append(info)
    fileList.append(info.name)

with open("scratch/" + tool + "/" + iid + "/fileList", "w") as f:
    for filename in fileList:
        try:
            f.write(filename + "\n")
        except:
            continue

for info in infos:
    tar.extract(info, path="/tmp/" + tool + "/" + iid)
    filepath = "/tmp/" + tool + "/" + iid + "/" + info.name
    filetype = subprocess.check_output(["file", filepath]).decode()

    arch = getArch(filetype)
    endian = getEndian(filetype)
    if arch and endian:
        print(arch + endian)
        subprocess.call(["rm", "-rf", "/tmp/" + tool + "/" + iid])
        dbh = psycopg2.connect(database="firmware_%s" % tool,
                               user="firmadyne",
                               password="firmadyne",
                               host=psql_ip, port=6666)
        cur = dbh.cursor()
        query = """UPDATE image SET arch = '%s' WHERE id = %s;"""
        cur.execute(query % (arch+endian, iid))
        dbh.commit()

        with open("scratch/" + tool + "/" + iid + "/fileType", "w") as f:
            f.write(filetype)

        break

subprocess.call(["rm", "-rf", "/tmp/" + tool + "/" + iid])
