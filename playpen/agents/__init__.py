
def init_clembench_agents(model_names: List[str]):
    agents = []

    for name in model_names:


        def build_agent_list(game: GameBenchmark, agent_kwargs: str, gen_kwargs: str) -> List[Agent]:

            agent_args = dict(pair.split("=") for pair in agent_kwargs.split(","))
            gen_kwargs = dict(pair.split("=") for pair in gen_kwargs.split(","))

            agents = [HFAgent(gen_kwargs=gen_kwargs, **agent_args)]

            min_num_agents = 1
            max_num_agents = 1 if game.is_single_player() else 2
            if len(agents) > max_num_agents:
                message = f"Too many agents for this game. The maximum number of player agents for this game is {max_num_agents}"
                stdout_logger.error(message)
                raise ValueError(message)
            elif len(agents) < min_num_agents:
                message = f"The number of agents was insufficient for playing the game. Creating {min_num_agents - len(agents)} agents with the last model specified in the arguments."
                stdout_logger.warning(message)
                agent = agents[-1]
                agents.extend([agent for _ in range(min_num_agents - len(agents))])
            return agents