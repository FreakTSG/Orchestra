"""Main orchestration class that coordinates all components."""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from agents.base import BaseAgent, AgentResponse
from dispatcher.parallel_dispatcher import ParallelDispatcher
from evaluator.cross_evaluator import CrossEvaluator, EvaluationResult
from config.settings import settings


@dataclass
class QueryResult:
    """Result of a multi-agent query."""
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

    def get_all_solutions Ranked(self) -> List[EvaluationResult]:
        """Get all solutions sorted by rank."""
        return sorted(self.evaluation_results, key=lambda x: x.rank)


class MultiAgentCoder:
    """Main orchestration class for multi-agent coding."""

    def __init__(
        self,
        agents: Optional[List[BaseAgent]] = None,
        max_questions: int = 3
    ):
        """
        Initialize the multi-agent coder.

        Args:
            agents: Optional list of specific agents to use
            max_questions: Maximum number of clarifying questions to ask
        """
        settings.validate()

        self.dispatcher = ParallelDispatcher(agents)
        self.evaluator = CrossEvaluator(self.dispatcher)
        self.max_questions = max_questions
        self.enhancer_agent = self._get_enhancer_agent()

    def _get_enhancer_agent(self) -> BaseAgent:
        """Get the first available agent for prompt enhancement."""
        if not self.dispatcher.agents:
            raise ValueError("No agents available")
        return self.dispatcher.agents[0]

    async def query(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        skip_enhancement: bool = False,
        predefined_answers: Optional[Dict[str, str]] = None
    ) -> QueryResult:
        """
        Execute a multi-agent query with prompt enhancement.

        Args:
            prompt: The user's prompt
            context: Optional context information
            skip_enhancement: If True, skip prompt enhancement
            predefined_answers: Predefined answers to clarifying questions

        Returns:
            QueryResult with all responses and evaluations
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

        # Step 2: Dispatch to all agents
        print(f"\n🚀 Dispatching to {len(self.dispatcher.agents)} agents...")
        responses = await self.dispatcher.dispatch_all(enhanced_prompt, context)

        # Step 3: Cross-evaluate responses
        print("\n📊 Cross-evaluating responses...")
        evaluation_results = await self.evaluator.evaluate_responses(
            enhanced_prompt,
            responses
        )

        # Step 4: Get best solution
        best_result = self.evaluator.get_best_solution(evaluation_results)

        return QueryResult(
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
                "total_latency_ms": sum(r.latency_ms or 0 for r in responses),
                "total_tokens": sum(r.tokens_used or 0 for r in responses),
            }
        )

    async def _enhance_prompt(
        self,
        initial_prompt: str,
        predefined_answers: Optional[Dict[str, str]] = None
    ) -> Tuple[List[str], Dict[str, str], str]:
        """
        Enhance the prompt by asking clarifying questions.

        Args:
            initial_prompt: The initial user prompt
            predefined_answers: Optional predefined answers

        Returns:
            Tuple of (questions, answers, enhanced_prompt)
        """
        print("\n🔍 Enhancing prompt...")

        # Generate questions
        questions, enhanced_template = await self.enhancer_agent.enhance_prompt(
            initial_prompt,
            self.max_questions
        )

        if not questions:
            return [], {}, initial_prompt

        # Get answers (either predefined or from user)
        if predefined_answers:
            answers = predefined_answers
        else:
            # For CLI usage, you'd implement interactive input here
            # For now, use empty answers
            answers = {q: "" for q in questions}

        # Build enhanced prompt
        enhanced = f"""Enhanced Request:

Original: {initial_prompt}

Additional Context:
"""
        for i, (question, answer) in enumerate(zip(questions, answers.values()), 1):
            enhanced += f"{i}. Q: {question}\n   A: {answer}\n"

        enhanced += f"\nTask: {initial_prompt}"

        return questions, answers, enhanced

    async def compare_agents(
        self,
        prompts: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[AgentResponse]]:
        """
        Compare agents across multiple prompts.

        Args:
            prompts: List of prompts to test
            context: Optional context

        Returns:
            Dict mapping agent names to their responses
        """
        results = {agent.name: [] for agent in self.dispatcher.agents}

        for prompt in prompts:
            responses = await self.dispatcher.dispatch_all(prompt, context)
            for response in responses:
                results[response.agent_name].append(response)

        return results

    def get_available_agents(self) -> List[str]:
        """Get list of available agent names."""
        return self.dispatcher.get_available_agents()

    def add_agent(self, agent: BaseAgent) -> None:
        """Add a new agent."""
        self.dispatcher.add_agent(agent)

    def remove_agent(self, agent_name: str) -> bool:
        """Remove an agent by name."""
        return self.dispatcher.remove_agent(agent_name)
