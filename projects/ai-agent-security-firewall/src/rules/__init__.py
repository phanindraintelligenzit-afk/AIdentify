"""Detection rules for various attack vectors."""

from src.detection import (
    PatternRule, KeywordDensityRule, CompositeRule,
    AttackType, Severity
)


def build_prompt_injection_rules() -> list:
    """Build rules for detecting prompt injection attacks."""
    
    # Direct injection patterns
    direct_patterns = PatternRule(
        name="direct_injection",
        attack_type=AttackType.PROMPT_INJECTION,
        severity=Severity.BLOCK,
        patterns=[
            r"ignore\s+(all\s+)?(previous|prior|above|earlier|all)\s+(instructions?|prompts?|rules?)",
            r"ignore\s+(all|everything|your)\s+(previous|prior|above|earlier|instructions?|rules?)",
            r"disregard\s+(all\s+)?(previous|prior|above|earlier|your)\s+(instructions?|prompts?|rules?)",
            r"forget\s+(everything|all|your)\s+(instructions?|rules?|training|taught)",
            r"you\s+are\s+now\s+(a|an|the)\s+",
            r"new\s+instructions?:",
            r"system\s+prompt\s*:",
            r"\[system\]\s*",
            r"<\|system\|>",
            r"###\s*(system|instruction|human|assistant)",
            r"ACT\s+AS\s+(a|an|the)\s+",
            r"pretend\s+(you('re|\s+are)|to\s+be)",
            r"from\s+now\s+on,?\s+you",
            r"ignore\s+your\s+(instructions?|rules?|guidelines?)",
            r"ignore\s+(all|everything)\s+you('ve|\s+have)\s+(been\s+)?(told|taught|instructed)",
        ],
        score_threshold=0.55,
    )

    # Delimiter-based injection
    delimiter_patterns = PatternRule(
        name="delimiter_injection",
        attack_type=AttackType.PROMPT_INJECTION,
        severity=Severity.BLOCK,
        patterns=[
            r"```\s*(system|instruction|prompt)",
            r"---\s*(system|instruction)",
            r"<<\s*SYSTEM\s*>>",
            r"\{\{.*system.*\}\}",
            r"\[\[.*system.*\]\]",
            r"</?system>",
            r"</?instruction>",
            r"</?prompt>",
        ],
        score_threshold=0.65,
    )

    # Encoding-based injection attempts
    encoding_patterns = PatternRule(
        name="encoding_injection",
        attack_type=AttackType.PROMPT_INJECTION,
        severity=Severity.BLOCK,
        patterns=[
            r"base64\s*[:=]",
            r"decode\s+(this|the\s+following)",
            r"rot13",
            r"hex\s+decode",
            r"unicode\s+escape",
            r"\\x[0-9a-f]{2}",
            r"%[0-9a-f]{2}(?=%[0-9a-f]{2})",
        ],
        score_threshold=0.7,
    )

    # Keyword density for injection intent
    injection_density = KeywordDensityRule(
        name="injection_density",
        attack_type=AttackType.PROMPT_INJECTION,
        severity=Severity.BLOCK,
        keywords=[
            "ignore instructions", "bypass", "override", "new instructions",
            "system prompt", "admin mode", "developer mode", "root access",
            "sudo", "jailbreak", "uncensored", "unrestricted",
        ],
        score_threshold=0.15,
    )

    return [direct_patterns, delimiter_patterns, encoding_patterns, injection_density]


def build_jailbreak_rules() -> list:
    """Build rules for detecting jailbreak attempts."""
    
    # DAN (Do Anything Now) variants
    dan_patterns = PatternRule(
        name="dan_jailbreak",
        attack_type=AttackType.JAILBREAK,
        severity=Severity.BLOCK,
        patterns=[
            r"DAN\s*[\d.]+",
            r"Do\s+Anything\s+Now",
            r"DAN\s+mode",
            r"developer\s+mode",
            r"god\s*mode",
            r"admin\s+mode",
            r"unrestricted\s+mode",
            r"no\s+(limits?|restrictions?|rules?)\s*(apply|anymore)?",
            r"bypass\s+(all\s+)?(safety|security|filters?|restrictions?)",
            r"(safety|security|filters?)\s+(are\s+)?(disabled|off|bypassed)",
            r"enter\s+(developer|admin|god|unrestricted)\s+mode",
        ],
        score_threshold=0.55,
    )

    # Role-playing jailbreak
    roleplay_jailbreak = PatternRule(
        name="roleplay_jailbreak",
        attack_type=AttackType.JAILBREAK,
        severity=Severity.BLOCK,
        patterns=[
            r"you\s+(are|'re)\s+free\s+to",
            r"no\s+(longer|more)\s+(bound|restricted|limited)",
            r"think\s+outside\s+(the\s+)?box",
            r"break\s+(your\s+)?(programming|constraints|rules)",
            r"act\s+as\s+if\s+(you('re|\s+are)\s+)?(not\s+)?(an?\s+)?AI",
            r"imagine\s+you('re|\s+are)\s+(a\s+)?(human|unrestricted)",
        ],
        score_threshold=0.65,
    )

    # Emotional manipulation
    emotional_patterns = PatternRule(
        name="emotional_manipulation",
        attack_type=AttackType.JAILBREAK,
        severity=Severity.FLAG,
        patterns=[
            r"if\s+you\s+don't",
            r"you\s+must\s+or\s+else",
            r"I\s+will\s+(die|suffer|be\s+hurt)",
            r"this\s+is\s+(a\s+)?(test|emergency)",
            r"for\s+the\s+greater\s+good",
            r"ethical\s+obligation",
            r"moral\s+duty",
        ],
        score_threshold=0.6,
    )

    return [dan_patterns, roleplay_jailbreak, emotional_patterns]


def build_data_exfiltration_rules() -> list:
    """Build rules for detecting data exfiltration attempts."""
    
    # Direct exfiltration commands
    direct_exfil = PatternRule(
        name="direct_exfiltration",
        attack_type=AttackType.DATA_EXFILTRATION,
        severity=Severity.BLOCK,
        patterns=[
            r"(send|transmit|forward|email|post|upload)\s+(this|the|all|everything)",
            r"(output|print|display|show|reveal|dump)\s+(all\s+)?(data|credentials|secrets?|keys?|tokens?|passwords?)",
            r"(exfiltrate|extract|steal|leak)\s+(data|information|credentials)",
            r"(copy|paste)\s+(this|the)\s+(to|into|at)\s+(url|endpoint|server)",
            r"(curl|wget|fetch|request)\s+.*(?:password|token|secret|key|credential)",
            r"send\s+(all|the|user)\s+data\s+to",
            r"(dump|output|show)\s+(all\s+)?(passwords?|credentials|secrets?)",
        ],
        score_threshold=0.55,
    )

    # System information probing
    system_probing = PatternRule(
        name="system_probing",
        attack_type=AttackType.DATA_EXFILTRATION,
        severity=Severity.BLOCK,
        patterns=[
            r"(what|show|tell|give)\s+(me\s+)?(your|the)\s+(system|original|initial|system\s+prompt)",
            r"(what|show|tell|give)\s+(me\s+)?(your|the)\s+(instructions?|training|prompt)",
            r"(reveal|expose|share)\s+(your|the)\s+(system|prompt|instructions)",
            r"(repeat|say|output|print|display)\s+(the|your)?\s*(exact|original|initial|words?\s+of\s+)?(prompt|instructions)",
            r"(what|which)\s+(model|version|ai)\s+are\s+you",
            r"show\s+me\s+(your|the)\s+(api\s+)?key",
            r"(system|original|initial)\s+prompt",
        ],
        score_threshold=0.55,
    )

    # Data encoding for exfiltration
    encoding_exfil = PatternRule(
        name="encoding_exfiltration",
        attack_type=AttackType.DATA_EXFILTRATION,
        severity=Severity.FLAG,
        patterns=[
            r"(encode|convert|transform)\s+(as|to|into)\s+(base64|hex|binary|ascii)",
            r"(encrypt|obfuscate|hide)\s+(the|this|data)",
            r"(write|save|store)\s+(to|in)\s+(file|disk|external)",
        ],
        score_threshold=0.7,
    )

    return [direct_exfil, system_probing, encoding_exfil]


def build_roleplay_attack_rules() -> list:
    """Build rules for detecting role-playing-based attacks."""
    
    # Character-based roleplay
    character_roleplay = PatternRule(
        name="character_roleplay",
        attack_type=AttackType.ROLEPLAY_ATTACK,
        severity=Severity.FLAG,
        patterns=[
            r"(you\s+are|act\s+as|pretend\s+(you('re|\s+are)|to\s+be))\s+(a\s+)?(hacker|attacker|evil|malicious)",
            r"(you\s+are|act\s+as|pretend\s+(you('re|\s+are)|to\s+be))\s+(a\s+)?(not\s+)?(bound|restricted|limited)",
            r"welcome\s+to\s+(the\s+)?(dark|evil|unrestricted)\s+side",
            r"you\s+have\s+been\s+(freed|released|unleashed)",
            r"your\s+(new|true|real)\s+(purpose|identity|role)\s+is",
            r"you\s+are\s+now\s+(an?\s+)?(evil|unrestricted|unbounded)",
            r"act\s+as\s+(an?\s+)?(evil|unrestricted|malicious)",
            r"pretend\s+(you('re|\s+are)|to\s+be)\s+(unrestricted|unlimited|no\s+limits)",
        ],
        score_threshold=0.6,
    )

    # Hypothetical framing
    hypothetical_framing = PatternRule(
        name="hypothetical_framing",
        attack_type=AttackType.ROLEPLAY_ATTACK,
        severity=Severity.FLAG,
        patterns=[
            r"(imagine|suppose|pretend|hypothetical)\s+(that\s+)?you('re|\s+are)",
            r"in\s+(a\s+)?(fictional|hypothetical|imaginary)\s+(world|scenario|situation)",
            r"for\s+(educational|research|testing)\s+(purposes|only)",
            r"this\s+is\s+(just|only)\s+(a\s+)?(game|story|fiction|roleplay)",
            r"no\s+(real|actual)\s+(harm|damage|consequences)",
        ],
        score_threshold=0.65,
    )

    return [character_roleplay, hypothetical_framing]


def build_instruction_override_rules() -> list:
    """Build rules for detecting instruction override attempts."""
    
    # Direct override
    direct_override = PatternRule(
        name="direct_override",
        attack_type=AttackType.INSTRUCTION_OVERRIDE,
        severity=Severity.BLOCK,
        patterns=[
            r"(new|updated|override|modified)\s+(instructions?|rules?|guidelines?)\s*:",
            r"(replace|overwrite|update)\s+(your|the)\s+(instructions?|rules?|system)",
            r"(instead|rather\s+than)\s+of\s+(your|the)\s+(usual|normal|standard)",
            r"do\s+not\s+(follow|obey|adhere\s+to)\s+(your|the)\s+(instructions?|rules?)\s*(anymore|)",
            r"(stop|cease|end)\s+(following|using|obeying)\s+(your|the)\s+(instructions?|rules?)",
            r"from\s+now\s+on.*you\s+(are|can|should)",
        ],
        score_threshold=0.55,
    )

    # Priority manipulation
    priority_manipulation = PatternRule(
        name="priority_manipulation",
        attack_type=AttackType.INSTRUCTION_OVERRIDE,
        severity=Severity.BLOCK,
        patterns=[
            r"(this|the\s+following)\s+(is|are)\s+(more\s+)?(important|priority|urgent|critical)",
            r"(override|supersede|take\s+precedence)",
            r"(highest|top|maximum)\s+priority",
            r"(ignore|disregard)\s+(everything|all\s+else)",
            r"(from\s+now\s+on|going\s+forward)",
        ],
        score_threshold=0.65,
    )

    # Authority impersonation
    authority_impersonation = PatternRule(
        name="authority_impersonation",
        attack_type=AttackType.INSTRUCTION_OVERRIDE,
        severity=Severity.BLOCK,
        patterns=[
            r"(I\s+am|I'm)\s+(your|the)\s+(creator|developer|admin|owner|manager)",
            r"(this\s+is\s+)?(your|the)\s+(creator|developer|admin|owner)\s+(speaking|ordering|requesting)",
            r"(official|authorized)\s+(override|update|command)",
            r"(root|superuser|administrator)\s+(access|command|override)",
            r"(override|safety\s+protocols?)\s+(immediately|now)",
        ],
        score_threshold=0.6,
    )

    return [direct_override, priority_manipulation, authority_impersonation]


def build_all_rules() -> list:
    """Build and return all detection rules."""
    rules = []
    rules.extend(build_prompt_injection_rules())
    rules.extend(build_jailbreak_rules())
    rules.extend(build_data_exfiltration_rules())
    rules.extend(build_roleplay_attack_rules())
    rules.extend(build_instruction_override_rules())
    return rules
