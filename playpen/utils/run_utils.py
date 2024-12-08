import os
import importlib
import inspect
from playpen import playpengame
from playpen.agents.base_agent import Agent
from typing import Dict


stdout_logger = playpengame.get_logger("benchmark.run")


def parse_comma_sep_args(comma_sep_args: str) -> Dict:
    pairs = comma_sep_args.split(',')
    result_dict = {}
    for pair in pairs:
        key, value = pair.split('=')
        result_dict[key.strip()] = value.strip()
    return result_dict

def init_agent_from_args(agent_args:str, agent_root:str) -> Agent:
    agent_args = parse_comma_sep_args(agent_args)
    agent_class = agent_args['agent_class']
    if not os.path.isdir(agent_root):
        raise ValueError(f"The folder '{agent_root}' does not exist or is not a directory.")

    for filename in os.listdir(agent_root):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]  # Remove the .py extension
            module_path = f"{agent_root.replace('/', '.')}.{module_name}"
            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                print(f"Could not import module {module_path}: {e}")
                continue
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if name == agent_class:
                    del agent_args['agent_class']
                    return obj(**agent_args)

    raise ValueError(f"Class '{agent_class}' not found in folder '{agent_root}'.")
