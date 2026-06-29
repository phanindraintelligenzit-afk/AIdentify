"""Assessment service - manages vendor assessments lifecycle."""
from datetime import datetime

ASSESSMENT_TEMPLATES = {
    "standard": {
        "name": "Standard Vendor Risk Assessment",
        "categories": {
            "security": {
                "questions": {
                    "q1": "Does the vendor have SOC 2 Type II or ISO 27001 certification?",
                    "q2": "Does the vendor encrypt data at rest and in transit?",
                    "q3": "Does the vendor have a documented incident response plan?",
                    "q4": "Does the vendor perform regular penetration testing?",
                }
            },
            "compliance": {
                "questions": {
                    "q1": "Is the vendor GDPR compliant?",
                    "q2": "Does the vendor sign Data Processing Agreements?",
                    "q3": "Has the vendor had any regulatory violations in the past 2 years?",
                }
            },
            "financial": {
                "questions": {
                    "q1": "Is the vendor financially stable (profitable or well-funded)?",
                    "q2": "Does the vendor have business liability insurance?",
                }
            },
            "data_privacy": {
                "questions": {
                    "q1": "Does the vendor have a published privacy policy?",
                    "q2": "Does the vendor minimize data collection?",
                    "q3": "Can the vendor delete all data upon contract termination?",
                }
            },
            "business_continuity": {
                "questions": {
                    "q1": "Does the vendor have a documented BCP/DR plan?",
                    "q2": "What is the vendor's guaranteed uptime SLA?",
                }
            },
        }
    },
    "quick": {
        "name": "Quick Vendor Screening",
        "categories": {
            "security": {"questions": {"q1": "Does the vendor have security certifications?", "q2": "Does the vendor use encryption?"}},
            "compliance": {"questions": {"q1": "Is the vendor GDPR/CCPA compliant?"}},
            "financial": {"questions": {"q1": "Is the vendor financially stable?"}},
        }
    },
    "critical": {
        "name": "Critical Vendor Deep Assessment",
        "categories": {
            "security": {
                "questions": {
                    "q1": "Does the vendor have SOC 2 Type II?",
                    "q2": "Does the vendor encrypt data at rest and in transit?",
                    "q3": "Does the vendor have a 24/7 SOC?",
                    "q4": "Does the vendor perform annual pen tests?",
                    "q5": "Does the vendor have a bug bounty program?",
                }
            },
            "compliance": {
                "questions": {
                    "q1": "Is the vendor GDPR, CCPA, HIPAA compliant?",
                    "q2": "Does the vendor undergo annual compliance audits?",
                    "q3": "Any data breaches in the past 3 years?",
                }
            },
            "financial": {
                "questions": {
                    "q1": "Is the vendor profitable with 12+ months runway?",
                    "q2": "Does the vendor carry cyber liability insurance?",
                    "q3": "Has the vendor ever filed for bankruptcy?",
                }
            },
            "operational": {
                "questions": {
                    "q1": "Does the vendor have geographic redundancy?",
                    "q2": "What is the vendor's historical uptime?",
                    "q3": "Does the vendor provide 24/7 support?",
                }
            },
            "data_privacy": {
                "questions": {
                    "q1": "Does the vendor have a Data Protection Officer?",
                    "q2": "Does the vendor support data portability?",
                    "q3": "Does the vendor conduct Privacy Impact Assessments?",
                }
            },
            "business_continuity": {
                "questions": {
                    "q1": "Does the vendor have a tested BCP with RTO < 4hrs?",
                    "q2": "Does the vendor perform annual DR drills?",
                    "q3": "Contractual liability for downtime?",
                }
            },
        }
    }
}


def get_template(template_name="standard"):
    return ASSESSMENT_TEMPLATES.get(template_name, ASSESSMENT_TEMPLATES["standard"])


def get_all_templates():
    return [
        {"name": k, "name_display": v["name"], "category_count": len(v["categories"])}
        for k, v in ASSESSMENT_TEMPLATES.items()
    ]


def process_assessment_responses(responses):
    from services.risk_scorer import calculate_assessment_score, generate_risk_recommendations
    score, risk_level = calculate_assessment_score(responses)
    recommendations = generate_risk_recommendations(responses)
    return {
        "score": score,
        "risk_level": risk_level,
        "recommendations": recommendations,
        "processed_at": datetime.utcnow().isoformat(),
    }
