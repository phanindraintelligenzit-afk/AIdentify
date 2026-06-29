"""Risk scoring engine - calculates vendor risk scores from assessment responses and findings."""
from typing import Optional

# Category weights for risk scoring
CATEGORY_WEIGHTS = {
    "security": 0.25,
    "compliance": 0.20,
    "financial": 0.15,
    "operational": 0.15,
    "data_privacy": 0.15,
    "business_continuity": 0.10,
}

# Severity point values
SEVERITY_POINTS = {
    "critical": 25,
    "high": 15,
    "medium": 8,
    "low": 3,
}

HIGH_RISK_THRESHOLD = 75
MEDIUM_RISK_THRESHOLD = 45


def calculate_assessment_score(responses):
    """Calculate risk score from assessment responses. Returns (score, risk_level)."""
    if not responses:
        return 50.0, "medium"
    
    category_scores = {}
    for category, questions in responses.items():
        if isinstance(questions, dict):
            scores = [v for v in questions.values() if isinstance(v, (int, float))]
            if scores:
                avg = sum(scores) / len(scores)
                category_scores[category] = avg
    
    if not category_scores:
        return 50.0, "medium"
    
    weighted_risk = 0
    total_weight = 0
    for category, avg_score in category_scores.items():
        weight = CATEGORY_WEIGHTS.get(category, 0.10)
        risk = ((5 - avg_score) / 4) * 100
        weighted_risk += risk * weight
        total_weight += weight
    
    if total_weight > 0:
        final_score = weighted_risk / total_weight
    else:
        final_score = 50.0
    
    final_score = round(max(0, min(100, final_score)), 1)
    risk_level = score_to_risk_level(final_score)
    return final_score, risk_level


def score_to_risk_level(score):
    """Convert numeric score to risk level label."""
    if score >= HIGH_RISK_THRESHOLD:
        return "high"
    elif score >= MEDIUM_RISK_THRESHOLD:
        return "medium"
    else:
        return "low"


def calculate_vendor_risk_score(assessment_score, open_findings, is_critical=False):
    """Calculate overall vendor risk score combining assessment results and active findings."""
    base = assessment_score if assessment_score is not None else 50.0
    
    finding_penalty = 0
    for finding in open_findings:
        severity = finding.get("severity", "medium")
        finding_penalty += SEVERITY_POINTS.get(severity, 5)
    
    finding_penalty = min(finding_penalty, 40)
    critical_bonus = 10 if is_critical else 0
    final_score = min(100, base + finding_penalty + critical_bonus)
    final_score = round(max(0, final_score), 1)
    risk_level = score_to_risk_level(final_score)
    
    if final_score >= 90:
        risk_level = "critical"
    
    return final_score, risk_level


def generate_risk_recommendations(responses):
    """Generate recommendations based on low-scoring areas."""
    recommendations = []
    for category, questions in responses.items():
        if not isinstance(questions, dict):
            continue
        for question_id, score in questions.items():
            if isinstance(score, (int, float)) and score <= 2:
                recommendations.append({
                    "category": category,
                    "question": question_id,
                    "severity": "high" if score == 1 else "medium",
                    "recommendation": _get_recommendation_text(category),
                })
    return recommendations


def _get_recommendation_text(category):
    """Get human-readable recommendation for a low-scoring area."""
    recs = {
        "security": "Request SOC 2 Type II report or equivalent security certification.",
        "compliance": "Verify regulatory compliance status. Request compliance documentation.",
        "financial": "Request financial statements or credit report.",
        "operational": "Review operational resilience plan.",
        "data_privacy": "Verify GDPR/CCPA compliance. Request data processing agreement.",
        "business_continuity": "Request business continuity and disaster recovery plan.",
    }
    return recs.get(category, f"Review and address concerns in {category}")
