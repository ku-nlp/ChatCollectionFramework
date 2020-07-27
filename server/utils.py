import os
import json

def load_config():
    """Loads a configuration file.

    :return dict: loaded configuration

    """
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, '..', 'config.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)
