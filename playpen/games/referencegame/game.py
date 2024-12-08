import random
from typing import Dict, List

from playpen.playpengame.playpengame import Player
from playpen.agents.base_agent import Agent



class InstructionFollower(Player):

    def __init__(self, agent: Agent):
        super().__init__(agent)

    def __call__(self, utterance: str):
        return super().act()

    def _custom_response(self, messages, turn_idx):
        answer = random.choice(["first", "second", "third"])
        return f"Answer: {answer}"


class InstructionGiver(Player):

    def __init__(self, agent: Agent):
        super().__init__(agent)

    def __call__(self, utterance: str):
        return super().act()

    def _custom_response(self, messages, turn_idx):
        return "Expression: The one that looks like the target."


class ReferenceGame:

    def __init__(self, game_instance: Dict, player_agents: List[Agent]):
        self.game_id = game_instance['game_id']
        self.player_1_prompt_header = game_instance['player_1_prompt_header']
        self.player_2_prompt_header = game_instance['player_2_prompt_header']
        self.target_grid_name = game_instance['target_grid_name']

        self.player_1_response_pattern = r'{}'.format(game_instance['player_1_response_pattern'])
        self.player_2_response_pattern = r'{}'.format(game_instance['player_2_response_pattern'])

        self.player_1_target_grid = game_instance['player_1_target_grid']
        self.player_1_second_grid = game_instance['player_1_second_grid']
        self.player_1_third_grid = game_instance['player_1_third_grid']

        self.player_2_first_grid = game_instance['player_2_first_grid']
        self.player_2_second_grid = game_instance['player_2_second_grid']
        self.player_2_third_grid = game_instance['player_2_third_grid']

        self.instruction_giver = InstructionGiver(player_agents[0])
        self.instruction_follower = InstructionFollower(player_agents[1])

        self.turn_count = 0


    def proceeds(self) -> bool:
        return True
