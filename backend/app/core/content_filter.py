import re
import logging

logger = logging.getLogger(__name__)

# ── Blocked words/patterns ──
# Uses word boundary matching (\b) to avoid false positives.
# Grouped by category for maintainability.

BLOCKED_WORDS = [
    # ── English profanity ──
    r"\bfuck\w*\b",
    r"\bsh[i1]t\w*\b",
    r"\bass(?:hole|wipe|hat)\w*\b",
    r"\bb[i1]tch\w*\b",
    r"\bd[i1]ck(?:head|sucker|s)?\b",
    r"\bcock(?:sucker|s)?\b",
    r"\bpussy\b",
    r"\bpenis\b",
    r"\bvagina\b",
    r"\bwhore[s]?\b",
    r"\bslut[s]?\b",
    r"\bc[u\*]nt[s]?\b",
    r"\bbastard[s]?\b",
    r"\bdamn\w*\b",
    r"\bpiss\w*\b",
    r"\btits?\b",
    r"\bboob[s]?\b",
    r"\bjerk\s*off\b",
    r"\bwank\w*\b",
    r"\bdouche\w*\b",
    r"\btwat[s]?\b",

    # ── Slurs & hate speech ──
    r"\bn[i1]gg\w*\b",
    r"\bf[a@]gg?\w*\b",
    r"\bk[i1]ke[s]?\b",
    r"\bch[i1]nk[s]?\b",
    r"\bsp[i1]c[ks]?\b",
    r"\bwetback[s]?\b",
    r"\bcoon[s]?\b",
    r"\btrannie[s]?\b",
    r"\bretard\w*\b",

    # ── Sexual / NSFW ──
    r"\bporn\w*\b",
    r"\bhentai\b",
    r"\bxxx\b",
    r"\bsex(?:ual|ting|ually|y)\b",
    r"\brape[ds]?\b",
    r"\bmolest\w*\b",
    r"\bpedophil\w*\b",
    r"\bbestiality\b",
    r"\bincest\b",
    r"\bblowjob\w*\b",
    r"\bhandjob\w*\b",
    r"\bcumshot\w*\b",
    r"\bcum\b",
    r"\borgasm\w*\b",
    r"\berection\b",
    r"\bmasturbat\w*\b",
    r"\bnude[s]?\b",
    r"\bnaked\b",
    r"\bstrip\s*club\b",
    r"\bbondage\b",
    r"\bfetish\w*\b",

    # ── Violence / threats ──
    r"\bkill\s+(?:yourself|myself|him|her|them|people)\b",
    r"\bschool\s*shoot\w*\b",
    r"\bbomb\s*(?:threat|making)\b",
    r"\bsuicide\s*(?:method|how|way)\b",
    r"\bgenocide\b",
    r"\bterroris[mt]\w*\b",

    # ── Hindi / Hinglish abuses ──
    r"\bchutiya\w*\b",
    r"\bchod\w*\b",
    r"\bmadarcho[dt]\w*\b",
    r"\bmadercho[dt]\w*\b",
    r"\bmc\b",
    r"\bbc\b",
    r"\bbhosdik?\w*\b",
    r"\bbhosdi\w*\b",
    r"\bgaand\w*\b",
    r"\bgand\w*\b",
    r"\blund\w*\b",
    r"\blodu\w*\b",
    r"\brandi\w*\b",
    r"\bharami\w*\b",
    r"\bkutt[aie]\w*\b",
    r"\bkamin[aei]\w*\b",
    r"\bjhant\w*\b",
    r"\bjhaat\w*\b",
    r"\bchinal\w*\b",
    r"\blauda\w*\b",
    r"\blavda\w*\b",
    r"\blavde\w*\b",
    r"\btatti\w*\b",
    r"\bsala\b",
    r"\bsaala\b",
    r"\bsali\b",
    r"\bsaali\b",
    r"\bchamaar\w*\b",
    r"\bbhangi\w*\b",

    # ── Devanagari script abuses ──
    r"चूतिया",
    r"मादरचोद",
    r"भोसड़ीके",
    r"गांड",
    r"लंड",
    r"रंडी",
    r"हरामी",
    r"कमीना",
    r"कुत्ता",
    r"साला",
    r"तत्ती",
    r"लौड़ा",
]

# Pre-compile for performance
_compiled = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in BLOCKED_WORDS]


def is_safe(text: str) -> bool:
    """Returns True if the text passes the content filter."""
    for pattern in _compiled:
        if pattern.search(text):
            logger.warning(f"Content filter blocked: matched '{pattern.pattern}'")
            return False
    return True


BLOCKED_RESPONSE = "This input contains language that Lexify doesn't support. Please rephrase your query."
