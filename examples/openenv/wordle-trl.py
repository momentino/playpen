from clemcore.clemgame import ClemGameEnv

game_env = ClemGameEnv(base_url="http://0.0.0.0:9000")

from dataclasses import dataclass, field
from playpen.agents.openenv import ClemGameEnvAgent


@dataclass
class GrpoEpisodeRollout:
    """Collect training info about a single episode.

    Following TRL's pattern, we accumulate all turns into a single completion
    sequence, using env_masks to distinguish model tokens (1) from env tokens (0).
    """
    prompt_ids: list[int] = field(default_factory=list)
    completion_ids: list[int] = field(default_factory=list)
    logprobs: list[float] = field(default_factory=list)
    env_masks: list[int] = field(default_factory=list)
    reward: float = 0.0  # Terminal reward from the environment

    def reset(self):
        self.prompt_ids.clear()
        self.completion_ids.clear()
        self.logprobs.clear()
        self.env_masks.clear()
        self.reward = 0.0


@dataclass
class GrpoEpisodeRollouts:
    """Collect training info about all episodes for a batch."""
    prompt_ids: list[list[int]] = field(default_factory=list)
    completion_ids: list[list[int]] = field(default_factory=list)
    logprobs: list[list[float]] = field(default_factory=list)
    env_mask: list[list[int]] = field(default_factory=list)
    rewards: list[float] = field(default_factory=list)  # Rewards for each episode

    def append(self, rollout: GrpoEpisodeRollout):
        """Append a completed episode rollout."""
        self.prompt_ids.append(list(rollout.prompt_ids))
        self.completion_ids.append(list(rollout.completion_ids))
        self.logprobs.append(list(rollout.logprobs))
        self.env_mask.append(list(rollout.env_masks))
        self.rewards.append(rollout.reward)

    def reset(self):
        self.prompt_ids.clear()
        self.completion_ids.clear()
        self.logprobs.clear()
        self.env_mask.clear()
        self.rewards.clear()


import trl
from playpen.agents import ClemObservation, ClemAgent
from trl.experimental.openenv import generate_rollout_completions


class WordleAgent(ClemAgent):
    """Agent that plays Wordle using TRL's GRPOTrainer for generation.

    Handles all tokenization and env_mask logic internally, accumulating
    the full episode trajectory for GRPO training.

    This implementation is based on the wordle openenv example given in the trl repository at
    https://github.com/huggingface/trl/blob/v0.28.0/examples/scripts/openenv/wordle.py
    """

    def __init__(self, trainer: trl.GRPOTrainer):
        super().__init__()
        self.trainer = trainer
        self.tokenizer = trainer.processing_class
        self.episode = GrpoEpisodeRollout()
        self._first_turn = True

    def track_env_completion(self, last: ClemObservation):
        if self._first_turn:  # On the first turn, set prompt_ids from the initial observation
            prompt_text = self.tokenizer.apply_chat_template(self.history, add_generation_prompt=True, tokenize=False)
            self.episode.prompt_ids = self.tokenizer.encode(prompt_text, add_special_tokens=False)
            self._first_turn = False
            return
        # Not first turn: the observation content is env feedback from the previous action
        # Prepend a blank line, so turns are visually separated when completions are logged
        # We can do this here, because these count toward the environment tokens and do not interfere with training
        env_feedback_ids = self.tokenizer.encode("\n\n" + last.content, add_special_tokens=False)
        self.episode.completion_ids.extend(env_feedback_ids)
        self.episode.logprobs.extend([0.0] * len(env_feedback_ids))
        self.episode.env_masks.extend([0] * len(env_feedback_ids))

    def track_agent_completion(self, outputs):
        self.episode.completion_ids.extend(outputs["completion_ids"])
        self.episode.logprobs.extend(outputs["logprobs"])
        self.episode.env_masks.extend([1] * len(outputs["completion_ids"]))

    def act(self, last: ClemObservation) -> str:
        self.track_env_completion(last)
        # We use text here so that we can better track the agent tokens versus the env tokens
        prompt_text = self.tokenizer.apply_chat_template(self.history, add_generation_prompt=True, tokenize=False)
        outputs = generate_rollout_completions(self.trainer, [prompt_text])[0]
        self.track_agent_completion(outputs)
        response = outputs.get("text") or self.tokenizer.decode(outputs["completion_ids"], skip_special_tokens=True)
        return response

    def get_episode(self) -> "GrpoEpisodeRollout":
        """Return the accumulated episode rollout for GRPO training."""
        return self.episode

    def reset(self):
        """Reset agent state for a new episode."""
        super().reset()
        self.episode.reset()
        self._first_turn = True


from dataclasses import asdict
import math
import random


def rollout_reward(history: list[dict], reward: float):
    """Apply a reward shaping hack for the degenerate all-abort case.

    Terminal rewards from the environment:
        - win:   +1.0
        - loss:   0.0
        - abort: -1.0  (model output violated the expected format)

    GRPO computes advantages by normalizing rewards within each group of K
    completions: ``advantage = (r - mean(r)) / (std(r) + eps)``.
    If **every** episode in a group aborts, all rewards are identical (-1.0),
    so the numerator ``r - mean(r) = -1.0 - (-1.0) = 0`` for every episode,
    every advantage = 0, and the gradient is exactly zero —
    the model receives no learning signal at all.

    To break this symmetry we replace each abort reward with a small uniformly
    sampled negative value in (-1, 0).  This introduces variance within an
    all-abort group so that ``r - mean(r) ≠ 0`` and the loss becomes non-zero,
    giving the model at least a weak signal to escape the degenerate regime.

    Best practice: run SFT first so the model already produces valid format
    output before starting GRPO, which avoids this situation entirely.
    """
    if math.isclose(reward, -1.0, abs_tol=1e-6):
        reward = -random.random()
    return reward


def rollout_episode(env: ClemGameEnv, agent: ClemGameEnvAgent, prompt: str) -> GrpoEpisodeRollout:
    """Play a single episode of Wordle and collect GRPO training data.

    The prompt encodes the game_id of the game instance, which is passed to
    env.reset() so that all K runs in a GRPO group play the same target word.
    Each run generates independently, giving GRPO the variance it needs.

    The agent handles all tokenization and env_mask logic internally.

    Returns:
        GrpoEpisodeRollout with accumulated prompt_ids, completion_ids, logprobs, env_masks, and reward.
    """
    obs = env.reset(game_id=int(prompt))
    while not obs.done:
        action = agent(obs)
        obs = env.step(action)
    rollout = agent.wrapped_agent.get_episode()
    rollout.reward = rollout_reward(agent.wrapped_agent.history, obs.reward)
    return rollout


def rollout_func(prompts: list[str], trainer: trl.GRPOTrainer) -> dict:
    """Custom rollout function for TRL GRPOTrainer with OpenEnv.

    TRL's RepeatSampler repeats each prompt K times consecutively, so the same
    game_id is passed to env.reset() for all K runs in a group — ensuring they
    play the same target word while generating independently.
    """
    agent = ClemGameEnvAgent(WordleAgent(trainer))
    rollouts = GrpoEpisodeRollouts()
    try:
        for prompt in prompts:
            rollout = rollout_episode(game_env, agent, prompt)
            rollouts.append(rollout)
            agent.reset()
        return asdict(rollouts)
    finally:
        rollouts.reset()
        agent.reset()


def reward_env(completions: list[str], **kwargs) -> list[float]:
    """Extract environment rewards passed from rollout_func.

    TRL calls this function with completions and any extra fields from the rollout dict.
    The 'rewards' field contains the terminal reward for each episode (1.0 = win, 0.0 = loss, -1.0 = abort).
    """
    return kwargs.get("rewards", [0.0] * len(completions))



from datasets import load_dataset

dataset = load_dataset("colab-potsdam/playpen-data", "instances", split="train")
dataset = dataset.filter(lambda game_instance: game_instance["game"] == "wordle")
# Use task_id as the prompt so rollout_func can recover the game_id for env.reset()
dataset = dataset.add_column("prompt", [str(x) for x in dataset["task_id"]])

from peft import LoraConfig
from datetime import datetime

TIMESTAMP = datetime.now().strftime("%b%d_%H-%M")

MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"
#MODEL_ID = "HuggingFaceTB/SmolLM2-135M-Instruct" # for debugging
grpo_config = trl.GRPOConfig(
    use_vllm=False,
    vllm_mode="colocate",
    vllm_gpu_memory_utilization=0.45,
    # vllm_gpu_memory_utilization=0.05, # for smol
    num_generations=2,
    per_device_train_batch_size=2,
    num_train_epochs=3, # 1 epoch == playing each of the 24 training game instances K times, once for each generation
    disable_dropout=True,
    max_completion_length=2048,  # Should capture full episode; note that the model is asked to give an explanation
    output_dir=f"models/grpo/wordle/{MODEL_ID}",
    report_to="tensorboard",
    logging_dir=f"/cache/tensorboard-logdir/grpo/wordle/{MODEL_ID}/{TIMESTAMP}",
    log_completions=True
)
peft_config = LoraConfig(  # see https://huggingface.co/docs/trl/sft_trainer#training-adapters
    r=8, lora_alpha=16,
    lora_dropout=0.05,
    target_modules="all-linear",
    modules_to_save=["lm_head", "embed_token"],
    task_type="CAUSAL_LM",
)

grpo_trainer = trl.GRPOTrainer(
    model=MODEL_ID,
    rollout_func=rollout_func,  # repeats each game instance in batch K times (using RepeatSampler)
    reward_funcs=reward_env,  # extracts terminal rewards from episode rollouts
    train_dataset=dataset,
    args=grpo_config,
    peft_config=peft_config
)

# Train on the dataset; this will save only the adapters to the checkpoints directory
grpo_trainer.train()