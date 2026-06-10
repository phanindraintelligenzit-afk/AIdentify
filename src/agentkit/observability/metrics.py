"""Cost and latency metrics tracking for pipeline runs.

Tracks per-agent and pipeline-level metrics across runs,
stores them in SQLite for historical analysis, and provides
budget alerting.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import structlog

from agentkit.models.pipeline import AgentResult, PipelineState

logger = structlog.get_logger("agentkit.metrics")


@dataclass
class AgentMetrics:
    """Metrics for a single agent execution."""

    agent_id: str
    pipeline_id: str
    trace_id: str
    step: int
    status: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    model: str = ""
    confidence: float = 0.0
    error_count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "pipeline_id": self.pipeline_id,
            "trace_id": self.trace_id,
            "step": self.step,
            "status": self.status,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "model": self.model,
            "confidence": self.confidence,
            "error_count": self.error_count,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PipelineMetrics:
    """Aggregated metrics for an entire pipeline run."""

    pipeline_id: str
    trace_id: str
    name: str = ""
    status: str = ""
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    agent_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    escalated_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    agent_metrics: list[AgentMetrics] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pipeline_id": self.pipeline_id,
            "trace_id": self.trace_id,
            "name": self.name,
            "status": self.status,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "total_latency_ms": self.total_latency_ms,
            "agent_count": self.agent_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "escalated_count": self.escalated_count,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class MetricsCollector:
    """Collects and stores metrics from pipeline runs.

    Usage:
        collector = MetricsCollector()
        collector.record_pipeline_start(state)
        collector.record_agent_result(state, result)
        collector.record_pipeline_end(state)
        summary = collector.get_summary(state)
    """

    def __init__(self, db_path: str | Path = "./agentsfactory_metrics.db"):
        self.db_path = Path(db_path)
        self._current: dict[str, PipelineMetrics] = {}
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database for metrics storage."""
        import sqlite3
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_metrics (
                pipeline_id TEXT PRIMARY KEY,
                trace_id TEXT,
                name TEXT,
                status TEXT,
                total_tokens INTEGER,
                total_cost_usd REAL,
                total_latency_ms REAL,
                agent_count INTEGER,
                success_count INTEGER,
                failure_count INTEGER,
                created_at TEXT,
                completed_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                pipeline_id TEXT,
                trace_id TEXT,
                step INTEGER,
                status TEXT,
                tokens_used INTEGER,
                cost_usd REAL,
                latency_ms REAL,
                model TEXT,
                confidence REAL,
                error_count INTEGER,
                timestamp TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budget_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_id TEXT,
                alert_type TEXT,
                message TEXT,
                value REAL,
                threshold REAL,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    def record_pipeline_start(self, state: PipelineMetrics | PipelineState, name: str = "") -> None:
        """Record the start of a pipeline run."""
        if isinstance(state, PipelineState):
            metrics = PipelineMetrics(
                pipeline_id=state.pipeline_id,
                trace_id=state.trace_id,
                name=name,
                status="running",
            )
        else:
            metrics = state
        self._current[metrics.pipeline_id] = metrics

    def record_agent_result(
        self,
        pipeline_id: str,
        result: AgentResult,
        model: str = "",
    ) -> None:
        """Record metrics from an agent execution."""
        if pipeline_id not in self._current:
            return

        pipeline = self._current[pipeline_id]
        agent_metric = AgentMetrics(
            agent_id=result.agent_id,
            pipeline_id=pipeline_id,
            trace_id=pipeline.trace_id,
            step=result.step,
            status=result.status.value,
            tokens_used=result.tokens_used,
            cost_usd=result.cost_usd,
            latency_ms=result.latency_ms,
            model=model or result.model,
            confidence=result.confidence,
            error_count=len(result.errors),
        )
        pipeline.agent_metrics.append(agent_metric)
        pipeline.total_tokens += result.tokens_used
        pipeline.total_cost_usd += result.cost_usd
        pipeline.total_latency_ms += result.latency_ms
        pipeline.agent_count += 1

        if result.status.value == "success":
            pipeline.success_count += 1
        elif result.status.value in ("failure", "partial"):
            pipeline.failure_count += 1
        elif result.status.value == "escalated":
            pipeline.escalated_count += 1

    def record_pipeline_end(self, state: PipelineState) -> PipelineMetrics:
        """Record the end of a pipeline run and persist to DB."""
        if state.pipeline_id not in self._current:
            return PipelineMetrics(pipeline_id=state.pipeline_id, trace_id=state.trace_id)

        metrics = self._current[state.pipeline_id]
        metrics.status = state.status
        metrics.completed_at = datetime.utcnow()

        # Persist to SQLite
        self._persist_metrics(metrics)

        # Check budget alerts
        self._check_budgets(metrics)

        return metrics

    def _persist_metrics(self, metrics: PipelineMetrics) -> None:
        """Persist metrics to SQLite."""
        import sqlite3
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("""
                INSERT OR REPLACE INTO pipeline_metrics
                (pipeline_id, trace_id, name, status, total_tokens, total_cost_usd,
                 total_latency_ms, agent_count, success_count, failure_count,
                 created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.pipeline_id, metrics.trace_id, metrics.name, metrics.status,
                metrics.total_tokens, metrics.total_cost_usd, metrics.total_latency_ms,
                metrics.agent_count, metrics.success_count, metrics.failure_count,
                metrics.created_at.isoformat(),
                metrics.completed_at.isoformat() if metrics.completed_at else None,
            ))
            for am in metrics.agent_metrics:
                conn.execute("""
                    INSERT INTO agent_metrics
                    (agent_id, pipeline_id, trace_id, step, status, tokens_used,
                     cost_usd, latency_ms, model, confidence, error_count, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    am.agent_id, am.pipeline_id, am.trace_id, am.step, am.status,
                    am.tokens_used, am.cost_usd, am.latency_ms, am.model,
                    am.confidence, am.error_count, am.timestamp.isoformat(),
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("metrics_persist_error", error=str(e))

    def _check_budgets(self, metrics: PipelineMetrics) -> list[dict]:
        """Check if any budget thresholds were exceeded."""
        alerts = []
        # Cost budget: $1.00 default
        if metrics.total_cost_usd > 1.0:
            alert = {
                "type": "cost_exceeded",
                "message": f"Pipeline cost ${metrics.total_cost_usd:.4f} exceeded $1.00 budget",
                "value": metrics.total_cost_usd,
                "threshold": 1.0,
            }
            alerts.append(alert)
            self._persist_alert(metrics.pipeline_id, alert)

        # Token budget: 50000 default
        if metrics.total_tokens > 50000:
            alert = {
                "type": "token_exceeded",
                "message": f"Pipeline tokens {metrics.total_tokens} exceeded 50000 budget",
                "value": metrics.total_tokens,
                "threshold": 50000,
            }
            alerts.append(alert)
            self._persist_alert(metrics.pipeline_id, alert)

        # Latency budget: 300s default
        if metrics.total_latency_ms > 300000:
            alert = {
                "type": "latency_exceeded",
                "message": f"Pipeline latency {metrics.total_latency_ms:.0f}ms exceeded 300s budget",
                "value": metrics.total_latency_ms,
                "threshold": 300000,
            }
            alerts.append(alert)
            self._persist_alert(metrics.pipeline_id, alert)

        if alerts:
            logger.warning("budget_alerts", pipeline_id=metrics.pipeline_id, alerts=len(alerts))

        return alerts

    def _persist_alert(self, pipeline_id: str, alert: dict) -> None:
        """Persist a budget alert to SQLite."""
        import sqlite3
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("""
                INSERT INTO budget_alerts
                (pipeline_id, alert_type, message, value, threshold, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                pipeline_id, alert["type"], alert["message"],
                alert["value"], alert["threshold"], datetime.utcnow().isoformat(),
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_summary(self, pipeline_id: str) -> dict[str, Any]:
        """Get a summary of a pipeline run."""
        if pipeline_id in self._current:
            m = self._current[pipeline_id]
            return {
                **m.to_dict(),
                "agent_breakdown": [am.to_dict() for am in m.agent_metrics],
            }
        return {}

    def get_recent_runs(self, limit: int = 20) -> list[dict]:
        """Get recent pipeline runs from the database."""
        import sqlite3
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM pipeline_metrics ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception:
            return []

    def get_agent_history(self, agent_id: str, limit: int = 50) -> list[dict]:
        """Get historical metrics for a specific agent."""
        import sqlite3
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM agent_metrics WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ?",
                (agent_id, limit),
            ).fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception:
            return []

    def get_budget_alerts(self, limit: int = 50) -> list[dict]:
        """Get recent budget alerts."""
        import sqlite3
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM budget_alerts ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception:
            return []
