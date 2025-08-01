import yaml
from pydantic import BaseModel
from typing import Dict, Union, List, Optional


class ProgramConfig(BaseModel):
    cmd: str
    numprocs: int = 1
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


class ConfigYAML(BaseModel):
    programs: Dict[str, ProgramConfig]


class Config:
    def __init__(self, path: str):
        if path.endswith(".yml") and len(path) > 4:
            try:
                with open(path) as file:
                    value = yaml.safe_load(file)
                self.config = ConfigYAML(**value)
            except yaml.YAMLError as e:
                print(e)
        elif path.endswith(".ini"):
            print("coucou")
        else:
            raise FileNotFoundError("""File not found or
            "doesn't respect subject requirements""")
