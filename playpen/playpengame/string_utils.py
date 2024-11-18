import string
from typing import List


def remove_punctuation(text: str) -> str:
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text


# the methods below might be composed into a new class
# ---
def to_pair_descriptor(model_pair: List[str]) -> str:
    assert len(model_pair) == 2, "Model pair should have exactly two entries"
    return "--".join(model_pair)


def to_model_pair(pair_descriptor: str) -> List[str]:
    model_pair = pair_descriptor.split("--")
    assert len(model_pair) == 2, "Model pair should have exactly two entries"
    return model_pair


def is_pair_descriptor(text: str) -> bool:
    return "--" in text

# ---
