from typing import Dict, List, Optional
import re
import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

_model = SentenceTransformer(MODEL_NAME)


def split_into_claims(response: str) -> List[str]:
    """
    Split an AI response into individual claims/sentences.
    """
    if not response:
        return []

    claims = re.split(r"(?<=[.!?])\s+", response.strip())

    return [
        claim.strip()
        for claim in claims
        if claim.strip()
    ]


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity between two pieces of text.
    """
    if not text1 or not text2:
        return 0.0

    embeddings = _model.encode(
        [text1, text2],
        normalize_embeddings=True
    )

    similarity = float(
        np.dot(embeddings[0], embeddings[1])
    )

    return max(0.0, min(1.0, similarity))


def extract_numbers(text: str) -> List[float]:
    """
    Extract numeric values from text.
    """
    if not text:
        return []

    values = re.findall(
        r"\b\d+(?:\.\d+)?\b",
        text
    )

    return [float(value) for value in values]


def has_numeric_contradiction(
    claim: str,
    evidence: str
) -> bool:
    """
    Detect a numeric contradiction only when both texts
    contain factual numeric values that conflict.
    """

    claim_numbers = extract_numbers(claim)
    evidence_numbers = extract_numbers(evidence)

    if not claim_numbers or not evidence_numbers:
        return False

    # A contradiction is considered only when the evidence
    # contains a directly relevant numeric value.
    for claim_number in claim_numbers:
        for evidence_number in evidence_numbers:

            if claim_number == evidence_number:
                continue

            # Avoid treating unrelated numbers in a long
            # evidence chunk as contradictions.
            number_context_claim = claim.lower()
            number_context_evidence = evidence.lower()

            similarity = calculate_similarity(
                number_context_claim,
                number_context_evidence
            )

            if similarity >= 0.70:
                return True

    return False


def evaluate_against_reference(
    claim: str,
    reference_answer: str
) -> Dict:
    """
    Evaluate a claim against the supplied reference answer.

    Reference answer has priority over retrieved RAG evidence
    when it is explicitly provided.
    """

    similarity = calculate_similarity(
        claim,
        reference_answer
    )

    numeric_contradiction = has_numeric_contradiction(
        claim,
        reference_answer
    )

    # Strong semantic match with conflicting numeric value
    if numeric_contradiction and similarity >= 0.55:

        return {
            "status": "contradictory",
            "similarity": round(similarity, 3),
            "reasoning": (
                "The claim is related to the reference answer "
                "but contains a conflicting factual value."
            ),
            "evidence": reference_answer
        }

    # Strong match with reference
    if similarity >= 0.60:

        return {
            "status": "supported",
            "similarity": round(similarity, 3),
            "reasoning": (
                "The claim is strongly supported by the "
                "provided reference answer."
            ),
            "evidence": reference_answer
        }

    return {
        "status": "unsupported",
        "similarity": round(similarity, 3),
        "reasoning": (
            "The claim does not have sufficient support "
            "from the provided reference answer."
        ),
        "evidence": reference_answer
    }


def evaluate_hallucination(
    ai_response: str,
    evidence: List[Dict],
    reference_answer: Optional[str] = None
) -> Dict:
    """
    Evaluate individual claims in an AI response.

    Priority:
        1. Reference answer, when provided
        2. Retrieved RAG evidence, when no reference answer exists

    Each claim is classified as:

        supported
        unsupported
        contradictory
    """

    ai_response = ai_response.strip()

    if not ai_response:
        raise ValueError("AI response cannot be empty.")

    claims = split_into_claims(ai_response)

    if not claims:
        return {
            "hallucination_detected": True,
            "status": "Unable to Verify",
            "reasoning": "No claims were found in the AI response.",
            "claims": [],
            "unsupported_claims": [],
            "contradictory_claims": []
        }

    results = []

    # =========================================================
    # CASE 1: REFERENCE ANSWER AVAILABLE
    # =========================================================

    if reference_answer and reference_answer.strip():

        reference_answer = reference_answer.strip()

        for claim in claims:

            result = evaluate_against_reference(
                claim,
                reference_answer
            )

            results.append({
                "claim": claim,
                "status": result["status"],
                "similarity": result["similarity"],
                "reasoning": result["reasoning"],
                "evidence": result["evidence"],
                "source": "reference_answer"
            })

    # =========================================================
    # CASE 2: NO REFERENCE ANSWER → USE RAG EVIDENCE
    # =========================================================

    else:

        if not evidence:
            return {
                "hallucination_detected": True,
                "status": "Unable to Verify",
                "reasoning": (
                    "No reference answer or retrieved evidence "
                    "was provided to verify the claims."
                ),
                "claims": [],
                "unsupported_claims": [],
                "contradictory_claims": []
            }

        for claim in claims:

            best_evidence = None
            best_similarity = 0.0

            # Compare claim with every retrieved evidence chunk
            for item in evidence:

                evidence_text = item.get("text", "")

                if not evidence_text:
                    continue

                similarity = calculate_similarity(
                    claim,
                    evidence_text
                )

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_evidence = item

            # No usable evidence
            if best_evidence is None:

                results.append({
                    "claim": claim,
                    "status": "unsupported",
                    "similarity": 0.0,
                    "reasoning": (
                        "No suitable evidence was found to support "
                        "this claim."
                    ),
                    "evidence": None,
                    "source": "rag_evidence"
                })

                continue

            evidence_text = best_evidence.get("text", "")

            numeric_contradiction = has_numeric_contradiction(
                claim,
                evidence_text
            )

            if (
                numeric_contradiction
                and best_similarity >= 0.55
            ):

                status = "contradictory"

                reasoning = (
                    "The claim is related to the retrieved evidence "
                    "but contains a conflicting factual value."
                )

            elif best_similarity >= 0.60:

                status = "supported"

                reasoning = (
                    "The claim is strongly supported by the "
                    "retrieved evidence."
                )

            else:

                status = "unsupported"

                reasoning = (
                    "The claim does not have sufficient support "
                    "in the retrieved evidence."
                )

            results.append({
                "claim": claim,
                "status": status,
                "similarity": round(best_similarity, 3),
                "reasoning": reasoning,
                "evidence": evidence_text,
                "source": "rag_evidence"
            })

    # =========================================================
    # FINAL CLASSIFICATION
    # =========================================================

    unsupported_claims = [
        item
        for item in results
        if item["status"] == "unsupported"
    ]

    contradictory_claims = [
        item
        for item in results
        if item["status"] == "contradictory"
    ]

    hallucination_detected = (
        len(unsupported_claims) > 0
        or len(contradictory_claims) > 0
    )

    if contradictory_claims:

        status = "Hallucination Detected"

        reasoning = (
            "One or more claims contradict the available "
            "reference information."
        )

    elif unsupported_claims:

        status = "Hallucination Detected"

        reasoning = (
            "One or more claims are not sufficiently supported "
            "by the available reference information."
        )

    else:

        status = "No Hallucination Detected"

        reasoning = (
            "All evaluated claims have sufficient support "
            "from the available reference information."
        )

    return {
        "hallucination_detected": hallucination_detected,
        "status": status,
        "reasoning": reasoning,
        "claims": results,
        "unsupported_claims": unsupported_claims,
        "contradictory_claims": contradictory_claims
    }