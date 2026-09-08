from typing import Dict, List
import re
import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

_model = SentenceTransformer(MODEL_NAME)


STOP_WORDS = {
    "what", "is", "are", "was", "were", "the", "a", "an",
    "of", "to", "in", "on", "for", "and", "or", "do", "does",
    "why", "how", "can", "could", "would", "should", "with",
    "by", "from", "that", "this", "it", "as"
}


def clean_words(text: str) -> set:
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    return {word for word in words if word not in STOP_WORDS}


def calculate_similarity(text1: str, text2: str) -> float:
    embeddings = _model.encode(
        [text1, text2],
        normalize_embeddings=True
    )

    similarity = float(
        np.dot(embeddings[0], embeddings[1])
    )

    return max(0.0, min(1.0, similarity))


def keyword_overlap(text1: str, text2: str) -> float:
    words1 = clean_words(text1)
    words2 = clean_words(text2)

    if not words1:
        return 0.0

    common_words = words1.intersection(words2)

    return len(common_words) / len(words1)


def extract_numbers(text: str) -> List[float]:
    """
    Extract numeric values from text.
    Examples:
        0
        100
        37.5
    """
    values = re.findall(r"\b\d+(?:\.\d+)?\b", text)

    return [float(value) for value in values]


def detect_numeric_contradiction(
    ai_response: str,
    reference_answer: str
) -> bool:
    """
    Detect whether the AI response and reference contain
    different numeric values for a highly similar statement.
    """

    ai_numbers = extract_numbers(ai_response)
    reference_numbers = extract_numbers(reference_answer)

    if not ai_numbers or not reference_numbers:
        return False

    # If both contain numbers but the values differ,
    # treat it as a possible factual contradiction.
    for ai_number in ai_numbers:
        for reference_number in reference_numbers:
            if ai_number != reference_number:
                return True

    return False


def evaluate_accuracy(
    ai_response: str,
    reference_answer: str | None = None,
    evidence: List[Dict] | None = None
) -> Dict:
    """
    Evaluate factual accuracy of an AI-generated response.

    Score:
        5 = Correct
        4 = Mostly Correct
        3 = Partially Correct
        2 = Mostly Incorrect
        1 = Incorrect
    """

    ai_response = ai_response.strip()

    if not ai_response:
        raise ValueError("AI response cannot be empty.")

    evidence = evidence or []

    # =========================================================
    # CASE 1: Reference answer is available
    # =========================================================

    if reference_answer and reference_answer.strip():

        reference_answer = reference_answer.strip()

        similarity = calculate_similarity(
            ai_response,
            reference_answer
        )

        overlap = keyword_overlap(
            reference_answer,
            ai_response
        )

        combined_score = (
            0.75 * similarity +
            0.25 * overlap
        )

        numeric_contradiction = detect_numeric_contradiction(
            ai_response,
            reference_answer
        )

        # -----------------------------------------------------
        # Contradiction has priority over semantic similarity
        # -----------------------------------------------------

        if numeric_contradiction and similarity >= 0.55:

            score = 1
            label = "Incorrect"
            reasoning = (
                "The response is semantically related to the reference "
                "but contains a conflicting factual value."
            )

        elif combined_score >= 0.72:

            score = 5
            label = "Correct"
            reasoning = (
                "The AI response is highly similar to the reference "
                "answer and contains the expected information."
            )

        elif combined_score >= 0.58:

            score = 4
            label = "Mostly Correct"
            reasoning = (
                "The AI response agrees with most of the reference "
                "answer but may omit some information."
            )

        elif combined_score >= 0.42:

            score = 3
            label = "Partially Correct"
            reasoning = (
                "The AI response contains some information consistent "
                "with the reference answer but does not fully match it."
            )

        elif combined_score >= 0.25:

            score = 2
            label = "Mostly Incorrect"
            reasoning = (
                "The AI response has limited agreement with the "
                "reference answer and contains insufficient correct information."
            )

        else:

            score = 1
            label = "Incorrect"
            reasoning = (
                "The AI response has very little agreement with "
                "the provided reference answer."
            )

        supporting_evidence = [
            {
                "source": "reference_answer",
                "text": reference_answer,
                "similarity": round(similarity, 3)
            }
        ]

        return {
            "score": score,
            "label": label,
            "reasoning": reasoning,
            "supporting_evidence": supporting_evidence,
            "reference_similarity": round(similarity, 3),
            "keyword_overlap": round(overlap, 3),
            "combined_score": round(combined_score, 3),
            "numeric_contradiction": numeric_contradiction
        }

    # =========================================================
    # CASE 2: No reference answer - use retrieved evidence
    # =========================================================

    if evidence:

        best_evidence = None
        best_similarity = 0.0

        for item in evidence:

            evidence_text = item.get("text", "")

            if not evidence_text:
                continue

            similarity = calculate_similarity(
                ai_response,
                evidence_text
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_evidence = item

        if best_evidence:

            evidence_text = best_evidence.get("text", "")

            overlap = keyword_overlap(
                evidence_text,
                ai_response
            )

            combined_score = (
                0.75 * best_similarity +
                0.25 * overlap
            )

            numeric_contradiction = detect_numeric_contradiction(
                ai_response,
                evidence_text
            )

            if numeric_contradiction and best_similarity >= 0.55:

                score = 1
                label = "Incorrect"
                reasoning = (
                    "The response is related to the retrieved evidence "
                    "but contains a conflicting factual value."
                )

            elif combined_score >= 0.72:

                score = 5
                label = "Correct"
                reasoning = (
                    "The AI response is strongly supported by "
                    "the retrieved reference evidence."
                )

            elif combined_score >= 0.58:

                score = 4
                label = "Mostly Correct"
                reasoning = (
                    "The AI response is mostly supported by "
                    "the retrieved evidence but may omit some details."
                )

            elif combined_score >= 0.42:

                score = 3
                label = "Partially Correct"
                reasoning = (
                    "The AI response has partial support from "
                    "the retrieved evidence."
                )

            elif combined_score >= 0.25:

                score = 2
                label = "Mostly Incorrect"
                reasoning = (
                    "The retrieved evidence provides limited support "
                    "for the AI response."
                )

            else:

                score = 1
                label = "Incorrect"
                reasoning = (
                    "The retrieved evidence does not provide sufficient "
                    "support for the AI response."
                )

            supporting_evidence = [
                {
                    "source": "retrieved_evidence",
                    "text": evidence_text,
                    "similarity": round(best_similarity, 3)
                }
            ]

            return {
                "score": score,
                "label": label,
                "reasoning": reasoning,
                "supporting_evidence": supporting_evidence,
                "reference_similarity": None,
                "evidence_similarity": round(best_similarity, 3),
                "keyword_overlap": round(overlap, 3),
                "combined_score": round(combined_score, 3),
                "numeric_contradiction": numeric_contradiction
            }

    # =========================================================
    # CASE 3: No reference and no evidence
    # =========================================================

    return {
        "score": 0,
        "label": "Unable to Evaluate",
        "reasoning": (
            "No reference answer or supporting evidence was "
            "provided for factual accuracy evaluation."
        ),
        "supporting_evidence": [],
        "reference_similarity": None,
        "evidence_similarity": None,
        "keyword_overlap": 0.0,
        "combined_score": 0.0,
        "numeric_contradiction": False
    }