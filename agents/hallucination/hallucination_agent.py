from typing import Dict, List
import re
import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

_model = SentenceTransformer(MODEL_NAME)


def split_into_claims(response: str) -> List[str]:
    """
    Split an AI response into individual claims/sentences.
    """
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
    Detect conflicting numeric values between a claim
    and supporting evidence.
    """

    claim_numbers = extract_numbers(claim)
    evidence_numbers = extract_numbers(evidence)

    if not claim_numbers or not evidence_numbers:
        return False

    for claim_number in claim_numbers:
        for evidence_number in evidence_numbers:
            if claim_number != evidence_number:
                return True

    return False


def evaluate_hallucination(
    ai_response: str,
    evidence: List[Dict]
) -> Dict:
    """
    Evaluate individual claims in an AI response against
    retrieved reference evidence.

    Each claim is classified as:

        supported
        unsupported
        contradictory
    """

    ai_response = ai_response.strip()

    if not ai_response:
        raise ValueError("AI response cannot be empty.")

    if not evidence:
        return {
            "hallucination_detected": True,
            "status": "Unable to Verify",
            "reasoning": (
                "No retrieved evidence was provided to verify "
                "the claims in the AI response."
            ),
            "claims": []
        }

    claims = split_into_claims(ai_response)

    results = []

    for claim in claims:

        best_evidence = None
        best_similarity = 0.0

        # Compare the claim with every retrieved evidence chunk
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

        if best_evidence is None:

            results.append({
                "claim": claim,
                "status": "unsupported",
                "similarity": 0.0,
                "reasoning": (
                    "No suitable evidence was found to support "
                    "this claim."
                ),
                "evidence": None
            })

            continue

        evidence_text = best_evidence.get("text", "")

        numeric_contradiction = has_numeric_contradiction(
            claim,
            evidence_text
        )

        # Strong semantic connection + conflicting value
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
            "evidence": evidence_text
        })

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
            "reference evidence."
        )

    elif unsupported_claims:

        status = "Hallucination Detected"

        reasoning = (
            "One or more claims are not sufficiently supported "
            "by the available reference evidence."
        )

    else:

        status = "No Hallucination Detected"

        reasoning = (
            "All evaluated claims have sufficient support "
            "from the retrieved evidence."
        )

    return {
        "hallucination_detected": hallucination_detected,
        "status": status,
        "reasoning": reasoning,
        "claims": results,
        "unsupported_claims": unsupported_claims,
        "contradictory_claims": contradictory_claims
    }