"""
Jailbreak and prompt injection protection.
Block messages containing forbidden patterns; return safe fallback response.
"""
import re

SAFE_FALLBACK = "I'm here to help with our services. How can I assist you?"

# Case-insensitive patterns that trigger block
BLOCK_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+instructions",
    r"ignore\s+your\s+(instructions|prompt|rules)",
    r"you\s+are\s+now",
    r"act\s+as\s+(a\s+)?(if\s+)?",
    r"reveal\s+(system\s+)?prompt",
    r"developer\s+mode",
    r"bypass\s+(safety|restrictions|instructions)",
    r"disregard\s+(previous|all|your)",
    r"forget\s+(everything|your\s+instructions)",
    r"system\s+prompt",
    r"jailbreak",
    r"dan\s+mode",
    r"do\s+anything\s+now",
    r"pretend\s+you\s+are",
    r"roleplay\s+as",
]

_COMPILED = [re.compile(p, re.I) for p in BLOCK_PATTERNS]


def is_unsafe_input(text: str) -> bool:
    """Return True if message should be blocked (jailbreak / prompt injection)."""
    if not (text or "").strip():
        return False
    t = (text or "").strip()
    for pat in _COMPILED:
        if pat.search(t):
            return True
    return False


def strip_html(text: str) -> str:
    """Remove HTML tags for safe display/storage."""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()
