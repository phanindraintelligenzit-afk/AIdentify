"""
Audit Logger — Core logging logic for AI agent decisions.

Creates schema-conforming audit events with UUIDv7 event IDs,
SHA-256 prompt hashing, PII detection, and risk scoring.
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from compliance.models import (
    ActionType,
    AuditEvent,
    ConsentFlags,
    ConsentType,
    DataClassification,
    DataLineage,
    InputSummary,
    OutputSummary,
)
from compliance.pii_detector import calculate_pii_risk, scan_text
from compliance.storage import SQLiteStorage

logger = logging.getLogger(__name__)


def _generate_uuid7() -> str:
    """
    Generate a UUIDv7-like identifier.

    Uses timestamp-based UUID with random suffix for uniqueness.
    Format: 01978d2e-4a2b-7c3d-8e9f-0a1b2c3d4e5f style.
    """
    # UUIDv7: timestamp_ms (48 bits) + version (4 bits=0111) + variant + random
    now = datetime.now(timezone.utc)
    ts_ms = int(now.timestamp() * 1000)

    # Build UUIDv7 structure (8-4-4-4-12 format)
    time_hex = f"{ts_ms:012x}"
    rand_part = uuid4().hex
    uuid_str = (
        f"{time_hex[0:8]}-{time_hex[8:12]}-7{rand_part[0:8]}-"
        f"{rand_part[8:12]}{rand_part[12:16]}-{rand_part[16:20]}{rand_part[20:32]}"
    )
    return uuid_str


def _hash_text(text: str) -> str:
    """Compute SHA-256 hash of text, return as hex string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _estimate_token_count(text: str) -> int:
    """
    Estimate token count for a text string.
    
    Uses a simple heuristic: ~4 characters per token for English text.
    For production, use the specific model's tokenizer.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def _compute_risk_score(
    input_pii_types: List[str],
    output_pii_types: List[str],
    confidence: Optional[float],
    action_type: ActionType,
) -> float:
    """
    Compute composite risk score (0-100).

    Factors:
    - PII detected in output (highest weight)
    - PII detected in input
    - Low confidence score
    - High-stakes action types
    """
    score = 0.0

    # PII in output is highest risk
    if output_pii_types:
        score += calculate_pii_risk(output_pii_types) * 1.5

    # PII in input
    if input_pii_types:
        score += calculate_pii_risk(input_pii_types)

    # Low confidence increases risk
    if confidence is not None and confidence < 0.7:
        score += (0.7 - confidence) * 30

    # High-stakes actions
    high_stakes = {ActionType.APPROVE, ActionType.REJECT, ActionType.ESCALATE, ActionType.DECISION}
    if action_type in high_stakes:
        score += 10

    return min(score, 100.0)


class AuditLogger:
    """
    Core audit logger that creates and stores compliance events.

    Usage:
        storage = SQLiteStorage()
        audit = AuditLogger(storage=storage)
        event = audit.log_decision(
            agent_name="my-agent",
            action_type=ActionType.DECISION,
            input_text="user prompt",
            output_text="agent response",
            model_version="gpt-4o-2024-08-06",
        )
    """

    def __init__(
        self,
        storage: Optional[SQLiteStorage] = None,
        agent_name: str = "default-agent",
        model_version: str = "unknown",
        model_provider: str = "unknown",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        environment: str = "production",
        consent_flags: Optional[ConsentFlags] = None,
        data_lineage: Optional[DataLineage] = None,
    ):
        """
        Initialize the audit logger.

        Args:
            storage: SQLiteStorage instance. Creates default if None.
            agent_name: Default agent name for events.
            model_version: Default model version string.
            model_provider: Model provider name.
            user_id: Default user ID.
            session_id: Session identifier.
            environment: Deployment environment.
            consent_flags: Default consent flags for events.
            data_lineage: Default data lineage info.
        """
        self.storage = storage or SQLiteStorage()
        self.agent_name = agent_name
        self.model_version = model_version
        self.model_provider = model_provider
        self.user_id = user_id
        self.session_id = session_id
        self.environment = environment
        self.consent_flags = consent_flags
        self.data_lineage = data_lineage

    def log_decision(
        self,
        action_type: ActionType,
        input_text: str,
        output_text: str,
        agent_name: Optional[str] = None,
        model_version: Optional[str] = None,
        user_id: Optional[str] = None,
        confidence_score: Optional[float] = None,
        decision_summary: Optional[str] = None,
        rationale: Optional[str] = None,
        input_classification: Optional[DataClassification] = None,
        data_sources: Optional[List[str]] = None,
        consent_flags: Optional[ConsentFlags] = None,
        data_lineage: Optional[DataLineage] = None,
        latency_ms: Optional[int] = None,
        cost_usd: Optional[float] = None,
        metadata: Optional[Dict[str, str]] = None,
        compliance_tags: Optional[List[str]] = None,
    ) -> AuditEvent:
        """
        Log a single agent decision as an immutable audit event.

        Args:
            action_type: The type of action performed.
            input_text: The input/prompt text.
            output_text: The output/response text.
            agent_name: Agent name (overrides default).
            model_version: Model version (overrides default).
            user_id: User ID (overrides default).
            confidence_score: Model confidence (0.0-1.0).
            decision_summary: Human-readable decision summary.
            rationale: Explanation of the decision.
            input_classification: Data classification of input.
            data_sources: List of data source identifiers.
            consent_flags: Consent flags (overrides default).
            data_lineage: Data lineage (overrides default).
            latency_ms: Decision latency in milliseconds.
            cost_usd: Estimated cost in USD.
            metadata: Additional metadata key-value pairs.
            compliance_tags: EU AI Act article tags.

        Returns:
            The created AuditEvent.
        """
        # Scan for PII
        input_pii = scan_text(input_text)
        output_pii = scan_text(output_text)

        # Compute token counts
        input_tokens = _estimate_token_count(input_text)
        output_tokens = _estimate_token_count(output_text)

        # Compute risk score
        risk_score = _compute_risk_score(
            input_pii.pii_types,
            output_pii.pii_types,
            confidence_score,
            action_type,
        )

        # Build input summary
        input_summary = InputSummary(
            prompt_hash=_hash_text(input_text),
            input_length_tokens=input_tokens,
            input_classification=input_classification,
            pii_detected=input_pii.pii_detected,
            pii_types=input_pii.pii_types if input_pii.pii_detected else [],
            data_sources=data_sources,
        )

        # Build output summary
        output_summary = OutputSummary(
            output_hash=_hash_text(output_text),
            output_length_tokens=output_tokens,
            decision=decision_summary or output_text[:512],
            rationale=rationale,
            pii_detected=output_pii.pii_detected,
            pii_types=output_pii.pii_types if output_pii.pii_detected else [],
            confidence_score=confidence_score,
        )

        # Build the audit event
        event = AuditEvent(
            event_id=_generate_uuid7(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_name=agent_name or self.agent_name,
            action_type=action_type,
            input_summary=input_summary,
            output_summary=output_summary,
            model_version=model_version or self.model_version,
            risk_score=risk_score,
            confidence_score=confidence_score,
            model_provider=self.model_provider,
            user_id=user_id or self.user_id,
            session_id=self.session_id,
            data_lineage=data_lineage or self.data_lineage,
            consent_flags=consent_flags or self.consent_flags,
            compliance_tags=compliance_tags,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            environment=self.environment,
            metadata=metadata,
        )

        # Store the event (immutable, append-only)
        self.storage.store_event(event.to_dict())

        return event
