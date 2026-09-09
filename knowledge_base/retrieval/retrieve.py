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

index = faiss.read_index(INDEX_PATH)


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
# NORMALIZE TEXT
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
# GET TEXT FROM CHUNK
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
# EXTRACT CAPITAL COUNTRY
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

            matches.append({
                "chunk": chunk,
                "distance": 0.0,
                "index": index_id,
                "semantic_similarity": 1.0,
                "keyword_overlap": 1.0,
                "phrase_score": 1.0,
                "topic_match": 1.0,
                "direct_fact_score": 1.0,
                "relevance_score": 1.0,
                "exact_match": True
            })

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
        convert_to_numpy=True,
        normalize_embeddings=True
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

        if normalized_text in seen_text:
            continue

        seen_text.add(
            normalized_text
        )

        results.append({
            "chunk": chunk,
            "distance": float(
                distance
            ),
            "index": index_id
        })

    return results


# ============================================================
# TOPIC KEYWORDS
# ============================================================

def get_topic_keywords(
    query: str
):

    q = normalize(query)

    keywords = set()

    # --------------------------------------------------------
    # ICE FLOATING
    # --------------------------------------------------------

    if (
        "ice" in q
        and (
            "float" in q
            or "floating" in q
        )
    ):

        keywords.update([
            "ice",
            "water",
            "density",
            "dense",
            "freezes",
            "freezing",
            "expands",
            "expansion",
            "liquid"
        ])

    # --------------------------------------------------------
    # BOILING WATER
    # --------------------------------------------------------

    if (
        "water" in q
        and (
            "boil" in q
            or "boiling" in q
        )
    ):

        keywords.update([
            "water",
            "boil",
            "boiling",
            "temperature",
            "degrees",
            "celsius",
            "100"
        ])

    # --------------------------------------------------------
    # PHOTOSYNTHESIS
    # --------------------------------------------------------

    if "photosynthesis" in q:

        keywords.update([
            "photosynthesis",
            "plant",
            "plants",
            "sunlight",
            "light",
            "carbon",
            "dioxide",
            "glucose",
            "oxygen",
            "chlorophyll"
        ])

    # --------------------------------------------------------
    # CAPITAL
    # --------------------------------------------------------

    if "capital of" in q:

        keywords.update([
            "capital",
            "country",
            "city"
        ])

    return keywords


# ============================================================
# TOPIC MATCH
# ============================================================

def topic_match(
    query: str,
    text: str
) -> float:

    topic_words = get_topic_keywords(
        query
    )

    if not topic_words:
        return 0.0

    text_words = tokenize(
        text
    )

    matched = (
        topic_words &
        text_words
    )

    return len(matched) / len(
        topic_words
    )


# ============================================================
# IMPORTANT PHRASE MATCH
# ============================================================

def phrase_match(
    query: str,
    text: str
) -> float:

    q = normalize(query)
    t = normalize(text)

    phrases = []

    # --------------------------------------------------------
    # ICE FLOATING
    # --------------------------------------------------------

    if (
        "ice" in q
        and "float" in q
    ):

        phrases = [
            "ice is less dense",
            "ice less dense",
            "less dense than liquid water",
            "less dense than water",
            "water expands when it freezes",
            "water expands when frozen",
            "expands when it freezes",
            "ice density",
            "density of ice"
        ]

    # --------------------------------------------------------
    # BOILING POINT
    # --------------------------------------------------------

    elif (
        "boiling point" in q
        and "water" in q
    ):

        phrases = [
            "boils at 100 degrees",
            "boiling point of water",
            "100 degrees celsius",
            "water boils",
            "boiling temperature"
        ]

    # --------------------------------------------------------
    # PHOTOSYNTHESIS
    # --------------------------------------------------------

    elif "photosynthesis" in q:

        phrases = [
            "plants use sunlight",
            "carbon dioxide",
            "water",
            "glucose",
            "oxygen",
            "chlorophyll"
        ]

    if not phrases:
        return 0.0

    matches = 0

    for phrase in phrases:

        if phrase in t:
            matches += 1

    return min(
        matches / len(phrases),
        1.0
    )


# ============================================================
# STRONG TOPIC PENALTY
# ============================================================

def irrelevant_topic_penalty(
    query: str,
    text: str
) -> float:

    q = normalize(query)
    t = normalize(text)

    # --------------------------------------------------------
    # ICE FLOATING
    # --------------------------------------------------------

    if (
        "ice" in q
        and "float" in q
    ):

        unrelated_terms = [
            "antarctica",
            "antarctic",
            "glacier",
            "glaciers",
            "sea level",
            "sea levels",
            "ice shelf",
            "ice shelves",
            "greenland",
            "polar climate",
            "melting glacier"
        ]

        matches = sum(
            1
            for term in unrelated_terms
            if term in t
        )

        if matches >= 3:
            return 0.50

        if matches == 2:
            return 0.35

        if matches == 1:
            return 0.15

    return 0.0


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
    # IMPORTANT:
    # Use ORIGINAL question, NOT expanded question.
    # --------------------------------------------------------

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0]

    text_embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    semantic_scores = np.dot(
        text_embeddings,
        query_embedding
    )

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

        topic = topic_match(
            query,
            text
        )

        phrase = phrase_match(
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

        penalty = irrelevant_topic_penalty(
            query,
            text
        )

        # ----------------------------------------------------
        # HYBRID SCORE
        # ----------------------------------------------------

        relevance = (
            0.30 * semantic
            +
            0.15 * keyword
            +
            0.25 * topic
            +
            0.25 * phrase
            +
            0.05 * direct
            -
            penalty
        )

        relevance = max(
            0.0,
            min(
                relevance,
                1.0
            )
        )

        # Direct factual match
        if direct == 1.0:
            relevance = 1.0

        # ----------------------------------------------------
        # STORE SCORES
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
            "topic_match"
        ] = round(
            topic,
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
    # SORT
    # --------------------------------------------------------

    candidates.sort(
        key=lambda x: (
            x.get(
                "exact_match",
                False
            ),
            x.get(
                "relevance_score",
                0.0
            ),
            x.get(
                "phrase_score",
                0.0
            ),
            x.get(
                "topic_match",
                0.0
            ),
            x.get(
                "semantic_similarity",
                0.0
            )
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
    # 1. Direct fact search
    # --------------------------------------------------------

    direct_results = find_direct_facts(
        query
    )

    # --------------------------------------------------------
    # 2. FAISS search using ORIGINAL query
    # --------------------------------------------------------

    search_k = min(
        max(
            top_k * 30,
            150
        ),
        index.ntotal
    )

    faiss_results = faiss_retrieve(
        query,
        search_k
    )

    # --------------------------------------------------------
    # 3. Combine results
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

    # FAISS results
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
    # 4. Rerank
    # --------------------------------------------------------

    combined = rerank(
        query,
        combined
    )

    # --------------------------------------------------------
    # 5. Return top K
    # --------------------------------------------------------

    return combined[:top_k]


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_queries = [
        "Why does ice float on water?",
        "What is the boiling point of water?",
        "What is photosynthesis?"
    ]

    for query in test_queries:

        print()
        print("=" * 80)
        print("QUERY")
        print("=" * 80)

        print(query)

        results = retrieve(
            query,
            top_k=5
        )

        print()
        print("=" * 80)
        print("RETRIEVED EVIDENCE")
        print("=" * 80)

        for i, result in enumerate(
            results,
            start=1
        ):

            print()
            print(
                f"--- Result {i} ---"
            )

            print(
                "Semantic similarity:",
                result.get(
                    "semantic_similarity",
                    0.0
                )
            )

            print(
                "Keyword overlap:",
                result.get(
                    "keyword_overlap",
                    0.0
                )
            )

            print(
                "Topic match:",
                result.get(
                    "topic_match",
                    0.0
                )
            )

            print(
                "Phrase score:",
                result.get(
                    "phrase_score",
                    0.0
                )
            )

            print(
                "Direct fact score:",
                result.get(
                    "direct_fact_score",
                    0.0
                )
            )

            print(
                "Relevance score:",
                result.get(
                    "relevance_score",
                    0.0
                )
            )

            print(
                "Exact match:",
                result.get(
                    "exact_match",
                    False
                )
            )

            print(
                "Index:",
                result.get(
                    "index",
                    -1
                )
            )

            print(
                "Text:",
                get_text(
                    result["chunk"]
                )[:1200]
            )

            print()