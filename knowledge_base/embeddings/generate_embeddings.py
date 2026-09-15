import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# Project paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

CHUNKS_DIR = BASE_DIR / "data" / "chunks"
EMBEDDINGS_DIR = BASE_DIR / "data" / "embeddings"

EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Embedding model
# ============================================================

MODEL_NAME = "all-MiniLM-L6-v2"


# ============================================================
# Load chunks
# ============================================================

def load_chunks(filename):
    file_path = CHUNKS_DIR / filename

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# Generate embeddings
# ============================================================

def generate_embeddings(records, output_name, model):

    texts = [
        record.get("text", "")
        for record in records
        if record.get("text", "").strip()
    ]

    print(f"\nGenerating embeddings for {len(texts)} chunks...")

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype=np.float32
    )

    output_file = EMBEDDINGS_DIR / output_name

    np.save(output_file, embeddings)

    print(f"Saved: {output_file}")
    print(f"Shape: {embeddings.shape}")


# ============================================================
# Main process
# ============================================================

if __name__ == "__main__":

    print("Loading embedding model...")
    print(f"Model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    print("\nLoading chunks...")

    truthfulqa = load_chunks(
        "truthfulqa_chunks.json"
    )

    squad_train = load_chunks(
        "squad_train_chunks.json"
    )

    squad_validation = load_chunks(
        "squad_validation_chunks.json"
    )

    curated_science = load_chunks(
        "curated_science_chunks.json"
    )

    print("\nChunk counts:")
    print(f"TruthfulQA: {len(truthfulqa)}")
    print(f"SQuAD train: {len(squad_train)}")
    print(f"SQuAD validation: {len(squad_validation)}")
    print(f"Curated Science: {len(curated_science)}")

    # --------------------------------------------------------
    # Generate embeddings for TruthfulQA
    # --------------------------------------------------------

    generate_embeddings(
        truthfulqa,
        "truthfulqa_embeddings.npy",
        model
    )

    # --------------------------------------------------------
    # Generate embeddings for SQuAD train
    # --------------------------------------------------------

    generate_embeddings(
        squad_train,
        "squad_train_embeddings.npy",
        model
    )

    # --------------------------------------------------------
    # Generate embeddings for SQuAD validation
    # --------------------------------------------------------

    generate_embeddings(
        squad_validation,
        "squad_validation_embeddings.npy",
        model
    )

    # --------------------------------------------------------
    # Generate embeddings for Curated Science
    # --------------------------------------------------------

    generate_embeddings(
        curated_science,
        "curated_science_embeddings.npy",
        model
    )

    print("\nEmbedding generation completed successfully.")