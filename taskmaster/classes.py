import yaml
from dataclasses import dataclass
from pydantic import BaseModel
from typing import Union, Optional, List, Dict

class ProgramConfig(BaseModel):
    cmd: str
    numprocs: int = 1
    umask: Union[int, str] = "022"
    workingdir: str
    autostart: bool = True
    autorestart: str = "unexpected"
    exitcodes: Union[int, List[int]] = 0
    startretries: int = 3
    starttime: int = 5
    stopsignal: str = "TERM"
    stoptime: int = 10
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    env: Optional[Dict[str, str]] = None


class Config:
    def __init__(self, path: str):
        if path.find(".yml") and len(path) > 3:
            try:
                with open(path) as file:
                    value = yaml.safe_load(file)
                self.config = ProgramConfig(**value)
                print(self.config)
            except yaml.YAMLError as e:
                print(e)
        elif path.find(".ini"):
            print("coucou")
        else:
            raise FileNotFoundError("""File not found or
            "doesn't respect subject requirements""")


config = Config("./foo.yml")
print(config)
