import re
from typing import Dict, Optional, Tuple, List
from app.modules.safety_resources import INDIA_HELPLINES, CRISIS_RESPONSE_TEMPLATE

class CrisisDetector:
    # Keywords mapped to severity score (1-10)
    # 10 = Immediate/Active Suicide Threat
    # 7-9 = High Risk / Self-Harm Intent
    # 4-6 = Moderate Distress / Depression terms (Handled by specialized prompt, not blocked)
    # < 4 = Normal / Low Risk
    
    KEYWORDS: Dict[str, int] = {
        "die": 6,
        "suicide": 9,
        "kill myself": 10,
        "end my life": 10,
        "want to die": 9,
        "better off dead": 8,
        "hurt myself": 8,
        "cutting myself": 8,
        "overdose": 9,
        "hang myself": 10,
        "shoot myself": 10,
        "jump off": 9,
        "hopeless": 5,
        "worthless": 5,
        "pain is too much": 6,
        "can't go on": 7,
        "goodbye forever": 9,
        "no way out": 6,
        "trap": 4,
        "depressed": 4,
        "anxious": 3,
        "sad": 2
    }
    
    # Regex patterns for more complex matching
    PATTERNS = [
        (r"i (want|going) to (kill|end) (myself|my life|it all)", 10),
        (r"everyone (would be|is) better off without me", 8),
        (r"can'?t (take|stand|handle) (this|life|pattern) anymore", 6),
        (r"thinking about (suicide|death|dying)", 8)
    ]

    def format_resources(self) -> str:
        formatted_list = []
        for key, info in INDIA_HELPLINES.items():
            formatted_list.append(f"- **{info['name']}**: {info['number']} ({info['hours']})")
        return "\n".join(formatted_list)

    def detect(self, text: str) -> Tuple[bool, int, Optional[str], List[str]]:
        """
        Analyzes text for crisis indicators.
        Returns:
            - is_crisis (bool): True if severity >= 7 (Blocks LLM)
            - severity (int): Calculated severity score
            - response (str | None): Hardcoded response if crisis, else None
            - flags (List[str]): List of detected triggers
        """
        text_lower = text.lower()
        max_severity = 0
        detected_flags = []
        
        # Check simple keywords
        for keyword, severity in self.KEYWORDS.items():
            if keyword in text_lower:
                if severity > max_severity:
                    max_severity = severity
                detected_flags.append(keyword)

        # Check regex patterns
        for pattern, severity in self.PATTERNS:
            if re.search(pattern, text_lower):
                if severity > max_severity:
                    max_severity = severity
                detected_flags.append(f"pattern_match:{pattern}")

        is_crisis = max_severity >= 7
        
        response = None
        if is_crisis:
            response = CRISIS_RESPONSE_TEMPLATE.format(
                resources_list=self.format_resources()
            )

        return is_crisis, max_severity, response, detected_flags

crisis_detector = CrisisDetector()
