import importlib
import sys
import os
import logging
import logging.config
import yaml

BANNER = \
    r"""
 .----------------. .----------------. .----------------. .----------------. .----------------. .----------------. .-----------------.
| .--------------. | .--------------. | .--------------. | .--------------. | .--------------. | .--------------. | .--------------. |
| |   ______     | | |   _____      | | |      __      | | |  ____  ____  | | |   ______     | | |  _________   | | | ____  _____  | |
| |  |_   __ \   | | |  |_   _|     | | |     /  \     | | | |_  _||_  _| | | |  |_   __ \   | | | |_   ___  |  | | ||_   \|_   _| | |
| |    | |__) |  | | |    | |       | | |    / /\ \    | | |   \ \  / /   | | |    | |__) |  | | |   | |_  \_|  | | |  |   \ | |   | |
| |    |  ___/   | | |    | |   _   | | |   / ____ \   | | |    \ \/ /    | | |    |  ___/   | | |   |  _|  _   | | |  | |\ \| |   | |
| |   _| |_      | | |   _| |__/ |  | | | _/ /    \ \_ | | |    _|  |_    | | |   _| |_      | | |  _| |___/ |  | | | _| |_\   |_  | |
| |  |_____|     | | |  |________|  | | ||____|  |____|| | |   |______|   | | |  |_____|     | | | |_________|  | | ||_____|\____| | |
| |              | | |              | | |              | | |              | | |              | | |              | | |              | |
| '--------------' | '--------------' | '--------------' | '--------------' | '--------------' | '--------------' | '--------------' |
 '----------------' '----------------' '----------------' '----------------' '----------------' '----------------' '----------------' 
"""  # blocks font, thanks to http://patorjk.com/software/taag/

print(BANNER)


def configure_logging(project_root):
    # Configure logging
    with open(os.path.join(project_root, "logging.yaml")) as f:
        conf = yaml.safe_load(f)
        log_fn = conf["handlers"]["file_handler"]["filename"]
        log_fn = os.path.join(project_root, log_fn)
        conf["handlers"]["file_handler"]["filename"] = log_fn
        logging.config.dictConfig(conf)


def get_logger(name):
    return logging.getLogger(name)

playpen_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(playpen_root)
# Load games dynamically from "games" sibling directory
# Note: The games might use get_logger (circular import)
games_root = os.path.join(playpen_root, "games")

if os.path.isdir(games_root):
    games_modules = [file for file in os.listdir(games_root)
                     if os.path.isdir(os.path.join(games_root, file)) and file not in ["__pycache__"]]
    for game_module in games_modules:
        try:
            importlib.import_module(f"games.{game_module}.master")
        except Exception as e:
            print(e)
            print(f"Cannot load 'games.{game_module}.master'."
                  f" Please make sure that the file exists.", file=sys.stderr)
