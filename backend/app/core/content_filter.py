import re
import logging

logger = logging.getLogger(__name__)

# ── Blocklist ──
# Common slurs, NSFW terms, and abusive language.
# Uses word boundary matching to avoid false positives (e.g. "classic" won't match "ass").
# This is intentionally minimal — extend as needed.
BLOCKED_PATTERNS = [
    # Slurs & hate speech
    r"\bn[i1]gg(?:a|er|ers|as)\b",
    r"\bf[a@]gg?(?:ot|ots)?\b",
    r"\bk[i1]ke[s]?\b",
    r"\bch[i1]nk[s]?\b",
    r"\bsp[i1]c[ks]?\b",
    r"\bwetback[s]?\b",
    r"\bcoon[s]?\b",
    r"\btrannie[s]?\b",
    r"\bretard(?:ed|s)?\b",

    # Sexual / NSFW
    r"\bporn(?:o|ography)?\b",
    r"\bhentai\b",
    r"\bxxx\b",
    r"\bse?x(?:ual|ting|ually)\b",
    r"\brape[ds]?\b",
    r"\bmolest(?:ation|ed|ing)?\b",
    r"\bpedophil(?:e|ia)\b",
    r"\bbestiality\b",
    r"\bincest\b",
    r"\bblowjob[s]?\b",
    r"\bhandjob[s]?\b",
    r"\bcumshot[s]?\b",
    r"\bc[u\*]nt[s]?\b",

    # Violent / threatening
    r"\bkill\s+(?:yourself|myself|him|her|them)\b",
    r"\bschool\s*shoot(?:ing|er)\b",
    r"\bbomb\s*(?:threat|making)\b",
    r"\bsuicide\s*(?:method|how|way)\b",

    # Extreme profanity used as attacks
    r"\bfuck\s+you\b",
    r"\bdie\s+(?:bitch|whore)\b",
    r"\bstfu\b",
]

# Pre-compile for performance
_compiled = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]


def is_safe(text: str) -> bool:
    """Returns True if the text passes the content filter."""
    for pattern in _compiled:
        if pattern.search(text):
            logger.warning(f"Content filter triggered: {pattern.pattern}")
            return False
    return True


BLOCKED_RESPONSE = "This input contains language that Lexify doesn't support. Please rephrase your query."
