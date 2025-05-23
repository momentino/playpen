from typing import List, Dict

from playpen.backends import Model
from playpen.clemgame.clemgame import Player


class Critic(Player):
    def __init__(self, model_name: Model = None, response_format_keywords: Dict = None):
        self.response_format_keywords = response_format_keywords
        super().__init__(model_name)

        # a list to keep the dialogue history
        self.history: List = []
        self.count_turn = 0

    def __call__(self, messages: List[Dict], turn_idx) -> str:
        # assert self.backend in ["human", "llm", "mock"], f"Invalid player role {self.backend}, please check the config file"
        if self.model.model_spec.is_human():
            guess_agreement = input("Enter your agreement for the guess: ")
            # Repeating the same to maintain similar results w.r.t LLM mode
            return [guess_agreement], guess_agreement, guess_agreement
        return super().__call__(messages, turn_idx)

    def _custom_response(self, messages, turn_idx) -> str:
        # Repeating the same to maintain similar results w.r.t LLM mode
        dummy_response = f'{self.response_format_keywords["agreement_lang"]} yes\n{self.response_format_keywords["explanation_lang"]} agree with your guess'
        return dummy_response
