import json
import re
from pathlib import Path


# ============================================================
# Directory Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Utility Functions
# ============================================================

def clean_text(text):
    """
    Remove extra spaces and convert the value to a string.
    """

    if not text:
        return ""

    text = str(text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def save_json(data, filename):
    """
    Save processed records as a JSON file.
    """

    output_file = PROCESSED_DIR / filename

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(f"Saved: {output_file}")


# ============================================================
# TruthfulQA Preprocessing
# ============================================================

def preprocess_truthfulqa():
    """
    Preprocess TruthfulQA records.
    """

    print("Processing TruthfulQA...")

    input_file = RAW_DIR / "truthfulqa.json"

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as file:
        records = json.load(file)

    processed = []

    for record in records:

        question = clean_text(
            record.get("question")
        )

        answer = clean_text(
            record.get("best_answer")
        )

        source = clean_text(
            record.get("source")
        )

        if not question:
            continue

        processed.append({
            "id": f"truthfulqa_{len(processed) + 1}",
            "dataset": "TruthfulQA",
            "question": question,
            "answer": answer,
            "source": source
        })

    save_json(
        processed,
        "truthfulqa_processed.json"
    )

    print(
        f"TruthfulQA processed: {len(processed)} records"
    )


# ============================================================
# SQuAD Preprocessing
# ============================================================

def preprocess_squad(
    filename,
    output_filename
):
    """
    Preprocess SQuAD records.
    """

    print(f"Processing {filename}...")

    input_file = RAW_DIR / filename

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as file:
        records = json.load(file)

    processed = []

    for record in records:

        question = clean_text(
            record.get("question")
        )

        context = clean_text(
            record.get("context")
        )

        title = clean_text(
            record.get("title")
        )

        answers = record.get(
            "answers",
            {}
        )

        answer = ""

        if isinstance(answers, dict):

            answer_list = answers.get(
                "text",
                []
            )

            if answer_list:
                answer = clean_text(
                    answer_list[0]
                )

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

    save_json(
        processed,
        output_filename
    )

    print(
        f"{filename} processed: {len(processed)} records"
    )


# ============================================================
# Curated Science Preprocessing
# ============================================================

def preprocess_curated_science():
    """
    Preprocess the curated science knowledge file.

    utf-8-sig is used because the JSON file was created
    with a UTF-8 BOM by PowerShell.
    """

    print("Processing Curated Science...")

    input_file = RAW_DIR / "curated_science.json"

    with open(
        input_file,
        "r",
        encoding="utf-8-sig"
    ) as file:
        records = json.load(file)

    processed = []

    for record in records:

        question = clean_text(
            record.get("question")
        )

        answer = clean_text(
            record.get("answer")
        )

        context = clean_text(
            record.get("context")
        )

        title = clean_text(
            record.get("title")
        )

        record_id = clean_text(
            record.get("id")
        )

        if not question or not context:
            continue

        if not record_id:
            record_id = (
                f"science_{len(processed) + 1}"
            )

        processed.append({
            "id": record_id,
            "dataset": "CuratedScience",
            "title": title,
            "question": question,
            "answer": answer,
            "context": context
        })

    save_json(
        processed,
        "curated_science_processed.json"
    )

    print(
        "Curated Science processed: "
        f"{len(processed)} records"
    )


# ============================================================
# Main Execution
# ============================================================

if __name__ == "__main__":

    print("Starting preprocessing...\n")

    # Process TruthfulQA
    preprocess_truthfulqa()

    print()

    # Process SQuAD training data
    preprocess_squad(
        "squad_train.json",
        "squad_train_processed.json"
    )

    print()

    # Process SQuAD validation data
    preprocess_squad(
        "squad_validation.json",
        "squad_validation_processed.json"
    )

    print()

    # Process curated science data
    preprocess_curated_science()

    print()
    print("Preprocessing completed successfully.")