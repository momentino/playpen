import os
import argparse
from pathlib import Path
from playpen import playpengame
from playpen.playpengame import benchmark
from playpen.agents import create_agents

stdout_logger = playpengame.get_logger("benchmark.run")

def main(args: argparse.Namespace):
    if args.command_name == "ls":
        benchmark.list_games()
    else:
        project_root = Path(__file__).resolve().parent.parent
        results_dir = args.results_dir if os.path.isabs(args.results_dir) else project_root / args.results_dir
        if args.command_name == "run":
            agents = create_agents(agent_args_list=args.agent_args,
                                   game=args.game,
                                   agents_root=args.agents_dir)
            benchmark.run(args.game,
                          agents=agents,
                          experiment_name=args.experiment_name,
                          instances_name=args.instances_name,
                          results_dir=results_dir)
        if args.command_name == "score":
            benchmark.score(args.game, experiment_name=args.experiment_name, results_dir=results_dir)
        if args.command_name == "transcribe":
            benchmark.transcripts(game_name=args.game, experiment_name=args.experiment_name, results_dir=results_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers(dest="command_name")
    sub_parsers.add_parser("ls")

    run_parser = sub_parsers.add_parser("run", formatter_class=argparse.RawTextHelpFormatter)
    run_parser.add_argument("-m", "--models", type=str, nargs="*",
                            help="""Assumes model names supported by the implemented backends.

      To run a specific game with a single player:
      $> python3 scripts/cli.py run -g taboo -m model_name

      To run a specific game with n players:
      $> python3 scripts/cli.py run -g taboo -m model_name model_name2 model_name3 ...

      If the game supports model expansion (using the single specified model for all players):
      $> python3 scripts/cli.py run -g taboo -m model_name

      When this option is not given, then the dialogue partners configured in the experiment are used. 
      Default: None.""")
    run_parser.add_argument("-e", "--experiment_name", type=str,
                            help="Optional argument to only run a specific experiment")
    run_parser.add_argument("-a", "--agent_args", nargs='+', type=str, default=["agent_class=ZeroShotLLMAgent"],
                            help="Arguments to initialize the agent class")
    run_parser.add_argument("-g", "--game", type=str,
                            required=True, help="A specific game name (see ls).")
    run_parser.add_argument("-t", "--temperature", type=float, default=0.0,
                            help="Argument to specify sampling temperature for the models. Default: 0.0.")
    run_parser.add_argument("-l", "--max_tokens", type=int, default=100,
                            help="Specify the maximum number of tokens to be generated per turn (except for cohere). "
                                 "Be careful with high values which might lead to exceed your API token limits."
                                 "Default: 100.")
    run_parser.add_argument("-i", "--instances_name", type=str, default="instances",
                            help="The instances file name (.json suffix will be added automatically.")
    run_parser.add_argument("-r", "--results_dir", type=str, default="results",
                            help="A relative or absolute path to the results root directory. "
                                 "For example '-r results/v1.5/de‘ or '-r /absolute/path/for/results'. "
                                 "When not specified, then the results will be located in './results'")
    run_parser.add_argument("-s", "--agents_dir", type=str, default="playpen/agents",
                            help="A relative or absolute path to the directory containing the agent classes. "
                                 "For example '-a playpen/agents‘ or '-r /absolute/path/for/agents'. "
                                 "When not specified, then the results will be located in './playpen/agents'")

    score_parser = sub_parsers.add_parser("score")
    score_parser.add_argument("-e", "--experiment_name", type=str,
                              help="Optional argument to only run a specific experiment")
    score_parser.add_argument("-g", "--game", type=str,
                              help="A specific game name (see ls).", default="all")
    score_parser.add_argument("-r", "--results_dir", type=str, default="results",
                              help="A relative or absolute path to the results root directory. "
                                   "For example '-r results/v1.5/de‘ or '-r /absolute/path/for/results'. "
                                   "When not specified, then the results will be located in './results'")

    transcribe_parser = sub_parsers.add_parser("transcribe")
    transcribe_parser.add_argument("-e", "--experiment_name", type=str,
                                   help="Optional argument to only run a specific experiment")
    transcribe_parser.add_argument("-g", "--game", type=str,
                                   help="A specific game name (see ls).", default="all")
    transcribe_parser.add_argument("-r", "--results_dir", type=str, default="results",
                                   help="A relative or absolute path to the results root directory. "
                                        "For example '-r results/v1.5/de‘ or '-r /absolute/path/for/results'. "
                                        "When not specified, then the results will be located in './results'")

    main(parser.parse_args())
