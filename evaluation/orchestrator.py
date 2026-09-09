from agents.relevance.relevance_agent import evaluate_relevance
from agents.accuracy.accuracy_agent import evaluate_accuracy
from agents.hallucination.hallucination_agent import evaluate_hallucination
from agents.completeness.completeness_agent import evaluate_completeness


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_evidence(evidence):
    """
    Normalize evidence so every agent receives
    a consistent evidence structure.
    """

    if not evidence:
        return []

    normalized = []

    for item in evidence:

        if not isinstance(item, dict):
            continue

        text = item.get("text", item.get("chunk", ""))

        if isinstance(text, dict):
            text = text.get("text", "")

        text = str(text)

        semantic_similarity = _safe_float(
            item.get(
                "semantic_similarity",
                item.get("similarity", 0.0)
            )
        )

        relevance_score = _safe_float(
            item.get(
                "relevance_score",
                item.get(
                    "combined_score",
                    semantic_similarity
                )
            )
        )

        normalized.append({
            "text": text,
            "semantic_similarity": semantic_similarity,
            "relevance_score": relevance_score,
            "keyword_overlap": _safe_float(
                item.get("keyword_overlap", 0.0)
            ),
            "phrase_score": _safe_float(
                item.get("phrase_score", 0.0)
            ),
            "direct_fact_score": _safe_float(
                item.get("direct_fact_score", 0.0)
            ),
            "exact_match": item.get(
                "exact_match",
                False
            ),
            "distance": _safe_float(
                item.get("distance", 0.0)
            ),
            "index": item.get(
                "index",
                -1
            )
        })

    return normalized


def _enrich_evidence_from_accuracy(
    evidence,
    accuracy_result
):
    """
    If the supplied evidence only contains text,
    use the similarity calculated by the Accuracy Agent
    to provide a useful evidence score to Completeness.
    """

    if not evidence:
        return evidence

    supporting = accuracy_result.get(
        "supporting_evidence",
        []
    )

    if not supporting:
        return evidence

    for item in evidence:

        text = item.get("text", "").strip()

        if not text:
            continue

        best_similarity = 0.0

        for support in supporting:

            support_text = str(
                support.get("text", "")
            ).strip()

            similarity = _safe_float(
                support.get("similarity", 0.0)
            )

            # Match the evidence text approximately.
            if (
                text == support_text
                or text in support_text
                or support_text in text
            ):
                best_similarity = max(
                    best_similarity,
                    similarity
                )

        if best_similarity > 0:

            item["semantic_similarity"] = best_similarity

            if item.get("relevance_score", 0.0) == 0.0:
                item["relevance_score"] = best_similarity

    return evidence


def evaluate_response(
    question: str,
    ai_response: str,
    reference_answer: str | None = None,
    evidence: list | None = None
) -> dict:
    """
    Evaluation Orchestrator

    Runs:

    1. Relevance Judge
    2. Accuracy Judge
    3. Hallucination Detection Agent
    4. Completeness Judge

    The agents use the same normalized evidence.
    """

    # =========================================================
    # PREPARE EVIDENCE
    # =========================================================

    evidence = _normalize_evidence(evidence)

    # =========================================================
    # 1. RELEVANCE
    # =========================================================

    relevance_result = evaluate_relevance(
        question=question,
        ai_response=ai_response
    )

    # =========================================================
    # 2. ACCURACY
    # =========================================================

    accuracy_result = evaluate_accuracy(
        ai_response=ai_response,
        reference_answer=reference_answer,
        evidence=evidence
    )

    # =========================================================
    # ENRICH EVIDENCE
    # =========================================================

    evidence = _enrich_evidence_from_accuracy(
        evidence,
        accuracy_result
    )

    # =========================================================
    # 3. HALLUCINATION
    # =========================================================

    hallucination_result = evaluate_hallucination(
        ai_response=ai_response,
        evidence=evidence
    )

    # =========================================================
    # 4. COMPLETENESS
    # =========================================================

    completeness_result = evaluate_completeness(
        question=question,
        ai_response=ai_response,
        reference_answer=reference_answer,
        evidence=evidence
    )

    # =========================================================
    # FINAL COMBINED RESULT
    # =========================================================

    return {
        "question": question,
        "ai_response": ai_response,

        "relevance": relevance_result,

        "accuracy": accuracy_result,

        "hallucination": hallucination_result,

        "completeness": completeness_result,

        "evidence": evidence
    }