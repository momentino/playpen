# Playpen
This is a modified version of clembench where we deal with agents instead of models. 
There are some changes compared to Clembench but (for now) the original documentation is mostly valid.

It it a natural evolution of the cLLM (chat-optimized Large Language Model, "clem"), which along with testing agents' ability to engage in games – rule-constituted activities, it also enables learning from them.
It makes it possible to define custom agent classes as which include a training logic for learning.
In case you don't want to use this framework as a standalone program, you may include the playpen environment composed of games within an external training/evaluation pipeline, and train/evaluate externally defined agents (this part is not 100% complete). 

This repository contains the code for setting up the framework and implements a number of games that are further discussed in 

> Chalamalasetti, K., Götze, J., Hakimov, S., Madureira, B., Sadler, P., & Schlangen, D. (2023). clembench: Using Game Play to Evaluate Chat-Optimized Language Models as Conversational Agents (arXiv:2305.13455). arXiv. https://doi.org/10.48550/arXiv.2305.13455

### Game details

- A Simple Word Game: [taboo](docs/taboo.md)
- A Word-Guessing Game Based on Clues: [wordle](docs/wordle.md)
- Drawing Instruction Giving and Following: [image](docs/image.md)
- An ASCII Picture Reference Game: [reference](docs/reference.md)
- Scorekeeping: [private and shared](docs/privateshared.md)

## Using the benchmark

This repository is tested on `Python 3.8+`

- [How to run the benchmark and evaluation locally](docs/howto_run_benchmark.md)
- [How to run the benchmark, update leaderboard workflow](docs/howto_benchmark_workflow.md)
- [How to add a new model](docs/howto_add_models.md)
- [How to add and run your own game](docs/howto_add_games.md)
- [How to integrate with Slurk](docs/howto_slurk.md)
