#!/usr/bin/env python3

import sys
import os
import subprocess

IID = -1
TOOL = ""

def ParseInit(cmd, out):
    for item in cmd.split(' '):
        if item.find("init=/") != -1:
            out.write(item + "\n")

def ParseCmd():
    if not os.path.exists("scratch/" + TOOL + "/" + IID + "/kernelCmd"):
        return
    with open("scratch/" + TOOL + "/" + IID + "/kernelCmd") as f:
        out = open("scratch/{}/{}/kernelInit".format(TOOL, IID), "w")
        cmds = f.read()
        for cmd in cmds.split('\n')[:-1]:
            ParseInit(cmd, out)
        out.close()

if __name__ == "__main__":
    # execute only if run as a script
    IID = sys.argv[1]
    TOOL = sys.argv[2]
    kernelPath = './images/' + TOOL + "/" + IID + '.kernel'
    os.system("strings {} | grep \"Linux version\" > {}".format(kernelPath,
                                                                "scratch/" + TOOL + "/" + IID + "/kernelVersion"))

    os.system("strings {} | grep \"init=/\" | sed -e 's/^\"//' -e 's/\"$//' > {}".format(kernelPath,
                                                                "scratch/" + TOOL + "/" + IID + "/kernelCmd"))

    ParseCmd()
