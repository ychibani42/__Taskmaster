from pydantic import BaseModel, ValidationError
from typing import Dict, List, Union, Optional
import configparser


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


def parse_exitcodes(value):
    if ',' in value:
        return [int(x.strip()) for x in value.split(',')]
    try:
        return int(value)
    except ValueError:
        return [int(x) for x in value.split()]


def parse_env(value):
    env_dict = {}
    for pair in value.split(','):
        if '=' in pair:
            k, v = pair.split('=', 1)
            env_dict[k.strip()] = v.strip()
    return env_dict if env_dict else None


def load_program_configs(path: str) -> Dict[str, ProgramConfig]:
    config = configparser.ConfigParser()
    config.read(path)
    programs = {}
    for section in config.sections():
        data = dict(config.items(section))

        if 'exitcodes' in data:
            data['exitcodes'] = parse_exitcodes(data['exitcodes'])
        if 'env' in data:
            data['env'] = parse_env(data['env'])

        try:
            programs[section] = ProgramConfig(**data)
        except ValidationError as e:
            print(f"Error in section [{section}]:\n{e}\n")
    return programs


def main():
    configs = load_program_configs('foo.conf')
    for name, cfg in configs.items():
        print(f"{name}: {cfg}")


main()
