"""Example usage of CLI-based Multi-Agent Coder."""

import asyncio
from multi_agent_coder.cli_orchestrator import MultiAgentCLICoder
from agents.generic_cli import GenericCLIAgent


async def example_1_basic_query():
    """Example 1: Basic query with auto-detected CLI tools."""
    print("=" * 60)
    print("Example 1: Basic Query")
    print("=" * 60)

    # Initialize with auto-detection
    mac = MultiAgentCLICoder(auto_detect=True)

    # Show detected agents
    print(f"\nDetected agents: {mac.get_available_agents()}")

    # Run a query
    result = await mac.query(
        "Implement a binary search in Python",
        skip_enhancement=True
    )

    # Display results
    print(f"\nBest solution: {result.best_response.agent_name}")
    print(f"Code:\n{result.best_response.code}")


async def example_2_with_enhancement():
    """Example 2: Query with prompt enhancement."""
    print("\n" + "=" * 60)
    print("Example 2: Query with Enhancement")
    print("=" * 60)

    mac = MultiAgentCLICoder(auto_detect=True)

    # Provide answers to clarifying questions
    predefined_answers = {
        "What programming language?": "Python",
        "Any specific requirements?": "Must handle edge cases",
        "Expected output?": "Just the function, no main code"
    }

    result = await mac.query(
        "Implement a sorting algorithm",
        predefined_answers=predefined_answers
    )

    print(f"\nClarifying questions asked: {len(result.clarifying_questions)}")
    for i, q in enumerate(result.clarifying_questions, 1):
        print(f"  {i}. {q}")

    print(f"\nBest solution from: {result.best_response.agent_name}")


async def example_3_specific_agents():
    """Example 3: Use specific CLI tools."""
    print("\n" + "=" * 60)
    print("Example 3: Specific Agents")
    print("=" * 60)

    # Create specific CLI agents
    from agents.claude_cli import ClaudeCLIAgent
    from agents.openai_cli import OpenAICLIAgent

    claude_agent = ClaudeCLIAgent(command="claude")
    openai_agent = OpenAICLIAgent(command="openai")

    # Initialize with specific agents
    mac = MultiAgentCLICoder(
        agents=[claude_agent, openai_agent],
        auto_detect=False
    )

    result = await mac.query(
        "Add error handling to this code",
        context={"language": "Python"}
    )

    print(f"\nUsed {len(result.all_responses)} agent(s)")
    for response in result.all_responses:
        print(f"  - {response.agent_name}: {response.execution_time_ms}ms")


async def example_4_custom_cli_tool():
    """Example 4: Use a custom CLI tool."""
    print("\n" + "=" * 60)
    print("Example 4: Custom CLI Tool")
    print("=" * 60)

    # Create a generic agent for any CLI tool
    # For example, if you have 'ollama' installed:
    ollama_agent = GenericCLIAgent(
        name="Ollama",
        command="ollama",
        query_args=["run", "llama2", "{prompt}"]
    )

    # Or for a custom tool:
    # custom_agent = GenericCLIAgent(
    #     name="MyAI",
    #     command="/path/to/my-ai-cli",
    #     query_args=["--ask", "{prompt}"],
    #     eval_args=["--evaluate", "{prompt}"],
    #     enhance_args=["--clarify", "{prompt}"]
    # )

    # Check if available
    if ollama_agent.available:
        mac = MultiAgentCLICoder(
            agents=[ollama_agent],
            auto_detect=False
        )

        result = await mac.query(
            "What is a binary search tree?",
            skip_enhancement=True
        )

        print(f"\nResponse from {result.best_response.agent_name}:")
        print(result.best_response.content[:200] + "...")
    else:
        print("\nOllama not detected. This example requires Ollama to be installed.")
        print("Install: https://ollama.ai/")


async def example_5_compare_solutions():
    """Example 5: Compare solutions from multiple agents."""
    print("\n" + "=" * 60)
    print("Example 5: Compare Solutions")
    print("=" * 60)

    mac = MultiAgentCLICoder(auto_detect=True)

    result = await mac.query(
        "Implement a function to validate email addresses",
        skip_enhancement=True
    )

    print(f"\nReceived {len(result.all_responses)} solutions:\n")

    for eval_result in result.evaluation_results:
        medal = "🥇" if eval_result.rank == 1 else "🥈" if eval_result.rank == 2 else "🥉"
        print(f"{medal} {eval_result.response.agent_name}")
        print(f"   Score: {eval_result.average_score:.1f}/100")
        print(f"   Time: {eval_result.response.execution_time_ms}ms")

        if eval_result.response.code:
            print(f"   Code: {eval_result.response.code[:100]}...")
        print()


async def example_6_error_handling():
    """Example 6: Handle errors gracefully."""
    print("\n" + "=" * 60)
    print("Example 6: Error Handling")
    print("=" * 60)

    try:
        # Try to initialize without any CLI tools
        mac = MultiAgentCLICoder(auto_detect=True)

        # This will work if at least one CLI tool is detected
        result = await mac.query("Test query")

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 To fix this, install at least one AI CLI tool:")
        print("   npm install -g @anthropic-ai/claude-code")
        print("   npm install -g openai-cli")
        print("   pip install google-generativeai")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("🤖 CLI-Based Multi-Agent Coder Examples")
    print("=" * 60)

    # Run examples
    try:
        await example_1_basic_query()
    except Exception as e:
        print(f"\nExample 1 failed: {e}")

    try:
        await example_2_with_enhancement()
    except Exception as e:
        print(f"\nExample 2 failed: {e}")

    try:
        await example_3_specific_agents()
    except Exception as e:
        print(f"\nExample 3 failed: {e}")

    try:
        await example_4_custom_cli_tool()
    except Exception as e:
        print(f"\nExample 4 failed: {e}")

    try:
        await example_5_compare_solutions()
    except Exception as e:
        print(f"\nExample 5 failed: {e}")

    await example_6_error_handling()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
