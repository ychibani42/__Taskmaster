import subprocess
# from subprocess import Popen, PIPE
import time
from classes import Config


def startProcess() -> None:
    while 1:
        subprocess.Popen(["ls", "-la"])
        time.sleep(0.5)


def main():
    # path = searchFilePath('.')
    config = Config(path="./foo.yml")
    print(config.config)
    # startProcess(config)


main()
