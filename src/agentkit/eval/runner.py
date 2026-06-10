"""Evaluation framework for agents and pipelines."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from agentkit.models.pipeline import PipelineState


@dataclass
class EvalCase:
    """A single evaluation test case."""

    case_id: str
    input_text: str
    expected_output: dict[str, Any] = field(default_factory=dict)
    expected_behavior: str = ""
    constraints: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)  # happy_path | edge_case | failure


@dataclass
class EvalResult:
    """Result of running a single eval case."""

    case_id: str
    passed: bool = False
    score: float = 0.0
    actual_output: dict[str, Any] = field(default_factory=dict)
    expected_output: dict[str, Any] = field(default_factory=dict)
    feedback: str = ""
    pipeline_state: Optional[PipelineState] = None


@dataclass
class EvalSuite:
    """A collection of eval cases for an agent or pipeline."""

    name: str
    cases: list[EvalCase] = field(default_factory=list)
    baseline_score: float = 0.0
    pass_threshold: float = 0.8

    def add_case(self, case: EvalCase) -> None:
        self.cases.append(case)

    @property
    def case_count(self) -> int:
        return len(self.cases)


class EvalRunner:
    """Runs eval suites against agents or pipelines."""

    def __init__(self):
        self._suites: dict[str, EvalSuite] = {}
        self._results: list[EvalResult] = []

    def register_suite(self, suite: EvalSuite) -> None:
        self._suites[suite.name] = suite

    def get_suite(self, name: str) -> Optional[EvalSuite]:
        return self._suites.get(name)

    async def run_suite(
        self,
        suite_name: str,
        orchestrator_factory,  # Callable that returns an Orchestrator
    ) -> dict[str, Any]:
        """Run all cases in a suite.

        Returns a summary dict with pass rate, scores, and per-case results.
        """
        suite = self._suites.get(suite_name)
        if not suite:
            return {"error": f"Suite '{suite_name}' not found"}

        results = []
        for case in suite.cases:
            orchestrator = orchestrator_factory()
            state = await orchestrator.execute(
                case.input_text,
                constraints=case.constraints,
            )

            # Evaluate
            score = self._score_result(state, case)
            passed = score >= suite.pass_threshold

            result = EvalResult(
                case_id=case.case_id,
                passed=passed,
                score=score,
                actual_output=self._extract_output(state),
                expected_output=case.expected_output,
                feedback=self._generate_feedback(state, case, score),
                pipeline_state=state,
            )
            results.append(result)

        # Calculate summary
        passed_count = sum(1 for r in results if r.passed)
        total = len(results)
        avg_score = sum(r.score for r in results) / total if total else 0

        summary = {
            "suite": suite_name,
            "total_cases": total,
            "passed": passed_count,
            "failed": total - passed_count,
            "pass_rate": round(passed_count / total, 2) if total else 0,
            "average_score": round(avg_score, 3),
            "meets_baseline": avg_score >= suite.baseline_score,
            "results": [
                {
                    "case_id": r.case_id,
                    "passed": r.passed,
                    "score": r.score,
                    "feedback": r.feedback,
                }
                for r in results
            ],
        }

        self._results = results
        return summary

    def _score_result(self, state: PipelineState, case: EvalCase) -> float:
        """Score a pipeline result against expected output.

        Simple implementation: check if expected keys exist in output.
        In production, this would use LLM-as-a-Judge or semantic similarity.
        """
        if state.status == "failed":
            return 0.0

        # Get the last agent's output
        last_output = {}
        for result in state.agent_results.values():
            last_output = result.output

        if not case.expected_output:
            # No expected output defined — score based on completion
            return 1.0 if state.status == "completed" else 0.5

        # Check expected keys
        matched = 0
        total = len(case.expected_output)
        for key, expected_value in case.expected_output.items():
            if key in last_output:
                if str(last_output[key]) == str(expected_value):
                    matched += 1
                else:
                    matched += 0.5  # Partial credit for having the key

        return matched / total if total else 0.0

    def _extract_output(self, state: PipelineState) -> dict[str, Any]:
        """Extract the final output from a pipeline state."""
        for result in state.agent_results.values():
            if result.output:
                return result.output
        return {}

    def _generate_feedback(
        self, state: PipelineState, case: EvalCase, score: float
    ) -> str:
        if score >= 0.9:
            return "Excellent — output matches expected behavior"
        elif score >= 0.7:
            return "Good — minor deviations from expected"
        elif score >= 0.5:
            return "Partial — significant deviations"
        else:
            return "Failed — output does not match expected behavior"

    def check_regression(
        self, suite_name: str, new_score: float
    ) -> dict[str, Any]:
        """Check if a new score represents a regression from baseline."""
        suite = self._suites.get(suite_name)
        if not suite:
            return {"error": f"Suite '{suite_name}' not found"}

        baseline = suite.baseline_score
        regression = new_score < baseline
        delta = new_score - baseline

        return {
            "suite": suite_name,
            "baseline": baseline,
            "new_score": round(new_score, 3),
            "delta": round(delta, 3),
            "regression": regression,
            "action": "block" if regression else "allow",
        }
