import re


# =========================================================
# CLAIM SPLITTER
# =========================================================

def _split_into_claims(text: str) -> list[str]:
    """
    Split an AI response into simple factual statements.
    """

    if not text:
        return []

    parts = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


# =========================================================
# KEYWORD COVERAGE
# =========================================================

def _keyword_coverage(
    reference_text: str,
    response_text: str
) -> float:
    """
    Calculate how much important information from the
    reference text is covered by the AI response.
    """

    if not reference_text or not response_text:
        return 0.0

    reference_words = re.findall(
        r"\b[a-zA-Z0-9]+\b",
        reference_text.lower()
    )

    response_lower = response_text.lower()

    if not reference_words:
        return 0.0

    # Remove common words that do not carry much meaning.
    stop_words = {
        "the",
        "and",
        "that",
        "this",
        "with",
        "from",
        "into",
        "where",
        "which",
        "when",
        "than",
        "they",
        "their",
        "there",
        "about",
        "what",
        "does",
        "have",
        "been",
        "are",
        "was",
        "were",
        "for",
        "using",
        "uses",
        "used",
        "also",
        "can",
        "may",
        "will",
        "its",
        "not",
        "how",
        "why"
    }

    important_words = [
        word
        for word in reference_words
        if len(word) > 3 and word not in stop_words
    ]

    if not important_words:
        important_words = [
            word
            for word in reference_words
            if len(word) > 2
        ]

    if not important_words:
        return 0.0

    matched = 0

    for word in important_words:
        if word in response_lower:
            matched += 1

    return matched / len(important_words)


# =========================================================
# EVIDENCE SCORE
# =========================================================

def _get_evidence_score(item: dict) -> float:
    """
    Extract evidence quality from different evidence formats.

    Supported fields:
        relevance_score
        semantic_similarity
        similarity
        combined_score
    """

    if not isinstance(item, dict):
        return 0.0

    possible_scores = [
        item.get("relevance_score"),
        item.get("semantic_similarity"),
        item.get("similarity"),
        item.get("combined_score")
    ]

    for value in possible_scores:

        try:
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            continue

    return 0.0


# =========================================================
# COMPLETENESS AGENT
# =========================================================

def evaluate_completeness(
    question: str,
    ai_response: str,
    reference_answer: str | None = None,
    evidence: list | None = None
) -> dict:
    """
    Completeness Judge Agent

    Evaluates whether the AI response provides enough
    information to answer the submitted question.

    Score:

        5 = Complete
        4 = Mostly Complete
        3 = Partially Complete
        2 = Mostly Incomplete
        1 = Incomplete

    The agent supports:

        1. Reference-answer based evaluation
        2. Retrieved-evidence based evaluation
        3. Basic response-length fallback
    """

    evidence = evidence or []

    response = (ai_response or "").strip()

    # =========================================================
    # EMPTY RESPONSE
    # =========================================================

    if not response:

        return {
            "score": 1,
            "label": "Incomplete",
            "coverage": 0.0,
            "reasoning": "The AI response is empty."
        }

    # =========================================================
    # SPLIT RESPONSE INTO CLAIMS
    # =========================================================

    response_claims = _split_into_claims(response)

    if not response_claims:

        return {
            "score": 1,
            "label": "Incomplete",
            "coverage": 0.0,
            "reasoning": (
                "The response does not contain enough "
                "information to evaluate completeness."
            )
        }

    # =========================================================
    # REFERENCE-BASED COMPLETENESS
    # =========================================================

    if reference_answer:

        reference = reference_answer.strip()

        if reference:

            reference_claims = _split_into_claims(reference)

            if reference_claims:

                matched_claims = 0
                claim_coverages = []

                for reference_claim in reference_claims:

                    coverage = _keyword_coverage(
                        reference_claim,
                        response
                    )

                    claim_coverages.append(coverage)

                    # A claim is considered covered when
                    # at least half of its important
                    # information appears in the response.
                    if coverage >= 0.50:
                        matched_claims += 1

                # Combine claim-level coverage and
                # overall keyword coverage.
                claim_level_coverage = (
                    matched_claims / len(reference_claims)
                )

                overall_keyword_coverage = (
                    sum(claim_coverages) /
                    len(claim_coverages)
                    if claim_coverages
                    else 0.0
                )

                coverage = (
                    0.70 * claim_level_coverage
                    + 0.30 * overall_keyword_coverage
                )

                # =================================================
                # SCORE
                # =================================================

                if coverage >= 0.90:

                    score = 5
                    label = "Complete"

                elif coverage >= 0.60:

                    score = 4
                    label = "Mostly Complete"

                elif coverage >= 0.35:

                    score = 3
                    label = "Partially Complete"

                elif coverage >= 0.15:

                    score = 2
                    label = "Mostly Incomplete"

                else:

                    score = 1
                    label = "Incomplete"

                return {
                    "score": score,
                    "label": label,
                    "coverage": round(coverage, 3),
                    "reasoning": (
                        f"The response covers approximately "
                        f"{round(coverage * 100)}% of the important "
                        f"information found in the reference answer."
                    )
                }

    # =========================================================
    # EVIDENCE-BASED COMPLETENESS
    # =========================================================

    if evidence:

        best_evidence_score = 0.0

        for item in evidence:

            score = _get_evidence_score(item)

            best_evidence_score = max(
                best_evidence_score,
                score
            )

        # ---------------------------------------------------------
        # Compare response with the strongest evidence text
        # when available.
        # ---------------------------------------------------------

        best_evidence_text = ""

        best_item_score = -1.0

        for item in evidence:

            if not isinstance(item, dict):
                continue

            score = _get_evidence_score(item)

            text = item.get("text", "")

            if isinstance(text, dict):

                text = text.get(
                    "text",
                    ""
                )

            text = str(text).strip()

            if text and score > best_item_score:

                best_item_score = score
                best_evidence_text = text

        evidence_coverage = 0.0

        if best_evidence_text:

            evidence_coverage = _keyword_coverage(
                best_evidence_text,
                response
            )

        # Use the stronger signal between evidence relevance
        # and actual information coverage.
        combined_coverage = max(
            best_evidence_score,
            evidence_coverage
        )

        # =========================================================
        # SCORE
        # =========================================================

        if combined_coverage >= 0.85:

            score = 5
            label = "Complete"

        elif combined_coverage >= 0.60:

            score = 4
            label = "Mostly Complete"

        elif combined_coverage >= 0.40:

            score = 3
            label = "Partially Complete"

        elif combined_coverage >= 0.20:

            score = 2
            label = "Mostly Incomplete"

        else:

            score = 1
            label = "Incomplete"

        return {
            "score": score,
            "label": label,
            "evidence_score": round(
                best_evidence_score,
                3
            ),
            "coverage": round(
                combined_coverage,
                3
            ),
            "reasoning": (
                "The response was evaluated against "
                "the available retrieved evidence. "
                f"The strongest evidence relevance was "
                f"{round(best_evidence_score * 100)}%."
            )
        }

    # =========================================================
    # BASIC RESPONSE COMPLETENESS FALLBACK
    # =========================================================

    word_count = len(
        response.split()
    )

    if word_count >= 40:

        score = 4
        label = "Mostly Complete"

    elif word_count >= 20:

        score = 3
        label = "Partially Complete"

    elif word_count >= 8:

        score = 2
        label = "Mostly Incomplete"

    else:

        score = 1
        label = "Incomplete"

    return {
        "score": score,
        "label": label,
        "coverage": 0.0,
        "reasoning": (
            "No reference answer or retrieved evidence "
            "was available, so completeness was estimated "
            "from the amount of information provided."
        )
    }