"""
Risk Score Calculator — Computes composite risk scores for audit events.

Provides the RiskScorer class which calculates a 0-100 risk score
based on triggered compliance rules, event metadata, and configurable
weighting strategies.

Usage:
    from compliance.risk_scorer import RiskScorer
    scorer = RiskScorer()
    score = scorer.calculate(triggered_rules, event)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from compliance.models import AuditEvent
from compliance.rules_engine import (
    EvaluationResult,
    Severity,
    SEVERITY_WEIGHTS,
    TriggeredRule,
)


class RiskScorer:
    """
    Calculates composite risk scores (0-100) for audit events.

    The scoring algorithm considers:
    - Severity of triggered rules (critical > violation > warning > info)
    - Number of triggered rules (with diminishing returns)
    - Event's base risk_score field
    - Presence of auto-block rules
    - Confidence score (lower confidence = higher risk)
    - Data classification of accessed sources
    """

    # Default weights for the scoring components
    DEFAULT_WEIGHTS = {
        "triggered_rules": 0.50,
        "base_risk": 0.20,
        "confidence_penalty": 0.15,
        "data_classification": 0.15,
    }

    # Data classification risk multipliers
    CLASSIFICATION_MULTIPLIER = {
        "public": 0.0,
        "internal": 0.3,
        "confidential": 0.7,
        "restricted": 1.0,
    }

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        max_score: float = 100.0,
    ):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.max_score = max_score

    # ------------------------------------------------------------------
    # Main scoring method
    # ------------------------------------------------------------------

    def calculate(
        self,
        triggered_rules: List[TriggeredRule],
        event: AuditEvent,
    ) -> float:
        """
        Calculate the overall risk score for an event given its triggered rules.

        Args:
            triggered_rules: List of rules triggered by the event.
            event: The audit event being scored.

        Returns:
            Risk score from 0.0 to 100.0.
        """
        if not triggered_rules and event.risk_score == 0:
            return 0.0

        # Component 1: Triggered rules score (0-100)
        rules_score = self._score_triggered_rules(triggered_rules)

        # Component 2: Base risk from event (0-100)
        base_risk = event.risk_score

        # Component 3: Confidence penalty (0-100)
        confidence_score = self._score_confidence(event)

        # Component 4: Data classification score (0-100)
        classification_score = self._score_data_classification(event)

        # Weighted combination
        combined = (
            self.weights["triggered_rules"] * rules_score
            + self.weights["base_risk"] * base_risk
            + self.weights["confidence_penalty"] * confidence_score
            + self.weights["data_classification"] * classification_score
        )

        # Auto-block bonus: if any rule has auto_block, add a floor
        if any(r.auto_block for r in triggered_rules):
            combined = max(combined, 30.0)

        # Critical bonus: each critical rule adds significant score (min 75 for any critical)
        critical_count = sum(1 for r in triggered_rules if r.severity == Severity.CRITICAL)
        if critical_count > 0:
            combined += 35.0 * critical_count
            combined = max(combined, 75.0)  # minimum 75 for any critical event

        return min(self.max_score, round(combined, 2))

    # ------------------------------------------------------------------
    # Evaluation result convenience method
    # ------------------------------------------------------------------

    def calculate_from_result(self, result: EvaluationResult) -> float:
        """
        Recalculate risk score from an EvaluationResult.

        This allows re-scoring with a different weighting strategy
        without re-running rule evaluation.
        """
        # We need the original event; if not stored, return existing score
        return result.risk_score

    # ------------------------------------------------------------------
    # Component scoring methods
    # ------------------------------------------------------------------

    def _score_triggered_rules(self, triggered_rules: List[TriggeredRule]) -> float:
        """
        Score based on triggered rules with diminishing returns.

        Each severity level contributes its weight, with subsequent
        rules of the same severity getting half the previous weight.
        """
        if not triggered_rules:
            return 0.0

        score = 0.0
        severity_counts: Dict[Severity, int] = {}
        for rule in triggered_rules:
            severity_counts[rule.severity] = severity_counts.get(rule.severity, 0) + 1

        for sev, count in severity_counts.items():
            weight = SEVERITY_WEIGHTS.get(sev, 5)
            for i in range(count):
                score += weight * (0.5 ** i)

        return min(100.0, score)

    def _score_confidence(self, event: AuditEvent) -> float:
        """
        Penalty for low confidence scores.

        Returns 0 for high confidence, up to 100 for zero confidence.
        """
        confidence = event.confidence_score
        if confidence is None:
            confidence = event.output_summary.confidence_score
        if confidence is None:
            return 50.0  # unknown confidence = moderate risk

        # Invert: low confidence -> high risk
        return (1.0 - confidence) * 100.0

    def _score_data_classification(self, event: AuditEvent) -> float:
        """
        Score based on the highest data classification accessed.
        """
        if event.data_lineage is None:
            return 0.0

        max_multiplier = 0.0
        for src in event.data_lineage.sources_accessed:
            classification = src.data_classification
            if classification is None:
                continue
            mult = self.CLASSIFICATION_MULTIPLIER.get(classification, 0.0)
            max_multiplier = max(max_multiplier, mult)

        return max_multiplier * 100.0

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    @staticmethod
    def risk_level(score: float) -> str:
        """
        Convert a numeric risk score to a human-readable level.

        Returns one of: "low", "medium", "high", "critical"
        """
        if score < 25:
            return "low"
        elif score < 50:
            return "medium"
        elif score < 75:
            return "high"
        else:
            return "critical"

    @staticmethod
    def should_auto_block(score: float, triggered_rules: List[TriggeredRule]) -> bool:
        """
        Determine if an event should be auto-blocked based on score and rules.
        """
        if score >= 75:
            return True
        if any(r.severity == Severity.CRITICAL for r in triggered_rules):
            return True
        return False

    @staticmethod
    def requires_human_review(
        score: float, triggered_rules: List[TriggeredRule]
    ) -> bool:
        """
        Determine if an event requires immediate human review.
        """
        if score >= 70:
            return True
        if any(r.severity == Severity.CRITICAL for r in triggered_rules):
            return True
        if any(r.severity == Severity.VIOLATION for r in triggered_rules):
            return True
        return False
