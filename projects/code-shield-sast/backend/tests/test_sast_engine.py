"""Tests for the SAST scanning engine."""
import os
import sys
import pytest
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.sast_engine import SASTScanner, Rule, Severity


@pytest.fixture
def scanner():
    return SASTScanner()


class TestSASTEngine:
    """Test the core scanning engine."""
    
    def test_scanner_initialization(self, scanner):
        """Scanner loads all rules on init."""
        assert scanner.rule_count > 0
        assert scanner.rule_count >= 15
    
    def test_no_vulnerabilities_in_safe_code(self, scanner):
        """Clean code should produce zero findings."""
        code = """
def hello(name):
    return f"Hello, {name}!"

def add(a, b):
    return a + b
"""
        matches = scanner.scan_code(code, "safe.py")
        assert len(matches) == 0
    
    def test_detects_sql_injection(self, scanner):
        """Should detect SQL injection via string concatenation."""
        code = """
import sqlite3
def get_user(user_id):
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = " + user_id)
    return cursor.fetchone()
"""
        matches = scanner.scan_code(code, "vulnerable.py")
        sql_findings = [m for m in matches if m.rule_id in ("CSAST-001", "CSAST-002")]
        assert len(sql_findings) >= 1
    
    def test_detects_hardcoded_secret(self, scanner):
        """Should detect hardcoded API keys."""
        code = """
api_key = "sk_live_1234567890abcdef"
secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
"""
        matches = scanner.scan_code(code, "config.py")
        secret_findings = [m for m in matches if m.rule_id == "CSAST-010"]
        assert len(secret_findings) >= 1
    
    def test_detects_eval_usage(self, scanner):
        """Should detect dangerous eval() calls."""
        code = """
def process(user_input):
    result = eval(user_input)
    return result
"""
        matches = scanner.scan_code(code, "danger.py")
        eval_findings = [m for m in matches if m.rule_id == "CSAST-005"]
        assert len(eval_findings) >= 1
    
    def test_detects_command_injection(self, scanner):
        """Should detect os.system with user input."""
        code = """
import os
def run_command(user_input):
    os.system("ping " + user_input)
"""
        matches = scanner.scan_code(code, "cmd.py")
        cmd_findings = [m for m in matches if m.rule_id in ("CSAST-003", "CSAST-004")]
        assert len(cmd_findings) >= 1
    
    def test_detects_weak_hash(self, scanner):
        """Should detect MD5/SHA1 usage."""
        code = """
import hashlib
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
"""
        matches = scanner.scan_code(code, "auth.py")
        hash_findings = [m for m in matches if m.rule_id == "CSAST-011"]
        assert len(hash_findings) >= 1
    
    def test_detects_debug_mode(self, scanner):
        """Should detect debug=True in Flask."""
        code = """
from flask import Flask
app = Flask(__name__)
app.run(host="0.0.0.0", port=5000, debug=True)
"""
        matches = scanner.scan_code(code, "app.py")
        debug_findings = [m for m in matches if m.rule_id == "CSAST-030"]
        assert len(debug_findings) >= 1
    
    def test_detects_cors_wildcard(self, scanner):
        """Should detect CORS wildcard."""
        code = """
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
)
"""
        matches = scanner.scan_code(code, "main.py")
        cors_findings = [m for m in matches if m.rule_id == "CSAST-031"]
        assert len(cors_findings) >= 1
    
    def test_detects_insecure_deserialization(self, scanner):
        """Should detect pickle.loads."""
        code = """
import pickle
def load_data(data):
    return pickle.loads(data)
"""
        matches = scanner.scan_code(code, "serialize.py")
        pickle_findings = [m for m in matches if m.rule_id in ("CSAST-040", "CSAST-060")]
        assert len(pickle_findings) >= 1
    
    def test_detects_ssrf(self, scanner):
        """Should detect SSRF via requests with user input."""
        code = """
import requests
def fetch_url(user_url):
    response = requests.get(user_url)
    return response.text
"""
        matches = scanner.scan_code(code, "fetcher.py")
        ssrf_findings = [m for m in matches if m.rule_id == "CSAST-080"]
        assert len(ssrf_findings) >= 1
    
    def test_detects_sensitive_logging(self, scanner):
        """Should detect passwords in log statements."""
        code = """
import logging
logger = logging.getLogger(__name__)
def login(user, password):
    logger.info("Login attempt: %s with password: %s", user, password)
"""
        matches = scanner.scan_code(code, "auth.py")
        log_findings = [m for m in matches if m.rule_id == "CSAST-070"]
        assert len(log_findings) >= 1
    
    def test_severity_levels(self, scanner):
        """Findings should have valid severity levels."""
        code = """
api_key = "sk_live_1234567890abcdef"
eval(user_input)
"""
        matches = scanner.scan_code(code, "test.py")
        for m in matches:
            assert m.severity in Severity
    
    def test_finding_has_required_fields(self, scanner):
        """Each finding should have all required fields."""
        code = """
eval(user_input)
"""
        matches = scanner.scan_code(code, "test.py")
        assert len(matches) > 0
        for m in matches:
            assert m.rule_id
            assert m.title
            assert m.description
            assert m.remediation
            assert m.cwe_id
            assert m.owasp_category
            assert m.file_path == "test.py"
            assert m.line_number > 0
    
    def test_rules_summary(self, scanner):
        """get_rules_summary should return structured data."""
        summary = scanner.get_rules_summary()
        assert len(summary) > 0
        for rule in summary:
            assert "rule_id" in rule
            assert "name" in rule
            assert "severity" in rule
            assert "owasp" in rule
    
    def test_multiple_vulnerabilities_in_one_file(self, scanner):
        """Should detect multiple different vulns in one file."""
        code = """
import os
import pickle
import hashlib

api_key = "sk_live_1234567890abcdef"

def process(user_input):
    os.system("cmd " + user_input)
    return pickle.loads(user_input)

def hash_data(data):
    return hashlib.md5(data).hexdigest()
"""
        matches = scanner.scan_code(code, "multi.py")
        rule_ids = {m.rule_id for m in matches}
        # Should find at least 3 different rule types
        assert len(rule_ids) >= 3


class TestRiskScoring:
    """Test risk score calculation."""
    
    def test_zero_risk_for_clean_code(self, scanner):
        """Clean code should have risk score 0."""
        from app.services.scan_service import ScanService
        service = ScanService()
        score = service._calculate_risk_score([])
        assert score == 0.0
    
    def test_higher_risk_for_critical(self, scanner):
        """Critical findings should produce higher risk scores."""
        from app.services.scan_service import ScanService
        from app.services.sast_engine import ScanMatch
        service = ScanService()
        
        critical_matches = [
            ScanMatch("f.py", 1, "R1", Severity.CRITICAL, "t", "d", "r", "c", "o", "s")
            for _ in range(5)
        ]
        low_matches = [
            ScanMatch("f.py", 1, "R1", Severity.LOW, "t", "d", "r", "c", "o", "s")
            for _ in range(5)
        ]
        
        critical_score = service._calculate_risk_score(critical_matches)
        low_score = service._calculate_risk_score(low_matches)
        
        assert critical_score > low_score
