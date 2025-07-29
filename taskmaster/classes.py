from dataclasses import dataclass


@dataclass
class ProgramConfig():
    cmd: str
    # numprocs: int = 1
    # umask: Union[int, str] = "022"
    # workingdir: str
    # autostart: bool = True
    # autorestart: str = "unexpected"
    # exitcodes: Union[int, List[int]] = 0
    # startretries: int = 3
    # starttime: int = 5
    # stopsignal: str = "TERM"
    # stoptime: int = 10
    # stdout: Optional[str] = None
    # stderr: Optional[str] = None
    # env: Optional[Dict[str, str]] = None


class Config:
    def __init__(self, target_file, is_yaml=False, is_ini=False):
        self.file = target_file
        self.application = []
        self.is_yaml = is_yaml
        self.is_ini = is_ini
        if is_yaml:
            self.loadYamlConfig()
        elif is_ini:
            self.loadIniConfig()
        else:
            raise NameError

    def loadYamlConfig(self):
        return

    def loadIniConfig(self):
        return
