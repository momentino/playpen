from typing import Dict, List

from playpen.agents.base_agent import Agent
from playpen.clemgame.clemgame import GameBenchmark, DialogueGameMaster, GameScorer
from playpen.games.wordle.master import WordleGameMaster, WordleGameScorer

# this will resolve into subdirectories to find the instances
GAME_NAME = "wordle_withclue"


class WordleWithClueGameBenchmark(GameBenchmark):
    def __init__(self):
        super().__init__(GAME_NAME)

    def get_description(self):
        return "Wordle Game with a clue given to the guesser"

    def create_game_master(self, experiment: Dict, player_agents: List[Agent]) -> DialogueGameMaster:
        return WordleGameMaster(self.name, experiment, player_agents)

    def create_game_scorer(self, experiment: Dict, game_instance: Dict) -> GameScorer:
        return WordleGameScorer(self.name, experiment, game_instance)

    def is_single_player(self) -> bool:
        return True
