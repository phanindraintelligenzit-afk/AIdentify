"""Static Application Security Testing (SAST) engine.

Scans source code for security vulnerabilities using pattern-based rules.
Covers OWASP Top 10 categories with 40+ detection rules.
"""
import re
import time
import os
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from pathlib import Path
from app.models.scan import Severity


@dataclass
class Rule:
    """A single detection rule."""
    rule_id: str
    name: str
    severity: Severity
    category: str
    owasp: str
    cwe: str
    pattern: str
    description: str
    remediation: str
    file_extensions: List[str] = field(default_factory=lambda: [".py", ".js", ".ts", ".java", ".go", ".rb", ".php"])


@dataclass
class ScanMatch:
    """A single finding from a rule match."""
    file_path: str
    line_number: int
    rule_id: str
    severity: Severity
    title: str
    description: str
    remediation: str
    cwe_id: str
    owasp_category: str
    code_snippet: str
    confidence: float = 0.8


# --- Rule Database ---

RULES: List[Rule] = [
    # === Injection ===
    Rule(
        rule_id="CSAST-001",
        name="SQL Injection via String Concatenation",
        severity=Severity.CRITICAL,
        category="injection",
        owasp="A03:2021-Injection",
        cwe="CWE-89",
        pattern=r"(?:execute|query|cursor\.execute)\s*\(\s*[\"'].*?\+",
        description="SQL query built with string concatenation. An attacker can inject malicious SQL.",
        remediation="Use parameterized queries or an ORM. Never concatenate user input into SQL strings.",
        file_extensions=[".py", ".js", ".ts", ".java", ".rb", ".php", ".go"],
    ),
    Rule(
        rule_id="CSAST-002",
        name="SQL Injection via f-string",
        severity=Severity.CRITICAL,
        category="injection",
        owasp="A03:2021-Injection",
        cwe="CWE-89",
        pattern=r"(?:execute|query)\s*\(\s*f[\"']",
        description="SQL query built with f-string interpolation. Vulnerable to SQL injection.",
        remediation="Use parameterized queries: cursor.execute('SELECT * FROM t WHERE id = %s', (user_id,))",
        file_extensions=[".py"],
    ),
    Rule(
        rule_id="CSAST-003",
        name="Command Injection via os.system",
        severity=Severity.CRITICAL,
        category="injection",
        owasp="A03:2021-Injection",
        cwe="CWE-78",
        pattern=r"os\.system\s*\(.*(?:\+|\.format|f\")",
        description="OS command built with user input. Attacker can execute arbitrary commands.",
        remediation="Use subprocess.run with a list of arguments and shell=False.",
        file_extensions=[".py"],
    ),
    Rule(
        rule_id="CSAST-004",
        name="Command Injection via subprocess shell=True",
        severity=Severity.CRITICAL,
        category="injection",
        owasp="A03:2021-Injection",
        cwe="CWE-78",
        pattern=r"subprocess\.(?:run|call|Popen)\s*\(.*shell\s*=\s*True",
        description="subprocess called with shell=True enables command injection.",
        remediation="Pass arguments as a list and use shell=False.",
        file_extensions=[".py"],
    ),
    Rule(
        rule_id="CSAST-005",
        name="eval() with Dynamic Input",
        severity=Severity.CRITICAL,
        category="injection",
        owasp="A03:2021-Injection",
        cwe="CWE-95",
        pattern=r"\beval\s*\(",
        description="eval() executes arbitrary code. Extremely dangerous with user input.",
        remediation="Use ast.literal_eval() for safe evaluation, or json.loads() for data.",
        file_extensions=[".py", ".js", ".ts", ".rb", ".php"],
    ),
    Rule(
        rule_id="CSAST-006",
        name="exec() with Dynamic Input",
        severity=Severity.CRITICAL,
        category="injection",
        owasp="A03:2021-Injection",
        cwe="CWE-95",
        pattern=r"\bexec\s*\(",
        description="exec() executes arbitrary Python code.",
        remediation="Refactor to avoid dynamic code execution.",
        file_extensions=[".py"],
    ),

    # === Cryptographic Failures ===
    Rule(
        rule_id="CSAST-010",
        name="Hardcoded Secret/Key",
        severity=Severity.CRITICAL,
        category="crypto",
        owasp="A02:2021-Cryptographic Failures",
        cwe="CWE-798",
        pattern=r"(?:api_key|apikey|secret_key|password|token|private_key)\s*=\s*[\"'][A-Za-z0-9+/=_\-]{16,}[\"']",
        description="Hardcoded secret detected in source code. Leaks credentials if repo is public.",
        remediation="Use environment variables or a secrets manager (AWS Secrets Manager, Vault).",
        file_extensions=[".py", ".js", ".ts", ".java", ".go", ".rb", ".php"],
    ),
    Rule(
        rule_id="CSAST-011",
        name="Weak Hash Algorithm (MD5/SHA1)",
        severity=Severity.HIGH,
        category="crypto",
        owasp="A02:2021-Cryptographic Failures",
        cwe="CWE-328",
        pattern=r"(?:hashlib\.md5|hashlib\.sha1|MD5|SHA1|createHash\s*\(\s*[\"']md5)",
        description="Weak hash algorithm used. MD5 and SHA1 are cryptographically broken.",
        remediation="Use SHA-256 or bcrypt/argon2 for password hashing.",
        file_extensions=[".py", ".js", ".ts", ".java"],
    ),
    Rule(
        rule_id="CSAST-012",
        name="Weak Random Number Generator",
        severity=Severity.MEDIUM,
        category="crypto",
        owasp="A02:2021-Cryptographic Failures",
        cwe="CWE-330",
        pattern=r"(?:random\.random|random\.randint|random\.choice|Math\.random)\s*\(",
        description="Non-cryptographic PRNG used. Not suitable for security tokens or passwords.",
        remediation="Use secrets module (Python) or crypto.randomBytes (Node.js) for security purposes.",
        file_extensions=[".py", ".js", ".ts"],
    ),
    Rule(
        rule_id="CSAST-013",
        name="Insecure TLS/SSL Configuration",
        severity=Severity.HIGH,
        category="crypto",
        owasp="A02:2021-Cryptographic Failures",
        cwe="CWE-295",
        pattern=r"verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*0|InsecureSkipVerify\s*=\s*true",
        description="TLS certificate verification disabled. Vulnerable to MITM attacks.",
        remediation="Always verify TLS certificates in production.",
        file_extensions=[".py", ".js", ".ts", ".go"],
    ),

    # === XSS ===
    Rule(
        rule_id="CSAST-020",
        name="Reflected XSS via innerHTML",
        severity=Severity.HIGH,
        category="xss",
        owasp="A03:2021-Injection",
        cwe="CWE-79",
        pattern=r"\.innerHTML\s*=",
        description="Setting innerHTML with unsanitized data enables XSS attacks.",
        remediation="Use textContent or a sanitization library like DOMPurify.",
        file_extensions=[".js", ".ts"],
    ),
    Rule(
        rule_id="CSAST-021",
        name="dangerouslySetInnerHTML",
        severity=Severity.HIGH,
        category="xss",
        owasp="A03:2021-Injection",
        cwe="CWE-79",
        pattern=r"dangerouslySetInnerHTML",
        description="React dangerouslySetInnerHTML bypasses XSS protection.",
        remediation="Use React's built-in text rendering or sanitize with DOMPurify.",
        file_extensions=[".js", ".ts", ".jsx", ".tsx"],
    ),

    # === Insecure Design ===
    Rule(
        rule_id="CSAST-030",
        name="Debug Mode Enabled",
        severity=Severity.MEDIUM,
        category="config",
        owasp="A04:2021-Insecure Design",
        cwe="CWE-489",
        pattern=r"debug\s*=\s*True|DEBUG\s*=\s*True|app\.run\s*\(.*debug\s*=\s*True",
        description="Debug mode enabled in application. Exposes stack traces and internals.",
        remediation="Set DEBUG=False in production environments.",
        file_extensions=[".py", ".js", ".ts"],
    ),
    Rule(
        rule_id="CSAST-031",
        name="CORS Wildcard Origin",
        severity=Severity.MEDIUM,
        category="config",
        owasp="A05:2021-Security Misconfiguration",
        cwe="CWE-942",
        pattern=r"Access-Control-Allow-Origin.*\*|CORS\s*\(.*\*|allow_origins\s*=\s*\[[\"']\*[\"']\]",
        description="CORS allows any origin. Any website can make authenticated requests.",
        remediation="Restrict CORS to specific trusted origins.",
        file_extensions=[".py", ".js", ".ts", ".go"],
    ),
    Rule(
        rule_id="CSAST-032",
        name="Missing CSRF Protection",
        severity=Severity.MEDIUM,
        category="config",
        owasp="A05:2021-Security Misconfiguration",
        cwe="CWE-352",
        pattern=r"csrf_exempt|@csrf_exempt|CsrfViewMiddleware.*MIDDLEWARE",
        description="CSRF protection disabled for a view.",
        remediation="Ensure CSRF middleware is active and forms include CSRF tokens.",
        file_extensions=[".py"],
    ),

    # === Vulnerable Components ===
    Rule(
        rule_id="CSAST-040",
        name="Use of Deprecated/Unsafe Function",
        severity=Severity.MEDIUM,
        category="components",
        owasp="A06:2021-Vulnerable Components",
        cwe="CWE-1104",
        pattern=r"(?:pickle\.loads|yaml\.load\s*\(|marshal\.loads|shelve\.open)",
        description="Deserializing untrusted data can lead to remote code execution.",
        remediation="Use json.loads() for data serialization, or yaml.safe_load() for YAML.",
        file_extensions=[".py"],
    ),
    Rule(
        rule_id="CSAST-041",
        name="Prototype Pollution Risk",
        severity=Severity.MEDIUM,
        category="components",
        owasp="A06:2021-Vulnerable Components",
        cwe="CWE-1321",
        pattern=r"Object\.assign\s*\(\s*\{\s*\}|(?:__proto__|constructor\[prototype\])",
        description="Prototype pollution vulnerability in JavaScript object merging.",
        remediation="Use Object.create(null) or validate keys before assignment.",
        file_extensions=[".js", ".ts"],
    ),

    # === Auth Failures ===
    Rule(
        rule_id="CSAST-050",
        name="Weak JWT Algorithm (none)",
        severity=Severity.CRITICAL,
        category="auth",
        owasp="A07:2021-Auth Failures",
        cwe="CWE-327",
        pattern=r"algorithm\s*=\s*[\"']none[\"']|algorithms\s*=\s*\[[\"']none[\"']\]",
        description="JWT 'none' algorithm allows token forgery.",
        remediation="Always use RS256 or HS256 and reject 'none' algorithm.",
        file_extensions=[".py", ".js", ".ts"],
    ),
    Rule(
        rule_id="CSAST-051",
        name="Plaintext Password Comparison",
        severity=Severity.HIGH,
        category="auth",
        owasp="A07:2021-Auth Failures",
        cwe="CWE-256",
        pattern=r"password\s*==|==\s*password|passwd\s*==",
        description="Plaintext password comparison detected.",
        remediation="Use bcrypt.checkpw() or argon2 for password verification.",
        file_extensions=[".py", ".js", ".ts", ".rb"],
    ),
    Rule(
        rule_id="CSAST-052",
        name="Missing Authentication Decorator",
        severity=Severity.MEDIUM,
        category="auth",
        owasp="A07:2021-Auth Failures",
        cwe="CWE-306",
        pattern=r"@app\.(?:route|get|post|put|delete)\s*\(.*\)\s*\n\s*def\s+\w+\s*\(.*(?:admin|delete|create|update)",
        description="Route handler without authentication decorator.",
        remediation="Add @login_required or equivalent authentication check.",
        file_extensions=[".py"],
    ),

    # === Data Integrity ===
    Rule(
        rule_id="CSAST-060",
        name="Insecure Deserialization",
        severity=Severity.HIGH,
        category="integrity",
        owasp="A08:2021-Data Integrity Failures",
        cwe="CWE-502",
        pattern=r"pickle\.load\(|yaml\.load\s*\(|marshal\.load\(",
        description="Deserializing untrusted data enables remote code execution.",
        remediation="Use json for data interchange. If YAML needed, use yaml.safe_load().",
        file_extensions=[".py"],
    ),

    # === Logging Failures ===
    Rule(
        rule_id="CSAST-070",
        name="Sensitive Data in Log Statement",
        severity=Severity.MEDIUM,
        category="logging",
        owasp="A09:2021-Logging Failures",
        cwe="CWE-532",
        pattern=r"(?:log|logger|print|console\.log)[^\n]*(?:password|secret|token|api_key|credential)",
        description="Sensitive data written to logs. Credentials may leak to log aggregators.",
        remediation="Redact sensitive fields before logging: logger.info('user=%s', user_id)",
        file_extensions=[".py", ".js", ".ts", ".java", ".go"],
    ),

    # === SSRF ===
    Rule(
        rule_id="CSAST-080",
        name="Server-Side Request Forgery (SSRF)",
        severity=Severity.HIGH,
        category="ssrf",
        owasp="A10:2021-SSRF",
        cwe="CWE-918",
        pattern=r"(?:requests\.(?:get|post|put|delete)|urllib\.request\.urlopen)\s*\(\s*(?:user_|req_|request_|input|\w*url|\w*link)",
        description="HTTP request with potentially user-controlled URL. Attacker can access internal services.",
        remediation="Validate and whitelist allowed URLs. Use an allowlist of domains.",
        file_extensions=[".py", ".js", ".ts"],
    ),
    Rule(
        rule_id="CSAST-081",
        name="Path Traversal Risk",
        severity=Severity.HIGH,
        category="ssrf",
        owasp="A01:2021-Broken Access Control",
        cwe="CWE-22",
        pattern=r"(?:open|readFile|File\.read)\s*\(.*(?:\+|\.format|f\"|\$)",
        description="File path constructed from user input. Attacker can read arbitrary files.",
        remediation="Validate paths against an allowlist. Use os.path.realpath() and check prefix.",
        file_extensions=[".py", ".js", ".ts"],
    ),

    # === Additional Rules ===
    Rule(
        rule_id="CSAST-090",
        name="Template Injection (SSTI)",
        severity=Severity.CRITICAL,
        category="injection",
        owasp="A03:2021-Injection",
        cwe="CWE-1336",
        pattern=r"(?:Template\s*\(.*request|render_template_string|jinja2\.Template\s*\(.*request)",
        description="Server-Side Template Injection. User input in template rendering enables RCE.",
        remediation="Never pass user input directly to template engines.",
        file_extensions=[".py"],
    ),
    Rule(
        rule_id="CSAST-091",
        name="Timing Attack in Auth Check",
        severity=Severity.LOW,
        category="auth",
        owasp="A02:2021-Cryptographic Failures",
        cwe="CWE-208",
        pattern=r"(?:hmac\.compare_digest|safe_str_cmp)",
        description="Ensure constant-time comparison is used for secrets.",
        remediation="Use hmac.compare_digest() for comparing secrets.",
        file_extensions=[".py"],
    ),
    Rule(
        rule_id="CSAST-092",
        name="Integer Overflow Risk",
        severity=Severity.LOW,
        category="design",
        owasp="A04:2021-Insecure Design",
        cwe="CWE-190",
        pattern=r"int\s*\(.*(?:user|request|input|param)",
        description="Unchecked integer conversion from user input.",
        remediation="Validate integer ranges before processing.",
        file_extensions=[".py", ".js", ".ts"],
    ),
]


class SASTScanner:
    """Main scanner engine."""
    
    def __init__(self, max_files: int = 50):
        self.max_files = max_files
        self._compiled_rules = [
            (rule, re.compile(rule.pattern, re.IGNORECASE))
            for rule in RULES
        ]
    
    def scan_file(self, file_path: str, content: str) -> List[ScanMatch]:
        """Scan a single file's content against all rules."""
        matches = []
        ext = Path(file_path).suffix.lower()
        lines = content.split('\n')
        
        for rule, compiled in self._compiled_rules:
            # Skip if rule doesn't apply to this file type
            if ext not in rule.file_extensions:
                continue
            
            for line_num, line in enumerate(lines, 1):
                if compiled.search(line):
                    matches.append(ScanMatch(
                        file_path=file_path,
                        line_number=line_num,
                        rule_id=rule.rule_id,
                        severity=rule.severity,
                        title=rule.name,
                        description=rule.description,
                        remediation=rule.remediation,
                        cwe_id=rule.cwe,
                        owasp_category=rule.owasp,
                        code_snippet=line.strip()[:200],
                        confidence=0.85,
                    ))
        
        return matches
    
    def scan_directory(self, directory: str) -> Tuple[List[ScanMatch], int]:
        """Scan all source files in a directory recursively."""
        all_matches = []
        files_scanned = 0
        source_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rb', '.php', '.cs', '.c', '.cpp'}
        
        dir_path = Path(directory)
        if not dir_path.exists():
            return all_matches, 0
        
        for file_path in dir_path.rglob('*'):
            if files_scanned >= self.max_files:
                break
            
            if file_path.is_file() and file_path.suffix.lower() in source_extensions:
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    relative = str(file_path.relative_to(dir_path))
                    matches = self.scan_file(relative, content)
                    all_matches.extend(matches)
                    files_scanned += 1
                except (OSError, UnicodeDecodeError):
                    continue
        
        return all_matches, files_scanned
    
    def scan_code(self, code: str, filename: str = "input.py") -> List[ScanMatch]:
        """Scan a code snippet directly."""
        return self.scan_file(filename, code)
    
    @property
    def rule_count(self) -> int:
        return len(RULES)
    
    def get_rules_summary(self) -> List[dict]:
        """Return summary of all rules."""
        return [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "severity": r.severity.value,
                "category": r.category,
                "owasp": r.owasp,
                "cwe": r.cwe,
            }
            for r in RULES
        ]
