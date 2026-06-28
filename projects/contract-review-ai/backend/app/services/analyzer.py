import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from app.services.playbook import PlaybookEngine, ClauseRiskLevel
from app.services.parser import ClauseExtractor


@dataclass
class ClauseAnalysisResult:
    clause_name: str
    clause_text: str
    risk_level: ClauseRiskLevel
    issues: List[str] = field(default_factory=list)
    matched_rules: List[str] = field(default_factory=list)
    redline_suggestion: Optional[str] = None
    explanation: Optional[str] = None
    confidence: float = 0.8


@dataclass
class RiskSummary:
    total_clauses: int
    high_risk: int
    medium_risk: int
    low_risk: int
    approved: int
    overall_risk_score: float
    risk_breakdown: Dict[str, int] = field(default_factory=dict)


class ContractAnalyzer:
    """Analyze contracts against playbook rules"""
    
    def __init__(self, playbook_engine: Optional[PlaybookEngine] = None):
        self.playbook_engine = playbook_engine or PlaybookEngine()
        self.clause_extractor = ClauseExtractor()
    
    def analyze(
        self, 
        contract_text: str, 
        contract_type: str = "nda",
        playbook_name: Optional[str] = None
    ) -> tuple[List[ClauseAnalysisResult], RiskSummary]:
        """Analyze contract text against playbook"""
        
        # Get playbook
        if playbook_name:
            playbook = self.playbook_engine.get_playbook(playbook_name)
            if not playbook:
                playbook = self.playbook_engine.get_default_playbook(contract_type)
        else:
            playbook = self.playbook_engine.get_default_playbook(contract_type)
        
        # Extract clauses from contract
        extracted_clauses = self.clause_extractor.extract_clauses(contract_text)
        
        # Analyze each clause against playbook rules
        analysis_results = []
        
        for extracted in extracted_clauses:
            result = self._analyze_clause(extracted, playbook, contract_text)
            analysis_results.append(result)
        
        # Check for missing required clauses
        missing_clauses = self._check_missing_clauses(extracted_clauses, playbook)
        for missing in missing_clauses:
            analysis_results.append(missing)
        
        # Generate risk summary
        risk_summary = self._generate_risk_summary(analysis_results)
        
        return analysis_results, risk_summary
    
    def _analyze_clause(
        self, 
        extracted: Dict[str, Any], 
        playbook, 
        full_text: str
    ) -> ClauseAnalysisResult:
        """Analyze a single extracted clause against playbook rules"""
        clause_name = extracted["clause_name"]
        clause_text = extracted["clause_text"]
        
        # Find matching rule in playbook
        matching_rule = None
        for rule in playbook.rules:
            if rule.clause_name == clause_name and rule.is_active:
                matching_rule = rule
                break
        
        if not matching_rule:
            # No rule for this clause - default to low risk
            return ClauseAnalysisResult(
                clause_name=clause_name,
                clause_text=clause_text,
                risk_level=ClauseRiskLevel.LOW,
                confidence=0.5,
            )
        
        # Check required elements
        issues = []
        clause_lower = clause_text.lower()
        
        for required in matching_rule.required_elements:
            if required.lower() not in clause_lower:
                issues.append(f"Missing required element: {required}")
        
        # Check forbidden elements
        for forbidden in matching_rule.forbidden_elements:
            if forbidden.lower() in clause_lower:
                issues.append(f"Contains forbidden element: {forbidden}")
        
        # Determine risk level based on issues
        if issues:
            risk_level = matching_rule.risk_level
        else:
            risk_level = ClauseRiskLevel.APPROVED
        
        return ClauseAnalysisResult(
            clause_name=clause_name,
            clause_text=clause_text,
            risk_level=risk_level,
            issues=issues,
            matched_rules=[matching_rule.clause_name],
            redline_suggestion=matching_rule.redline_suggestion if issues else None,
            explanation=matching_rule.explanation if issues else None,
            confidence=0.85,
        )
    
    def _check_missing_clauses(
        self, 
        extracted_clauses: List[Dict[str, Any]], 
        playbook
    ) -> List[ClauseAnalysisResult]:
        """Check for required clauses that are missing from the contract"""
        extracted_names = {c["clause_name"] for c in extracted_clauses}
        missing = []
        
        for rule in playbook.rules:
            if rule.is_active and rule.clause_name not in extracted_names:
                # Check if this clause is required (has required_elements)
                if rule.required_elements:
                    missing.append(ClauseAnalysisResult(
                        clause_name=rule.clause_name,
                        clause_text="",
                        risk_level=ClauseRiskLevel.HIGH,
                        issues=[f"Required clause '{rule.clause_name}' is missing from contract"],
                        matched_rules=[rule.clause_name],
                        redline_suggestion=rule.redline_suggestion,
                        explanation=rule.explanation,
                        confidence=0.9,
                    ))
        
        return missing
    
    def _generate_risk_summary(self, results: List[ClauseAnalysisResult]) -> RiskSummary:
        """Generate risk summary from analysis results"""
        high = sum(1 for r in results if r.risk_level == ClauseRiskLevel.HIGH)
        medium = sum(1 for r in results if r.risk_level == ClauseRiskLevel.MEDIUM)
        low = sum(1 for r in results if r.risk_level == ClauseRiskLevel.LOW)
        approved = sum(1 for r in results if r.risk_level == ClauseRiskLevel.APPROVED)
        total = len(results)
        
        # Calculate overall risk score (0-100)
        if total == 0:
            overall_score = 0.0
        else:
            # Weight: HIGH=100, MEDIUM=60, LOW=20, APPROVED=0
            weights = {
                ClauseRiskLevel.HIGH: 100,
                ClauseRiskLevel.MEDIUM: 60,
                ClauseRiskLevel.LOW: 20,
                ClauseRiskLevel.APPROVED: 0,
            }
            weighted_sum = sum(weights[r.risk_level] for r in results)
            overall_score = weighted_sum / total
        
        risk_breakdown = {}
        for r in results:
            risk_breakdown[r.risk_level.value] = risk_breakdown.get(r.risk_level.value, 0) + 1
        
        return RiskSummary(
            total_clauses=total,
            high_risk=high,
            medium_risk=medium,
            low_risk=low,
            approved=approved,
            overall_risk_score=round(overall_score, 1),
            risk_breakdown=risk_breakdown,
        )


class LLMAnalyzer:
    """Use local LLM (Ollama) for enhanced clause analysis"""
    
    def __init__(self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                import ollama
                self._client = ollama.Client(host=self.base_url)
            except ImportError:
                self._client = False
        return self._client
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        if not self.client:
            return False
        try:
            models = self.client.list()
            return any(self.model in m.get("name", "") for m in models.get("models", []))
        except Exception:
            return False
    
    def analyze_clause_with_llm(
        self, 
        clause_name: str, 
        clause_text: str, 
        playbook_rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to analyze clause against playbook rule"""
        if not self.is_available():
            return {"error": "LLM not available"}
        
        prompt = f"""You are a legal contract analyst. Analyze the following clause against the playbook rule.

Clause Name: {clause_name}
Clause Text: {clause_text[:1500]}

Playbook Rule:
- Required Elements: {playbook_rule.get('required_elements', [])}
- Forbidden Elements: {playbook_rule.get('forbidden_elements', [])}
- Risk Level: {playbook_rule.get('risk_level', 'medium')}
- Redline Suggestion: {playbook_rule.get('redline_suggestion', 'N/A')}
- Explanation: {playbook_rule.get('explanation', 'N/A')}

Provide a JSON response with:
{{
    "risk_level": "high|medium|low|approved",
    "issues": ["list of specific issues found"],
    "confidence": 0.0-1.0,
    "redline_suggestion": "specific redline text if issues found",
    "explanation": "why this risk level was assigned"
}}"""
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
                options={"temperature": 0.1}
            )
            return json.loads(response["message"]["content"])
        except Exception as e:
            return {"error": str(e)}
    
    def extract_clauses_with_llm(self, contract_text: str) -> List[Dict[str, Any]]:
        """Use LLM to extract and identify clauses"""
        if not self.is_available():
            return []
        
        prompt = f"""Extract all legal clauses from this contract. Return JSON array of clauses with:
- clause_name: standard name (confidentiality, term, termination, liability_cap, indemnification, governing_law, assignment, non_solicit, non_compete, data_protection, force_majeure, dispute_resolution, ip_ownership, payment_terms, other)
- clause_text: the full clause text (max 2000 chars)
- confidence: 0.0-1.0

Contract:
{contract_text[:8000]}

Return only JSON array."""
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
                options={"temperature": 0.1}
            )
            return json.loads(response["message"]["content"])
        except Exception:
            return []