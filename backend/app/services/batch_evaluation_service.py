import csv
import io
from typing import Any

from backend.app.models.evaluation import EvaluationInput
from backend.app.services.evaluation_service import process_evaluation


REQUIRED_COLUMNS = {"question", "ai_response"}


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = {}

    for key, value in row.items():
        if key is None:
            continue

        normalized[key.strip().lower()] = (
            value.strip() if isinstance(value, str) else value
        )

    return normalized


def _validate_row(row: dict[str, Any], row_number: int) -> list[str]:
    errors = []

    for column in REQUIRED_COLUMNS:
        if column not in row:
            errors.append(f"Missing required field: {column}")
        elif not str(row[column]).strip():
            errors.append(f"Empty required field: {column}")

    if errors:
        return [
            f"Row {row_number}: {error}"
            for error in errors
        ]

    return []


def evaluate_batch_csv(csv_content: str) -> dict[str, Any]:
    results = []
    errors = []

    try:
        reader = csv.DictReader(io.StringIO(csv_content))

        if not reader.fieldnames:
            return {
                "status": "failed",
                "message": "CSV file is empty or has no header row.",
                "total_records": 0,
                "successful_records": 0,
                "failed_records": 0,
                "results": [],
                "errors": []
            }

        columns = {
            column.strip().lower()
            for column in reader.fieldnames
            if column
        }

        missing_columns = REQUIRED_COLUMNS - columns

        if missing_columns:
            return {
                "status": "failed",
                "message": (
                    "CSV is missing required columns: "
                    + ", ".join(sorted(missing_columns))
                ),
                "total_records": 0,
                "successful_records": 0,
                "failed_records": 0,
                "results": [],
                "errors": []
            }

        rows = list(reader)
        total_records = len(rows)

        for index, raw_row in enumerate(rows, start=2):
            row = _normalize_row(raw_row)

            row_errors = _validate_row(row, index)

            if row_errors:
                errors.extend(row_errors)

                results.append({
                    "row_number": index,
                    "status": "failed",
                    "errors": row_errors
                })

                continue

            try:
                evaluation_input = EvaluationInput(
                    question=row["question"],
                    ai_response=row["ai_response"],
                    reference_answer=row.get("reference_answer") or None,
                    source_document=row.get("source_document") or None
                )

                evaluation = process_evaluation(evaluation_input)

                validation = evaluation.get("validation", {})
                verdict = evaluation.get("verdict", {})

                results.append({
                    "row_number": index,
                    "status": "success",
                    "question": row["question"],
                    "ai_response": row["ai_response"],
                    "submission_id": evaluation.get("submission_id"),
                    "relevance_score": validation.get(
                        "relevance", {}
                    ).get("score"),
                    "accuracy_score": validation.get(
                        "accuracy", {}
                    ).get("score"),
                    "hallucination": validation.get(
                        "hallucination", {}
                    ).get("hallucination_detected"),
                    "completeness_score": validation.get(
                        "completeness", {}
                    ).get("score"),
                    "overall_score": verdict.get("final_score"),
                    "verdict": verdict.get("verdict"),
                    "reasoning": verdict.get("reasoning"),
                    "evidence": validation.get(
                        "accuracy", {}
                    ).get("supporting_evidence", []),
                    "hallucinated_claims": validation.get(
                        "hallucination", {}
                    ).get("unsupported_claims", []),
                    "missing_aspects": validation.get(
                        "completeness", {}
                    ).get("missing_aspects", [])
                })

            except Exception as exc:
                error_message = (
                    f"Row {index}: Evaluation failed - {str(exc)}"
                )

                errors.append(error_message)

                results.append({
                    "row_number": index,
                    "status": "failed",
                    "question": row.get("question"),
                    "ai_response": row.get("ai_response"),
                    "errors": [error_message]
                })

    except Exception as exc:
        return {
            "status": "failed",
            "message": f"Unable to process CSV: {str(exc)}",
            "total_records": 0,
            "successful_records": 0,
            "failed_records": 0,
            "results": [],
            "errors": [str(exc)]
        }

    successful_records = sum(
        1 for result in results
        if result.get("status") == "success"
    )

    failed_records = sum(
        1 for result in results
        if result.get("status") == "failed"
    )

    successful_results = [
        result
        for result in results
        if result.get("status") == "success"
    ]

    scores = [
        result["overall_score"]
        for result in successful_results
        if isinstance(result.get("overall_score"), (int, float))
    ]

    verdict_counts = {}

    for result in successful_results:
        verdict = result.get("verdict")

        if verdict:
            verdict_counts[verdict] = (
                verdict_counts.get(verdict, 0) + 1
            )

    hallucination_count = sum(
        1
        for result in successful_results
        if result.get("hallucination") is True
    )

    average_score = (
        sum(scores) / len(scores)
        if scores
        else 0.0
    )

    if failed_records == 0:
        status = "completed"
    elif successful_records > 0:
        status = "completed_with_errors"
    else:
        status = "failed"

    return {
        "status": status,
        "message": "Batch evaluation completed.",
        "total_records": total_records,
        "successful_records": successful_records,
        "failed_records": failed_records,
        "average_score": round(average_score, 2),
        "verdict_counts": verdict_counts,
        "hallucination_count": hallucination_count,
        "results": results,
        "errors": errors
    }