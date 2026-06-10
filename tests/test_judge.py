"""Tests for LLM-as-a-Judge."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from agentkit.eval.judge import LLMJudge, JudgeCriteria, JudgeResult, JudgeScore, DEFAULT_CRITERIA


class TestJudgeCriteria:
    def test_default_criteria_exist(self):
        assert len(DEFAULT_CRITERIA) >= 3
        names = [c.name for c in DEFAULT_CRITERIA]
        assert "accuracy" in names
        assert "completeness" in names

    def test_criteria_have_weights(self):
        for c in DEFAULT_CRITERIA:
            assert c.weight > 0
            assert c.max_score > 0


class TestJudgeScore:
    def test_normalized(self):
        s = JudgeScore(criterion="accuracy", score=8, max_score=10)
        assert s.normalized == 0.8

    def test_normalized_zero_max(self):
        s = JudgeScore(criterion="accuracy", score=0, max_score=0)
        assert s.normalized == 0.0

    def test_normalized_perfect(self):
        s = JudgeScore(criterion="accuracy", score=10, max_score=10)
        assert s.normalized == 1.0


class TestJudgeResult:
    def test_to_dict(self):
        result = JudgeResult(
            overall_score=0.85,
            scores=[
                JudgeScore(criterion="accuracy", score=8, max_score=10, reasoning="Good"),
            ],
            feedback="Nice work",
            passed=True,
        )
        d = result.to_dict()
        assert d["overall_score"] == 0.85
        assert d["passed"] is True
        assert len(d["scores"]) == 1


class TestLLMJudge:
    def test_init_defaults(self):
        judge = LLMJudge()
        assert judge.model == "openrouter/owl-alpha"
        assert judge.temperature == 0.0

    async def test_evaluate_with_mock(self):
        mock_client = AsyncMock()
        mock_client.chat.return_value = MagicMock(
            content='{"scores": [{"criterion": "accuracy", "score": 8, "reasoning": "Factually correct"}], "overall_score": 0.8, "feedback": "Good output", "passed": true}',
            total_tokens=100,
            cost_usd=0.0,
            latency_ms=500,
        )

        judge = LLMJudge(client=mock_client)
        result = await judge.evaluate(
            output="Test output",
            input_text="Test input",
            criteria=[JudgeCriteria("accuracy", "Is it accurate?", weight=1.0)],
            threshold=0.7,
        )

        assert result.overall_score > 0
        assert result.passed is True
        assert result.feedback == "Good output"
        assert len(result.scores) >= 1

    async def test_evaluate_handles_error(self):
        from agentkit.llm import LLMError
        mock_client = AsyncMock()
        mock_client.chat.side_effect = LLMError("API error")

        judge = LLMJudge(client=mock_client)
        result = await judge.evaluate(
            output="Test",
            criteria=[JudgeCriteria("accuracy", "test")],
        )

        assert result.overall_score == 0.0
        assert result.passed is False
        assert "API error" in result.feedback
