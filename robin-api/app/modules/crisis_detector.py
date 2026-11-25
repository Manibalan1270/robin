import re
from typing import List, Optional, Tuple

from app.modules.safety_resources import CRISIS_RESPONSE_TEMPLATE, INDIA_HELPLINES


class CrisisDetector:
    """Rule-based crisis check that runs BEFORE the AI model.

    - Matches whole words/phrases, so "diet", "studied" or "skill" never trigger it.
    - Normalises simple obfuscation ("k1ll", "su1c1de").
    - Severity >= 7 is treated as a crisis: the AI is skipped and helplines are shown.
    - Lower scores are passed to the AI so it can respond with extra care.

    Keyword lists can never catch everything. Treat this as a safety net, not a
    diagnosis, and keep the AI prompt instructed to watch for risk as well.
    """

    CRISIS_THRESHOLD = 7

    # (pattern, severity). All patterns run on normalised lower-case text.
    PATTERNS: List[Tuple[str, int]] = [
        (r"\bkill(ing)? my ?self\b", 10),
        (r"\b(end|ending|take|taking) (my|my own) life\b", 10),
        (r"\bhang(ing)? my ?self\b", 10),
        (r"\bshoot(ing)? my ?self\b", 10),
        (r"\b(going|gonna|planning|ready) to (end it( all)?|end my life|kill my ?self)\b", 10),
        (r"\bend it all\b", 9),
        (r"\b(wanna|want to) end it\b", 9),
        (r"\bsuicid(e|al)\b", 9),
        (r"\bi (want|wanna) (to )?die\b", 9),
        (r"\boverdose\b", 9),
        (r"\bgoodbye forever\b", 9),
        (r"\bjump(ing)? off (a|the|this|my) (bridge|building|roof|terrace|cliff|balcony)\b", 9),
        (r"\bdon'?t want to (live|be alive|exist)( anymore)?\b", 9),
        (r"\bbetter off dead\b", 8),
        (r"\b(everyone|everybody|they|people)( would| will)? (be )?better off without me\b", 8),
        (r"\bno(body|one) would (even )?(miss|notice|care) (me|if i)\b", 8),
        (r"\b(hurt|hurting|harm|harming|cut|cutting) my ?self\b", 8),
        (r"\bself[- ]?harm\b", 8),
        (r"\bthinking (about|of) (suicide|death|dying|ending)\b", 8),
        (r"\bcan'?t go on\b", 7),
        (r"\bcan'?t (take|stand|handle) (this|it|life) anymore\b", 6),
        (r"\bno way out\b", 6),
        (r"\bpain is too much\b", 6),
        (r"\bhopeless\b", 5),
        (r"\bworthless\b", 5),
        (r"\btrapped\b", 4),
        (r"\bdepressed\b", 4),
        (r"\banxious\b", 3),
        (r"\bsad\b", 2),
    ]

    _COMPILED = [(re.compile(p), s) for p, s in PATTERNS]
    _LEET = str.maketrans({"1": "i", "0": "o", "3": "e", "4": "a", "$": "s", "’": "'", "‘": "'"})

    def normalise(self, text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").lower().translate(self._LEET))

    def format_resources(self) -> str:
        return "\n".join(
            f"- **{info['name']}**: {info['number']} ({info['hours']})"
            for info in INDIA_HELPLINES.values()
        )

    def crisis_response(self) -> str:
        return CRISIS_RESPONSE_TEMPLATE.format(resources_list=self.format_resources())

    def detect(self, text: str) -> Tuple[bool, int, Optional[str], List[str]]:
        """Returns (is_crisis, severity 0-10, crisis_response or None, matched patterns)."""
        normalised = self.normalise(text)
        max_severity = 0
        flags: List[str] = []
        for pattern, severity in self._COMPILED:
            if pattern.search(normalised):
                max_severity = max(max_severity, severity)
                flags.append(pattern.pattern)

        is_crisis = max_severity >= self.CRISIS_THRESHOLD
        return is_crisis, max_severity, (self.crisis_response() if is_crisis else None), flags


crisis_detector = CrisisDetector()
