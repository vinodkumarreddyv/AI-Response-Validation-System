from agents.completeness.completeness_agent import evaluate_completeness


def print_result(title, result):
    print("=" * 70)
    print(title)
    print("=" * 70)

    print(f"Score: {result.get('score')} / 5")
    print(f"Label: {result.get('label')}")
    print(f"Reasoning: {result.get('reasoning')}")

    if "coverage" in result:
        print(f"Coverage: {result.get('coverage')}")

    if "evidence_score" in result:
        print(f"Evidence Score: {result.get('evidence_score')}")

    print()


# =========================================================
# TEST 1 - Complete Response
# =========================================================

reference_1 = (
    "Photosynthesis is the process by which plants use sunlight, "
    "water, and carbon dioxide to produce glucose and oxygen."
)

response_1 = (
    "Photosynthesis is the process by which plants use sunlight, "
    "water, and carbon dioxide to produce glucose and oxygen."
)

result_1 = evaluate_completeness(
    question="What is photosynthesis?",
    ai_response=response_1,
    reference_answer=reference_1
)

print_result("TEST 1 - Complete Response", result_1)


# =========================================================
# TEST 2 - Mostly Complete Response
# =========================================================

reference_2 = (
    "Photosynthesis is the process by which plants use sunlight, "
    "water, and carbon dioxide to produce glucose and oxygen."
)

response_2 = (
    "Photosynthesis is a process in plants that uses sunlight "
    "to make food."
)

result_2 = evaluate_completeness(
    question="What is photosynthesis?",
    ai_response=response_2,
    reference_answer=reference_2
)

print_result("TEST 2 - Mostly Complete Response", result_2)


# =========================================================
# TEST 3 - Partially Complete Response
# =========================================================

reference_3 = (
    "Photosynthesis is the process by which plants use sunlight, "
    "water, and carbon dioxide to produce glucose and oxygen."
)

response_3 = (
    "Plants use sunlight to make food."
)

result_3 = evaluate_completeness(
    question="What is photosynthesis?",
    ai_response=response_3,
    reference_answer=reference_3
)

print_result("TEST 3 - Partially Complete Response", result_3)


# =========================================================
# TEST 4 - Incomplete Response
# =========================================================

reference_4 = (
    "Photosynthesis is the process by which plants use sunlight, "
    "water, and carbon dioxide to produce glucose and oxygen."
)

response_4 = (
    "Plants."
)

result_4 = evaluate_completeness(
    question="What is photosynthesis?",
    ai_response=response_4,
    reference_answer=reference_4
)

print_result("TEST 4 - Incomplete Response", result_4)


# =========================================================
# TEST 5 - Evidence Based Response
# =========================================================

evidence_5 = [
    {
        "relevance_score": 0.90,
        "semantic_similarity": 0.90,
        "text": (
            "Photosynthesis uses sunlight to convert carbon dioxide "
            "and water into sugars and releases oxygen."
        )
    }
]

response_5 = (
    "Photosynthesis uses sunlight to convert carbon dioxide "
    "and water into sugars and releases oxygen."
)

result_5 = evaluate_completeness(
    question="What is photosynthesis?",
    ai_response=response_5,
    evidence=evidence_5
)

print_result("TEST 5 - Evidence Based Response", result_5)


print("=" * 70)
print("COMPLETENESS AGENT TESTING COMPLETED")
print("=" * 70)