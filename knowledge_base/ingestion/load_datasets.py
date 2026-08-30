from datasets import load_dataset
from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)


def save_json(data, filename):
    output_file = RAW_DIR / filename

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"Saved: {output_file}")


def load_truthfulqa():
    print("[1/2] Loading TruthfulQA...", end=" ")

    dataset = load_dataset(
        "truthfulqa/truthful_qa",
        "generation"
    )

    print("OK")
    return dataset["validation"]


def load_squad():
    print("[2/2] Loading SQuAD...", end=" ")

    dataset = load_dataset("rajpurkar/squad")

    print("OK")
    return dataset


if __name__ == "__main__":

    truthfulqa = load_truthfulqa()
    squad = load_squad()

    save_json(
        truthfulqa.to_list(),
        "truthfulqa.json"
    )

    save_json(
        squad["train"].to_list(),
        "squad_train.json"
    )

    save_json(
        squad["validation"].to_list(),
        "squad_validation.json"
    )

    print()
    print("Dataset ingestion completed.")
    print(f"TruthfulQA: {len(truthfulqa)} records")
    print(f"SQuAD train: {len(squad['train'])} records")
    print(f"SQuAD validation: {len(squad['validation'])} records")