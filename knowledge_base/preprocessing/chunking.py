import json
from pathlib import Path


# ============================================================
# Directory Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"
CHUNKS_DIR = BASE_DIR / "data" / "chunks"

CHUNKS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Chunk Configuration
# ============================================================

CHUNK_SIZE = 500
OVERLAP = 50


# ============================================================
# Text Chunking
# ============================================================

def split_text(text):
    """
    Split text into chunks of 500 words
    with an overlap of 50 words.
    """

    words = text.split()
    chunks = []

    start = 0

    while start < len(words):

        end = min(
            start + CHUNK_SIZE,
            len(words)
        )

        chunk = " ".join(
            words[start:end]
        )

        if chunk.strip():
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - OVERLAP

    return chunks


# ============================================================
# JSON Loading
# ============================================================

def load_json(filename):
    """
    Load a JSON file from the processed directory.
    """

    input_file = PROCESSED_DIR / filename

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ============================================================
# Create Dataset Chunks
# ============================================================

def create_chunks(records, dataset_name):
    """
    Create chunks for TruthfulQA, SQuAD,
    and CuratedScience datasets.
    """

    chunks = []
    chunk_id = 1

    for record in records:

        question = record.get(
            "question",
            ""
        )

        answer = record.get(
            "answer",
            ""
        )

        record_id = record.get(
            "id",
            ""
        )

        title = record.get(
            "title",
            ""
        )

        # Select the correct source text
        if dataset_name == "SQuAD":
            source_text = record.get(
                "context",
                ""
            )

        elif dataset_name == "CuratedScience":
            source_text = record.get(
                "context",
                ""
            )

        else:
            source_text = record.get(
                "source",
                ""
            )

        # Fallback if source text is empty
        if not source_text:
            source_text = (
                f"{question} {answer}"
            )

        source_text = str(source_text).strip()

        if not source_text:
            continue

        text_chunks = split_text(
            source_text
        )

        for chunk in text_chunks:

            chunks.append({
                "chunk_id": (
                    f"{dataset_name.lower()}_{chunk_id}"
                ),
                "record_id": record_id,
                "dataset": dataset_name,
                "question": question,
                "answer": answer,
                "title": title,
                "source": source_text,
                "text": chunk
            })

            chunk_id += 1

    return chunks


# ============================================================
# Save Chunks
# ============================================================

def save_chunks(chunks, filename):
    """
    Save generated chunks as JSON.
    """

    output_file = CHUNKS_DIR / filename

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            chunks,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(f"Saved: {output_file}")
    print(f"Chunks created: {len(chunks)}")


# ============================================================
# Main Execution
# ============================================================

if __name__ == "__main__":

    print("Loading processed datasets...\n")

    # TruthfulQA
    truthfulqa = load_json(
        "truthfulqa_processed.json"
    )

    print("Creating TruthfulQA chunks...")

    truthfulqa_chunks = create_chunks(
        truthfulqa,
        "TruthfulQA"
    )

    save_chunks(
        truthfulqa_chunks,
        "truthfulqa_chunks.json"
    )

    print()

    # SQuAD training data
    squad_train = load_json(
        "squad_train_processed.json"
    )

    print("Creating SQuAD train chunks...")

    squad_train_chunks = create_chunks(
        squad_train,
        "SQuAD"
    )

    save_chunks(
        squad_train_chunks,
        "squad_train_chunks.json"
    )

    print()

    # SQuAD validation data
    squad_validation = load_json(
        "squad_validation_processed.json"
    )

    print("Creating SQuAD validation chunks...")

    squad_validation_chunks = create_chunks(
        squad_validation,
        "SQuAD"
    )

    save_chunks(
        squad_validation_chunks,
        "squad_validation_chunks.json"
    )

    print()

    # Curated Science
    curated_science = load_json(
        "curated_science_processed.json"
    )

    print("Creating Curated Science chunks...")

    curated_science_chunks = create_chunks(
        curated_science,
        "CuratedScience"
    )

    save_chunks(
        curated_science_chunks,
        "curated_science_chunks.json"
    )

    print()
    print("Chunking completed successfully.")