"""Core DSAR processing service."""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DSARProcessor:
    """Main service for processing Data Subject Access Requests."""

    def __init__(self):
        self.gdpr_deadline_days = 30
        self.ccpa_deadline_days = 45

    def calculate_deadline(self, received_at: datetime, regulation: str = "gdpr") -> datetime:
        """Calculate legal deadline based on regulation."""
        days = self.gdpr_deadline_days if regulation == "gdpr" else self.ccpa_deadline_days
        return received_at + timedelta(days=days)

    def calculate_days_remaining(self, deadline: datetime) -> int:
        """Calculate days until deadline."""
        now = datetime.now(timezone.utc)
        delta = deadline - now
        return max(0, delta.days)

    def assess_risk(self, request_data: dict) -> str:
        """Assess risk level of a DSAR request."""
        risk_score = 0
        if request_data.get("records_found_count", 0) > 1000:
            risk_score += 2
        sensitive_categories = {"financial_data", "health_data", "biometric"}
        found_categories = set(request_data.get("data_categories_found", []))
        if found_categories & sensitive_categories:
            risk_score += 3
        description = request_data.get("description", "").lower()
        if any(word in description for word in ["lawyer", "legal", "court", "complaint", "regulator"]):
            risk_score += 2
        if request_data.get("has_third_party_data"):
            risk_score += 1
        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        return "low"

    def classify_request_type(self, description: str) -> str:
        """Auto-classify the type of DSAR from description."""
        description = description.lower()
        if any(w in description for w in ["delete", "remove", "erase", "forget"]):
            return "erasure"
        elif any(w in description for w in ["correct", "update", "fix", "change"]):
            return "rectification"
        elif any(w in description for w in ["export", "download", "port", "transfer"]):
            return "portability"
        elif any(w in description for w in ["stop", "unsubscribe", "object", "opt out"]):
            return "objection"
        else:
            return "access"

    def generate_response_summary(self, discovery_results: List[dict]) -> dict:
        """Generate a summary of discovered data for response."""
        categories = {}
        total_records = 0
        for result in discovery_results:
            cat = result.get("data_category", "unknown")
            categories[cat] = categories.get(cat, 0) + result.get("records_count", 0)
            total_records += result.get("records_count", 0)
        return {
            "total_records": total_records,
            "categories": categories,
            "systems_scanned": len(set(r.get("source_system") for r in discovery_results)),
            "pii_found": any(r.get("contains_pii") for r in discovery_results),
            "third_party_data_found": any(r.get("contains_third_party_data") for r in discovery_results),
        }

    def should_escalate(self, dsar_data: dict) -> bool:
        """Determine if a DSAR should be escalated to senior review."""
        days_remaining = dsar_data.get("days_remaining", 999)
        status = dsar_data.get("status", "")
        if days_remaining <= 3 and status not in ("completed", "rejected"):
            return True
        if dsar_data.get("risk_level") == "high":
            return True
        return False


dsar_processor = DSARProcessor()
