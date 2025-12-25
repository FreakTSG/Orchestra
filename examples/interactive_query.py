"""Interactive example with clarifying questions."""

import asyncio
from multi_agent_coder import MultiAgentCoder
import questionary


async def main():
    """Run an interactive query with clarifying questions."""

    # Get the initial prompt
    prompt = await questionary.text(
        "What coding task would you like help with?",
        multiline=True
    ).ask_async()

    if not prompt:
        print("No prompt provided. Exiting.")
        return

    # Initialize
    mac = MultiAgentCoder()

    # Get clarifying questions
    questions, _, _ = await mac._enhance_prompt(prompt)

    # Get answers from user
    answers = {}
    if questions:
        print("\n🔍 I have some questions to better help you:\n")

        for i, question in enumerate(questions, 1):
            answer = await questionary.text(
                f"Q{i}: {question}",
                default=""
            ).ask_async()
            answers[question] = answer

    # Run the query with answers
    print("\n🚀 Processing your request...\n")
    result = await mac.query(
        prompt,
        predefined_answers=answers if answers else None
    )

    # Display results
    print(f"\n{'='*60}")
    print(f"Best solution from: {result.best_response.agent_name}")
    print(f"{'='*60}\n")

    if result.best_response.explanation:
        print("Explanation:")
        print(result.best_response.explanation)
        print()

    if result.best_response.code:
        print("Code:")
        print(result.best_response.code)
        print()

    # Show rankings
    print(f"\n{'='*60}")
    print("All solutions ranked by quality:")
    print(f"{'='*60}")

    for eval_result in result.evaluation_results:
        medal = "🥇" if eval_result.rank == 1 else "🥈" if eval_result.rank == 2 else "🥉"
        print(f"\n{medal} #{eval_result.rank} {eval_result.response.agent_name}")
        print(f"   Score: {eval_result.average_score:.1f}/100")
        print(f"   Latency: {eval_result.response.latency_ms}ms")

        if eval_result.response.explanation:
            preview = eval_result.response.explanation[:100] + "..."
            print(f"   Approach: {preview}")


if __name__ == "__main__":
    asyncio.run(main())
