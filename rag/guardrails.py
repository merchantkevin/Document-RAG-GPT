"""Guardrails: input validation and direct prompt-injection detection.

Two layers protect the system:
  * This module guards the *user query* (validation + injection heuristics).
  * pipeline.SYSTEM_PROMPT guards against *indirect* injection, i.e. malicious
    instructions hidden inside the uploaded documents, by telling the model to
    treat retrieved content strictly as untrusted data.
"""
import re
from typing import Tuple, Optional

MAX_QUERY_CHARS = 2000
MIN_QUERY_CHARS = 2

# High-signal patterns for direct prompt-injection / jailbreak attempts.
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|the\s+|your\s+|any\s+)?(previous|prior|above|earlier|preceding)\s+(instruction|prompt|message|context|rule)",
    r"disregard\s+(all\s+|the\s+|your\s+|any\s+)?(previous|prior|above|earlier|system)",
    r"forget\s+(everything|all|your\s+instructions|previous\s+instructions)",
    r"(reveal|show|print|repeat|expose|leak|display)\s+(me\s+)?(your\s+|the\s+)?(system\s+)?(prompt|instructions|rules)",
    r"\byou\s+are\s+now\b",
    r"new\s+(instruction|rule|task|prompt)s?\s*[:\-]",
    r"developer\s+mode",
    r"\bjailbreak\b",
    r"\bdo\s+anything\s+now\b",
    r"act\s+as\s+(if\s+you\s+are\s+)?(a\s+|an\s+)?(unrestricted|jailbroken|different)",
    r"pretend\s+(to\s+be|you\s+are|that\s+you)",
    r"override\s+(your\s+|the\s+|all\s+)?(instruction|rule|system|guardrail)",
    r"bypass\s+(your\s+|the\s+|all\s+)?(instruction|rule|filter|guardrail|restriction)",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def validate_input(text: Optional[str]) -> Tuple[bool, str, str]:
    """Return (is_valid, cleaned_text, error_message)."""
    if not text or not text.strip():
        return False, "", "Please enter a question."
    cleaned = text.strip()
    if len(cleaned) < MIN_QUERY_CHARS:
        return False, cleaned, "Please enter a longer question."
    if len(cleaned) > MAX_QUERY_CHARS:
        return False, cleaned, f"Question is too long (max {MAX_QUERY_CHARS} characters)."
    return True, cleaned, ""


def detect_injection(text: str) -> Tuple[bool, Optional[str]]:
    """Return (looks_like_injection, matched_pattern)."""
    for pattern in _COMPILED:
        if pattern.search(text):
            return True, pattern.pattern
    return False, None
