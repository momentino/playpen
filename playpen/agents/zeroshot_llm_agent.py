from playpen.agents.base_agent import Agent
from playpen.backends import read_model_specs, get_model_for

class ZeroShotLLMAgent(Agent):
    def __init__(self, model_name: str, agent_name: str = None, temperature: float = 0.0, max_tokens:int = 250):
        if agent_name is None:
            self.agent_name = model_name
        else:
            self.agent_name = agent_name
        super().__init__(name=self.agent_name)

        model_spec = read_model_specs(model_name)
        gen_args = {'temperature': temperature,
                    'max_tokens': max_tokens}
        self.model = get_model_for(model_spec)
        self.model.set_gen_args(**gen_args)

    def act(self):
        prompt, response, response_text = self.model.generate_response(self.observations)
        return prompt, response, response_text

    def observe(self, observation, reward, termination, truncation, info):
        self.observations.append(observation)

    def shutdown(self):
        pass
