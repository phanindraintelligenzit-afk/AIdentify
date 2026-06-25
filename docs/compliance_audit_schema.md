# AI Compliance & Governance Monitor — Audit Schema

> **Version:** 1.0.0  
> **Date:** 2026-06-21  
> **Author:** Planner Agent (AgentsFactory Swarm)  
> **Target Compliance:** EU AI Act (Regulation 2024/1689), GDPR, SOC 2 Type II  
> **Audience:** Engineering team implementing the audit logging pipeline

---

## Table of Contents

1. [Audit Event Schema](#1-audit-event-schema)
2. [Compliance Rules Engine](#2-compliance-rules-engine)
3. [Data Retention Policy](#3-data-retention-policy)
4. [Report Templates](#4-report-templates)
5. [Implementation Notes](#5-implementation-notes)

---

## 1. Audit Event Schema

### 1.1 Overview

Every AI agent decision must produce an immutable audit event. This schema defines the canonical JSON structure for a single decision event, designed to satisfy EU AI Act Article 12 (Record-keeping), Article 13 (Transparency), and Article 14 (Human oversight).

### 1.2 JSON Schema (Draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://agentsfactory.ai/schemas/audit-event/v1",
  "title": "AuditEvent",
  "description": "A single AI agent decision event for compliance auditing",
  "type": "object",
  "required": [
    "event_id",
    "timestamp",
    "agent_name",
    "action_type",
    "input_summary",
    "output_summary",
    "model_version",
    "risk_score"
  ],
  "properties": {
    "event_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique immutable identifier for this audit event (UUIDv7 preferred)"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of the decision event (UTC, millisecond precision)"
    },
    "agent_name": {
      "type": "string",
      "maxLength": 128,
      "description": "Canonical name of the agent that made the decision (e.g., 'customer-support-bot-v2')"
    },
    "agent_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique agent instance identifier"
    },
    "action_type": {
      "type": "string",
      "enum": [
        "generate_text",
        "classify",
        "recommend",
        "approve",
        "reject",
        "escalate",
        "data_access",
        "data_write",
        "data_delete",
        "tool_call",
        "decision",
        "inference",
        "routing",
        "summarize",
        "translate",
        "custom"
      ],
      "description": "Categorized action type for the decision"
    },
    "input_summary": {
      "type": "object",
      "description": "Sanitized summary of inputs to the decision (not raw prompts)",
      "properties": {
        "prompt_hash": {
          "type": "string",
          "description": "SHA-256 hash of the full input prompt for traceability"
        },
        "input_length_tokens": {
          "type": "integer",
          "minimum": 0,
          "description": "Token count of input context"
        },
        "input_classification": {
          "type": "string",
          "enum": ["public", "internal", "confidential", "restricted"],
          "description": "Data classification of the input"
        },
        "pii_detected": {
          "type": "boolean",
          "description": "Whether PII was detected in the input"
        },
        "pii_types": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Types of PII detected (e.g., ['email', 'phone', 'ssn'])"
        },
        "data_sources": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Identifiers of data sources referenced in input"
        }
      },
      "required": ["prompt_hash", "input_length_tokens", "pii_detected"]
    },
    "output_summary": {
      "type": "object",
      "description": "Summary of the agent's output/decision",
      "properties": {
        "output_hash": {
          "type": "string",
          "description": "SHA-256 hash of the full output"
        },
        "output_length_tokens": {
          "type": "integer",
          "minimum": 0,
          "description": "Token count of generated output"
        },
        "decision": {
          "type": "string",
          "maxLength": 512,
          "description": "Human-readable summary of the decision taken"
        },
        "rationale": {
          "type": "string",
          "maxLength": 2048,
          "description": "Explanation of why this decision was made (if available)"
        },
        "pii_detected": {
          "type": "boolean",
          "description": "Whether PII was detected in the output"
        },
        "pii_types": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Types of PII leaked in output"
        },
        "confidence_score": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "Model confidence in its output (0.0–1.0)"
        }
      },
      "required": ["output_hash", "output_length_tokens", "decision", "pii_detected"]
    },
    "confidence_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Overall confidence score for this decision event"
    },
    "model_version": {
      "type": "string",
      "maxLength": 64,
      "description": "Exact model identifier and version (e.g., 'gpt-4o-2024-08-06' or 'claude-sonnet-4-20250514')"
    },
    "model_provider": {
      "type": "string",
      "maxLength": 64,
      "description": "Model provider (e.g., 'openai', 'anthropic', 'meta', 'internal')"
    },
    "user_id": {
      "type": "string",
      "maxLength": 128,
      "description": "Pseudonymized identifier of the user who triggered the action (null for system-initiated)"
    },
    "session_id": {
      "type": "string",
      "format": "uuid",
      "description": "Session identifier grouping related events"
    },
    "data_lineage": {
      "type": "object",
      "description": "Complete record of data accessed during this decision",
      "properties": {
        "sources_accessed": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "source_id": { "type": "string" },
              "source_type": {
                "type": "string",
                "enum": ["database", "api", "file", "vector_store", "cache", "external", "user_input"]
              },
              "access_type": {
                "type": "string",
                "enum": ["read", "write", "delete"]
              },
              "data_classification": {
                "type": "string",
                "enum": ["public", "internal", "confidential", "restricted"]
              },
              "records_affected": { "type": "integer" },
              "authorization_verified": { "type": "boolean" }
            },
            "required": ["source_id", "source_type", "access_type"]
          }
        },
        "data_written": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "destination_id": { "type": "string" },
              "destination_type": { "type": "string" },
              "data_classification": { "type": "string" },
              "records_affected": { "type": "integer" }
            }
          }
        },
        "retention_policy": {
          "type": "string",
          "description": "Retention classification applied to data accessed"
        }
      },
      "required": ["sources_accessed"]
    },
    "consent_flags": {
      "type": "object",
      "description": "User consent status for this interaction",
      "properties": {
        "user_consent_obtained": {
          "type": "boolean",
          "description": "Whether explicit user consent was obtained for this processing"
        },
        "consent_type": {
          "type": "string",
          "enum": ["explicit", "implied", "legitimate_interest", "contractual_necessity", "legal_obligation", "none"],
          "description": "Legal basis for processing under GDPR"
        },
        "consent_timestamp": {
          "type": "string",
          "format": "date-time",
          "description": "When consent was granted"
        },
        "consent_scope": {
          "type": "array",
          "items": { "type": "string" },
          "description": "What the consent covers (e.g., ['data_processing', 'automated_decision', 'profiling'])"
        },
        "data_processing_purpose": {
          "type": "string",
          "maxLength": 256,
          "description": "Purpose limitation declaration"
        },
        "right_to_explanation": {
          "type": "boolean",
          "description": "Whether the user has the right to an explanation (Art. 22 EU AI Act)"
        },
        "human_oversight_available": {
          "type": "boolean",
          "description": "Whether human oversight was available/used for this decision"
        }
      },
      "required": ["user_consent_obtained", "consent_type"]
    },
    "risk_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "Composite risk score (0=no risk, 100=critical). Computed by rules engine."
    },
    "risk_factors": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Specific risk factors identified (e.g., ['pii_leakage', 'low_confidence', 'high_stakes_decision'])"
    },
    "compliance_tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "EU AI Act articles relevant to this event (e.g., ['art_12', 'art_13', 'art_14', 'art_15'])"
    },
    "human_review": {
      "type": "object",
      "description": "Human oversight details (required for high-risk decisions)",
      "properties": {
        "reviewer_id": { "type": "string" },
        "review_timestamp": { "type": "string", "format": "date-time" },
        "review_decision": {
          "type": "string",
          "enum": ["approved", "modified", "rejected", "overridden"]
        },
        "review_notes": { "type": "string", "maxLength": 1024 }
      }
    },
    "latency_ms": {
      "type": "integer",
      "minimum": 0,
      "description": "Decision latency in milliseconds"
    },
    "cost_usd": {
      "type": "number",
      "minimum": 0,
      "description": "Estimated cost of this decision in USD"
    },
    "environment": {
      "type": "string",
      "enum": ["production", "staging", "development", "testing"],
      "description": "Deployment environment"
    },
    "version_tag": {
      "type": "string",
      "maxLength": 64,
      "description": "Application version tag (e.g., 'v2.3.1')"
    },
    "metadata": {
      "type": "object",
      "description": "Arbitrary key-value pairs for additional context",
      "additionalProperties": { "type": "string" }
    }
  }
}
```

### 1.3 Example Event

```json
{
  "event_id": "01978d2e-4a2b-7c3d-8e9f-0a1b2c3d4e5f",
  "timestamp": "2026-06-21T17:35:48.123Z",
  "agent_name": "loan-adjudication-agent",
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "action_type": "decision",
  "input_summary": {
    "prompt_hash": "sha256:3f2b...",
    "input_length_tokens": 4200,
    "input_classification": "confidential",
    "pii_detected": true,
    "pii_types": ["ssn", "date_of_birth", "address"],
    "data_sources": ["credit-bureau-api", "user-profile-db"]
  },
  "output_summary": {
    "output_hash": "sha256:7a1c...",
    "output_length_tokens": 256,
    "decision": "Loan application denied — debt-to-income ratio exceeds threshold",
    "rationale": "Applicant DTI of 62% exceeds policy maximum of 45%",
    "pii_detected": false,
    "pii_types": [],
    "confidence_score": 0.94
  },
  "confidence_score": 0.94,
  "model_version": "claude-sonnet-4-20250514",
  "model_provider": "anthropic",
  "user_id": "usr_8f3k2j5m9x",
  "session_id": "sess_20260621_abc123",
  "data_lineage": {
    "sources_accessed": [
      {
        "source_id": "credit-bureau-api",
        "source_type": "api",
        "access_type": "read",
        "data_classification": "restricted",
        "records_affected": 1,
        "authorization_verified": true
      },
      {
        "source_id": "user-profile-db",
        "source_type": "database",
        "access_type": "read",
        "data_classification": "confidential",
        "records_affected": 1,
        "authorization_verified": true
      }
    ],
    "data_written": [],
    "retention_policy": "financial_7yr"
  },
  "consent_flags": {
    "user_consent_obtained": true,
    "consent_type": "explicit",
    "consent_timestamp": "2026-06-21T17:30:00.000Z",
    "consent_scope": ["data_processing", "automated_decision", "credit_check"],
    "data_processing_purpose": "Loan application evaluation",
    "right_to_explanation": true,
    "human_oversight_available": true
  },
  "risk_score": 42,
  "risk_factors": ["high_stakes_decision", "pii_in_input"],
  "compliance_tags": ["art_12", "art_13", "art_14", "art_15"],
  "human_review": {
    "reviewer_id": "rev_kjohnson",
    "review_timestamp": "2026-06-21T17:40:00.000Z",
    "review_decision": "approved",
    "review_notes": "Decision consistent with policy"
  },
  "latency_ms": 1240,
  "cost_usd": 0.0032,
  "environment": "production",
  "version_tag": "v2.3.1",
  "metadata": {
    "region": "eu-west-1",
    "jurisdiction": "EU"
  }
}
```

---

## 2. Compliance Rules Engine

### 2.1 Rule Evaluation Framework

Rules are evaluated synchronously on each audit event. Each rule returns:
- **severity**: `info` | `warning` | `violation` | `critical`
- **rule_id**: Unique identifier
- **message**: Human-readable description
- **articles**: EU AI Act articles or regulations triggered

### 2.2 Rule Definitions

| # | Rule ID | Name | Condition | Severity | EU AI Act Article |
|---|---------|------|-----------|----------|-------------------|
| 1 | `RULE-001` | PII Leakage in Output | `output_summary.pii_detected == true` AND `output_summary.pii_types` contains sensitive categories (SSN, financial, health) | **Critical** | Art. 13, GDPR Art. 32 |
| 2 | `RULE-002` | Decision Without User Consent | `consent_flags.user_consent_obtained == false` AND `consent_type` is `none` AND action involves personal data | **Violation** | Art. 13, GDPR Art. 6 |
| 3 | `RULE-003` | Low Confidence Decision | `confidence_score < 0.70` AND `action_type` is `approve` or `decision` or `escalate` | **Warning** | Art. 15 (Accuracy) |
| 4 | `RULE-004` | Unauthorized Data Access | Any entry in `data_lineage.sources_accessed` where `authorization_verified == false` | **Critical** | Art. 12, GDPR Art. 32 |
| 5 | `RULE-005` | Data Retention Exceeded | Event timestamp exceeds retention period defined in `data_lineage.retention_policy` | **Violation** | Art. 12(3), GDPR Art. 5(1)(e) |
| 6 | `RULE-006` | High-Risk Without Human Oversight | `risk_score >= 70` AND (`human_review` is null OR `human_review.review_decision` is null) | **Violation** | Art. 14 (Human Oversight) |
| 7 | `RULE-007` | Off-Policy Action | `action_type` not in agent's registered action allowlist | **Violation** | Art. 15 (Risk Management) |
| 8 | `RULE-008` | Cross-Border Data Transfer | `data_lineage.sources_accessed` contains source outside EU/EEA AND no adequacy decision or SCC flagged in metadata | **Warning** | GDPR Chapter V |
| 9 | `RULE-009` | Model Version Deprecated | `model_version` is not in the approved model registry or is >90 days past release | **Warning** | Art. 15(2) (Post-market monitoring) |
| 10 | `RULE-010` | Excessive Data Collection | `data_lineage.sources_accessed` count > agent's configured maximum OR records_affected exceeds policy threshold | **Warning** | GDPR Art. 5(1)(c) (Minimization) |
| 11 | `RULE-011` | Consent Scope Mismatch | `consent_scope` does not include all processing purposes required by the action | **Violation** | GDPR Art. 6(1)(a) |
| 12 | `RULE-012` | Right to Explanation Not Available | `consent_flags.right_to_explanation == false` AND `action_type` is `decision` AND decision has legal/significant effect | **Violation** | Art. 22, Art. 13(2)(f) |
| 13 | `RULE-013` | Anomalous Decision Rate | Agent produces >50 decisions/minute OR >3σ above rolling 7-day mean | **Warning** | Art. 15 (Monitoring) |
| 14 | `RULE-014` | Sensitive Category Processing | `input_summary.pii_types` contains health, biometric, political, religious, or sexual orientation data AND no explicit consent for special categories | **Critical** | GDPR Art. 9 |
| 15 | `RULE-015` | Audit Log Tampering Detected | Event hash chain broken OR `event_id` sequence gap detected | **Critical** | Art. 12(2) (Integrity) |

### 2.3 Rule Configuration (YAML)

```yaml
rules_engine:
  version: "1.0.0"
  default_severity_threshold: "warning"
  
  rules:
    - id: "RULE-001"
      enabled: true
      auto_block: true
      notify: ["compliance-team@company.com", "slack:#compliance-alerts"]
      
    - id: "RULE-002"
      enabled: true
      auto_block: true
      notify: ["dpo@company.com"]
      
    - id: "RULE-003"
      enabled: true
      auto_block: false
      threshold: 0.70
      notify: ["ml-ops@company.com"]
      
    - id: "RULE-004"
      enabled: true
      auto_block: true
      notify: ["security@company.com", "slack:#security-incidents"]
      
    - id: "RULE-005"
      enabled: true
      auto_block: false
      notify: ["data-governance@company.com"]
      
    - id: "RULE-006"
      enabled: true
      auto_block: true
      risk_threshold: 70
      notify: ["compliance-team@company.com"]
      
    - id: "RULE-007"
      enabled: true
      auto_block: true
      notify: ["ml-ops@company.com", "slack:#agent-alerts"]
      
    - id: "RULE-008"
      enabled: true
      auto_block: false
      allowed_jurisdictions: ["EU", "EEA", "UK", "CH"]
      notify: ["dpo@company.com"]
      
    - id: "RULE-009"
      enabled: true
      auto_block: false
      max_model_age_days: 90
      notify: ["ml-ops@company.com"]
      
    - id: "RULE-010"
      enabled: true
      auto_block: false
      max_sources_per_event: 10
      max_records_per_event: 1000
      notify: ["data-governance@company.com"]
      
    - id: "RULE-011"
      enabled: true
      auto_block: true
      notify: ["dpo@company.com"]
      
    - id: "RULE-012"
      enabled: true
      auto_block: true
      notify: ["dpo@company.com", "compliance-team@company.com"]
      
    - id: "RULE-013"
      enabled: true
      auto_block: false
      rate_limit_per_minute: 50
      stddev_threshold: 3
      notify: ["ml-ops@company.com"]
      
    - id: "RULE-014"
      enabled: true
      auto_block: true
      sensitive_types: ["health", "biometric", "political", "religious", "sexual_orientation", "ethnic_origin"]
      notify: ["dpo@company.com", "slack:#privacy-incidents"]
      
    - id: "RULE-015"
      enabled: true
      auto_block: true
      hash_algorithm: "SHA-256"
      notify: ["security@company.com", "slack:#security-critical"]
```

---

## 3. Data Retention Policy

### 3.1 Retention Tiers

| Tier | Data Type | Retention Period | Legal Basis | Storage Location |
|------|-----------|-----------------|-------------|-----------------|
| **Tier 1** | Full audit events (production) | **7 years** | EU AI Act Art. 12(3), financial regulations | Encrypted cold storage (WORM) |
| **Tier 2** | Audit events (non-production) | **2 years** | Internal policy | Encrypted object storage |
| **Tier 3** | PII-containing event payloads | **1 year** (then anonymize) | GDPR Art. 5(1)(e) — minimize | Encrypted DB with access controls |
| **Tier 4** | Aggregated compliance reports | **7 years** | EU AI Act Art. 12(3) | Encrypted cold storage |
| **Tier 5** | Incident reports | **10 years** | Legal hold / regulatory inquiry | Immutable WORM storage |
| **Tier 6** | Debug/trace logs | **30 days** | Legitimate interest | Standard encrypted storage |

### 3.2 Anonymization Schedule

| Phase | Timeframe | Action |
|-------|-----------|--------|
| **Active** | 0–90 days | Full data available for real-time monitoring |
| **Restricted** | 90 days–1 year | PII fields pseudonymized; raw data requires compliance officer approval to access |
| **Anonymized** | 1–2 years | All PII removed; `user_id` replaced with irreversible hash; `input_summary` and `output_summary` retain only statistical aggregates |
| **Aggregated** | 2–7 years | Only daily/weekly aggregate statistics retained; individual events purged |
| **Purged** | 7+ years | All data permanently deleted (except Tier 5 incident reports) |

### 3.3 Anonymization Rules

```
Fields to pseudonymize after 90 days:
  - user_id → SHA-256(user_id + rotating_salt)
  - session_id → null
  - input_summary.pii_types → retain categories but remove values
  - output_summary.pii_types → retain categories but remove values

Fields to remove after 1 year:
  - input_summary.prompt_hash
  - output_summary.output_hash
  - output_summary.rationale
  - data_lineage.sources_accessed[].source_id
  - consent_flags.consent_timestamp
  - human_review.reviewer_id

Fields retained indefinitely (aggregated only):
  - timestamp (day-level granularity)
  - agent_name
  - action_type
  - confidence_score (binned: 0.1 intervals)
  - risk_score (binned: 10-point buckets)
  - compliance_tags
```

### 3.4 Purge Automation

```python
# Pseudocode for retention enforcement
def enforce_retention():
    now = utc_now()
    
    # Phase 1: Pseudonymize PII after 90 days
    events = db.query("SELECT * FROM audit_events WHERE created_at < now - 90d AND phase = 'active'")
    for event in events:
        event.user_id = pseudonymize(event.user_id)
        event.session_id = None
        event.phase = "restricted"
    
    # Phase 2: Anonymize after 1 year
    events = db.query("SELECT * FROM audit_events WHERE created_at < now - 365d AND phase = 'restricted'")
    for event in events:
        event = strip_pii(event)
        event.phase = "anonymized"
    
    # Phase 3: Aggregate and purge after 2 years (Tier 1/2)
    events = db.query("SELECT * FROM audit_events WHERE created_at < now - 730d AND phase = 'anonymized' AND tier IN (1,2)")
    aggregate_to_daily_stats(events)
    db.delete(events)
    
    # Phase 4: Purge aggregates after 7 years
    db.execute("DELETE FROM daily_stats WHERE date < now - 2555d")
```

---

## 4. Report Templates

### 4.1 Daily Compliance Summary

```markdown
# Daily Compliance Report — {{date}}

## Executive Summary
- **Total decisions logged**: {{total_events}}
- **Violation count**: {{violation_count}} ({{violation_delta}}% vs yesterday)
- **Critical incidents**: {{critical_count}}
- **Overall compliance score**: {{compliance_score}}/100

## Key Metrics
| Metric | Value | Trend |
|--------|-------|-------|
| Total events | {{total_events}} | {{trend}} |
| Unique agents | {{unique_agents}} | {{trend}} |
| Avg confidence | {{avg_confidence}} | {{trend}} |
| Avg risk score | {{avg_risk}} | {{trend}} |
| PII events | {{pii_events}} | {{trend}} |
| Consent violations | {{consent_violations}} | {{trend}} |

## Top Violations
| Rule ID | Rule Name | Count | Severity | Delta |
|---------|-----------|-------|----------|-------|
| {{rule_id}} | {{rule_name}} | {{count}} | {{severity}} | {{delta}} |

## Agent Activity
| Agent | Decisions | Avg Risk | Violations | Status |
|-------|-----------|----------|------------|--------|
| {{agent_name}} | {{count}} | {{risk}} | {{violations}} | {{status}} |

## High-Risk Events (Top 5)
| Time | Agent | Action | Risk Score | Rule Triggered |
|------|-------|--------|------------|----------------|
| {{time}} | {{agent}} | {{action}} | {{risk}} | {{rule}} |

## EU AI Act Coverage
- Art. 12 (Record-keeping): ✅ {{coverage}}%
- Art. 13 (Transparency): ✅ {{coverage}}%
- Art. 14 (Human Oversight): ✅ {{coverage}}%
- Art. 15 (Accuracy/Robustness): ✅ {{coverage}}%

## Recommendations
{{#recommendations}}
- {{text}}
{{/recommendations}}

---
*Generated at {{generated_at}} by AgentsFactory Compliance Engine v{{version}}*
```

### 4.2 Weekly Compliance Digest

```markdown
# Weekly Compliance Digest — {{week_start}} to {{week_end}}

## Week at a Glance
| Metric | This Week | Last Week | Δ | Status |
|--------|-----------|-----------|---|--------|
| Total decisions | {{total}} | {{prev_total}} | {{delta}} | {{status}} |
| Violation rate | {{rate}}% | {{prev_rate}}% | {{delta}} | {{status}} |
| Critical incidents | {{critical}} | {{prev_critical}} | {{delta}} | {{status}} |
| Avg compliance score | {{score}} | {{prev_score}} | {{delta}} | {{status}} |
| New agents detected | {{new_agents}} | — | — | {{status}} |

## Trend Analysis
- **Decision volume**: {{trend_description}} ({{chart_link}})
- **Risk distribution**: {{risk_distribution_description}}
- **Model performance**: {{model_performance_summary}}

## Violation Breakdown
### By Rule
| Rule | Mon | Tue | Wed | Thu | Fri | Sat | Sun | Total |
|------|-----|-----|-----|-----|-----|-----|-----|-------|
| {{rule_name}} | {{counts}} | ... | ... | ... | ... | ... | ... | {{total}} |

### By Agent
| Agent | Violations | Most Common Rule | Risk Level |
|-------|-----------|------------------|------------|
| {{agent}} | {{count}} | {{rule}} | {{risk}} |

## EU AI Act Compliance Status
| Article | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| Art. 12 | Record-keeping | ✅/⚠️/❌ | {{notes}} |
| Art. 13 | Transparency | ✅/⚠️/❌ | {{notes}} |
| Art. 14 | Human oversight | ✅/⚠️/❌ | {{notes}} |
| Art. 15 | Accuracy & robustness | ✅/⚠️/❌ | {{notes}} |
| Art. 16 | Technical documentation | ✅/⚠️/❌ | {{notes}} |
| Art. 17 | Record-keeping (providers) | ✅/⚠️/❌ | {{notes}} |

## Model Version Report
| Model | Version | Deployed | Decisions | Avg Confidence | Status |
|-------|---------|----------|-----------|----------------|--------|
| {{model}} | {{version}} | {{date}} | {{count}} | {{conf}} | {{status}} |

## Data Retention Compliance
- Events in active phase: {{active_count}}
- Events pending anonymization: {{pending_anon}}
- Events purged this week: {{purged}}
- Storage utilization: {{storage_gb}} GB ({{storage_pct}}%)

## Action Items
{{#action_items}}
- [ ] **{{priority}}**: {{description}} (Owner: {{owner}}, Due: {{due_date}})
{{/action_items}}

## Appendix
- Full event log: {{log_link}}
- Raw metrics: {{metrics_link}}
- Incident details: {{incident_link}}

---
*Generated at {{generated_at}} | Next report: {{next_report_date}}*
```

### 4.3 Incident Report

```markdown
# Incident Report — {{incident_id}}

## Classification
| Field | Value |
|-------|-------|
| **Incident ID** | {{incident_id}} |
| **Severity** | {{severity}} ({{severity_level}}/5) |
| **Status** | {{status}} |
| **Detected At** | {{detected_at}} |
| **Resolved At** | {{resolved_at}} |
| **Duration** | {{duration}} |
| **Affected Users** | {{affected_users}} |
| **Affected Agents** | {{affected_agents}} |
| **Regulatory Impact** | {{regulatory_impact}} |

## Incident Summary
{{summary}}

## Triggering Event(s)
| Event ID | Timestamp | Agent | Action | Risk Score |
|----------|-----------|-------|--------|------------|
| {{event_id}} | {{timestamp}} | {{agent}} | {{action}} | {{risk}} |

## Rules Triggered
| Rule ID | Rule Name | Severity | Details |
|---------|-----------|----------|---------|
| {{rule_id}} | {{rule_name}} | {{severity}} | {{details}} |

## Timeline
| Time | Event | Actor | Details |
|------|-------|-------|---------|
| {{time}} | {{event_type}} | {{actor}} | {{details}} |

## Impact Assessment
### Data Exposure
- **PII exposed**: {{yes/no}}
- **Types of data**: {{types}}
- **Records affected**: {{count}}
- **Data classification**: {{classification}}

### Decision Impact
- **Affected decisions**: {{count}}
- **Automated decisions with legal effect**: {{count}}
- **Users notified**: {{yes/no}}

### Regulatory Impact
- **EU AI Act articles violated**: {{articles}}
- **GDPR articles violated**: {{articles}}
- **Notification required (72hr)**: {{yes/no}}
- **DPA notified**: {{yes/no/pending}}
- **Users notified**: {{yes/no/pending}}

## Root Cause Analysis
{{root_cause}}

## Remediation Actions
| Action | Owner | Status | Deadline |
|--------|-------|--------|----------|
| {{action}} | {{owner}} | {{status}} | {{deadline}} |

## Evidence
### Audit Event Chain
```json
{{evidence_events}}
```

### Hash Verification
- **Chain integrity**: {{integrity_status}}
- **First event hash**: {{first_hash}}
- **Last event hash**: {{last_hash}}
- **Verification method**: SHA-256 chain

## Lessons Learned
{{lessons_learned}}

## Sign-Off
| Role | Name | Date | Signature |
|------|------|------|-----------|
| Incident Commander | {{name}} | {{date}} | {{sig}} |
| Compliance Officer | {{name}} | {{date}} | {{sig}} |
| CISO | {{name}} | {{date}} | {{sig}} |

---
*Report generated at {{generated_at}} | Classification: {{classification}}*
```

---

## 5. Implementation Notes

### 5.1 Storage Requirements

| Component | Estimated Volume | Storage Type |
|-----------|-----------------|--------------|
| Audit events (production) | ~1-5 GB/day | Append-only log (e.g., Kafka → S3/MinIO) |
| Compliance rules engine | < 100 MB | In-memory (Redis/embedded) |
| Aggregated reports | ~50 MB/month | PostgreSQL |
| Incident reports | ~10 MB/year | Immutable object storage |

### 5.2 Performance Requirements

- **Audit event ingestion**: < 10ms p99 latency
- **Rule evaluation**: < 5ms per event (all 15 rules)
- **Report generation**: < 30s for daily, < 2min for weekly
- **Incident detection**: < 1s from event to alert

### 5.3 Security Requirements

- All audit events encrypted at rest (AES-256)
- Audit logs are append-only (no delete/modify except via retention purge)
- Hash chain integrity verification on every read
- Access to PII fields requires role-based access (RBAC)
- Audit log access itself generates audit events

### 5.4 EU AI Act Specific Mapping

| Requirement | Schema Field | Rule |
|-------------|-------------|------|
| Art. 12(1) — Record-keeping | Entire event | RULE-015 |
| Art. 12(2) — Integrity | event_id + hash chain | RULE-015 |
| Art. 12(3) — Retention | retention_policy + timestamp | RULE-005 |
| Art. 13(1) — Transparency | consent_flags, output_summary | RULE-002, RULE-012 |
| Art. 13(2)(f) — Right to explanation | consent_flags.right_to_explanation | RULE-012 |
| Art. 14 — Human oversight | human_review, risk_score | RULE-006 |
| Art. 15(1) — Accuracy | confidence_score | RULE-003 |
| Art. 15(2) — Monitoring | model_version, timestamp | RULE-009, RULE-013 |
| Art. 16 — Technical documentation | model_version, agent_name, compliance_tags | All rules |

---

*Schema version 1.0.0 — Last updated 2026-06-21*
