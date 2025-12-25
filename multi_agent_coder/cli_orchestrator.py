"""Main orchestration class for CLI-based multi-agent coding system."""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from agents.base_cli import BaseCLIAgent, AgentResponse
from dispatcher.cli_dispatcher import CLIDispatcher
from evaluator.cross_evaluator import CrossEvaluator, EvaluationResult


@dataclass
class CLIQueryResult:
    """Result of a CLI-based multi-agent query."""
    original_prompt: str
    enhanced_prompt: str
    clarifying_questions: List[str]
    user_answers: Dict[str, str]
    all_responses: List[AgentResponse]
    evaluation_results: List[EvaluationResult]
    best_response: AgentResponse
    metadata: Dict[str, Any]

    def get_solution_by_rank(self, rank: int) -> Optional[EvaluationResult]:
        """Get solution by rank (1-based)."""
        for result in self.evaluation_results:
            if result.rank == rank:
                return result
        return None


class MultiAgentCLICoder:
    """Main orchestration class for CLI-based multi-agent coding (NO API KEYS NEEDED!)."""

    def __init__(
        self,
        agents: Optional[List[BaseCLIAgent]] = None,
        max_questions: int = 3,
        auto_detect: bool = True
    ):
        """
        Initialize the CLI-based multi-agent coder.

        Args:
            agents: Optional list of specific CLI agents
            max_questions: Maximum number of clarifying questions
            auto_detect: Auto-detect available CLI tools
        """
        self.dispatcher = CLIDispatcher(agents, auto_detect=auto_detect)

        # Use the CLI dispatcher for cross-evaluation too
        # (CLI agents evaluate each other)
        self.evaluator = CLIOrchestratorCrossEvaluator(self.dispatcher)

        self.max_questions = max_questions
        self.enhancer_agent = self._get_enhancer_agent()

        # Validate we have at least one agent
        if not self.dispatcher.agents:
            raise ValueError(
                "No CLI agents detected! Please install at least one AI CLI tool:\n"
                "  - Claude: irm https://claude.ai/install.ps1 | iex (Windows)\n"
                "           curl https://claude.ai/install.sh | sh (Linux/Mac)\n"
                "  - OpenAI Codex: npm i -g @openai/codex\n"
                "  - Gemini: npm install -g @google/gemini-cli\n"
                "Or configure custom CLI tools in .env file"
            )

    def _get_enhancer_agent(self) -> BaseCLIAgent:
        """Get the first available agent for prompt enhancement."""
        return self.dispatcher.agents[0]

    async def query(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        skip_enhancement: bool = False,
        predefined_answers: Optional[Dict[str, str]] = None
    ) -> CLIQueryResult:
        """
        Execute a multi-agent query using CLI tools.

        Args:
            prompt: The user's prompt
            context: Optional context information
            skip_enhancement: Skip prompt enhancement
            predefined_answers: Predefined answers to clarifying questions

        Returns:
            CLIQueryResult with all responses and evaluations
        """
        # Step 1: Enhance prompt (unless skipped)
        if skip_enhancement:
            enhanced_prompt = prompt
            clarifying_questions = []
            user_answers = predefined_answers or {}
        else:
            clarifying_questions, user_answers, enhanced_prompt = await self._enhance_prompt(
                prompt,
                predefined_answers
            )

        # Step 2: Dispatch to all CLI agents
        print(f"\n🚀 Dispatching to {len(self.dispatcher.agents)} CLI agent(s)...")
        responses = await self.dispatcher.dispatch_all(enhanced_prompt, context)

        # Step 3: Cross-evaluate responses
        print("\n📊 Cross-evaluating responses...")
        evaluation_results = await self.evaluator.evaluate_responses(
            enhanced_prompt,
            responses
        )

        # Step 4: Get best solution
        best_result = self.evaluator.get_best_solution(evaluation_results)

        return CLIQueryResult(
            original_prompt=prompt,
            enhanced_prompt=enhanced_prompt,
            clarifying_questions=clarifying_questions,
            user_answers=user_answers,
            all_responses=responses,
            evaluation_results=evaluation_results,
            best_response=best_result.response,
            metadata={
                "num_agents": len(self.dispatcher.agents),
                "num_questions": len(clarifying_questions),
                "total_time_ms": sum(r.execution_time_ms or 0 for r in responses),
            }
        )

    async def _enhance_prompt(
        self,
        initial_prompt: str,
        predefined_answers: Optional[Dict[str, str]] = None
    ) -> Tuple[List[str], Dict[str, str], str]:
        """Enhance prompt by asking clarifying questions."""
        print("\n🔍 Enhancing prompt...")

        # Generate questions
        questions, enhanced_template = await self.enhancer_agent.enhance_prompt(
            initial_prompt,
            self.max_questions
        )

        if not questions:
            return [], {}, initial_prompt

        # Get answers
        if predefined_answers:
            answers = predefined_answers
        else:
            # For CLI usage, you'd implement interactive input here
            answers = {q: "" for q in questions}

        # Build enhanced prompt
        enhanced = f"""Enhanced Request:

Original: {initial_prompt}

Additional Context:
"""
        for question, answer in zip(questions, answers.values()):
            enhanced += f"Q: {question}\nA: {answer}\n"

        enhanced += f"\nTask: {initial_prompt}"

        return questions, answers, enhanced

    def get_available_agents(self) -> List[str]:
        """Get list of available agent names."""
        return self.dispatcher.get_available_agents()

    def add_agent(self, agent: BaseCLIAgent) -> None:
        """Add a new agent."""
        self.dispatcher.add_agent(agent)

    def print_agent_info(self):
        """Print information about available agents."""
        self.dispatcher.print_agent_status()


class CLIOrchestratorCrossEvaluator:
    """Cross-evaluator that works with CLI-based agents."""

    def __init__(self, dispatcher: CLIDispatcher):
        self.dispatcher = dispatcher

    async def evaluate_responses(
        self,
        original_prompt: str,
        responses: List[AgentResponse]
    ) -> List[EvaluationResult]:
        """Have all CLI agents evaluate all other responses."""
        if not responses:
            return []

        if len(responses) == 1:
            from evaluator.cross_evaluator import EvaluationResult
            return [EvaluationResult(
                response=responses[0],
                scores={"self": 85.0},
                average_score=85.0,
                rank=1
            )]

        # Create evaluation matrix
        evaluation_matrix = await self._create_evaluation_matrix(
            original_prompt,
            responses
        )

        # Calculate results
        results = self._calculate_results(responses, evaluation_matrix)
        results.sort(key=lambda x: x.average_score, reverse=True)

        for i, result in enumerate(results, 1):
            result.rank = i

        return results

    async def _create_evaluation_matrix(
        self,
        original_prompt: str,
        responses: List[AgentResponse]
    ) -> Dict[str, Dict[str, float]]:
        """Create evaluation matrix."""
        matrix = {}

        for i, response_to_eval in enumerate(responses):
            matrix[str(i)] = {}

            other_responses = [r for j, r in enumerate(responses) if j != i]

            for agent in self.dispatcher.agents:
                # Skip if this is the agent that generated the response
                if agent.name.lower() == response_to_eval.agent_name.lower():
                    continue

                try:
                    score = await agent.evaluate(
                        original_prompt,
                        response_to_eval,
                        other_responses
                    )

                    matrix[str(i)][agent.name] = score

                except Exception:
                    matrix[str(i)][agent.name] = 50.0

        return matrix

    def _calculate_results(
        self,
        responses: List[AgentResponse],
        evaluation_matrix: Dict[str, Dict[str, float]]
    ) -> List:
        """Calculate results from evaluation matrix."""
        from evaluator.cross_evaluator import EvaluationResult

        results = []

        for i, response in enumerate(responses):
            scores = evaluation_matrix.get(str(i), {})

            if scores:
                avg_score = sum(scores.values()) / len(scores)
            else:
                avg_score = 75.0

            results.append(EvaluationResult(
                response=response,
                scores=scores,
                average_score=avg_score,
                rank=0
            ))

        return results

    def get_best_solution(self, evaluation_results: List):
        """Get best solution."""
        if not evaluation_results:
            raise ValueError("No evaluation results")

        sorted_results = sorted(
            evaluation_results,
            key=lambda x: x.average_score,
            reverse=True
        )

        return sorted_results[0]
