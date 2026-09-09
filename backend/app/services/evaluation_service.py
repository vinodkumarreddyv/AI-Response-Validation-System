from backend.app.database import save_evaluation
from backend.app.models.evaluation import EvaluationInput
from knowledge_base.retrieval.retrieve import retrieve
from backend.app.services.validation_service import validate_response

from evaluation.orchestrator import evaluate_response


def process_evaluation(
    data: EvaluationInput
) -> dict:

    # ---------------------------------------------------------
    # 1. Retrieve supporting evidence
    # ---------------------------------------------------------

    retrieved = retrieve(
        data.question,
        top_k=5
    )

    evidence = []

    for result in retrieved:

        chunk = result.get("chunk", "")

        if isinstance(chunk, dict):
            text = chunk.get("text", "")
        else:
            text = str(chunk)

        evidence.append({
            "text": text,
            "distance": result.get("distance", 0.0),
            "index": result.get("index", -1),
            "semantic_similarity": result.get(
                "semantic_similarity", 0.0
            ),
            "keyword_overlap": result.get(
                "keyword_overlap", 0.0
            ),
            "phrase_score": result.get(
                "phrase_score", 0.0
            ),
            "direct_fact_score": result.get(
                "direct_fact_score", 0.0
            ),
            "relevance_score": result.get(
                "relevance_score", 0.0
            ),
            "exact_match": result.get(
                "exact_match", False
            )
        })

    # ---------------------------------------------------------
    # 2. Existing validation / overall scoring
    # ---------------------------------------------------------

    validation = validate_response(
        question=data.question,
        ai_response=data.ai_response,
        reference_answer=data.reference_answer,
        evidence=evidence
    )

    # ---------------------------------------------------------
    # 3. Run M2 Evaluation Orchestrator
    # ---------------------------------------------------------

    agent_results = evaluate_response(
        question=data.question,
        ai_response=data.ai_response,
        reference_answer=data.reference_answer,
        evidence=evidence
    )

    # ---------------------------------------------------------
    # 4. Attach agent results to validation result
    # ---------------------------------------------------------

    validation["relevance"] = agent_results["relevance"]

    validation["accuracy"] = agent_results["accuracy"]

    validation["hallucination"] = agent_results["hallucination"]

    validation["completeness"] = agent_results["completeness"]

    # ---------------------------------------------------------
    # 5. Save evaluation
    # ---------------------------------------------------------

    submission_id = save_evaluation(
        question=data.question,
        ai_response=data.ai_response,
        reference_answer=data.reference_answer,
        source_document=data.source_document,
        validation=validation
    )

    # ---------------------------------------------------------
    # 6. Return complete result
    # ---------------------------------------------------------

    return {
        "status": "received",
        "message": "Evaluation input stored successfully.",
        "submission_id": submission_id,
        "question": data.question,
        "ai_response": data.ai_response,
        "reference_answer": data.reference_answer,
        "source_document": data.source_document,
        "retrieved_evidence": evidence,
        "validation": validation
    }