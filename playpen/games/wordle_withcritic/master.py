from typing import Dict, List

from playpen.agents.base_agent import Agent
from playpen.playpengame.playpengame import GameBenchmark, GameMaster, GameScorer
from playpen.games.wordle.master import WordleGameMaster, WordleGameScorer

GAME_NAME = "wordle_withcritic"


class WordleWithClueAndCriticGameBenchmark(GameBenchmark):
    def __init__(self):
        super().__init__(GAME_NAME)

    def get_description(self):
        return "Wordle Game with a clue given to the guesser and a critic for the clue"

    def create_game_master(self, experiment: Dict, player_agents: List[Agent]) -> GameMaster:
        return WordleGameMaster(self.name, experiment, player_agents)

    def create_game_scorer(self, experiment: Dict, game_instance: Dict) -> GameScorer:
        return WordleGameScorer(self.name, experiment, game_instance)
