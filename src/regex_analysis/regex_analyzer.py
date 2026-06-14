import re
from typing import Dict, List
import config

def analyze_regex_patterns(text: str, patterns: List[str]) -> Dict:
    per_pattern: Dict[str, Dict] = {}
    total_matches = 0
    for pattern in patterns:
        compiled = re.compile(pattern)
        matches = list(compiled.finditer(text))
        substrings = [match.group() for match in matches]
        positions = [match.start() for match in matches]
        per_pattern[pattern] = {
            "name": pattern,
            "count": len(matches),
            "matches": substrings,
            "positions": positions,
        }
        total_matches += len(matches)
    return {
        "per_pattern": per_pattern,
        "total_matches": total_matches,
    }

def analyze_ai_regex_patterns(text: str) -> Dict:
    return analyze_regex_patterns(text, config.AI_REGEX_PATTERNS)

def analyze_real_regex_patterns(text: str) -> Dict:
    return analyze_regex_patterns(text, config.REAL_REGEX_PATTERNS)