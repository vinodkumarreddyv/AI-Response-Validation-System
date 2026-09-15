import re
import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# MODEL
# ============================================================

model = SentenceTransformer("all-MiniLM-L6-v2")


# ============================================================
# NORMALIZE
# ============================================================

def normalize(text: str) -> str:
    if not text:
        return ""

    text = str(text).lower().strip()

    # Remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(text1: str, text2: str) -> float:

    if not text1 or not text2:
        return 0.0

    embeddings = model.encode(
        [text1, text2],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return float(
        np.dot(
            embeddings[0],
            embeddings[1]
        )
    )


# ============================================================
# NUMBER EXTRACTION
# ============================================================

def extract_numbers(text: str) -> list[float]:
    """
    Extract numeric values from text.

    Examples:
        100
        20
        3.14
        2026
    """

    if not text:
        return []

    values = re.findall(
        r"\b\d+(?:\.\d+)?\b",
        str(text)
    )

    return [
        float(value)
        for value in values
    ]


# ============================================================
# GENERAL NUMERIC CONTRADICTION
# ============================================================

def check_numeric_contradiction(
    ai_response: str,
    reference_answer: str | None
) -> bool:
    """
    Detect conflicting numeric factual values between
    the AI response and the reference answer.

    Example:

        Reference:
        Water boils at 100 degrees Celsius.

        Response:
        Water boils at 20 degrees Celsius.

        Result:
        Contradiction = True
    """

    if not ai_response or not reference_answer:
        return False

    response_numbers = extract_numbers(
        ai_response
    )

    reference_numbers = extract_numbers(
        reference_answer
    )

    if not response_numbers or not reference_numbers:
        return False

    # If the response and reference are semantically unrelated,
    # do not automatically treat different numbers as a
    # contradiction.
    similarity = cosine_similarity(
        ai_response,
        reference_answer
    )

    if similarity < 0.55:
        return False

    # Same number is not a contradiction.
    for response_number in response_numbers:

        for reference_number in reference_numbers:

            if response_number != reference_number:
                return True

    return False


# ============================================================
# EXPECTED FACT
# ============================================================

def extract_expected_fact(
    question: str,
    reference_answer: str | None
) -> str | None:

    if not reference_answer:
        return None

    return normalize(
        reference_answer
    )


# ============================================================
# DIRECT FACT CHECK
# ============================================================

def check_direct_fact(
    question: str,
    ai_response: str,
    expected_fact: str | None
) -> tuple[bool, bool]:

    if not expected_fact:
        return False, False

    question = normalize(
        question
    )

    response = normalize(
        ai_response
    )

    fact = normalize(
        expected_fact
    )

    # ========================================================
    # CAPITAL QUESTION
    # ========================================================

    if "capital" in question:

        # ----------------------------------------------------
        # CASE 1:
        # Exact short answer
        # ----------------------------------------------------

        if response == fact:
            return True, False

        # ----------------------------------------------------
        # CASE 2:
        # Full correct sentence
        # ----------------------------------------------------

        correct_patterns = [

            rf"^{re.escape(fact)} is the capital of",

            rf"^the capital of .+ is {re.escape(fact)}$",

            rf"^capital of .+ is {re.escape(fact)}$",

            rf"^capital\s*:\s*{re.escape(fact)}$",

            rf"{re.escape(fact)} is the capital of"
        ]

        for pattern in correct_patterns:

            if re.search(
                pattern,
                response
            ):
                return True, False

        # ----------------------------------------------------
        # CASE 3:
        # Wrong capital
        # ----------------------------------------------------

        wrong_capital_patterns = [

            r"^the capital is .+$",

            r"^capital is .+$",

            r"^the capital of .+ is .+$",

            r"^capital of .+ is .+$",

            r"^.+ is the capital of .+$"
        ]

        for pattern in wrong_capital_patterns:

            if re.search(
                pattern,
                response
            ):

                if fact not in response:
                    return False, True

        # ----------------------------------------------------
        # CASE 4:
        # Simple alternative answer
        # ----------------------------------------------------

        if (
            len(response.split()) <= 3
            and response != fact
            and "is" not in response
            and "capital" not in response
        ):
            return False, True

        # ----------------------------------------------------
        # CASE 5:
        # Expected fact mentioned but not answering directly
        # ----------------------------------------------------

        if fact in response:
            return False, False

        return False, False

    # ========================================================
    # GENERAL FACT
    # ========================================================

    # Exact answer
    if response == fact:
        return True, False

    # Reference answer appears inside response
    if fact in response:
        return True, False

    # --------------------------------------------------------
    # GENERAL NUMERIC CONTRADICTION
    # --------------------------------------------------------
    #
    # This handles factual questions such as:
    #
    # Reference:
    # "Water boils at 100 degrees Celsius."
    #
    # Response:
    # "Water boils at 20 degrees Celsius."
    #
    # The response is semantically related but contains
    # a conflicting factual value.
    # --------------------------------------------------------

    numeric_contradiction = check_numeric_contradiction(
        ai_response=ai_response,
        reference_answer=expected_fact
    )

    if numeric_contradiction:
        return False, True

    return False, False


# ============================================================
# VALIDATE RESPONSE
# ============================================================

def validate_response(
    question: str,
    ai_response: str,
    reference_answer: str | None,
    evidence: list
) -> dict:

    # ========================================================
    # REFERENCE SIMILARITY
    # ========================================================

    reference_score = None

    if reference_answer:

        reference_score = cosine_similarity(
            ai_response,
            reference_answer
        )

    # ========================================================
    # EXPECTED FACT
    # ========================================================

    expected_fact = extract_expected_fact(
        question,
        reference_answer
    )

    # ========================================================
    # DIRECT FACT CHECK
    # ========================================================

    (
        direct_fact_match,
        direct_fact_contradiction
    ) = check_direct_fact(
        question,
        ai_response,
        expected_fact
    )

    # ========================================================
    # EXACT MATCH
    # ========================================================

    reference_exact_match = direct_fact_match

    # ========================================================
    # EVIDENCE SCORES
    # ========================================================

    evidence_scores = []

    for item in evidence:

        text = item.get(
            "text",
            ""
        )

        score = cosine_similarity(
            ai_response,
            text
        )

        evidence_scores.append({
            "text": text,

            "similarity": round(
                score,
                4
            ),

            "distance": item.get(
                "distance",
                0.0
            ),

            "index": item.get(
                "index",
                -1
            ),

            "relevance_score": item.get(
                "relevance_score",
                0.0
            ),

            "direct_fact_score": item.get(
                "direct_fact_score",
                0.0
            ),

            "exact_match": item.get(
                "exact_match",
                False
            )
        })

    # ========================================================
    # BEST EVIDENCE
    # ========================================================

    best_evidence_score = max(
        [
            x["similarity"]
            for x in evidence_scores
        ],
        default=0.0
    )

    # ========================================================
    # CONTRADICTION
    # ========================================================

    contradiction = {
        "contradiction": (
            1.0
            if direct_fact_contradiction
            else 0.0
        ),

        "entailment": (
            1.0
            if direct_fact_match
            else 0.0
        ),

        "neutral": (
            0.0
            if (
                direct_fact_match
                or direct_fact_contradiction
            )
            else 1.0
        ),

        "is_contradiction":
            direct_fact_contradiction
    }

    # ========================================================
    # FINAL SCORE
    # ========================================================

    # --------------------------------------------------------
    # DEFINITELY WRONG
    # --------------------------------------------------------

    if direct_fact_contradiction:

        final_score = 0.20

    # --------------------------------------------------------
    # DEFINITELY CORRECT
    # --------------------------------------------------------

    elif direct_fact_match:

        final_score = 1.00

    # --------------------------------------------------------
    # Correct fact mentioned but not answering directly
    # --------------------------------------------------------

    elif (
        expected_fact
        and expected_fact in normalize(
            ai_response
        )
    ):

        final_score = 0.60

    # --------------------------------------------------------
    # Semantic fallback
    # --------------------------------------------------------

    elif reference_score is not None:

        final_score = (
            0.70 * reference_score
            +
            0.30 * best_evidence_score
        )

    else:

        final_score = best_evidence_score

    # ========================================================
    # VERDICT
    # ========================================================

    if direct_fact_contradiction:

        verdict = "INCORRECT"

    elif direct_fact_match:

        verdict = "CORRECT"

    elif (
        expected_fact
        and expected_fact in normalize(
            ai_response
        )
    ):

        verdict = "PARTIALLY CORRECT"

    elif final_score >= 0.75:

        verdict = "CORRECT"

    elif final_score >= 0.50:

        verdict = "PARTIALLY CORRECT"

    else:

        verdict = "INCORRECT"

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "score": round(
            final_score,
            4
        ),

        "verdict": verdict,

        "reference_similarity": (
            round(
                reference_score,
                4
            )
            if reference_score is not None
            else None
        ),

        "reference_exact_match":
            reference_exact_match,

        "contradiction":
            contradiction,

        "expected_fact":
            expected_fact,

        "direct_fact_match":
            direct_fact_match,

        "direct_fact_contradiction":
            direct_fact_contradiction,

        "best_evidence_similarity":
            round(
                best_evidence_score,
                4
            ),

        "evidence_scores":
            evidence_scores
    }