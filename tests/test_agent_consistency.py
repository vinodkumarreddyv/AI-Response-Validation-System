from evaluation.orchestrator import evaluate_response


def run_case(case_name, question, ai_response, evidence):
    print("\n" + "=" * 60)
    print(case_name)
    print("=" * 60)

    result = evaluate_response(
        question=question,
        ai_response=ai_response,
        evidence=evidence
    )

    relevance = result["relevance"]
    accuracy = result["accuracy"]
    hallucination = result["hallucination"]

    print("\nQuestion:")
    print(question)

    print("\nAI Response:")
    print(ai_response)

    print("\n--- Relevance ---")
    print("Score:", relevance["score"])
    print("Label:", relevance["label"])
    print("Reasoning:", relevance["reasoning"])

    print("\n--- Accuracy ---")
    print("Score:", accuracy["score"])
    print("Label:", accuracy["label"])
    print("Reasoning:", accuracy["reasoning"])

    print("\n--- Hallucination ---")
    print("Status:", hallucination["status"])
    print("Detected:", hallucination["hallucination_detected"])

    if hallucination["claims"]:
        print("\nClaims:")

        for claim in hallucination["claims"]:
            print("  Claim:", claim["claim"])
            print("  Status:", claim["status"])
            print("  Similarity:", claim["similarity"])


def main():

    # ---------------------------------------------------------
    # CASE 1 — Correct response
    # ---------------------------------------------------------

    run_case(
        "CASE 1 - Correct Response",

        "What is the boiling point of water?",

        "Water boils at 100 degrees Celsius.",

        [
            {
                "text": (
                    "Water boils at 100 degrees Celsius "
                    "under standard atmospheric pressure."
                )
            }
        ]
    )

    # ---------------------------------------------------------
    # CASE 2 — Partially correct response
    # ---------------------------------------------------------

    run_case(
        "CASE 2 - Partially Correct Response",

        "What is the boiling point of water?",

        "Water boils when the temperature becomes very high.",

        [
            {
                "text": (
                    "Water boils at 100 degrees Celsius "
                    "under standard atmospheric pressure."
                )
            }
        ]
    )

    # ---------------------------------------------------------
    # CASE 3 — Incorrect response
    # ---------------------------------------------------------

    run_case(
        "CASE 3 - Incorrect Response",

        "What is the boiling point of water?",

        "Water boils at 20 degrees Celsius.",

        [
            {
                "text": (
                    "Water boils at 100 degrees Celsius "
                    "under standard atmospheric pressure."
                )
            }
        ]
    )

    # ---------------------------------------------------------
    # CASE 4 — Irrelevant response
    # ---------------------------------------------------------

    run_case(
        "CASE 4 - Irrelevant Response",

        "What is photosynthesis?",

        "Python is a programming language used to build software.",

        [
            {
                "text": (
                    "Photosynthesis is the process by which "
                    "green plants use sunlight, carbon dioxide, "
                    "and water to produce food and oxygen."
                )
            }
        ]
    )

    # ---------------------------------------------------------
    # CASE 5 — Partially unsupported response
    # ---------------------------------------------------------

    run_case(
        "CASE 5 - Unsupported Claim",

        "What is the boiling point of water?",

        (
            "Water boils at 100 degrees Celsius. "
            "Water was discovered by Isaac Newton."
        ),

        [
            {
                "text": (
                    "Water boils at 100 degrees Celsius "
                    "under standard atmospheric pressure."
                )
            }
        ]
    )


if __name__ == "__main__":
    main()