from typing import List, Dict

from playpen.agents.base_agent import Agent
from playpen.playpengame.playpengame import Player


class Critic(Player):
    def __init__(self, agent_name: Agent = None, response_format_keywords: Dict = None):
        self.response_format_keywords = response_format_keywords
        super().__init__(agent_name)

    def __call__(self, messages: List[Dict], turn_idx) -> str:
        # assert self.backend in ["human", "llm", "mock"], f"Invalid player role {self.backend}, please check the config file"
        return super().act()

    def _custom_response(self, messages, turn_idx) -> str:
        # Repeating the same to maintain similar results w.r.t LLM mode
        dummy_response = f'{self.response_format_keywords["agreement"]}:yes\n{self.response_format_keywords["explanation"]}:agree with your guess'
        return dummy_response
