from backend.app.database import save_evaluation
from backend.app.models.evaluation import EvaluationInput
from knowledge_base.retrieval.retrieve import retrieve
from backend.app.services.validation_service import validate_response
from evaluation.orchestrator import evaluate_response
from agents.verdict.verdict_agent import evaluate_verdict


def process_evaluation(
    data: EvaluationInput
) -> dict:

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

    validation = validate_response(
        question=data.question,
        ai_response=data.ai_response,
        reference_answer=data.reference_answer,
        evidence=evidence
    )

    agent_results = evaluate_response(
        question=data.question,
        ai_response=data.ai_response,
        reference_answer=data.reference_answer,
        evidence=evidence
    )

    validation["relevance"] = agent_results["relevance"]
    validation["accuracy"] = agent_results["accuracy"]
    validation["hallucination"] = agent_results["hallucination"]
    validation["completeness"] = agent_results["completeness"]

    verdict_result = evaluate_verdict(
        relevance=agent_results["relevance"],
        accuracy=agent_results["accuracy"],
        hallucination=agent_results["hallucination"],
        completeness=agent_results["completeness"]
    )

    validation["verdict"] = verdict_result["verdict"]
    validation["final_score"] = verdict_result["final_score"]
    validation["weighted_score"] = verdict_result["weighted_score"]
    validation["dimension_scores"] = verdict_result["dimension_scores"]
    validation["weights"] = verdict_result["weights"]
    validation["verdict_reasoning"] = verdict_result["reasoning"]

    submission_id = save_evaluation(
        question=data.question,
        ai_response=data.ai_response,
        reference_answer=data.reference_answer,
        source_document=data.source_document,
        validation=validation
    )

    return {
        "status": "received",
        "message": "Evaluation input stored successfully.",
        "submission_id": submission_id,
        "question": data.question,
        "ai_response": data.ai_response,
        "reference_answer": data.reference_answer,
        "source_document": data.source_document,
        "retrieved_evidence": evidence,
        "validation": validation,
        "verdict": verdict_result
    }