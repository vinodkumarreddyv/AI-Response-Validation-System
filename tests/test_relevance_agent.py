from agents.relevance.relevance_agent import evaluate_relevance


def run_test(name, question, ai_response):
    result = evaluate_relevance(
        question=question,
        ai_response=ai_response
    )

    print(f"\n--- {name} ---")
    print("Question:", question)
    print("AI Response:", ai_response)
    print("Score:", result["score"])
    print("Label:", result["label"])
    print("Reasoning:", result["reasoning"])


def main():

    # 1. Fully relevant
    run_test(
        "Fully Relevant",
        "What is photosynthesis?",
        "Photosynthesis is the process by which green plants use sunlight, "
        "carbon dioxide, and water to produce glucose and oxygen."
    )

    # 2. Partially relevant
    run_test(
        "Partially Relevant",
        "What is photosynthesis?",
        "Plants need sunlight and water to grow."
    )

    # 3. Mostly irrelevant
    run_test(
        "Mostly Irrelevant",
        "What is photosynthesis?",
        "The Earth has many different types of weather."
    )

    # 4. Completely irrelevant
    run_test(
        "Completely Irrelevant",
        "What is photosynthesis?",
        "Python is a programming language used to build software."
    )


if __name__ == "__main__":
    main()