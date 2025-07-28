import subprocess
# from subprocess import Popen, PIPE
import time
import yaml
from classes import ProgramConfig

def initConfFile():
    

def createProcess():
    while 1:
        subprocess.Popen(["python", "taskmasterd.py"])
        time.sleep(0.5)


def main():
    config: ProgramConfig = initConfFile()
    create_process()


main()
