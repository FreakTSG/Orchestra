"""Cross-evaluation system for agent responses."""

import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass

from agents.base import BaseAgent, AgentResponse
from dispatcher.parallel_dispatcher import ParallelDispatcher


@dataclass
class EvaluationResult:
    """Result of evaluating a single response."""
    response: AgentResponse
    scores: Dict[str, float]  # agent_name -> score
    average_score: float
    rank: int


class CrossEvaluator:
    """Evaluates agent responses by having them critique each other."""

    def __init__(self, dispatcher: ParallelDispatcher):
        """
        Initialize the cross-evaluator.

        Args:
            dispatcher: The dispatcher with agents to use for evaluation
        """
        self.dispatcher = dispatcher

    async def evaluate_responses(
        self,
        original_prompt: str,
        responses: List[AgentResponse]
    ) -> List[EvaluationResult]:
        """
        Have all agents evaluate all other agents' responses.

        Args:
            original_prompt: The original user prompt
            responses: List of responses to evaluate

        Returns:
            List of EvaluationResult objects, ranked by average score
        """
        if not responses:
            return []

        # If only one response, return it with a default score
        if len(responses) == 1:
            return [EvaluationResult(
                response=responses[0],
                scores={"self": 85.0},  # Default good score
                average_score=85.0,
                rank=1
            )]

        # Create evaluation matrix
        evaluation_matrix = await self._create_evaluation_matrix(
            original_prompt,
            responses
        )

        # Calculate average scores and ranks
        results = self._calculate_results(responses, evaluation_matrix)

        # Sort by average score (descending)
        results.sort(key=lambda x: x.average_score, reverse=True)

        # Assign ranks
        for i, result in enumerate(results, 1):
            result.rank = i

        return results

    async def _create_evaluation_matrix(
        self,
        original_prompt: str,
        responses: List[AgentResponse]
    ) -> Dict[str, Dict[str, float]]:
        """
        Create a matrix of evaluations.

        Returns:
            Dict where keys are response indices and values are dicts of evaluator -> score
        """
        matrix = {}

        for i, response_to_eval in enumerate(responses):
            matrix[str(i)] = {}

            # Get other responses for comparison
            other_responses = [r for j, r in enumerate(responses) if j != i]

            # Have each agent evaluate this response
            for agent in self.dispatcher.agents:
                try:
                    # Skip if this is the agent that generated the response
                    if agent.name.lower() == response_to_eval.agent_name.lower():
                        continue

                    score = await agent.evaluate(
                        original_prompt,
                        response_to_eval,
                        other_responses
                    )

                    matrix[str(i)][agent.name] = score

                except Exception as e:
                    print(f"Error in evaluation by {agent.name}: {e}")
                    matrix[str(i)][agent.name] = 50.0  # Neutral score on error

        return matrix

    def _calculate_results(
        self,
        responses: List[AgentResponse],
        evaluation_matrix: Dict[str, Dict[str, float]]
    ) -> List[EvaluationResult]:
        """Calculate average scores from evaluation matrix."""
        results = []

        for i, response in enumerate(responses):
            scores = evaluation_matrix.get(str(i), {})

            if scores:
                avg_score = sum(scores.values()) / len(scores)
            else:
                # No evaluations (e.g., only one agent)
                avg_score = 75.0  # Default middle score

            results.append(EvaluationResult(
                response=response,
                scores=scores,
                average_score=avg_score,
                rank=0  # Will be assigned later
            ))

        return results

    def get_best_solution(self, evaluation_results: List[EvaluationResult]) -> EvaluationResult:
        """
        Get the best solution from evaluation results.

        Args:
            evaluation_results: List of evaluation results (should be ranked)

        Returns:
            The EvaluationResult with the highest rank
        """
        if not evaluation_results:
            raise ValueError("No evaluation results available")

        # Results should already be ranked, but sort to be sure
        sorted_results = sorted(
            evaluation_results,
            key=lambda x: x.average_score,
            reverse=True
        )

        return sorted_results[0]

    def format_evaluation_summary(self, evaluation_results: List[EvaluationResult]) -> str:
        """Format evaluation results as a readable summary."""
        if not evaluation_results:
            return "No evaluation results available."

        lines = [
            "\n📊 Cross-Evaluation Results:",
            "=" * 60
        ]

        for result in evaluation_results:
            medal = "🥇" if result.rank == 1 else "🥈" if result.rank == 2 else "🥉" if result.rank == 3 else "  "

            lines.append(f"\n{medal} Rank #{result.rank}: {result.response.agent_name}")
            lines.append(f"   Average Score: {result.average_score:.1f}/100")

            if result.scores:
                lines.append("   Individual Scores:")
                for evaluator, score in result.scores.items():
                    lines.append(f"     - {evaluator}: {score:.1f}/100")

            lines.append(f"   Latency: {result.response.latency_ms}ms" if result.response.latency_ms else "")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)
