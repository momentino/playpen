import time
from pathlib import Path

from clemcore.backends import Model
from clemcore.clemgame import GameInstanceIterator, GameBenchmarkCallbackList, GameBenchmark, \
    InstanceFileSaver, ExperimentFileSaver, InteractionsFileSaver, EpochResultsFolder, EpochResultsFolderCallback
from clemcore.clemgame.runners import batchwise
from playpen import BasePlaypenTrainer, to_sub_selector
from playpen.clemdatasets import ClemDatasetv2

from playpen.buffers import EpisodeBuffer
from playpen.callbacks.buffers import EpisodeBufferCallback


class BatchwisePlaypenTrainer(BasePlaypenTrainer):

    def __init__(self, num_epochs: int, learner: Model, teacher: Model = None):
        """
        Note:
            Both models will always be loaded into memory, even if they are the same.
            This is intentional: While we want to adjust the learner's parameters,
            the teacher model must remain fixed as part of the environment to allow proper convergence.

        Args:
            learner: The learner model instance to be trained or adapted.
            teacher: The teacher model instance that remains fixed and acts as part of the environment.
        """
        super().__init__(learner, teacher)
        self.batch_size = 8
        self.num_epochs = num_epochs
        player_models = [learner]
        if teacher is not None:
            player_models.append(teacher)
        self.episode_buffer = EpisodeBuffer()
        # setup callbacks for the clem benchmark run
        run_dir = f"{learner}" if teacher is None else f"{learner}-{teacher}"
        results_folder = EpochResultsFolder(Path("playpen-records"), run_dir)
        model_infos = Model.to_infos(player_models)
        self.callbacks = GameBenchmarkCallbackList([
            # a callback to collect episodes into the buffer during the benchmark run
            EpisodeBufferCallback(self.episode_buffer),
            # a callback to increase the epoch number in the result folder
            EpochResultsFolderCallback(results_folder),
            # a callback to save the instance.json using the epoch result folder structure
            InstanceFileSaver(results_folder),
            # a callback to save the experiment.json using the epoch result folder structure
            ExperimentFileSaver(results_folder=results_folder, player_model_infos=model_infos),
            # a callback to save the interactions.json and requests.json using the epoch result folder structure
            InteractionsFileSaver(results_folder=results_folder, player_model_infos=model_infos)
        ])

    def learn(self):
        game_registry = self.get_game_registry()
        game_specs = game_registry.get_game_specs_that_unify_with("all", verbose=False)

        # We take both training and validation set from the training split
        dataset = ClemDatasetv2("instances", split="train").dataset.train_test_split(0.2, shuffle=True, seed=42)
        game_instance_iterator = GameInstanceIterator.from_game_spec(game_specs, sub_selector=to_sub_selector(dataset))

        # We initialize the game benchmark which creates the game master for each game instance
        with GameBenchmark.load_from_spec(game_specs) as game_benchmark:
            # We run as many epochs over all game instances as specified
            for epoch in range(self.num_epochs):
                # We collect the episodes using the batchwise runner from clemcore
                self._collect_episodes(game_benchmark, game_instance_iterator)
                # We use the collected episodes to adjust model parameters of the learner
                self._train()

    def _collect_episodes(self, game_benchmark, game_instance_iterator):
        # We reset the iterator to play all game instances once again
        game_instance_iterator.reset(verbose=False)
        # We reset the episode buffer before each epoch over game instances
        # Note: We could also collect episodes over multiple epochs by calling reset only later
        self.episode_buffer.reset()
        # We invoke the batchwise runner to collect the episode trajectories for the game instance,
        # so that all game instances are prepared first and then processed in batches. Note that
        # for this to work, the model backends must support batching! Otherwise, fallback to sequential.
        batchwise.run(
            game_benchmark,
            game_instance_iterator,
            # Note: Here the order is important! We assign the roles so that:
            # - the teacher plays as the word describer (player at index 0)
            # - the learner plays as the word guesser (player at index 1)
            [self.teacher, self.learner],
            callbacks=self.callbacks,
            batch_size=self.batch_size
        )

    def _train(self):
        # Convert the collected trajectories into conversational data format
        conversational_dataset = self.episode_buffer.to_conversational_dataset(self.learner)
        print("Collected episodes (perspective=learner):", len(conversational_dataset))
        print("Example episode:")
        for conversation in conversational_dataset:
            for message in conversation["messages"]:
                print(message)
            break
        # Apply a training algorithm of your choice
        print("Training...")
        time.sleep(1)
