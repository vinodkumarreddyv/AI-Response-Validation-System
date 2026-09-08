from agents.accuracy.accuracy_agent import evaluate_accuracy


def run_test(name, ai_response, reference_answer=None, evidence=None):
    result = evaluate_accuracy(
        ai_response=ai_response,
        reference_answer=reference_answer,
        evidence=evidence
    )

    print(f"\n--- {name} ---")
    print("AI Response:", ai_response)
    print("Score:", result["score"])
    print("Label:", result["label"])
    print("Reasoning:", result["reasoning"])
    print("Supporting Evidence:", result["supporting_evidence"])


def main():

    reference = (
        "Water freezes at 0 degrees Celsius under standard atmospheric pressure."
    )

    # 1. Correct response
    run_test(
        "Correct Response",
        "Water freezes at 0 degrees Celsius.",
        reference_answer=reference
    )

    # 2. Partially correct response
    run_test(
        "Partially Correct Response",
        "Water freezes when the temperature becomes very cold.",
        reference_answer=reference
    )

    # 3. Incorrect response
    run_test(
        "Incorrect Response",
        "Water freezes at 100 degrees Celsius.",
        reference_answer=reference
    )

    # 4. No reference - use retrieved evidence
    evidence = [
        {
            "text": (
                "The boiling point of water is 100 degrees Celsius "
                "at standard atmospheric pressure."
            )
        }
    ]

    run_test(
        "Evidence Based Evaluation",
        "Water boils at 100 degrees Celsius.",
        evidence=evidence
    )


if __name__ == "__main__":
    main()