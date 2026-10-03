import json
from collections import Counter

from backend.app.database import get_connection as database_get_connection


def get_connection():
    return database_get_connection()


def safe_json_load(value, default=None):
    if default is None:
        default = {}

    if not value:
        return default

    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_verdict(verdict):
    if not verdict:
        return "NEEDS IMPROVEMENT"

    verdict = str(verdict).strip().upper()

    if verdict == "CORRECT":
        return "PASS"

    if verdict == "PARTIALLY CORRECT":
        return "NEEDS IMPROVEMENT"

    if verdict == "INCORRECT":
        return "FAIL"

    if verdict in {
        "PASS",
        "NEEDS IMPROVEMENT",
        "FAIL"
    }:
        return verdict

    return "NEEDS IMPROVEMENT"


def get_all_rows(
    verdict=None,
    min_score=None,
    max_score=None,
    batch_id=None
):
    connection = get_connection()

    query = """
        SELECT *
        FROM evaluation_submissions
        WHERE relevance_score IS NOT NULL
          AND accuracy_score IS NOT NULL
          AND hallucination_score IS NOT NULL
          AND completeness_score IS NOT NULL
    """

    parameters = []

    if verdict:
        normalized = verdict.strip().upper()

        if normalized == "PASS":
            query += " AND UPPER(verdict) = 'CORRECT'"

        elif normalized == "NEEDS IMPROVEMENT":
            query += " AND UPPER(verdict) = 'PARTIALLY CORRECT'"

        elif normalized == "FAIL":
            query += " AND UPPER(verdict) = 'INCORRECT'"

        else:
            query += " AND UPPER(verdict) = ?"
            parameters.append(normalized)

    if min_score is not None:
        query += " AND COALESCE(score, 0) >= ?"
        parameters.append(min_score)

    if max_score is not None:
        query += " AND COALESCE(score, 0) <= ?"
        parameters.append(max_score)

    if batch_id:
        query += " AND batch_id = ?"
        parameters.append(batch_id)

    query += """
        ORDER BY created_at DESC, id DESC
    """

    rows = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    return rows


def calculate_average(rows, field):
    values = [
        safe_float(row[field])
        for row in rows
        if row[field] is not None
    ]

    if not values:
        return 0.0

    return round(
        sum(values) / len(values),
        2
    )


def calculate_percentage(count, total):
    if total == 0:
        return 0.0

    return round(
        (count / total) * 100,
        2
    )


def build_verdict_summary(rows):
    total = len(rows)

    pass_count = 0
    needs_improvement_count = 0
    fail_count = 0

    for row in rows:
        verdict = normalize_verdict(
            row["verdict"]
        )

        if verdict == "PASS":
            pass_count += 1

        elif verdict == "NEEDS IMPROVEMENT":
            needs_improvement_count += 1

        elif verdict == "FAIL":
            fail_count += 1

    return {
        "pass": {
            "count": pass_count,
            "percentage": calculate_percentage(
                pass_count,
                total
            )
        },
        "needs_improvement": {
            "count": needs_improvement_count,
            "percentage": calculate_percentage(
                needs_improvement_count,
                total
            )
        },
        "fail": {
            "count": fail_count,
            "percentage": calculate_percentage(
                fail_count,
                total
            )
        }
    }


def build_dimension_averages(rows):
    return {
        "relevance": calculate_average(
            rows,
            "relevance_score"
        ),
        "accuracy": calculate_average(
            rows,
            "accuracy_score"
        ),
        "hallucination_detection": calculate_average(
            rows,
            "hallucination_score"
        ),
        "completeness": calculate_average(
            rows,
            "completeness_score"
        )
    }


def build_score_distribution(rows):
    distribution = {
        "1": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0
    }

    fields = [
        "relevance_score",
        "accuracy_score",
        "hallucination_score",
        "completeness_score"
    ]

    for row in rows:
        for field in fields:
            value = row[field]

            if value is None:
                continue

            score = int(
                round(
                    safe_float(value)
                )
            )

            if 1 <= score <= 5:
                distribution[str(score)] += 1

    return distribution


def build_hallucination_statistics(rows):
    responses_with_hallucinations = 0
    unsupported_claim_frequency = 0
    contradictory_claim_frequency = 0

    for row in rows:
        hallucination = safe_json_load(
            row["hallucination_json"],
            {}
        )

        unsupported_claims = hallucination.get(
            "unsupported_claims",
            []
        )

        contradictory_claims = hallucination.get(
            "contradictory_claims",
            []
        )

        stored_claims = safe_json_load(
            row["hallucinated_claims_json"],
            []
        )

        if not isinstance(
            unsupported_claims,
            list
        ):
            unsupported_claims = []

        if not isinstance(
            contradictory_claims,
            list
        ):
            contradictory_claims = []

        if not isinstance(
            stored_claims,
            list
        ):
            stored_claims = []

        unsupported_count = max(
            len(unsupported_claims),
            len(stored_claims)
        )

        contradictory_count = len(
            contradictory_claims
        )

        has_hallucination = (
            unsupported_count > 0
            or contradictory_count > 0
            or bool(row["is_contradiction"])
        )

        if has_hallucination:
            responses_with_hallucinations += 1

        unsupported_claim_frequency += (
            unsupported_count
        )

        contradictory_claim_frequency += (
            contradictory_count
        )

    total = len(rows)

    return {
        "responses_with_hallucinated_claims":
            responses_with_hallucinations,

        "hallucination_frequency_percentage":
            calculate_percentage(
                responses_with_hallucinations,
                total
            ),

        "unsupported_claim_frequency":
            unsupported_claim_frequency,

        "contradictory_claim_frequency":
            contradictory_claim_frequency
    }


def build_completeness_statistics(rows):
    responses_with_missing_info = 0
    missing_aspect_counter = Counter()

    for row in rows:
        completeness = safe_json_load(
            row["completeness_json"],
            {}
        )

        missing_aspects = completeness.get(
            "missing_aspects",
            []
        )

        stored_missing = safe_json_load(
            row["missing_aspects_json"],
            []
        )

        if not isinstance(
            missing_aspects,
            list
        ):
            missing_aspects = []

        if not isinstance(
            stored_missing,
            list
        ):
            stored_missing = []

        combined = (
            missing_aspects
            if missing_aspects
            else stored_missing
        )

        if combined:
            responses_with_missing_info += 1

            for aspect in combined:
                if aspect:
                    missing_aspect_counter[
                        str(aspect)
                    ] += 1

    return {
        "responses_with_missing_information":
            responses_with_missing_info,

        "missing_information_frequency_percentage":
            calculate_percentage(
                responses_with_missing_info,
                len(rows)
            ),

        "missing_aspects_frequency": [
            {
                "aspect": aspect,
                "count": count
            }
            for aspect, count
            in missing_aspect_counter.most_common()
        ]
    }


def build_issue_summary(rows):
    issues = {
        "low_accuracy": 0,
        "low_relevance": 0,
        "incomplete_responses": 0,
        "hallucinated_claims": 0
    }

    for row in rows:
        accuracy = safe_float(
            row["accuracy_score"]
        )

        relevance = safe_float(
            row["relevance_score"]
        )

        completeness = safe_float(
            row["completeness_score"]
        )

        if row["accuracy_score"] is not None:
            if accuracy <= 2:
                issues["low_accuracy"] += 1

        if row["relevance_score"] is not None:
            if relevance <= 2:
                issues["low_relevance"] += 1

        if row["completeness_score"] is not None:
            if completeness <= 3:
                issues["incomplete_responses"] += 1

        hallucination = safe_json_load(
            row["hallucination_json"],
            {}
        )

        unsupported = hallucination.get(
            "unsupported_claims",
            []
        )

        contradictory = hallucination.get(
            "contradictory_claims",
            []
        )

        if (
            unsupported
            or contradictory
            or bool(row["is_contradiction"])
        ):
            issues["hallucinated_claims"] += 1

    return issues


def build_batch_summary(rows):
    batches = {}

    for row in rows:
        batch_id = row["batch_id"]

        if not batch_id:
            batch_id = "single"

        if batch_id not in batches:
            batches[batch_id] = []

        batches[batch_id].append(row)

    result = []

    for batch_id, batch_rows in batches.items():
        result.append(
            {
                "batch_id":
                    batch_id,

                "total_responses":
                    len(batch_rows),

                "average_score":
                    calculate_average(
                        batch_rows,
                        "score"
                    ),

                "average_relevance":
                    calculate_average(
                        batch_rows,
                        "relevance_score"
                    ),

                "average_accuracy":
                    calculate_average(
                        batch_rows,
                        "accuracy_score"
                    ),

                "average_hallucination":
                    calculate_average(
                        batch_rows,
                        "hallucination_score"
                    ),

                "average_completeness":
                    calculate_average(
                        batch_rows,
                        "completeness_score"
                    ),

                "verdict_distribution":
                    build_verdict_summary(
                        batch_rows
                    )
            }
        )

    return result


def serialize_row(row):
    hallucination = safe_json_load(
        row["hallucination_json"],
        {}
    )

    completeness = safe_json_load(
        row["completeness_json"],
        {}
    )

    accuracy = safe_json_load(
        row["accuracy_json"],
        {}
    )

    relevance = safe_json_load(
        row["relevance_json"],
        {}
    )

    evidence = safe_json_load(
        row["supporting_evidence_json"],
        []
    )

    hallucinated_claims = safe_json_load(
        row["hallucinated_claims_json"],
        []
    )

    missing_aspects = safe_json_load(
        row["missing_aspects_json"],
        []
    )

    dimension_scores = safe_json_load(
        row["dimension_scores_json"],
        {}
    )

    return {
        "id": row["id"],
        "question": row["question"],
        "ai_response": row["ai_response"],
        "reference_answer": row["reference_answer"],
        "source_document": row["source_document"],
        "score": safe_float(row["score"]),
        "verdict": row["verdict"],
        "dashboard_verdict": normalize_verdict(
            row["verdict"]
        ),
        "relevance_score": row["relevance_score"],
        "accuracy_score": row["accuracy_score"],
        "hallucination_score": row["hallucination_score"],
        "completeness_score": row["completeness_score"],
        "weighted_score": row["weighted_score"],
        "dimension_scores": dimension_scores,
        "relevance": relevance,
        "accuracy": accuracy,
        "hallucination": hallucination,
        "completeness": completeness,
        "hallucinated_claims": hallucinated_claims,
        "missing_aspects": missing_aspects,
        "supporting_evidence": evidence,
        "verdict_reasoning": row["verdict_reasoning"],
        "batch_id": row["batch_id"] or "single",
        "created_at": row["created_at"]
    }


def get_dashboard_summary(
    verdict=None,
    min_score=None,
    max_score=None,
    batch_id=None
):
    rows = get_all_rows(
        verdict=verdict,
        min_score=min_score,
        max_score=max_score,
        batch_id=batch_id
    )

    return {
        "status": "success",
        "total_responses": len(rows),

        "average_score":
            calculate_average(
                rows,
                "score"
            ),

        "average_weighted_score":
            calculate_average(
                rows,
                "weighted_score"
            ),

        "verdict_summary":
            build_verdict_summary(
                rows
            ),

        "average_dimension_scores":
            build_dimension_averages(
                rows
            ),

        "dimension_score_distribution":
            build_score_distribution(
                rows
            ),

        "hallucination_statistics":
            build_hallucination_statistics(
                rows
            ),

        "completeness_statistics":
            build_completeness_statistics(
                rows
            ),

        "most_frequent_issues":
            build_issue_summary(
                rows
            ),

        "batch_summary":
            build_batch_summary(
                rows
            ),

        "records": [
            serialize_row(row)
            for row in rows
        ]
    }


def get_dashboard_batches():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            COALESCE(batch_id, 'single') AS batch_id,
            COUNT(*) AS total_responses,
            MIN(created_at) AS first_created_at,
            MAX(created_at) AS last_created_at
        FROM evaluation_submissions
        WHERE relevance_score IS NOT NULL
          AND accuracy_score IS NOT NULL
          AND hallucination_score IS NOT NULL
          AND completeness_score IS NOT NULL
        GROUP BY COALESCE(batch_id, 'single')
        ORDER BY last_created_at DESC
        """
    ).fetchall()

    connection.close()

    return [
        {
            "batch_id": row["batch_id"],
            "total_responses": row["total_responses"],
            "first_created_at": row["first_created_at"],
            "last_created_at": row["last_created_at"]
        }
        for row in rows
    ]


def get_evaluation_detail(submission_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM evaluation_submissions
        WHERE id = ?
        """,
        (submission_id,)
    ).fetchone()

    connection.close()

    if row is None:
        return None

    return serialize_row(row)