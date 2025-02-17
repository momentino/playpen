import abc
from typing import Tuple, Any

class Agent(abc.ABC):
    def __init__(self):
        self.observations = []

    @abc.abstractmethod
    def act(self) -> Tuple[Any, Any, str]:
        pass

    @abc.abstractmethod
    def observe(self, observation, reward, termination, truncation, info):
        pass

    @abc.abstractmethod
    def shutdown(self):
        pass

    def reset(self):
        self.observations = []


    def get_observations(self):
        return self.observations

    def get_last_observation(self):
        return self.observations[-1]

    def get_name(self) -> str:
        return self.name

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self.get_name()

    def __eq__(self, other: "Agent"):
        if not isinstance(other, Agent):
            return False
        return self.get_name() == other.get_name()