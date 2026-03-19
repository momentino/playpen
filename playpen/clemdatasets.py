from datasets import load_dataset

class ClemDataset:
    def __init__(self, path: str, name: str, split: str):
        """
            path: str -> the name of a Huggingface's dataset path
            name: str -> The name of the Huggingface dataset's subset (e.g. interactions, instances)
            split: str -> the name of the split (e.g. train, validation)
        """
        self.dataset = load_dataset(path, name, split=split)

class ClemDatasetv2(ClemDataset):
    def __init__(self, name: str, split: str):
        """
            name: str -> The name of the Huggingface dataset's subset (e.g. interactions, instances)
            split: str -> the name of the split (e.g. train, validation)
        """
        path = "colab-potsdam/playpen-data"
        super().__init__(path, name, split)