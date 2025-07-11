import signal
import typing
from types import FrameType

class Controller:
    configFile = None
    def __init__(self, options):
        self.options = options
        self.configFile = "/etc/supervisord.conf"


def signal_handler(signal: int, frame :FrameType):
    print("Process Done")

def main():
    signal.signal(signal.SIGINT, signal_handler)
    while 1:
        print("1")

main()