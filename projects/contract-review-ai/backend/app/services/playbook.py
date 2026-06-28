import yaml
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ClauseRiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    APPROVED = "approved"


@dataclass
class ClauseRule:
    clause_name: str
    clause_patterns: List[str] = field(default_factory=list)
    required_elements: List[str] = field(default_factory=list)
    forbidden_elements: List[str] = field(default_factory=list)
    risk_level: ClauseRiskLevel = ClauseRiskLevel.MEDIUM
    redline_suggestion: Optional[str] = None
    explanation: Optional[str] = None
    is_active: bool = True
    order: int = 0


@dataclass
class Playbook:
    name: str
    description: str = ""
    contract_type: str = "other"
    rules: List[ClauseRule] = field(default_factory=list)
    is_default: bool = False
    is_active: bool = True


class PlaybookEngine:
    """Engine for managing and applying playbooks to contract analysis"""
    
    DEFAULT_NDA_PLAYBOOK = {
        "name": "Standard NDA Playbook",
        "description": "Standard NDA playbook for mutual NDAs",
        "contract_type": "nda",
        "rules": [
            {
                "clause_name": "confidentiality",
                "clause_patterns": ["confidential", "non-disclosure", "proprietary information", "trade secrets"],
                "required_elements": ["definition of confidential information", "exceptions", "permitted disclosures"],
                "forbidden_elements": ["unilateral confidentiality (only one party protected)", "perpetual confidentiality without sunset"],
                "risk_level": "high",
                "redline_suggestion": "Make confidentiality mutual. Add sunset clause (2-3 years). Define confidential information clearly.",
                "explanation": "NDAs should protect both parties equally. Perpetual confidentiality is rarely enforceable.",
                "order": 1
            },
            {
                "clause_name": "term",
                "clause_patterns": ["term", "duration", "period of agreement"],
                "required_elements": ["start date", "end date or duration"],
                "forbidden_elements": ["perpetual term", "auto-renewal without notice"],
                "risk_level": "medium",
                "redline_suggestion": "Limit term to 2-3 years with clear start/end dates. Require 30-day notice for renewal.",
                "explanation": "NDAs typically last 2-3 years. Perpetual terms are unreasonable for most business relationships.",
                "order": 2
            },
            {
                "clause_name": "termination",
                "clause_patterns": ["terminat", "expir"],
                "required_elements": ["termination for convenience", "notice period"],
                "forbidden_elements": ["no termination right", "termination only for cause"],
                "risk_level": "medium",
                "redline_suggestion": "Add 30-day termination for convenience clause for both parties.",
                "explanation": "Both parties should be able to terminate with reasonable notice.",
                "order": 3
            },
            {
                "clause_name": "governing_law",
                "clause_patterns": ["governing law", "choice of law", "jurisdiction"],
                "required_elements": ["specified jurisdiction", "specified venue"],
                "forbidden_elements": ["foreign jurisdiction unfavorable to client"],
                "risk_level": "low",
                "redline_suggestion": "Set governing law to client's home state (e.g., Delaware, California).",
                "explanation": "Governing law should be predictable and favorable to client.",
                "order": 4
            },
            {
                "clause_name": "assignment",
                "clause_patterns": ["assign", "transfer", "delegate"],
                "required_elements": ["consent required for assignment"],
                "forbidden_elements": ["unrestricted assignment", "assignment to competitors without consent"],
                "risk_level": "low",
                "redline_suggestion": "Require written consent for assignment. Carve-out for affiliates and successors.",
                "explanation": "Assignment should require consent to prevent unwanted third parties.",
                "order": 5
            },
        ]
    }
    
    DEFAULT_MSA_PLAYBOOK = {
        "name": "Standard MSA Playbook",
        "description": "Standard MSA playbook for master services agreements",
        "contract_type": "msa",
        "rules": [
            {
                "clause_name": "liability_cap",
                "clause_patterns": ["limitation of liability", "liability cap", "maximum liability", "cap on damages"],
                "required_elements": ["cap amount", "carve-outs for IP breach, confidentiality, indemnification"],
                "forbidden_elements": ["unlimited liability", "cap below 12 months fees", "no carve-outs"],
                "risk_level": "high",
                "redline_suggestion": "Cap liability at 12 months fees. Carve out IP infringement, confidentiality breach, indemnification obligations.",
                "explanation": "Liability cap should be at least 12 months fees with standard carve-outs.",
                "order": 1
            },
            {
                "clause_name": "indemnification",
                "clause_patterns": ["indemnif", "hold harmless"],
                "required_elements": ["mutual indemnification", "IP infringement indemnification", "confidentiality breach indemnification"],
                "forbidden_elements": ["unilateral indemnification", "no IP indemnification", "no cap on indemnification"],
                "risk_level": "high",
                "redline_suggestion": "Make indemnification mutual. Add IP infringement and confidentiality breach indemnification. Cap indemnification at liability cap.",
                "explanation": "Indemnification should be mutual with standard carve-outs. Unilateral indemnification favors vendor.",
                "order": 2
            },
            {
                "clause_name": "termination",
                "clause_patterns": ["terminat", "expir"],
                "required_elements": ["termination for convenience (30-90 days)", "termination for cause (30-day cure)", "effect of termination"],
                "forbidden_elements": ["no termination for convenience", "termination only for cause", "immediate termination without cure"],
                "risk_level": "high",
                "redline_suggestion": "Add 60-day termination for convenience. 30-day cure period for cause. Define post-termination obligations.",
                "explanation": "MSAs need clear termination rights. No termination for convenience traps client.",
                "order": 3
            },
            {
                "clause_name": "data_protection",
                "clause_patterns": ["data protection", "privacy", "personal data", "gdpr", "ccpa"],
                "required_elements": ["DPA reference", "data processing terms", "security obligations", "breach notification"],
                "forbidden_elements": ["no DPA", "no breach notification", "vendor owns customer data"],
                "risk_level": "high",
                "redline_suggestion": "Reference DPA. Require GDPR/CCPA compliance. 72-hour breach notification. Customer owns data.",
                "explanation": "Data protection terms are mandatory for modern MSAs. Vendor must not own customer data.",
                "order": 4
            },
            {
                "clause_name": "ip_ownership",
                "clause_patterns": ["intellectual property", "ip ownership", "work product", "deliverables"],
                "required_elements": ["client owns deliverables", "vendor retains background IP", "license grant for background IP"],
                "forbidden_elements": ["vendor owns deliverables", "no license grant", "broad IP assignment to vendor"],
                "risk_level": "high",
                "redline_suggestion": "Client owns all deliverables. Vendor retains background IP with broad license grant to client.",
                "explanation": "Client should own work product. Vendor gets license to use background IP in deliverables.",
                "order": 5
            },
            {
                "clause_name": "payment_terms",
                "clause_patterns": ["payment", "fees", "invoicing", "net 30", "net 60"],
                "required_elements": ["payment terms (Net 30)", "late payment interest", "dispute process"],
                "forbidden_elements": ["Net 60+ without justification", "no late payment terms", "vendor can suspend without notice"],
                "risk_level": "medium",
                "redline_suggestion": "Net 30 payment terms. 1.5%/month late fee. 15-day notice before suspension.",
                "explanation": "Standard payment terms are Net 30. Net 60+ hurts vendor cash flow.",
                "order": 6
            },
            {
                "clause_name": "governing_law",
                "clause_patterns": ["governing law", "choice of law", "jurisdiction"],
                "required_elements": ["specified jurisdiction", "specified venue"],
                "forbidden_elements": ["foreign jurisdiction unfavorable to client"],
                "risk_level": "low",
                "redline_suggestion": "Set governing law to client's home state (e.g., Delaware, California).",
                "explanation": "Governing law should be predictable and favorable to client.",
                "order": 7
            },
        ]
    }
    
    def __init__(self):
        self.playbooks: Dict[str, Playbook] = {}
        self._load_defaults()
    
    def _load_defaults(self):
        """Load default playbooks"""
        self.playbooks["default_nda"] = self._dict_to_playbook(self.DEFAULT_NDA_PLAYBOOK)
        self.playbooks["default_msa"] = self._dict_to_playbook(self.DEFAULT_MSA_PLAYBOOK)
    
    def _dict_to_playbook(self, data: Dict[str, Any]) -> Playbook:
        rules = []
        for rule_data in data.get("rules", []):
            rules.append(ClauseRule(
                clause_name=rule_data["clause_name"],
                clause_patterns=rule_data.get("clause_patterns", []),
                required_elements=rule_data.get("required_elements", []),
                forbidden_elements=rule_data.get("forbidden_elements", []),
                risk_level=ClauseRiskLevel(rule_data.get("risk_level", "medium")),
                redline_suggestion=rule_data.get("redline_suggestion"),
                explanation=rule_data.get("explanation"),
                order=rule_data.get("order", 0),
            ))
        return Playbook(
            name=data["name"],
            description=data.get("description", ""),
            contract_type=data.get("contract_type", "other"),
            rules=rules,
            is_default=data.get("is_default", False),
            is_active=data.get("is_active", True),
        )
    
    def load_from_yaml(self, yaml_content: str) -> Playbook:
        """Load playbook from YAML string"""
        data = yaml.safe_load(yaml_content)
        playbook = self._dict_to_playbook(data)
        self.playbooks[playbook.name] = playbook
        return playbook
    
    def load_from_json(self, json_content: str) -> Playbook:
        """Load playbook from JSON string"""
        data = json.loads(json_content)
        playbook = self._dict_to_playbook(data)
        self.playbooks[playbook.name] = playbook
        return playbook
    
    def get_playbook(self, name: str) -> Optional[Playbook]:
        """Get playbook by name"""
        return self.playbooks.get(name)
    
    def get_default_playbook(self, contract_type: str) -> Playbook:
        """Get default playbook for contract type"""
        if contract_type == "nda":
            return self.playbooks["default_nda"]
        elif contract_type == "msa":
            return self.playbooks["default_msa"]
        return self.playbooks["default_nda"]
    
    def to_yaml(self, playbook: Playbook) -> str:
        """Export playbook to YAML"""
        data = {
            "name": playbook.name,
            "description": playbook.description,
            "contract_type": playbook.contract_type,
            "rules": [
                {
                    "clause_name": rule.clause_name,
                    "clause_patterns": rule.clause_patterns,
                    "required_elements": rule.required_elements,
                    "forbidden_elements": rule.forbidden_elements,
                    "risk_level": rule.risk_level.value,
                    "redline_suggestion": rule.redline_suggestion,
                    "explanation": rule.explanation,
                    "is_active": rule.is_active,
                    "order": rule.order,
                }
                for rule in playbook.rules
            ]
        }
        return yaml.dump(data, sort_keys=False)
    
    def to_json(self, playbook: Playbook) -> str:
        """Export playbook to JSON"""
        data = {
            "name": playbook.name,
            "description": playbook.description,
            "contract_type": playbook.contract_type,
            "rules": [
                {
                    "clause_name": rule.clause_name,
                    "clause_patterns": rule.clause_patterns,
                    "required_elements": rule.required_elements,
                    "forbidden_elements": rule.forbidden_elements,
                    "risk_level": rule.risk_level.value,
                    "redline_suggestion": rule.redline_suggestion,
                    "explanation": rule.explanation,
                    "is_active": rule.is_active,
                    "order": rule.order,
                }
                for rule in playbook.rules
            ]
        }
        return json.dumps(data, indent=2)