'''
pip install pyyaml
'''
import yaml
import os

class Config:
    _config = None

    @classmethod
    def load(cls, config_file):
        if cls._config is None:
            with open(config_file, 'r',encoding="utf-8") as file:
                cls._config = yaml.safe_load(file)
        return cls._config

    @classmethod
    def get(cls, key):
        return cls._config.get(key)

# load configuration from config.yaml
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
config = Config.load(config_path)

# now config can be used anywhere in the program to access configuration
# for example:
# database_host = config.get('database')['host']
# logging_level = config.get('logging')['level']