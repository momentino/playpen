from typing import List, Dict

from playpen.agents import Agent
from playpen.playpengame.playpengame import Player


class Guesser(Player):
    def __init__(self, agent: Agent = None, response_format_keywords: Dict = None):
        self.response_format_keywords = response_format_keywords
        super().__init__(agent)

    def __call__(self, messages: List[Dict], turn_idx) -> str:
        return super().act()

    def _custom_response(self, messages, turn_idx) -> str:
        # Repeating the same to maintain similar results w.r.t LLM mode
        dummy_response = f'{self.response_format_keywords["guess"]}:dummy\n{self.response_format_keywords["explanation"]}:dummy'
        return dummy_response
