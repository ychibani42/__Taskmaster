from pydantic import BaseModel
from typing import Dict, List, Union, Optional


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
