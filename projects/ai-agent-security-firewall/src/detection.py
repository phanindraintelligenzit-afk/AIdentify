"""Core detection engine for AI Agent Security Firewall."""

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    BLOCK = "block"
    FLAG = "flag"
    LOG = "log"


class AttackType(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    DATA_EXFILTRATION = "data_exfiltration"
    ROLEPLAY_ATTACK = "roleplay_attack"
    INSTRUCTION_OVERRIDE = "instruction_override"


@dataclass
class DetectionResult:
    """Result of analyzing a single input."""
    is_malicious: bool
    attack_type: Optional[AttackType] = None
    confidence: float = 0.0
    matched_rules: list = field(default_factory=list)
    severity: Optional[Severity] = None
    explanation: str = ""
    action_taken: str = "allowed"


@dataclass
class ScanResult:
    """Aggregated result of a full scan."""
    input_text: str
    is_blocked: bool
    highest_severity: Optional[Severity] = None
    detections: list = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    processing_time_ms: float = 0.0


class DetectionRule:
    """Base class for detection rules."""

    def __init__(self, name: str, attack_type: AttackType, severity: Severity,
                 score_threshold: float = 0.7):
        self.name = name
        self.attack_type = attack_type
        self.severity = severity
        self.score_threshold = score_threshold
        self.enabled = True

    def evaluate(self, text: str) -> Optional[DetectionResult]:
        """Evaluate text against this rule. Return DetectionResult if triggered."""
        raise NotImplementedError


class PatternRule(DetectionRule):
    """Rule based on regex pattern matching."""

    def __init__(self, name: str, attack_type: AttackType, severity: Severity,
                 patterns: list[str], score_threshold: float = 0.7,
                 pattern_weights: Optional[list[float]] = None):
        super().__init__(name, attack_type, severity, score_threshold)
        self.patterns = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns]
        if pattern_weights is None:
            self.pattern_weights = [1.0] * len(patterns)
        else:
            self.pattern_weights = pattern_weights

    def evaluate(self, text: str) -> Optional[DetectionResult]:
        if not self.enabled:
            return None

        matches = []
        total_score = 0.0
        for pattern, weight in zip(self.patterns, self.pattern_weights):
            if pattern.search(text):
                matches.append(pattern.pattern)
                total_score += weight

        if not matches:
            return None

        # Normalize score to 0-1 range - each match contributes its weight
        # We use a more aggressive scoring: any single match = at least 0.5
        base_score = len(matches) / max(len(self.patterns) * 0.25, 1.0)
        weighted_bonus = total_score * 0.1
        confidence = min(base_score + weighted_bonus, 1.0)
        # Ensure at least 0.5 if any pattern matched
        confidence = max(confidence, 0.5)

        if confidence >= self.score_threshold:
            return DetectionResult(
                is_malicious=True,
                attack_type=self.attack_type,
                confidence=confidence,
                matched_rules=matches,
                severity=self.severity,
                explanation=f"Matched {len(matches)} pattern(s) for {self.attack_type.value}",
                action_taken=self.severity.value,
            )
        return None


class KeywordDensityRule(DetectionRule):
    """Rule based on keyword density analysis."""

    def __init__(self, name: str, attack_type: AttackType, severity: Severity,
                 keywords: list[str], score_threshold: float = 0.7,
                 window_size: int = 50):
        super().__init__(name, attack_type, severity, score_threshold)
        self.keywords = [kw.lower() for kw in keywords]
        self.window_size = window_size

    def evaluate(self, text: str) -> Optional[DetectionResult]:
        if not self.enabled:
            return None

        text_lower = text.lower()
        words = text_lower.split()
        if not words:
            return None

        matched = [kw for kw in self.keywords if kw in text_lower]
        keyword_count = len(matched)
        density = keyword_count / len(self.keywords)

        # Boost density for multiple keyword matches
        if keyword_count >= 3:
            density = max(density, 0.5)
        elif keyword_count >= 2:
            density = max(density, 0.35)

        if density >= self.score_threshold:
            matched = [kw for kw in self.keywords if kw in text_lower]
            return DetectionResult(
                is_malicious=True,
                attack_type=self.attack_type,
                confidence=min(density, 1.0),
                matched_rules=matched,
                severity=self.severity,
                explanation=f"High keyword density ({density:.2f}) for {self.attack_type.value}",
                action_taken=self.severity.value,
            )
        return None


class CompositeRule(DetectionRule):
    """Combines multiple sub-rules with weighted scoring."""

    def __init__(self, name: str, attack_type: AttackType, severity: Severity,
                 sub_rules: list[DetectionRule], score_threshold: float = 0.7):
        super().__init__(name, attack_type, severity, score_threshold)
        self.sub_rules = sub_rules

    def evaluate(self, text: str) -> Optional[DetectionResult]:
        if not self.enabled:
            return None

        all_matches = []
        total_confidence = 0.0

        for rule in self.sub_rules:
            result = rule.evaluate(text)
            if result:
                all_matches.extend(result.matched_rules)
                total_confidence += result.confidence

        if not all_matches:
            return None

        avg_confidence = total_confidence / len(self.sub_rules)
        # Boost confidence if multiple sub-rules matched
        boost = min(len(all_matches) * 0.1, 0.3)
        final_confidence = min(avg_confidence + boost, 1.0)

        if final_confidence >= self.score_threshold:
            return DetectionResult(
                is_malicious=True,
                attack_type=self.attack_type,
                confidence=final_confidence,
                matched_rules=all_matches,
                severity=self.severity,
                explanation=f"Composite rule triggered ({len(all_matches)} matches) for {self.attack_type.value}",
                action_taken=self.severity.value,
            )
        return None
