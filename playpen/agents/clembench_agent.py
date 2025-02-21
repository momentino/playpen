from playpen.agents.base_agent import Agent
from playpen.backends import Model

class ClembenchAgent(Agent):
    def __init__(self, model: Model):
        super().__init__(name=model.get_name())
        self.model = model

    def act(self):
        prompt, response, response_text = self.model.generate_response(self.observations)
        return prompt, response, response_text

    def observe(self, observation, reward, termination, truncation, info):
        self.observations.append(observation)

    def get_temperature(self):
        return self.model.get_temperature()

    def shutdown(self):
        pass
