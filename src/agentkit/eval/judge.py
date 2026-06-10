"""LLM-as-a-Judge evaluation scoring.

Uses an LLM to evaluate agent outputs against defined criteria,
providing structured scores and feedback instead of simple keyword matching.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

import structlog

from agentkit.llm import LLMClient, LLMError

logger = structlog.get_logger("agentkit.judge")


@dataclass
class JudgeCriteria:
    """A single evaluation criterion."""

    name: str
    description: str
    weight: float = 1.0  # Relative weight for this criterion
    max_score: int = 10


@dataclass
class JudgeScore:
    """Score for a single criterion."""

    criterion: str
    score: float  # 0 to max_score
    max_score: float
    reasoning: str = ""

    @property
    def normalized(self) -> float:
        """Return score normalized to 0-1."""
        if self.max_score == 0:
            return 0.0
        return self.score / self.max_score


@dataclass
class JudgeResult:
    """Complete evaluation result from the judge."""

    overall_score: float  # 0-1 normalized
    scores: list[JudgeScore] = field(default_factory=list)
    feedback: str = ""
    passed: bool = False
    confidence: float = 0.0
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "passed": self.passed,
            "feedback": self.feedback,
            "confidence": self.confidence,
            "scores": [
                {
                    "criterion": s.criterion,
                    "score": s.score,
                    "max_score": s.max_score,
                    "normalized": round(s.normalized, 3),
                    "reasoning": s.reasoning,
                }
                for s in self.scores
            ],
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
        }


# Default evaluation criteria
DEFAULT_CRITERIA = [
    JudgeCriteria("accuracy", "Is the information factually correct and free from hallucinations?", weight=3.0),
    JudgeCriteria("completeness", "Does the output cover all required aspects of the task?", weight=2.0),
    JudgeCriteria("clarity", "Is the output well-structured, clear, and easy to understand?", weight=2.0),
    JudgeCriteria("relevance", "Is the output directly relevant to the input/task?", weight=2.0),
    JudgeCriteria("actionability", "Does the output provide actionable insights or next steps?", weight=1.0),
]


class LLMJudge:
    """Uses an LLM to evaluate agent outputs against criteria.

    Usage:
        judge = LLMJudge()
        result = await judge.evaluate(
            output="The agent's output text...",
            input_text="The original task input...",
            criteria=DEFAULT_CRITERIA,
            threshold=0.7,
        )
        print(f"Score: {result.overall_score:.2f}, Passed: {result.passed}")
    """

    def __init__(
        self,
        client: LLMClient | None = None,
        model: str = "openrouter/owl-alpha",
        temperature: float = 0.0,
    ):
        self.client = client or LLMClient()
        self.model = model
        self.temperature = temperature

    async def evaluate(
        self,
        output: str,
        input_text: str = "",
        criteria: list[JudgeCriteria] | None = None,
        context: str = "",
        threshold: float = 0.7,
    ) -> JudgeResult:
        """Evaluate an output against criteria.

        Args:
            output: The agent output to evaluate
            input_text: The original task input
            criteria: Evaluation criteria (defaults to DEFAULT_CRITERIA)
            context: Additional context for the judge
            threshold: Score threshold for passing (0-1)

        Returns:
            JudgeResult with scores, feedback, and pass/fail
        """
        criteria = criteria or DEFAULT_CRITERIA

        # Build the evaluation prompt
        criteria_text = "\n".join(
            f"- {c.name} (weight: {c.weight}, max: {c.max_score}): {c.description}"
            for c in criteria
        )

        system_prompt = (
            "You are an expert evaluator. Your job is to evaluate the quality of an AI agent's "
            "output against specific criteria. Be fair, objective, and specific in your assessment.\n\n"
            "For each criterion, provide:\n"
            "1. A score (0 to max_score)\n"
            "2. A brief reasoning for the score\n\n"
            "Then provide an overall assessment.\n\n"
            "Respond with JSON in this exact format:\n"
            "{\n"
            "  \"scores\": [\n"
            "    {\"criterion\": \"name\", \"score\": N, \"reasoning\": \"...\"}\n"
            "  ],\n"
            "  \"overall_score\": 0.N,\n"
            "  \"feedback\": \"Overall feedback...\",\n"
            "  \"passed\": true\n"
            "}"
        )

        user_message = f"## Evaluation Criteria\n{criteria_text}\n\n"
        if input_text:
            user_message += f"## Original Task\n{input_text}\n\n"
        if context:
            user_message += f"## Additional Context\n{context}\n\n"
        user_message += f"## Agent Output to Evaluate\n\n{output}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            response = await self.client.chat(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            # Parse the JSON response
            try:
                data = json.loads(response.content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                data = json.loads(content.strip())

            # Build JudgeScore objects
            scores = []
            for s in data.get("scores", scores):
                # Find matching criterion for max_score
                criterion_name = s.get("criterion", "")
                max_score = 10
                for c in criteria:
                    if c.name == criterion_name:
                        max_score = c.max_score
                        break

                scores.append(JudgeScore(
                    criterion=criterion_name,
                    score=float(s.get("score", 0)),
                    max_score=float(max_score),
                    reasoning=s.get("reasoning", ""),
                ))

            # Calculate weighted overall score
            if scores:
                total_weight = sum(
                    next((c.weight for c in criteria if c.name == s.criterion), 1.0)
                    for s in scores
                )
                weighted_sum = sum(
                    s.normalized * next((c.weight for c in criteria if c.name == s.criterion), 1.0)
                    for s in scores
                )
                overall = weighted_sum / total_weight if total_weight > 0 else 0.0
            else:
                overall = data.get("overall_score", 0.0)

            passed = overall >= threshold

            return JudgeResult(
                overall_score=round(overall, 3),
                scores=scores,
                feedback=data.get("feedback", ""),
                passed=passed,
                confidence=0.85,
                tokens_used=response.total_tokens,
                cost_usd=response.cost_usd,
                latency_ms=response.latency_ms,
            )

        except (LLMError, json.JSONDecodeError, KeyError) as e:
            logger.error("judge_evaluation_error", error=str(e))
            return JudgeResult(
                overall_score=0.0,
                scores=[],
                feedback=f"Evaluation failed: {str(e)}",
                passed=False,
                confidence=0.0,
            )

    async def compare_outputs(
        self,
        output_a: str,
        output_b: str,
        input_text: str = "",
        criteria: list[JudgeCriteria] | None = None,
    ) -> dict[str, Any]:
        """Compare two outputs and determine which is better.

        Returns:
            Dict with winner ('A', 'B', or 'tie'), scores for both, and reasoning.
        """
        criteria = criteria or DEFAULT_CRITERIA

        criteria_text = "\n".join(f"- {c.name}: {c.description}" for c in criteria)

        system_prompt = (
            "You are an expert evaluator. Compare two AI agent outputs for the same task. "
            "Determine which is better overall and explain your reasoning.\n\n"
            "Respond with JSON:\n"
            "{\n"
            "  \"winner\": \"A\" | \"B\" | \"tie\",\n"
            "  \"score_A\": 0.N,\n"
            "  \"score_B\": 0.N,\n"
            "  \"reasoning\": \"...\"\n"
            "}"
        )

        user_message = f"## Criteria\n{criteria_text}\n\n"
        if input_text:
            user_message += f"## Task\n{input_text}\n\n"
        user_message += f"## Output A\n{output_a}\n\n## Output B\n{output_b}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            response = await self.client.chat(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                max_tokens=1500,
                response_format={"type": "json_object"},
            )
            data = json.loads(response.content)
            return {
                "winner": data.get("winner", "tie"),
                "score_a": data.get("score_A", 0.0),
                "score_b": data.get("score_B", 0.0),
                "reasoning": data.get("reasoning", ""),
            }
        except (LLMError, json.JSONDecodeError) as e:
            return {"winner": "tie", "score_a": 0, "score_b": 0, "reasoning": f"Error: {str(e)}"}
