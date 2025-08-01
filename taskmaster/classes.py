import yaml
from pydantic import BaseModel, ValidationError
from typing import Dict, Union, List, Optional, Any


class ProgramConfig(BaseModel):
    cmd: str
    numprocs: int = 1
    umask: Union[int, str]
    workingdir: str
    autostart: bool = True
    autorestart: Union[bool, str] = "unexpected"
    exitcodes: Union[int, List[int]] = 0
    startretries: int
    starttime: int
    stopsignal: Optional[str] = None
    stoptime: Optional[int] = 0
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    env: Optional[Dict[str, Any]] = None


class ConfigYAML(BaseModel):
    programs: Dict[str, ProgramConfig]


class Config:
    def __init__(self, path: str):
        if path.endswith(".yml") and len(path) > 4:
            try:
                with open(path) as file:
                    value = yaml.safe_load(file)
                self.config = ConfigYAML(**value)
            except ValidationError as e:
                print(e.errors())
        elif path.endswith(".ini"):
            print("coucou")
        else:
            raise FileNotFoundError("""File not found or
            "doesn't respect subject requirements""")
