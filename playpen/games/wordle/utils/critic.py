from typing import List, Dict

from playpen.agents.base_agent import Agent
from playpen.clemgame.clemgame import Player


class Critic(Player):
    def __init__(self, agent_name: Agent = None, response_format_keywords: Dict = None):
        self.response_format_keywords = response_format_keywords
        super().__init__(agent_name)

        # a list to keep the dialogue history
        #self.history: List = []
        self.count_turn = 0

    def __call__(self, turn_idx) -> str:
        # assert self.backend in ["human", "llm", "mock"], f"Invalid player role {self.backend}, please check the config file"
        """if self.model.model_spec.is_human():
            guess_agreement = input("Enter your agreement for the guess: ")
            # Repeating the same to maintain similar results w.r.t LLM mode
            return [guess_agreement], guess_agreement, guess_agreement"""
        return super().__call__(turn_idx)

    def _custom_response(self, turn_idx) -> str:
        # Repeating the same to maintain similar results w.r.t LLM mode
        dummy_response = f'{self.response_format_keywords["agreement_lang"]} yes\n{self.response_format_keywords["explanation_lang"]} agree with your guess'
        return dummy_response
