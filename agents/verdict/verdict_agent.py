from typing import Any, Dict, Optional


# ============================================================
# Helper Functions
# ============================================================

def _safe_float(
    value: Any,
    default: float = 0.0
) -> float:
    """
    Safely convert a value into a float.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp_score(
    score: Any,
    minimum: float = 1.0,
    maximum: float = 5.0
) -> float:
    """
    Keep a score within the expected range.
    """
    score = _safe_float(score, minimum)

    return max(
        minimum,
        min(maximum, score)
    )


def _get_dimension_score(
    result: Optional[Dict[str, Any]],
    default: float = 1.0
) -> float:
    """
    Extract a dimension score from an agent result.
    """
    if not isinstance(result, dict):
        return default

    possible_fields = [
        "score",
        "rating",
        "dimension_score"
    ]

    for field in possible_fields:
        if field in result:
            return _clamp_score(
                result[field],
                minimum=1.0,
                maximum=5.0
            )

    return default


def _get_hallucination_score(
    hallucination_result: Optional[Dict[str, Any]]
) -> float:
    """
    Convert hallucination detection into a score.

    No hallucination:
        5 points

    Hallucination detected:
        1 point
    """
    if not isinstance(hallucination_result, dict):
        return 1.0

    hallucination_detected = hallucination_result.get(
        "hallucination_detected",
        hallucination_result.get(
            "has_hallucination",
            False
        )
    )

    if isinstance(hallucination_detected, str):
        hallucination_detected = (
            hallucination_detected.strip().lower()
            in {
                "true",
                "yes",
                "1",
                "detected"
            }
        )

    if hallucination_detected:
        return 1.0

    return 5.0


def _score_to_percentage(
    score: float
) -> float:
    """
    Convert a score from a 1–5 scale into a percentage.

    1 -> 0%
    2 -> 25%
    3 -> 50%
    4 -> 75%
    5 -> 100%
    """
    score = _clamp_score(
        score,
        minimum=1.0,
        maximum=5.0
    )

    return ((score - 1.0) / 4.0) * 100.0


def _get_verdict(
    final_score: float,
    hallucination_score: float,
    accuracy_score: float,
    completeness_score: float
) -> str:
    """
    Generate the final verdict.

    INCORRECT:
        Serious factual errors or hallucinations.

    PARTIALLY CORRECT:
        Moderate score or incomplete response.

    CORRECT:
        High score and all major dimensions are strong.
    """

    # Serious factual problems or hallucinations
    if (
        hallucination_score <= 1.0
        or accuracy_score <= 2.0
    ):
        return "INCORRECT"

    # A low completeness score means that the response
    # does not fully answer the question.
    if completeness_score <= 3.0:
        return "PARTIALLY CORRECT"

    # A high score is required for a fully correct answer.
    if final_score >= 80.0:
        return "CORRECT"

    if final_score >= 50.0:
        return "PARTIALLY CORRECT"

    return "INCORRECT"


def _build_reasoning(
    relevance_score: float,
    accuracy_score: float,
    hallucination_score: float,
    completeness_score: float,
    final_score: float,
    verdict: str
) -> str:
    """
    Create a readable explanation for the final verdict.
    """
    reasons = []

    if relevance_score >= 4.0:
        reasons.append("the response was relevant")
    elif relevance_score >= 3.0:
        reasons.append("the response was partially relevant")
    else:
        reasons.append("the response had low relevance")

    if accuracy_score >= 4.0:
        reasons.append("the response was factually accurate")
    elif accuracy_score >= 3.0:
        reasons.append("the response had some accuracy limitations")
    else:
        reasons.append("the response had factual accuracy problems")

    if hallucination_score >= 4.0:
        reasons.append("no significant hallucination was detected")
    else:
        reasons.append(
            "hallucinated or unsupported information was detected"
        )

    if completeness_score >= 4.0:
        reasons.append("the response was sufficiently complete")
    elif completeness_score >= 3.0:
        reasons.append("the response was partially complete")
    else:
        reasons.append("the response was incomplete")

    return (
        f"The final verdict is {verdict}. "
        f"The weighted score was {final_score:.2f}%. "
        + "; ".join(reasons)
        + "."
    )


# ============================================================
# Main Verdict Agent
# ============================================================

def evaluate_verdict(
    relevance: Optional[Dict[str, Any]] = None,
    accuracy: Optional[Dict[str, Any]] = None,
    hallucination: Optional[Dict[str, Any]] = None,
    completeness: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Combine the four evaluation dimensions into a final verdict.

    Weight distribution:

        Relevance     = 20%
        Accuracy      = 35%
        Hallucination = 25%
        Completeness  = 20%

    Parameters:
        relevance:
            Result from the Relevance Agent.

        accuracy:
            Result from the Accuracy Agent.

        hallucination:
            Result from the Hallucination Agent.

        completeness:
            Result from the Completeness Agent.

    Returns:
        A structured verdict result.
    """

    # --------------------------------------------------------
    # Extract dimension scores
    # --------------------------------------------------------

    relevance_score = _get_dimension_score(
        relevance,
        default=1.0
    )

    accuracy_score = _get_dimension_score(
        accuracy,
        default=1.0
    )

    hallucination_score = _get_hallucination_score(
        hallucination
    )

    completeness_score = _get_dimension_score(
        completeness,
        default=1.0
    )

    # --------------------------------------------------------
    # Define weights
    # --------------------------------------------------------

    relevance_weight = 0.20
    accuracy_weight = 0.35
    hallucination_weight = 0.25
    completeness_weight = 0.20

    # --------------------------------------------------------
    # Calculate weighted score
    # --------------------------------------------------------

    weighted_score = (
        (relevance_score * relevance_weight)
        + (accuracy_score * accuracy_weight)
        + (hallucination_score * hallucination_weight)
        + (completeness_score * completeness_weight)
    )

    final_score = _score_to_percentage(
        weighted_score
    )

    # --------------------------------------------------------
    # Generate final verdict
    # --------------------------------------------------------

    verdict = _get_verdict(
        final_score=final_score,
        hallucination_score=hallucination_score,
        accuracy_score=accuracy_score,
        completeness_score=completeness_score
    )

    # --------------------------------------------------------
    # Build reasoning
    # --------------------------------------------------------

    reasoning = _build_reasoning(
        relevance_score=relevance_score,
        accuracy_score=accuracy_score,
        hallucination_score=hallucination_score,
        completeness_score=completeness_score,
        final_score=final_score,
        verdict=verdict
    )

    # --------------------------------------------------------
    # Return structured result
    # --------------------------------------------------------

    return {
        "verdict": verdict,
        "final_score": round(final_score, 2),
        "weighted_score": round(weighted_score, 4),
        "dimension_scores": {
            "relevance": round(relevance_score, 2),
            "accuracy": round(accuracy_score, 2),
            "hallucination": round(hallucination_score, 2),
            "completeness": round(completeness_score, 2)
        },
        "weights": {
            "relevance": relevance_weight,
            "accuracy": accuracy_weight,
            "hallucination": hallucination_weight,
            "completeness": completeness_weight
        },
        "reasoning": reasoning
    }


# ============================================================
# Backward-Compatible Alias
# ============================================================

def generate_verdict(
    relevance: Optional[Dict[str, Any]] = None,
    accuracy: Optional[Dict[str, Any]] = None,
    hallucination: Optional[Dict[str, Any]] = None,
    completeness: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Backward-compatible function name.
    """
    return evaluate_verdict(
        relevance=relevance,
        accuracy=accuracy,
        hallucination=hallucination,
        completeness=completeness
    )


# ============================================================
# Manual Test
# ============================================================

if __name__ == "__main__":
    import json

    test_result = evaluate_verdict(
        relevance={
            "score": 5,
            "label": "Fully Relevant"
        },
        accuracy={
            "score": 5,
            "label": "Correct"
        },
        hallucination={
            "hallucination_detected": False,
            "label": "No Hallucination Detected"
        },
        completeness={
            "score": 5,
            "label": "Complete"
        }
    )

    print(
        json.dumps(
            test_result,
            indent=2
        )
    )