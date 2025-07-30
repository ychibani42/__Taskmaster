import subprocess
# from subprocess import Popen, PIPE
import time
from classes import ProgramConfig
import yaml


def initConfFile(path: str) -> ProgramConfig:
    if path.find(".yml"):
        with open(path) as file:
            try:
                yaml.safe_load(file)
            except yaml.YAMLError as e:
                print(e)


def startProcess() -> None:
    while 1:
        subprocess.Popen(["ls", "-la"])
        time.sleep(0.5)


def main():
    # path = searchFilePath('.')
    config: ProgramConfig = initConfFile(path="./foo.yml")
    # startProcess(config)


main()
