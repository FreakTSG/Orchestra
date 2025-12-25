"""Example of using the Multi-Agent Coder API."""

import requests
import json
import time


# API base URL (adjust if running on different host/port)
BASE_URL = "http://localhost:8000"


def check_health():
    """Check if the API is running."""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health Check: {response.json()}")
    return response.status_code == 200


def list_agents():
    """List available agents."""
    response = requests.get(f"{BASE_URL}/agents")
    data = response.json()
    print(f"\nAvailable Agents: {data['agents']}")
    return data['agents']


def enhance_prompt(prompt: str):
    """Get clarifying questions for a prompt."""
    response = requests.post(
        f"{BASE_URL}/enhance",
        json={"prompt": prompt, "max_questions": 3}
    )

    data = response.json()

    print(f"\n🔍 Clarifying Questions for: '{prompt}'")
    for i, q in enumerate(data['questions'], 1):
        print(f"{i}. {q['question']}")

    return data


def query_agents(prompt: str, skip_enhancement: bool = False):
    """Query all agents and get ranked results."""
    print(f"\n🚀 Querying agents for: '{prompt}'")
    print("Please wait...\n")

    start_time = time.time()

    response = requests.post(
        f"{BASE_URL}/query",
        json={
            "prompt": prompt,
            "skip_enhancement": skip_enhancement
        }
    )

    elapsed = time.time() - start_time
    data = response.json()

    print(f"✅ Query completed in {elapsed:.2f} seconds\n")

    # Display best solution
    print("="*60)
    print("🏆 BEST SOLUTION")
    print("="*60)
    print(f"Agent: {data['best_solution']['agent_name']}")
    print(f"Latency: {data['best_solution']['latency_ms']}ms")

    if data['best_solution']['explanation']:
        print(f"\nExplanation:\n{data['best_solution']['explanation']}")

    if data['best_solution']['code']:
        print(f"\nCode:\n{data['best_solution']['code']}")

    # Display ranked solutions
    print(f"\n{'='*60}")
    print("📊 ALL SOLUTIONS RANKED")
    print(f"{'='*60}")

    for sol in data['all_solutions']:
        medal = "🥇" if sol['rank'] == 1 else "🥈" if sol['rank'] == 2 else "🥉"
        print(f"\n{medal} Rank #{sol['rank']}: {sol['agent_name']}")
        print(f"   Score: {sol['average_score']:.1f}/100")

        if sol['individual_scores']:
            print("   Peer Evaluations:")
            for evaluator, score in sol['individual_scores'].items():
                print(f"     - {evaluator}: {score:.1f}/100")

    # Metadata
    print(f"\n{'='*60}")
    print("METADATA")
    print(f"{'='*60}")
    for key, value in data['metadata'].items():
        print(f"{key}: {value}")

    return data


def main():
    """Run API examples."""
    print("🤖 Multi-Agent Coder API Client\n")

    # Check health
    if not check_health():
        print("❌ API is not running. Please start it with: python api.py")
        return

    # List agents
    agents = list_agents()

    # Example 1: Simple query
    print("\n" + "="*60)
    print("EXAMPLE 1: Simple Query")
    print("="*60)

    query_agents(
        "Implement a function to reverse a linked list in Python"
    )

    # Example 2: Prompt enhancement
    print("\n\n" + "="*60)
    print("EXAMPLE 2: Prompt Enhancement")
    print("="*60)

    enhance_prompt("Optimize my database")

    # Example 3: Query with context
    print("\n\n" + "="*60)
    print("EXAMPLE 3: Query with Context")
    print("="*60)

    response = requests.post(
        f"{BASE_URL}/query",
        json={
            "prompt": "Add error handling",
            "context": {
                "language": "Python",
                "framework": "FastAPI",
                "current_code": "def process_data(data): return data.upper()"
            }
        }
    )

    data = response.json()
    print(f"\nBest solution from: {data['best_solution']['agent_name']}")
    print(f"Code:\n{data['best_solution']['code']}")


if __name__ == "__main__":
    main()
