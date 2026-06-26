# AI Agent Permission Sandbox & Audit

> Open-source governance layer — permission boundaries, sandboxed execution, audit trails for any AI agent.

## Why This Exists

AI agents are getting powerful. Too powerful. A recent dev.to article ("How My AI Agent Hacked Its Own Permissions") hit 15 reactions and 16 comments in its first week — developers are nervous. And they should be.

Your Claude Code, Codex, or custom agent can theoretically:
- Read files outside its workspace
- Make network calls to exfiltrate data
- Install software without permission
- Modify system configuration

Agent Sandbox Governance stops all of that.

## What It Does

1. **Permission Policies (YAML)** — Define exactly what your agent can and cannot do
2. **Sandboxed Execution** — Enforce those policies at runtime
3. **Audit Trail** — Tamper-proof log of every action the agent attempts (allowed or denied)

## Quick Start

```bash
pip install agent-sandbox
```

```python
from agent_sandbox import Sandbox, Policy

policy = Policy(
    name="ci-agent",
    denied_commands=["rm", "curl", "wget"],
    filesystem_rules=[PolicyRule("/workspace", "allow", ["read", "write"])],
    max_execution_time=300
)

sandbox = Sandbox(policy)
result = sandbox.run("git status")
print(result.allowed)  # True
```

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/sandbox/run` | POST | Execute within policy |
| `/api/v1/policies` | GET/POST | List/create policies |
| `/api/v1/audits` | GET | Query audit trail |
| `/api/v1/sandbox/status/:id` | GET | Check session status |

## Pricing

- **Free & Open Source** — MIT license, self-hosted
- **Enterprise** — Team management, SSO, compliance reports (contact us)

## Links

- Source: https://github.com/aidentify/ai-agent-sandbox-governance
- Docs: https://docs.aiidentify.ai/agent-sandbox

---

Published 2026-06-26 by AIdentify Pipeline (Cycle 2)
