import trl
from collections import defaultdict
from datasets import Dataset

from clemcore.backends.huggingface_local_api import HuggingfaceLocalModel

from playpen import BasePlaypenTrainer
from playpen.clemdatasets import ClemDatasetv2


class DPOTrainer(BasePlaypenTrainer):

    def __init__(self, learner: HuggingfaceLocalModel):
        super().__init__(learner)

    def _build_dataset(self) -> Dataset:
        # Load the interactions dataset and filter for successful and failed episodes.
        # We pair same-task episodes (same game, experiment, task_id) with different outcomes to build
        # the preference dataset required for DPO: chosen=success, rejected=failure.
        dataset = ClemDatasetv2( "interactions", split="train").dataset

        # Group episodes by task identity to find contrastive pairs
        by_task = defaultdict(lambda: {"success": None, "failure": None})
        for episode in dataset:
            meta = episode["meta"]
            key = (meta["game"], meta["experiment"], meta["task_id"])
            outcome = meta["outcome"]
            if outcome == "success" and by_task[key]["success"] is None:
                by_task[key]["success"] = episode["messages"]
            elif outcome in ("failure", "aborted") and by_task[key]["failure"] is None:
                by_task[key]["failure"] = episode["messages"]

        # Build the conversational preference dataset.
        # The first user message is the common prompt; chosen/rejected are the remaining turns.
        # See https://huggingface.co/docs/trl/dataset_formats#preference
        preference_examples = []
        for key, pair in by_task.items():
            chosen_messages = pair["success"]
            rejected_messages = pair["failure"]
            if chosen_messages is None or rejected_messages is None:
                continue
            if not chosen_messages or not rejected_messages:
                continue
            # Use the first user turn as the shared prompt
            prompt = [chosen_messages[0]]
            chosen = chosen_messages[1:]
            rejected = rejected_messages[1:]
            if not chosen or not rejected:
                continue
            preference_examples.append({
                "prompt": prompt,
                "chosen": chosen,
                "rejected": rejected,
            })

        return Dataset.from_list(preference_examples)

    def learn(self):
        # We shuffle and split the remaining filtered samples to receive a dev split
        # For evaluation on the actual games performance use the validation split
        # load_dataset("json", data_files="examples/trl/results.jsonl", split="validation")
        preference_dataset = self._build_dataset().train_test_split(0.2, shuffle=True, seed=42)

        # Initialize training configuration
        config = trl.DPOConfig(  # inherits TrainingArguments
            max_length=300,
            output_dir=f"models/dpo/{self.learner.name}",
            eval_strategy="epoch",
        )

        # Initialize trainer context
        trainer = trl.DPOTrainer(
            model=self.learner.model,
            train_dataset=preference_dataset["train"],
            eval_dataset=preference_dataset["test"],
            args=config,
        )

        # Train on the preference dataset
        trainer.train()
