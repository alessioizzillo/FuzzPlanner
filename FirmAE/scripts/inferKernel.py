#!/usr/bin/env python3

import sys
import os
import subprocess

IID = -1
MODE = ""

def ParseInit(cmd, out):
    for item in cmd.split(' '):
        if item.find("init=/") != -1:
            out.write(item + "\n")

def ParseCmd():
    if not os.path.exists("scratch/" + MODE + "/" + IID + "/kernelCmd"):
        return
    with open("scratch/" + MODE + "/" + IID + "/kernelCmd") as f:
        out = open("scratch/{}/{}/kernelInit".format(MODE, IID), "w")
        cmds = f.read()
        for cmd in cmds.split('\n')[:-1]:
            ParseInit(cmd, out)
        out.close()

if __name__ == "__main__":
    # execute only if run as a script
    IID = sys.argv[1]
    MODE = sys.argv[2]
    kernelPath = './images/' + MODE + "/" + IID + '.kernel'
    os.system("strings {} | grep \"Linux version\" > {}".format(kernelPath,
                                                                "scratch/" + MODE + "/" + IID + "/kernelVersion"))

    os.system("strings {} | grep \"init=/\" | sed -e 's/^\"//' -e 's/\"$//' > {}".format(kernelPath,
                                                                "scratch/" + MODE + "/" + IID + "/kernelCmd"))

    ParseCmd()
