import tomli


def read_config(config_filename='config.toml'):
    with open(config_filename, 'rb') as config:
        return tomli.load(config)
