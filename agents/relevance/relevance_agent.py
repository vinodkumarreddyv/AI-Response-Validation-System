from typing import Dict
import re
import numpy as np
from sentence_transformers import SentenceTransformer


# Use the same embedding model used by the knowledge base
MODEL_NAME = "all-MiniLM-L6-v2"

_model = SentenceTransformer(MODEL_NAME)


STOP_WORDS = {
    "what", "is", "are", "was", "were", "the", "a", "an",
    "of", "to", "in", "on", "for", "and", "or", "do", "does",
    "why", "how", "can", "could", "would", "should", "with",
    "by", "from", "that", "this", "it", "as"
}


def clean_words(text: str):
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    return {word for word in words if word not in STOP_WORDS}


def semantic_similarity(question: str, response: str) -> float:
    embeddings = _model.encode(
        [question, response],
        normalize_embeddings=True
    )

    similarity = float(np.dot(embeddings[0], embeddings[1]))

    return max(0.0, min(1.0, similarity))


def evaluate_relevance(
    question: str,
    ai_response: str
) -> Dict:
    """
    Evaluate how relevant an AI response is to a question.

    Score:
        5 = Fully Relevant
        4 = Mostly Relevant
        3 = Partially Relevant
        2 = Mostly Irrelevant
        1 = Completely Irrelevant
    """

    question = question.strip()
    ai_response = ai_response.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    if not ai_response:
        raise ValueError("AI response cannot be empty.")

    question_words = clean_words(question)
    response_words = clean_words(ai_response)

    common_words = question_words.intersection(response_words)

    if question_words:
        keyword_overlap = len(common_words) / len(question_words)
    else:
        keyword_overlap = 0.0

    similarity = semantic_similarity(
        question,
        ai_response
    )

    # Combine semantic and lexical signals
    combined_score = (
        0.75 * similarity +
        0.25 * keyword_overlap
    )

    # Relevance classification
    if combined_score >= 0.72:
        score = 5
        label = "Fully Relevant"
        reasoning = (
            "The response directly addresses the question "
            "and provides information closely related to what was asked."
        )

    elif combined_score >= 0.58:
        score = 4
        label = "Mostly Relevant"
        reasoning = (
            "The response addresses the main topic of the question "
            "but may omit some relevant details."
        )

    elif combined_score >= 0.42:
        score = 3
        label = "Partially Relevant"
        reasoning = (
            "The response has a meaningful connection to the question "
            "but only partially addresses what was asked."
        )

    elif combined_score >= 0.25:
        score = 2
        label = "Mostly Irrelevant"
        reasoning = (
            "The response has limited connection to the question "
            "and does not adequately answer it."
        )

    else:
        score = 1
        label = "Completely Irrelevant"
        reasoning = (
            "The response does not meaningfully address the subject "
            "of the question."
        )

    return {
        "score": score,
        "label": label,
        "reasoning": reasoning,
        "question": question,
        "ai_response": ai_response,
        "semantic_similarity": round(similarity, 3),
        "keyword_overlap": round(keyword_overlap, 3),
        "combined_score": round(combined_score, 3)
    }