import os
import json
import numpy as np
import faiss


# ============================================================
# Project directories
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

EMBEDDINGS_DIR = os.path.join(
    BASE_DIR,
    "data",
    "embeddings"
)

CHUNKS_DIR = os.path.join(
    BASE_DIR,
    "data",
    "chunks"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "data",
    "vector_store"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# Datasets included in the knowledge base
# ============================================================

DATASETS = [
    (
        "truthfulqa",
        "truthfulqa_embeddings.npy",
        "truthfulqa_chunks.json"
    ),
    (
        "squad_train",
        "squad_train_embeddings.npy",
        "squad_train_chunks.json"
    ),
    (
        "squad_validation",
        "squad_validation_embeddings.npy",
        "squad_validation_chunks.json"
    ),
    (
        "curated_science",
        "curated_science_embeddings.npy",
        "curated_science_chunks.json"
    )
]


# ============================================================
# Prepare storage
# ============================================================

all_embeddings = []
all_chunks = []
metadata = []

print("Building FAISS vector store...\n")


# ============================================================
# Load all datasets
# ============================================================

for dataset_name, embedding_file, chunk_file in DATASETS:

    embedding_path = os.path.join(
        EMBEDDINGS_DIR,
        embedding_file
    )

    chunk_path = os.path.join(
        CHUNKS_DIR,
        chunk_file
    )

    print(f"Loading {dataset_name}...")

    if not os.path.exists(embedding_path):
        raise FileNotFoundError(
            f"Embedding file not found: {embedding_path}"
        )

    if not os.path.exists(chunk_path):
        raise FileNotFoundError(
            f"Chunk file not found: {chunk_path}"
        )

    embeddings = np.load(embedding_path)

    with open(
        chunk_path,
        "r",
        encoding="utf-8"
    ) as file:
        chunks = json.load(file)

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    if len(embeddings) != len(chunks):
        raise ValueError(
            f"Mismatch in {dataset_name}: "
            f"{len(embeddings)} embeddings vs "
            f"{len(chunks)} chunks"
        )

    all_embeddings.append(embeddings)
    all_chunks.extend(chunks)

    metadata.extend(
        [
            {
                "dataset": dataset_name,
                "chunk_id": i
            }
            for i in range(len(chunks))
        ]
    )

    print(f"  Embeddings: {len(embeddings)}")
    print(f"  Chunks:     {len(chunks)}")


# ============================================================
# Combine all embeddings
# ============================================================

print("\nCombining embeddings...")

combined_embeddings = np.vstack(
    all_embeddings
)

print(
    f"Combined embedding shape: "
    f"{combined_embeddings.shape}"
)


# ============================================================
# Create FAISS index
# ============================================================

print("\nCreating FAISS index...")

dimension = combined_embeddings.shape[1]

index = faiss.IndexFlatL2(
    dimension
)

index.add(
    combined_embeddings
)

print(
    f"Embedding dimension: {dimension}"
)

print(
    f"Total vectors: {index.ntotal}"
)


# ============================================================
# Save FAISS index
# ============================================================

index_path = os.path.join(
    OUTPUT_DIR,
    "knowledge_base.index"
)

faiss.write_index(
    index,
    index_path
)


# ============================================================
# Save combined chunks
# ============================================================

chunks_path = os.path.join(
    OUTPUT_DIR,
    "chunks.json"
)

with open(
    chunks_path,
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        all_chunks,
        file,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# Save metadata
# ============================================================

metadata_path = os.path.join(
    OUTPUT_DIR,
    "metadata.json"
)

with open(
    metadata_path,
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        metadata,
        file,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# Completion message
# ============================================================

print("\nFAISS vector store created successfully.")

print(f"\nIndex:    {index_path}")
print(f"Chunks:   {chunks_path}")
print(f"Metadata: {metadata_path}")
print(f"Total chunks saved: {len(all_chunks)}")