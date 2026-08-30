import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"
CHUNKS_DIR = BASE_DIR / "data" / "chunks"

CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 500
OVERLAP = 50


def split_text(text):
    words = text.split()
    chunks = []

    start = 0

    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))

        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - OVERLAP

    return chunks


def load_json(filename):
    with open(PROCESSED_DIR / filename, "r", encoding="utf-8") as file:
        return json.load(file)


def create_chunks(records, dataset_name):
    chunks = []
    chunk_id = 1

    for record in records:

        question = record.get("question", "")
        answer = record.get("answer", "")
        record_id = record.get("id", "")

        if dataset_name == "SQuAD":
            source_text = record.get("context", "")
            title = record.get("title", "")
        else:
            source_text = record.get("source", "")
            title = ""

        if not source_text:
            source_text = f"{question} {answer}"

        text_chunks = split_text(source_text)

        for chunk in text_chunks:
            chunks.append({
                "chunk_id": f"{dataset_name.lower()}_{chunk_id}",
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


def save_chunks(chunks, filename):
    output_file = CHUNKS_DIR / filename

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            chunks,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(f"Saved: {output_file}")
    print(f"Chunks created: {len(chunks)}")


if __name__ == "__main__":

    print("Loading processed datasets...")

    truthfulqa = load_json("truthfulqa_processed.json")
    squad_train = load_json("squad_train_processed.json")
    squad_validation = load_json("squad_validation_processed.json")

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
    print("Chunking completed successfully.")