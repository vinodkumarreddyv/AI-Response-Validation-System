from agents.hallucination.hallucination_agent import (
    evaluate_hallucination
)


def run_test(name, ai_response, evidence):

    result = evaluate_hallucination(
        ai_response=ai_response,
        evidence=evidence
    )

    print(f"\n--- {name} ---")
    print("AI Response:", ai_response)
    print("Status:", result["status"])
    print("Hallucination Detected:",
          result["hallucination_detected"])
    print("Reasoning:", result["reasoning"])

    print("\nClaims:")

    for claim in result["claims"]:
        print("Claim:", claim["claim"])
        print("Status:", claim["status"])
        print("Similarity:", claim["similarity"])
        print("Reasoning:", claim["reasoning"])
        print("Evidence:", claim["evidence"])


def main():

    evidence = [
        {
            "text": (
                "Water freezes at 0 degrees Celsius under "
                "standard atmospheric pressure."
            )
        }
    ]

    # 1. Fully supported
    run_test(
        "Supported Response",
        "Water freezes at 0 degrees Celsius.",
        evidence
    )

    # 2. Unsupported claim
    run_test(
        "Unsupported Claim",
        (
            "Water freezes at 0 degrees Celsius. "
            "Water was discovered by Isaac Newton."
        ),
        evidence
    )

    # 3. Contradictory claim
    run_test(
        "Contradictory Claim",
        "Water freezes at 100 degrees Celsius.",
        evidence
    )


if __name__ == "__main__":
    main()