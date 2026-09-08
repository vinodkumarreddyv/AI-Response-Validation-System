from evaluation.orchestrator import evaluate_response


def main():

    question = "Why does ice float on water?"

    ai_response = (
        "Ice floats on water because it is less dense than liquid water. "
        "When water freezes, its molecules form an open structure."
    )

    evidence = [
        {
            "text": (
                "Ice floats because solid ice is less dense than "
                "liquid water. When water freezes, hydrogen bonds "
                "create an open molecular structure."
            )
        }
    ]

    result = evaluate_response(
        question=question,
        ai_response=ai_response,
        evidence=evidence
    )

    print("\n========== EVALUATION ORCHESTRATOR ==========")

    print("\n--- RELEVANCE ---")
    print("Score:", result["relevance"]["score"])
    print("Label:", result["relevance"]["label"])
    print("Reasoning:", result["relevance"]["reasoning"])

    print("\n--- ACCURACY ---")
    print("Score:", result["accuracy"]["score"])
    print("Label:", result["accuracy"]["label"])
    print("Reasoning:", result["accuracy"]["reasoning"])

    print("\n--- HALLUCINATION ---")
    print("Status:", result["hallucination"]["status"])
    print(
        "Detected:",
        result["hallucination"]["hallucination_detected"]
    )

    print("\n--- COMPLETE RESULT ---")
    print(result)


if __name__ == "__main__":
    main()