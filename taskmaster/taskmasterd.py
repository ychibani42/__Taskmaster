import subprocess
import time


cmd = ['ls',  '-la']


class Supervisor:
    def exec_cmd() -> int:
        process = subprocess.Popen(cmd)
        time.sleep(2)
        if process.poll() is None:
            print("Le processus est toujours vivant")
        else:
            print("Le processus est terminé")
        return 1

def main():
    Supervisor.exec_cmd()

main()