from typing import List
from playpen import playpengame
from playpen.playpengame.playpengame import num_players
from playpen.agents.base_agent import Agent
from playpen.utils.run_utils import init_agent_from_args
stdout_logger = playpengame.get_logger("benchmark.run")

def create_agents(agent_args_list: List[str], agents_root: str, game:str) -> List[Agent]:
    min_num_agents, max_num_agents = num_players(game)
    agents = [init_agent_from_args(agent_args, agents_root) for agent_args in agent_args_list]
    # TODO: when we have the same model playing multiple agents, we could have one single instance in the memory rather than two, and have separate histories
    if len(agents) > max_num_agents:
        message = f"Too many agents for this game. The maximum number of player agents for this game is {max_num_agents}"
        stdout_logger.error(message)
        raise ValueError(message)
    elif len(agents) < min_num_agents:
        message = f"The number of agents was insufficient for playing the game. Creating {min_num_agents - len(agents)} agents with the last model specified in the arguments."
        stdout_logger.warning(message)
        agent = agents[-1]
        agents.extend([agent for _ in range(min_num_agents - len(agents))])
    return agents