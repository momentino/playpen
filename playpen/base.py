import abc

from clemcore.backends import Model, BatchGenerativeModel
from clemcore.clemgame import Player, GameRegistry



class BasePlaypenTrainer(abc.ABC):

    def __init__(self, learner: Model | BatchGenerativeModel, teacher: Model | BatchGenerativeModel = None):
        self.learner = learner
        self.teacher = teacher

    def is_learner(self, player: Player):
        return player.model is self.learner

    def is_teacher(self, player: Player):
        return player.model is self.teacher

    def get_game_registry(self):
        return GameRegistry.from_directories_and_cwd_files()

    @abc.abstractmethod
    def learn(self):
        pass
