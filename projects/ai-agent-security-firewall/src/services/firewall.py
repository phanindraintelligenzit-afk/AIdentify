"""Firewall engine that orchestrates detection and enforcement."""

import logging
import time
from collections import defaultdict
from typing import Optional

import yaml

from src.detection import (
    DetectionResult, DetectionRule, ScanResult, Severity, AttackType
)
from src.rules import build_all_rules


logger = logging.getLogger("aisf.firewall")


class FirewallStats:
    """Thread-safe (for async single-thread) statistics tracker."""

    def __init__(self):
        self.total_requests: int = 0
        self.blocked_requests: int = 0
        self.flagged_requests: int = 0
        self.allowed_requests: int = 0
        self.attack_type_counts: dict = defaultdict(int)
        self.recent_blocks: list = []
        self.start_time: float = time.time()

    def record(self, result: ScanResult):
        self.total_requests += 1
        if result.is_blocked:
            self.blocked_requests += 1
        elif result.highest_severity == Severity.FLAG:
            self.flagged_requests += 1
        else:
            self.allowed_requests += 1

        for detection in result.detections:
            if detection.attack_type:
                self.attack_type_counts[detection.attack_type.value] += 1

        if result.is_blocked:
            self.recent_blocks.append({
                "timestamp": result.timestamp,
                "attack_types": [d.attack_type.value for d in result.detections if d.attack_type],
                "confidence": max((d.confidence for d in result.detections), default=0),
                "preview": result.input_text[:100] + ("..." if len(result.input_text) > 100 else ""),
            })
            # Keep only last 100 blocked entries
            if len(self.recent_blocks) > 100:
                self.recent_blocks = self.recent_blocks[-100:]

    def to_dict(self) -> dict:
        uptime = time.time() - self.start_time
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "flagged_requests": self.flagged_requests,
            "allowed_requests": self.allowed_requests,
            "block_rate": round(self.blocked_requests / max(self.total_requests, 1) * 100, 2),
            "attack_type_breakdown": dict(self.attack_type_counts),
            "recent_blocks": self.recent_blocks[-20:],
            "uptime_seconds": round(uptime, 2),
        }


class FirewallEngine:
    """Main firewall engine."""

    def __init__(self, config_path: Optional[str] = None):
        self.rules: list[DetectionRule] = build_all_rules()
        self.stats = FirewallStats()
        self.config = self._load_config(config_path)
        self._apply_config()

    def _load_config(self, config_path: Optional[str]) -> dict:
        if config_path is None:
            config_path = "config/settings.yaml"
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {}

    def _apply_config(self):
        """Apply configuration to rules."""
        fw_config = self.config.get("firewall", {})
        rules_config = fw_config.get("rules", {})

        for rule in self.rules:
            attack_key = rule.attack_type.value
            if attack_key in rules_config:
                rc = rules_config[attack_key]
                rule.enabled = rc.get("enabled", True)
                if "severity" in rc:
                    try:
                        rule.severity = Severity(rc["severity"])
                    except ValueError:
                        pass
                if "score_threshold" in rc:
                    rule.score_threshold = rc["score_threshold"]

    def scan(self, text: str) -> ScanResult:
        """Scan input text and return detection results."""
        start_time = time.time()
        detections: list[DetectionResult] = []

        for rule in self.rules:
            try:
                result = rule.evaluate(text)
                if result:
                    detections.append(result)
            except Exception as e:
                logger.error(f"Rule {rule.name} failed: {e}")

        # Determine action based on highest severity
        highest_severity = None
        is_blocked = False

        severity_order = {Severity.LOG: 0, Severity.FLAG: 1, Severity.BLOCK: 2}

        for detection in detections:
            if highest_severity is None or severity_order.get(detection.severity, 0) > severity_order.get(highest_severity, 0):
                highest_severity = detection.severity

            if detection.severity == Severity.BLOCK:
                is_blocked = True

        processing_time = (time.time() - start_time) * 1000

        scan_result = ScanResult(
            input_text=text,
            is_blocked=is_blocked,
            highest_severity=highest_severity,
            detections=detections,
            processing_time_ms=round(processing_time, 2),
        )

        self.stats.record(scan_result)

        if is_blocked:
            logger.warning(
                f"BLOCKED input ({len(detections)} detections, "
                f"highest confidence: {max((d.confidence for d in detections), default=0):.2f}): "
                f"{text[:100]}..."
            )
        elif detections:
            logger.info(
                f"FLAGGED input ({len(detections)} detections): {text[:100]}..."
            )

        return scan_result

    def get_stats(self) -> dict:
        return self.stats.to_dict()

    def get_health(self) -> dict:
        return {
            "status": "healthy",
            "rules_loaded": len(self.rules),
            "rules_enabled": sum(1 for r in self.rules if r.enabled),
            "version": "1.0.0",
        }
