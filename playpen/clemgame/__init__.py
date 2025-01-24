import importlib
import sys
import os
import logging
import logging.config
import yaml

BANNER = \
    r"""
      _                _                     _     
     | |              | |                   | |    
  ___| | ___ _ __ ___ | |__   ___ _ __   ___| |__  
 / __| |/ _ \ '_ ` _ \| '_ \ / _ \ '_ \ / __| '_ \ 
| (__| |  __/ | | | | | |_) |  __/ | | | (__| | | |
 \___|_|\___|_| |_| |_|_.__/ \___|_| |_|\___|_| |_|
"""  # doom font, thanks to http://patorjk.com/software/taag/

print(BANNER)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
with open(os.path.join(project_root, "logging.yaml")) as f:
    conf = yaml.safe_load(f)
    log_fn = conf["handlers"]["file_handler"]["filename"]
    log_fn = os.path.join(project_root, log_fn)
    conf["handlers"]["file_handler"]["filename"] = log_fn
    logging.config.dictConfig(conf)


def get_logger(name):
    return logging.getLogger(name)


# Load games dynamically from "games" sibling directory
# Note: The games might use get_logger (circular import)
games_root = os.path.join(project_root, "games")
if os.path.isdir(games_root):
    games_modules = [file for file in os.listdir(games_root)
                     if os.path.isdir(os.path.join(games_root, file)) and file not in ["__pycache__"]]
    for game_module in games_modules:
        try:
            importlib.import_module(f"playpen.games.{game_module}.master")
        except Exception as e:
            print(e)
            print(f"Cannot load 'games.{game_module}.master'."
                  f" Please make sure that the file exists.", file=sys.stderr)
