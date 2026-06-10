"""Full eval pipeline example.

Demonstrates:
1. Loading a pipeline from YAML
2. Running it on multiple test cases
3. Evaluating outputs with LLM-as-a-Judge
4. Generating an eval report
5. Viewing results in the dashboard

Usage:
    uv run python examples/eval_pipeline.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentkit.agents.roles import ResearcherAgent, AnalyzerAgent, WriterAgent
from agentkit.config import settings
from agentkit.eval.judge import LLMJudge, DEFAULT_CRITERIA
from agentkit.eval.runner import EvalCase, EvalRunner, EvalSuite
from agentkit.llm import LLMClient
from agentkit.models.topology import AgentConfig, TopologyConfig, TopologyType
from agentkit.observability.metrics import MetricsCollector
from agentkit.orchestrator.engine import Orchestrator
from agentkit.observability.tracer import PipelineTracer


def create_agents():
    """Create LLM-powered agents."""
    return [
        ResearcherAgent(config=AgentConfig(
            agent_id="researcher",
            role="researcher",
            model="openrouter/owl-alpha",
            temperature=0.3,
            max_tokens=1500,
        )),
        AnalyzerAgent(config=AgentConfig(
            agent_id="analyzer",
            role="analyzer",
            model="openrouter/owl-alpha",
            temperature=0.2,
            max_tokens=1000,
        )),
        WriterAgent(config=AgentConfig(
            agent_id="writer",
            role="writer",
            model="openrouter/owl-alpha",
            temperature=0.5,
            max_tokens=2000,
        )),
    ]


def create_eval_suite() -> EvalSuite:
    """Create an eval suite with test cases."""
    suite = EvalSuite(
        name="research_quality",
        baseline_score=0.7,
        pass_threshold=0.7,
    )

    suite.add_case(EvalCase(
        case_id="test_1",
        input_text="Explain the circuit breaker pattern in distributed systems.",
        expected_behavior="Should explain the pattern with states (closed/open/half-open), use cases, and examples",
        tags=["happy_path"],
    ))

    suite.add_case(EvalCase(
        case_id="test_2",
        input_text="What are the key differences between LangGraph and raw LangChain for building multi-agent systems?",
        expected_behavior="Should compare state management, routing, observability, and production readiness",
        tags=["happy_path"],
    ))

    suite.add_case(EvalCase(
        case_id="test_3",
        input_text="Describe 3 common failure modes in multi-agent AI pipelines and how to mitigate them.",
        expected_behavior="Should identify specific failure modes (cascading, context exhaustion, infinite loops) with mitigations",
        tags=["edge_case"],
    ))

    return suite


async def run_eval():
    """Run the full eval pipeline."""
    if not settings.openrouter_api_key:
        print("❌ No OPENROUTER_API_KEY found! Create a .env file first.")
        return

    print("🔬 AgentsFactory — Full Eval Pipeline")
    print("=" * 55)

    # Setup
    agents = create_agents()
    topology = TopologyConfig(
        name="eval_pipeline",
        topology_type=TopologyType.SEQUENTIAL,
        agents=[a.config for a in agents],
    )

    tracer = PipelineTracer()
    collector = MetricsCollector()
    judge = LLMJudge()
    runner = EvalRunner()
    suite = create_eval_suite()
    runner.register_suite(suite)

    print(f"\n📋 Eval Suite: {suite.name}")
    print(f"   Cases: {suite.case_count}")
    print(f"   Baseline: {suite.baseline_score}")
    print(f"   Threshold: {suite.pass_threshold}")

    # Run each test case
    results = []
    for i, case in enumerate(suite.cases):
        print(f"\n{'─' * 55}")
        print(f"📝 Case {i + 1}/{suite.case_count}: {case.case_id}")
        print(f"   Input: {case.input_text[:80]}...")

        orchestrator = Orchestrator(config=topology, agents=agents, tracer=tracer)

        # Execute pipeline
        state = await orchestrator.execute(
            input_text=case.input_text,
            constraints=["Be technical and specific"],
        )

        # Record metrics
        collector.record_pipeline_start(state, name=f"eval_{case.case_id}")
        for agent_id, result in state.agent_results.items():
            collector.record_agent_result(state.pipeline_id, result)
        collector.record_pipeline_end(state)

        # Get the final output
        last_result = list(state.agent_results.values())[-1] if state.agent_results else None
        output = last_result.output.get("result", "") if last_result else ""

        # Judge the evaluation
        judge_result = await judge.evaluate(
            output=output,
            input_text=case.input_text,
            criteria=DEFAULT_CRITERIA,
            threshold=suite.pass_threshold,
        )

        results.append({
            "case_id": case.case_id,
            "status": state.status,
            "pipeline_tokens": state.total_tokens,
            "pipeline_cost": state.total_cost_usd,
            "judge_score": judge_result.overall_score,
            "judge_passed": judge_result.passed,
            "judge_feedback": judge_result.feedback,
            "output_preview": output[:200] if output else "",
        })

        print(f"   Pipeline: {state.status} | Tokens: {state.total_tokens} | Cost: ${state.total_cost_usd:.6f}")
        print(f"   Judge: {judge_result.overall_score:.2f} | Passed: {judge_result.passed}")
        if judge_result.feedback:
            print(f"   Feedback: {judge_result.feedback[:100]}")

    # Summary
    print(f"\n{'=' * 55}")
    print("📊 Eval Summary")
    print(f"{'=' * 55}")

    passed = sum(1 for r in results if r["judge_passed"])
    total = len(results)
    avg_score = sum(r["judge_score"] for r in results) / total if total else 0
    total_tokens = sum(r["pipeline_tokens"] for r in results)
    total_cost = sum(r["pipeline_cost"] for r in results)

    print(f"   Passed: {passed}/{total} ({passed/total*100:.0f}%)")
    print(f"   Avg Score: {avg_score:.2f}")
    print(f"   Total Tokens: {total_tokens:,}")
    print(f"   Total Cost: ${total_cost:.6f}")
    print(f"   Meets Baseline: {avg_score >= suite.baseline_score}")

    # Per-case breakdown
    print(f"\n📋 Per-Case Results:")
    for r in results:
        icon = "✅" if r["judge_passed"] else "❌"
        print(f"   {icon} {r['case_id']}: {r['judge_score']:.2f} ({r['status']})")

    # Budget alerts
    alerts = collector.get_budget_alerts()
    if alerts:
        print(f"\n🚨 Budget Alerts: {len(alerts)}")

    print(f"\n💡 To view the dashboard, run:")
    print(f"   uv run streamlit run src/agentkit/observability/dashboard.py")


if __name__ == "__main__":
    asyncio.run(run_eval())
