import os
import json
import re

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

VECTOR_STORE_DIR = os.path.join(
    BASE_DIR,
    "data",
    "vector_store"
)

INDEX_PATH = os.path.join(
    VECTOR_STORE_DIR,
    "knowledge_base.index"
)

CHUNKS_PATH = os.path.join(
    VECTOR_STORE_DIR,
    "chunks.json"
)


# ============================================================
# LOAD FAISS INDEX
# ============================================================

index = faiss.read_index(
    INDEX_PATH
)


# ============================================================
# LOAD CHUNKS
# ============================================================

with open(
    CHUNKS_PATH,
    "r",
    encoding="utf-8"
) as f:

    chunks = json.load(f)


# ============================================================
# EMBEDDING MODEL
# ============================================================

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize(text: str) -> str:

    text = text.lower()

    text = re.sub(
        r"[^a-zA-ZÀ-ÿ0-9\s]",
        " ",
        text
    )

    return " ".join(
        text.split()
    )


# ============================================================
# GET CHUNK TEXT
# ============================================================

def get_text(chunk) -> str:

    if isinstance(chunk, dict):

        return chunk.get(
            "text",
            ""
        )

    return str(chunk)


# ============================================================
# TOKENIZE
# ============================================================

def tokenize(text: str):

    return set(
        normalize(text).split()
    )


# ============================================================
# KEYWORD OVERLAP
# ============================================================

def keyword_overlap(
    query: str,
    text: str
) -> float:

    query_words = tokenize(query)
    text_words = tokenize(text)

    if not query_words:
        return 0.0

    overlap = (
        query_words &
        text_words
    )

    return len(overlap) / len(
        query_words
    )


# ============================================================
# EXTRACT CAPITAL QUESTION
# ============================================================

def extract_capital_country(
    query: str
):

    q = normalize(query)

    match = re.search(
        r"what is (?:the )?capital of ([a-zA-ZÀ-ÿ-]+)",
        q
    )

    if match:

        return match.group(1)

    return None


# ============================================================
# DIRECT CAPITAL FACT
# ============================================================

def direct_capital_match(
    query: str,
    text: str
) -> bool:

    country = extract_capital_country(
        query
    )

    if not country:
        return False

    normalized_text = normalize(
        text
    )

    pattern = (
        r"\b([a-zA-ZÀ-ÿ-]+)"
        r"\s+is\s+"
        r"(?:the\s+)?capital\s+of\s+"
        + re.escape(country)
        + r"\b"
    )

    return bool(
        re.search(
            pattern,
            normalized_text,
            re.IGNORECASE
        )
    )


# ============================================================
# FIND DIRECT FACTS
# ============================================================

def find_direct_facts(
    query: str
):

    matches = []

    country = extract_capital_country(
        query
    )

    if not country:
        return matches

    pattern = re.compile(
        r"\b([a-zA-ZÀ-ÿ-]+)"
        r"\s+is\s+"
        r"(?:the\s+)?capital\s+of\s+"
        + re.escape(country)
        + r"\b",
        re.IGNORECASE
    )

    for index_id, chunk in enumerate(
        chunks
    ):

        text = get_text(
            chunk
        )

        normalized_text = normalize(
            text
        )

        if pattern.search(
            normalized_text
        ):

            matches.append(
                {
                    "chunk": chunk,
                    "distance": 0.0,
                    "index": index_id,
                    "semantic_similarity": 1.0,
                    "keyword_overlap": 1.0,
                    "phrase_score": 1.0,
                    "direct_fact_score": 1.0,
                    "relevance_score": 1.0,
                    "exact_match": True
                }
            )

    return matches


# ============================================================
# FAISS RETRIEVAL
# ============================================================

def faiss_retrieve(
    query: str,
    search_k: int
):

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    ).astype("float32")

    distances, indices = index.search(
        query_embedding,
        search_k
    )

    results = []

    seen_text = set()

    for distance, index_id in zip(
        distances[0],
        indices[0]
    ):

        if index_id == -1:
            continue

        index_id = int(
            index_id
        )

        chunk = chunks[
            index_id
        ]

        text = get_text(
            chunk
        )

        normalized_text = normalize(
            text
        )

        if not normalized_text:
            continue

        # Remove duplicate text
        if normalized_text in seen_text:
            continue

        seen_text.add(
            normalized_text
        )

        results.append(
            {
                "chunk": chunk,
                "distance": float(
                    distance
                ),
                "index": index_id
            }
        )

    return results


# ============================================================
# RERANK RESULTS
# ============================================================

def rerank(
    query: str,
    candidates: list
):

    if not candidates:
        return []

    texts = [
        get_text(
            item["chunk"]
        )
        for item in candidates
    ]

    # --------------------------------------------------------
    # Query embedding
    # --------------------------------------------------------

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0]

    # --------------------------------------------------------
    # Text embeddings
    # --------------------------------------------------------

    text_embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # --------------------------------------------------------
    # Semantic similarity
    # --------------------------------------------------------

    semantic_scores = np.dot(
        text_embeddings,
        query_embedding
    )

    # --------------------------------------------------------
    # Calculate scores
    # --------------------------------------------------------

    for i, item in enumerate(
        candidates
    ):

        text = texts[i]

        semantic = float(
            semantic_scores[i]
        )

        keyword = keyword_overlap(
            query,
            text
        )

        direct = (
            1.0
            if direct_capital_match(
                query,
                text
            )
            else 0.0
        )

        normalized_query = normalize(
            query
        )

        normalized_text = normalize(
            text
        )

        phrase = (
            1.0
            if normalized_query
            in normalized_text
            else 0.0
        )

        # ----------------------------------------------------
        # Hybrid relevance
        # ----------------------------------------------------

        relevance = (
            0.30 * semantic
            +
            0.20 * keyword
            +
            0.10 * phrase
            +
            0.40 * direct
        )

        # Direct fact gets highest priority
        if direct == 1.0:

            relevance = 1.0

        # ----------------------------------------------------
        # Store scores
        # ----------------------------------------------------

        item[
            "semantic_similarity"
        ] = round(
            semantic,
            4
        )

        item[
            "keyword_overlap"
        ] = round(
            keyword,
            4
        )

        item[
            "phrase_score"
        ] = round(
            phrase,
            4
        )

        item[
            "direct_fact_score"
        ] = round(
            direct,
            4
        )

        item[
            "relevance_score"
        ] = round(
            relevance,
            4
        )

        item[
            "exact_match"
        ] = (
            direct == 1.0
        )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    candidates.sort(
        key=lambda x: (
            x["exact_match"],
            x["direct_fact_score"],
            x["relevance_score"],
            x["semantic_similarity"]
        ),
        reverse=True
    )

    return candidates


# ============================================================
# MAIN RETRIEVE FUNCTION
# ============================================================

def retrieve(
    query: str,
    top_k: int = 5
):

    # --------------------------------------------------------
    # STEP 1
    # Direct factual search
    # --------------------------------------------------------

    direct_results = find_direct_facts(
        query
    )

    # --------------------------------------------------------
    # STEP 2
    # FAISS search
    # --------------------------------------------------------

    search_k = min(
        max(
            top_k * 20,
            100
        ),
        index.ntotal
    )

    faiss_results = faiss_retrieve(
        query,
        search_k
    )

    # --------------------------------------------------------
    # STEP 3
    # Combine and remove duplicates
    # --------------------------------------------------------

    combined = []

    seen_text = set()

    # Direct results first
    for item in direct_results:

        text = get_text(
            item["chunk"]
        )

        normalized_text = normalize(
            text
        )

        if not normalized_text:
            continue

        if normalized_text in seen_text:
            continue

        seen_text.add(
            normalized_text
        )

        combined.append(
            item
        )

    # FAISS results second
    for item in faiss_results:

        text = get_text(
            item["chunk"]
        )

        normalized_text = normalize(
            text
        )

        if not normalized_text:
            continue

        if normalized_text in seen_text:
            continue

        seen_text.add(
            normalized_text
        )

        combined.append(
            item
        )

    # --------------------------------------------------------
    # STEP 4
    # Rerank
    # --------------------------------------------------------

    combined = rerank(
        query,
        combined
    )

    # --------------------------------------------------------
    # STEP 5
    # Return top K
    # --------------------------------------------------------

    return combined[:top_k]


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    query = (
        "What is the capital of France?"
    )

    results = retrieve(
        query,
        top_k=5
    )

    print()
    print("=" * 70)
    print("QUERY")
    print("=" * 70)

    print(query)

    print()
    print("=" * 70)
    print("RETRIEVED EVIDENCE")
    print("=" * 70)

    for i, result in enumerate(
        results,
        start=1
    ):

        print()
        print(
            f"--- Result {i} ---"
        )

        print(
            "FAISS distance:",
            round(
                result["distance"],
                4
            )
        )

        print(
            "Semantic similarity:",
            result[
                "semantic_similarity"
            ]
        )

        print(
            "Keyword overlap:",
            result[
                "keyword_overlap"
            ]
        )

        print(
            "Phrase score:",
            result[
                "phrase_score"
            ]
        )

        print(
            "Direct fact score:",
            result[
                "direct_fact_score"
            ]
        )

        print(
            "Relevance score:",
            result[
                "relevance_score"
            ]
        )

        print(
            "Exact match:",
            result[
                "exact_match"
            ]
        )

        print(
            "Index:",
            result["index"]
        )

        print(
            "Text:",
            get_text(
                result["chunk"]
            )[:1200]
        )

        print()