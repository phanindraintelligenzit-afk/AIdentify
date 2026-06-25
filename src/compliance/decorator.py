"""
@audit_log() Decorator — Automatic audit logging for agent functions.

Wraps any function to automatically capture inputs, outputs,
timing, and PII detection, then log them as immutable audit events.

Usage:
    @audit_log(agent_name="my-agent", action_type=ActionType.DECISION)
    def my_agent_function(prompt, **kwargs):
        return "response"
"""

import functools
import logging
import time
from typing import Any, Callable, Optional

from compliance.audit_logger import AuditLogger
from compliance.models import ActionType, ConsentFlags, DataLineage
from compliance.storage import SQLiteStorage

logger = logging.getLogger(__name__)

# Module-level default logger instance
_default_audit_logger: Optional[AuditLogger] = None


def configure(
    storage: Optional[SQLiteStorage] = None,
    agent_name: str = "default-agent",
    model_version: str = "unknown",
    model_provider: str = "unknown",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    environment: str = "production",
    consent_flags: Optional[ConsentFlags] = None,
    data_lineage: Optional[DataLineage] = None,
) -> AuditLogger:
    """
    Configure the module-level default audit logger.

    Args:
        storage: SQLiteStorage instance.
        agent_name: Default agent name.
        model_version: Default model version.
        model_provider: Model provider name.
        user_id: Default user ID.
        session_id: Session identifier.
        environment: Deployment environment.
        consent_flags: Default consent flags.
        data_lineage: Default data lineage.

    Returns:
        The configured AuditLogger instance.
    """
    global _default_audit_logger
    _default_audit_logger = AuditLogger(
        storage=storage,
        agent_name=agent_name,
        model_version=model_version,
        model_provider=model_provider,
        user_id=user_id,
        session_id=session_id,
        environment=environment,
        consent_flags=consent_flags,
        data_lineage=data_lineage,
    )
    return _default_audit_logger


def get_default_logger() -> AuditLogger:
    """Get the default audit logger, creating one if needed."""
    global _default_audit_logger
    if _default_audit_logger is None:
        _default_audit_logger = AuditLogger()
    return _default_audit_logger


def audit_log(
    agent_name: Optional[str] = None,
    action_type: ActionType = ActionType.CUSTOM,
    model_version: Optional[str] = None,
    user_id: Optional[str] = None,
    log_args: bool = True,
    log_return: bool = True,
    audit_logger: Optional[AuditLogger] = None,
):
    """
    Decorator that automatically logs function calls as audit events.

    Captures:
    - Function arguments (as input)
    - Return value (as output)
    - Execution time (latency)
    - Exceptions (as rejected decisions)

    Args:
        agent_name: Name of the agent. Defaults to function name.
        action_type: Type of action being logged.
        model_version: Model version string.
        user_id: User ID for the event.
        log_args: Whether to log function arguments.
        log_return: Whether to log the return value.
        audit_logger: Custom AuditLogger instance. Uses default if None.

    Returns:
        Decorated function.

    Example:
        @audit_log(agent_name="support-bot", action_type=ActionType.GENERATE_TEXT)
        def handle_query(prompt: str) -> str:
            return generate_response(prompt)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Resolve agent name
            _agent_name = agent_name or func.__name__
            _logger = audit_logger or get_default_logger()

            # Build input text from args
            if log_args:
                input_parts = []
                if args:
                    input_parts.append(str(args))
                if kwargs:
                    input_parts.append(str(kwargs))
                input_text = " | ".join(input_parts) if input_parts else func.__name__
            else:
                input_text = f"call:{func.__name__}"

            # Execute with timing
            start_time = time.monotonic()
            output_text = ""
            confidence = None
            success = True

            try:
                result = func(*args, **kwargs)

                # Handle different return types
                if isinstance(result, dict):
                    output_text = str(result.get("output", result.get("result", result)))
                    confidence = result.get("confidence", result.get("confidence_score"))
                elif isinstance(result, str):
                    output_text = result
                elif result is not None:
                    output_text = str(result)

                return result

            except Exception as e:
                success = False
                output_text = f"ERROR: {type(e).__name__}: {str(e)}"
                raise

            finally:
                # Always log, even on exception
                elapsed_ms = int((time.monotonic() - start_time) * 1000)

                try:
                    _logger.log_decision(
                        action_type=action_type,
                        input_text=input_text,
                        output_text=output_text,
                        agent_name=_agent_name,
                        model_version=model_version,
                        user_id=user_id,
                        confidence_score=confidence,
                        decision_summary=f"{'SUCCESS' if success else 'FAILED'}: {func.__name__}",
                        rationale=f"Function {'completed successfully' if success else 'raised exception'}",
                        latency_ms=elapsed_ms,
                    )
                except Exception as log_err:
                    # Don't let logging failures break the application
                    logger.error(f"Audit logging failed for {_agent_name}: {log_err}")

        return wrapper
    return decorator
