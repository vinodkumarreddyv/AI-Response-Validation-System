import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text):
    if not text:
        return ""

    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def save_json(data, filename):
    output_file = PROCESSED_DIR / filename

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print(f"Saved: {output_file}")


def preprocess_truthfulqa():
    print("Processing TruthfulQA...")

    with open(RAW_DIR / "truthfulqa.json", "r", encoding="utf-8") as file:
        records = json.load(file)

    processed = []

    for record in records:
        question = clean_text(record.get("question"))
        answer = clean_text(record.get("best_answer"))
        source = clean_text(record.get("source"))

        if not question:
            continue

        processed.append({
            "id": f"truthfulqa_{len(processed) + 1}",
            "dataset": "TruthfulQA",
            "question": question,
            "answer": answer,
            "source": source
        })

    save_json(processed, "truthfulqa_processed.json")
    print(f"TruthfulQA processed: {len(processed)} records")


def preprocess_squad(filename, output_filename):
    print(f"Processing {filename}...")

    with open(RAW_DIR / filename, "r", encoding="utf-8") as file:
        records = json.load(file)

    processed = []

    for record in records:
        question = clean_text(record.get("question"))
        context = clean_text(record.get("context"))
        title = clean_text(record.get("title"))

        answers = record.get("answers", {})
        answer = ""

        if isinstance(answers, dict):
            answer_list = answers.get("text", [])

            if answer_list:
                answer = clean_text(answer_list[0])

        if not question or not context:
            continue

        processed.append({
            "id": f"squad_{len(processed) + 1}",
            "dataset": "SQuAD",
            "title": title,
            "question": question,
            "answer": answer,
            "context": context
        })

    save_json(processed, output_filename)
    print(f"{filename} processed: {len(processed)} records")


if __name__ == "__main__":

    preprocess_truthfulqa()

    preprocess_squad(
        "squad_train.json",
        "squad_train_processed.json"
    )

    preprocess_squad(
        "squad_validation.json",
        "squad_validation_processed.json"
    )

    print()
    print("Preprocessing completed successfully.")