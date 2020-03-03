import yaml

from utils.role_manager import get_role

config = {}


def load_config():
    if get_role():
        file = open('client.yaml')
    else:
        file = open('server.yml')
    config.update(yaml.full_load(file))
    file.close()


def get_config(key: str) -> int:
    global config
    return config[key]
