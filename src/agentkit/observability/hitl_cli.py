"""Human-in-the-Loop (HITL) CLI interface.

Provides a simple command-line interface for reviewing pipeline gates.
In production, this would be a web UI or Slack/Telegram integration.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any, Optional

import structlog

from agentkit.core.hitl import HITLManager, GateDecision, GateResult
from agentkit.models.pipeline import PipelineState, HITLGate

logger = structlog.get_logger("agentkit.hitl_cli")


class HitlCLI:
    """Command-line interface for reviewing HITL gates.

    Usage:
        cli = HitlCLI(hitl_manager)
        decision = await cli.review_gate(gate, state)
    """

    def __init__(self, manager: HITLManager | None = None):
        self.manager = manager or HITLManager()

    def print_banner(self) -> None:
        print("\n" + "=" * 60)
        print("🔍 AgentsFactory — Human-in-the-Loop Review")
        print("=" * 60)

    def print_gate_info(self, gate: HITLGate, state: PipelineState) -> None:
        """Display gate information for review."""
        print(f"\n📍 Gate: {gate.gate_id} (Step {gate.step})")
        print(f"   Type: {gate.gate_type}")
        print(f"   Timeout: {gate.timeout_seconds}s → {gate.timeout_behavior}")
        if gate.criteria:
            print(f"   Criteria: {', '.join(gate.criteria)}")

        # Show what triggered the gate
        evaluations = self.manager.evaluate_gates(state)
        for evaluation in evaluations:
            if evaluation.get("gate_id") == gate.gate_id and evaluation.get("needs_review"):
                print(f"\n⚠️  Triggers:")
                for reason in evaluation.get("reasons", []):
                    print(f"   - {reason}")

        # Show current pipeline state
        print(f"\n📊 Pipeline State:")
        print(f"   Step: {state.current_step}")
        print(f"   Agents completed: {len(state.agent_results)}")
        print(f"   Total tokens: {state.total_tokens}")
        print(f"   Total cost: ${state.total_cost_usd:.6f}")

        # Show agent results at this step
        for agent_id, result in state.agent_results.items():
            if result.step == gate.step:
                print(f"\n🤖 Agent: {agent_id}")
                print(f"   Status: {result.status.value}")
                print(f"   Confidence: {result.confidence:.2f}")
                if result.summary:
                    lines = result.summary.split("\n")[:5]
                    for line in lines:
                        print(f"   → {line[:80]}")

    async def review_gate(
        self,
        gate: HITLGate,
        state: PipelineState,
        auto_approve: bool = False,
    ) -> GateResult:
        """Review a gate and get human decision.

        Args:
            gate: The gate to review
            state: Current pipeline state
            auto_approve: If True, auto-approve (for testing)

        Returns:
            GateResult with the decision
        """
        self.print_banner()
        self.print_gate_info(gate, state)

        if auto_approve:
            print("\n✅ Auto-approved (testing mode)")
            return self.manager.approve(gate.gate_id, "Auto-approved")

        if gate.gate_type == "advisory":
            print(f"\n💡 Advisory gate — pipeline will continue. Review for awareness.")

        print(f"\n{'=' * 60}")
        print("Options:")
        print("  [a]pprove  — Allow pipeline to continue")
        print("  [r]eject   — Stop pipeline")
        print("  [m]odify   — Approve with modifications")
        print("  [s]kip     — Skip this gate (use timeout behavior)")
        print(f"{'=' * 60}")

        # Get user input
        while True:
            try:
                choice = input("\nYour decision [a/r/m/s]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️  Interrupted — using timeout behavior")
                if gate.timeout_behavior == "approve":
                    return self.manager.approve(gate.gate_id, "Timeout: approve")
                return self.manager.reject(gate.gate_id, "Timeout: reject")

            if choice in ("a", "approve", ""):
                notes = input("Notes (optional): ").strip()
                result = self.manager.approve(gate.gate_id, notes)
                print("✅ Approved")
                return result

            if choice in ("r", "reject"):
                notes = input("Rejection reason: ").strip()
                result = self.manager.reject(gate.gate_id, notes)
                print("❌ Rejected")
                return result

            if choice in ("m", "modify"):
                notes = input("Modification notes: ").strip()
                result = self.manager.approve(gate.gate_id, f"Modified: {notes}")
                print("✅ Approved with modifications")
                return result

            if choice in ("s", "skip"):
                if gate.timeout_behavior == "approve":
                    result = self.manager.approve(gate.gate_id, "Skipped")
                    print("⏭️  Skipped (timeout: approve)")
                    return result
                result = self.manager.reject(gate.gate_id, "Skipped")
                print("⏭️  Skipped (timeout: reject)")
                return result

            print("Invalid option. Choose a/r/m/s.")

    async def review_all_gates(
        self,
        state: PipelineState,
        auto_approve: bool = False,
    ) -> list[GateResult]:
        """Review all pending gates in the pipeline."""
        evaluations = self.manager.evaluate_gates(state)
        results = []

        for evaluation in evaluations:
            if evaluation.get("needs_review"):
                gate = self.manager.get_gate(evaluation["gate_id"])
                if gate:
                    result = await self.review_gate(gate, state, auto_approve)
                    results.append(result)
                    if result.decision == GateDecision.REJECTED:
                        break  # Stop on rejection

        return results
