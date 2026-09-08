from agents.relevance.relevance_agent import evaluate_relevance
from agents.accuracy.accuracy_agent import evaluate_accuracy
from agents.hallucination.hallucination_agent import evaluate_hallucination


def evaluate_response(
    question: str,
    ai_response: str,
    reference_answer: str | None = None,
    evidence: list | None = None
) -> dict:
    """
    Evaluation Orchestrator

    Runs the Relevance, Accuracy, and Hallucination
    Detection agents and combines their results.
    """

    evidence = evidence or []

    # ---------------------------------------------------------
    # 1. Relevance Evaluation
    # ---------------------------------------------------------

    relevance_result = evaluate_relevance(
        question=question,
        ai_response=ai_response
    )

    # ---------------------------------------------------------
    # 2. Accuracy Evaluation
    # ---------------------------------------------------------

    accuracy_result = evaluate_accuracy(
        ai_response=ai_response,
        reference_answer=reference_answer,
        evidence=evidence
    )

    # ---------------------------------------------------------
    # 3. Hallucination Evaluation
    # ---------------------------------------------------------

    hallucination_result = evaluate_hallucination(
        ai_response=ai_response,
        evidence=evidence
    )

    # ---------------------------------------------------------
    # Return combined result
    # ---------------------------------------------------------

    return {
        "question": question,
        "ai_response": ai_response,
        "relevance": relevance_result,
        "accuracy": accuracy_result,
        "hallucination": hallucination_result
    }