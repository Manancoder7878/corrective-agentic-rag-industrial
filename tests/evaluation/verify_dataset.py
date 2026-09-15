import json
from pathlib import Path


def verify_golden_dataset():
    dataset_path = Path("tests/evaluation/golden_dataset.json")
    assert dataset_path.exists(), f"Missing dataset file at {dataset_path}"

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list) and len(data) >= 5, "Dataset must contain at least 5 test cases."

    required_keys = {"id", "category", "question", "ground_truth_answer", "ground_truth_pages"}
    for idx, sample in enumerate(data):
        missing = required_keys - set(sample.keys())
        assert not missing, f"Sample #{idx} missing keys: {missing}"
        assert len(sample["ground_truth_pages"]) > 0, f"Sample #{idx} has no ground-truth pages."

    print(f" Golden dataset validated: {len(data)} test cases loaded successfully.")


if __name__ == "__main__":
    verify_golden_dataset()