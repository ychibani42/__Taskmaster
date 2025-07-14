from models import ProgramConfig
from pydantic import ValidationError
import configparser
import subprocess
from typing import Dict, List
import time


def parse_exitcodes(value: str) -> List[int]:
    if ',' in value:
        return [int(x.strip()) for x in value.split(',')]
    else:
        return int(value.strip())


def parse_env(value: str) -> Dict[str, str]:
    env_dict = {}
    for pair in value.split(','):
        if '=' in pair:
            key, k_value = pair.split("=")
            env_dict[key.strip()] = k_value.strip()
    return env_dict if env_dict else None


def load_program_configs(path: str) -> Dict[str, ProgramConfig]:
    config = configparser.ConfigParser()
    config.read(path)
    programs = {}
    for section in config.sections():
        Data = dict(config.items(section))
        if 'exitcodes' in Data:
            Data["exitcodes"] = parse_exitcodes(Data["exitcodes"])
        if 'env' in Data:
            Data['env'] = parse_env(Data['env'])
        try:
            programs[section] = ProgramConfig(**Data)
        except ValidationError as exc:
            print(repr(exc.errors()[0]['type']))
    return programs


def launch_programs(Config: ProgramConfig):
    process = subprocess.Popen(Config["cmd"])
    time.sleep(2)
    if process.poll() is None:
        print("Le processus est toujours vivant")
    else:
        print("Le processus est terminé")
    return 1


def main():
    configs = load_program_configs('foo.conf')
    launch_programs(configs)


main()
