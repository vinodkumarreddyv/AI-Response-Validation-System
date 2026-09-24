import re
from typing import Any, Dict, List, Optional


# ============================================================
# Text Processing Helpers
# ============================================================

def _clean_text(text: Any) -> str:
    """
    Convert any value into clean text.
    """
    if text is None:
        return ""

    return str(text).strip()


def _split_into_claims(text: str) -> List[str]:
    """
    Split a response into simple claims or sentences.
    """
    text = _clean_text(text)

    if not text:
        return []

    claims = re.split(r"[.!?;\n]+", text)

    return [
        claim.strip()
        for claim in claims
        if claim.strip()
    ]


def _normalize_words(text: str) -> set:
    """
    Extract normalized words for basic keyword comparison.
    """
    text = _clean_text(text).lower()

    words = re.findall(r"\b[a-zA-Z0-9]+\b", text)

    return set(words)


def _keyword_coverage(
    response: str,
    reference: str
) -> float:
    """
    Calculate how many meaningful reference words
    are covered by the AI response.
    """
    response_words = _normalize_words(response)
    reference_words = _normalize_words(reference)

    if not reference_words:
        return 0.0

    stop_words = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "to",
        "of",
        "in",
        "on",
        "and",
        "or",
        "for",
        "with",
        "that",
        "this",
        "it",
        "as",
        "by",
        "from",
        "does",
        "do",
        "why",
        "what",
        "how",
        "when",
        "where",
        "who"
    }

    meaningful_reference_words = {
        word
        for word in reference_words
        if word not in stop_words and len(word) > 2
    }

    if not meaningful_reference_words:
        return 0.0

    covered_words = (
        meaningful_reference_words.intersection(response_words)
    )

    return len(covered_words) / len(meaningful_reference_words)


# ============================================================
# Requirement Extraction
# ============================================================

def _extract_requirements(question: str) -> List[str]:
    """
    Identify the main requirement from the question.
    """
    question = _clean_text(question).lower()

    if not question:
        return ["Provide a meaningful answer"]

    if question.startswith("why") or " why " in question:
        return ["Explain the reason or cause"]

    if question.startswith("how") or " how " in question:
        return ["Explain the process or method"]

    if question.startswith("what") or " what " in question:
        return ["Provide the requested definition or explanation"]

    if question.startswith("when") or " when " in question:
        return ["Provide the relevant time or condition"]

    if question.startswith("where") or " where " in question:
        return ["Provide the relevant location"]

    if question.startswith("who") or " who " in question:
        return ["Identify the relevant person or entity"]

    return ["Provide a direct and relevant answer"]


# ============================================================
# Requirement Assessment
# ============================================================

def _assess_aspects(
    requirements: List[str],
    response: str,
    reference_answer: Optional[str],
    evidence: List[Dict[str, Any]]
) -> Dict[str, List[str]]:
    """
    Determine which requirements are addressed by the response.

    This uses the response content rather than relying only
    on the relevance score of the retrieved evidence.
    """
    response_text = _clean_text(response).lower()

    addressed_aspects: List[str] = []
    missing_aspects: List[str] = []

    reference_text = _clean_text(reference_answer).lower()

    evidence_text = " ".join(
        _clean_text(item.get("text", item.get("chunk", "")))
        for item in evidence
        if isinstance(item, dict)
    ).lower()

    combined_source_text = f"{reference_text} {evidence_text}"

    for requirement in requirements:
        requirement_lower = requirement.lower()

        if "reason or cause" in requirement_lower:
            cause_words = {
                "because",
                "due",
                "since",
                "therefore",
                "reason",
                "causes",
                "caused",
                "density",
                "less dense",
                "more dense",
                "explain"
            }

            contains_cause_indicator = any(
                word in response_text
                for word in cause_words
            )

            response_word_count = len(
                _normalize_words(response_text)
            )

            if contains_cause_indicator and response_word_count >= 5:
                addressed_aspects.append(requirement)
            else:
                missing_aspects.append(requirement)

        elif "process or method" in requirement_lower:
            process_words = {
                "first",
                "then",
                "next",
                "finally",
                "process",
                "step",
                "through",
                "by",
                "using",
                "formed",
                "changes"
            }

            contains_process_indicator = any(
                word in response_text
                for word in process_words
            )

            if contains_process_indicator:
                addressed_aspects.append(requirement)
            else:
                missing_aspects.append(requirement)

        elif "definition or explanation" in requirement_lower:
            response_word_count = len(
                _normalize_words(response_text)
            )

            if response_word_count >= 5:
                addressed_aspects.append(requirement)
            else:
                missing_aspects.append(requirement)

        elif "time or condition" in requirement_lower:
            if any(
                word in response_text
                for word in [
                    "when",
                    "during",
                    "at",
                    "before",
                    "after",
                    "temperature",
                    "condition"
                ]
            ):
                addressed_aspects.append(requirement)
            else:
                missing_aspects.append(requirement)

        elif "location" in requirement_lower:
            if response_word_count_if_valid(response_text) >= 2:
                addressed_aspects.append(requirement)
            else:
                missing_aspects.append(requirement)

        elif "person or entity" in requirement_lower:
            if response_word_count_if_valid(response_text) >= 2:
                addressed_aspects.append(requirement)
            else:
                missing_aspects.append(requirement)

        else:
            if response_word_count_if_valid(response_text) >= 3:
                addressed_aspects.append(requirement)
            else:
                missing_aspects.append(requirement)

    return {
        "addressed_aspects": addressed_aspects,
        "missing_aspects": missing_aspects
    }


def response_word_count_if_valid(text: str) -> int:
    """
    Return the number of normalized words in a response.
    """
    return len(_normalize_words(text))


# ============================================================
# Evidence Helpers
# ============================================================

def _get_evidence_text(item: Dict[str, Any]) -> str:
    """
    Extract evidence text from different supported formats.
    """
    text = item.get("text", item.get("chunk", ""))

    if isinstance(text, dict):
        text = text.get("text", "")

    return _clean_text(text)


def _get_evidence_score(item: Dict[str, Any]) -> float:
    """
    Read the strongest available evidence score.
    """
    score_fields = [
        "relevance_score",
        "semantic_similarity",
        "similarity",
        "combined_score"
    ]

    scores: List[float] = []

    for field in score_fields:
        value = item.get(field)

        try:
            if value is not None:
                scores.append(float(value))
        except (TypeError, ValueError):
            continue

    if not scores:
        return 0.0

    return max(scores)


def _best_evidence_score(
    evidence: Optional[List[Dict[str, Any]]]
) -> float:
    """
    Get the highest evidence score.
    """
    if not evidence:
        return 0.0

    scores = [
        _get_evidence_score(item)
        for item in evidence
        if isinstance(item, dict)
    ]

    if not scores:
        return 0.0

    return max(scores)


def _evidence_coverage(
    response: str,
    evidence: Optional[List[Dict[str, Any]]]
) -> float:
    """
    Estimate how much of the retrieved evidence is reflected
    in the AI response.
    """
    if not evidence:
        return 0.0

    response_words = _normalize_words(response)

    if not response_words:
        return 0.0

    best_coverage = 0.0

    for item in evidence:
        if not isinstance(item, dict):
            continue

        evidence_text = _get_evidence_text(item)

        if not evidence_text:
            continue

        coverage = _keyword_coverage(
            response,
            evidence_text
        )

        best_coverage = max(
            best_coverage,
            coverage
        )

    return best_coverage


# ============================================================
# Score and Label Helpers
# ============================================================

def _score_from_coverage(coverage: float) -> int:
    """
    Convert coverage into a score from 1 to 5.
    """
    coverage = max(0.0, min(1.0, coverage))

    if coverage >= 0.85:
        return 5

    if coverage >= 0.65:
        return 4

    if coverage >= 0.40:
        return 3

    if coverage >= 0.20:
        return 2

    return 1


def _label_from_score(score: int) -> str:
    """
    Convert a numeric score into a completeness label.
    """
    labels = {
        5: "Complete",
        4: "Mostly Complete",
        3: "Partially Complete",
        2: "Mostly Incomplete",
        1: "Incomplete"
    }

    return labels.get(score, "Incomplete")


def _build_result(
    coverage: float,
    requirements: List[str],
    addressed_aspects: List[str],
    missing_aspects: List[str],
    reasoning: str,
    evidence_score: Optional[float] = None
) -> Dict[str, Any]:
    """
    Build a consistent completeness result.
    """
    score = _score_from_coverage(coverage)

    result: Dict[str, Any] = {
        "score": score,
        "label": _label_from_score(score),
        "coverage": round(coverage, 4),
        "requirements": requirements,
        "addressed_aspects": addressed_aspects,
        "missing_aspects": missing_aspects,
        "reasoning": reasoning
    }

    if evidence_score is not None:
        result["evidence_score"] = round(
            max(0.0, min(1.0, evidence_score)),
            4
        )

    return result


# ============================================================
# Main Completeness Judge Agent
# ============================================================

def evaluate_completeness(
    question: str,
    ai_response: str,
    reference_answer: Optional[str] = None,
    evidence: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Evaluate how completely the AI response answers the question.

    Parameters:
        question:
            Original user question.

        ai_response:
            AI-generated response being evaluated.

        reference_answer:
            Optional trusted reference answer.

        evidence:
            Optional retrieved evidence records.

    Returns:
        A structured completeness evaluation containing:
            - score
            - label
            - coverage
            - requirements
            - addressed_aspects
            - missing_aspects
            - reasoning
            - evidence_score when evidence is available
    """
    question = _clean_text(question)
    ai_response = _clean_text(ai_response)
    reference_answer = _clean_text(reference_answer)

    evidence = evidence or []

    requirements = _extract_requirements(question)

    # --------------------------------------------------------
    # Empty response
    # --------------------------------------------------------

    if not ai_response:
        return _build_result(
            coverage=0.0,
            requirements=requirements,
            addressed_aspects=[],
            missing_aspects=requirements,
            reasoning=(
                "The AI response was empty, so none of the "
                "question requirements were addressed."
            ),
            evidence_score=(
                _best_evidence_score(evidence)
                if evidence
                else None
            )
        )

    # --------------------------------------------------------
    # Assess the actual response content
    # --------------------------------------------------------

    aspect_result = _assess_aspects(
        requirements=requirements,
        response=ai_response,
        reference_answer=reference_answer or None,
        evidence=evidence
    )

    addressed_aspects = aspect_result["addressed_aspects"]
    missing_aspects = aspect_result["missing_aspects"]

    # --------------------------------------------------------
    # Reference-based completeness
    # --------------------------------------------------------

    reference_coverage = None

    if reference_answer:
        reference_coverage = _keyword_coverage(
            ai_response,
            reference_answer
        )

    # --------------------------------------------------------
    # Evidence-based completeness
    # --------------------------------------------------------

    best_evidence_score = _best_evidence_score(evidence)

    evidence_coverage = _evidence_coverage(
        ai_response,
        evidence
    )

    # --------------------------------------------------------
    # Requirement-based coverage
    # --------------------------------------------------------

    if requirements:
        requirement_coverage = (
            len(addressed_aspects) / len(requirements)
        )
    else:
        requirement_coverage = 0.0

    # --------------------------------------------------------
    # Final completeness calculation
    # --------------------------------------------------------

    coverage_candidates: List[float] = [
        requirement_coverage
    ]

    if reference_coverage is not None:
        coverage_candidates.append(reference_coverage)

    if evidence:
        coverage_candidates.append(evidence_coverage)

    # The response content and addressed requirements have
    # priority over evidence relevance.
    #
    # Evidence quality contributes only 15%.
    # Actual content coverage contributes 85%.
    content_coverage = max(
        requirement_coverage,
        reference_coverage or 0.0,
        evidence_coverage
    )

    if evidence:
        combined_coverage = (
            0.85 * content_coverage
            + 0.15 * best_evidence_score
        )
    else:
        combined_coverage = content_coverage

    # If the response clearly misses a required aspect,
    # prevent the result from being marked Complete.
    if missing_aspects:
        combined_coverage = min(
            combined_coverage,
            0.64
        )

    # A very short answer to a "why" question should not be
    # marked complete unless it contains an explanation.
    if (
        "Explain the reason or cause" in requirements
        and len(_normalize_words(ai_response)) < 5
    ):
        combined_coverage = min(
            combined_coverage,
            0.39
        )

    # --------------------------------------------------------
    # Reasoning
    # --------------------------------------------------------

    if missing_aspects:
        reasoning = (
            "The response addressed some information, but it "
            "did not fully satisfy the required aspect(s): "
            + ", ".join(missing_aspects)
            + "."
        )
    elif evidence:
        reasoning = (
            "The response addressed the identified question "
            "requirements. The strongest evidence relevance "
            f"was {best_evidence_score:.0%}."
        )
    elif reference_answer:
        reasoning = (
            "The response was compared with the supplied "
            "reference answer and the identified question "
            "requirements."
        )
    else:
        reasoning = (
            "The response was evaluated using the identified "
            "question requirements and available response content."
        )

    return _build_result(
        coverage=combined_coverage,
        requirements=requirements,
        addressed_aspects=addressed_aspects,
        missing_aspects=missing_aspects,
        reasoning=reasoning,
        evidence_score=(
            best_evidence_score
            if evidence
            else None
        )
    )


# ============================================================
# Manual Test
# ============================================================

if __name__ == "__main__":
    test_result = evaluate_completeness(
        question="Why does ice float on water?",
        ai_response="Ice floats on water.",
        evidence=[
            {
                "text": (
                    "Ice floats on water because solid ice is "
                    "less dense than liquid water."
                ),
                "relevance_score": 0.9
            }
        ]
    )

    import json

    print(
        json.dumps(
            test_result,
            indent=2
        )
    )