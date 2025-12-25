"""Simple example of using the Multi-Agent Coder."""

import asyncio
from multi_agent_coder import MultiAgentCoder


async def main():
    """Run a simple query."""
    # Initialize the multi-agent coder
    mac = MultiAgentCoder()

    # Run a query
    result = await mac.query(
        "Implement a binary search tree in Python with insert, search, and delete operations"
    )

    # Print the best solution
    print(f"\n🏆 Best Solution: {result.best_response.agent_name}")
    print(f"\nScore: {max(r.average_score for r in result.evaluation_results):.1f}/100")
    print(f"\nCode:\n{result.best_response.code}")

    # Print all solutions ranked
    print("\n\n📊 All Solutions:")
    for eval_result in result.evaluation_results:
        print(f"\n#{eval_result.rank} {eval_result.response.agent_name} ({eval_result.average_score:.1f}/100)")
        if eval_result.response.code:
            print(f"Code: {eval_result.response.code[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
