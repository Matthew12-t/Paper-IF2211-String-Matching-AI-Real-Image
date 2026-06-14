from typing import Dict, List, Tuple
import config
from imaging.image_to_string import image_to_visual_string
from regex_analysis.regex_analyzer import analyze_ai_regex_patterns, analyze_real_regex_patterns
from algorithms.string_matching import analyze_patterns_with_all_algorithms

def calculate_scores(visual_string: str) -> Dict:
    ai_exact_results = analyze_patterns_with_all_algorithms(visual_string, config.AI_EXACT_PATTERNS)
    real_exact_results = analyze_patterns_with_all_algorithms(visual_string, config.REAL_EXACT_PATTERNS)
    ai_regex_results = analyze_ai_regex_patterns(visual_string)
    real_regex_results = analyze_real_regex_patterns(visual_string)
    ai_exact_score = ai_exact_results["kmp_total_count"]
    real_exact_score = real_exact_results["kmp_total_count"]
    ai_regex_score = ai_regex_results["total_matches"]
    real_regex_score = real_regex_results["total_matches"]
    ai_score = ai_exact_score + ai_regex_score
    real_score = real_exact_score + real_regex_score

    return {
        "ai_exact_results": ai_exact_results,
        "real_exact_results": real_exact_results,
        "ai_regex_results": ai_regex_results,
        "real_regex_results": real_regex_results,
        "ai_exact_score": ai_exact_score,
        "real_exact_score": real_exact_score,
        "ai_regex_score": ai_regex_score,
        "real_regex_score": real_regex_score,
        "ai_score": ai_score,
        "real_score": real_score,
    }

def calculate_confidence(ai_score: int, real_score: int) -> float:
    total = ai_score + real_score
    if total == 0:
        return 0.0
    return abs(ai_score - real_score) / total

def determine_tendency(ai_score: int, real_score: int, confidence: float) -> str:
    if ai_score == real_score:
        return "inconclusive"
    if confidence < config.CONFIDENCE_THRESHOLD:
        return "inconclusive"
    if ai_score > real_score:
        return "tends to have AI-generated visual characteristics"
    return "tends to have real image visual characteristics"

def _most_frequent_patterns(per_pattern: Dict, count_key: str, limit: int = 3) -> List[Tuple[str, int]]:
    items = [(name, data[count_key]) for name, data in per_pattern.items() if data[count_key] > 0]
    items.sort(key=lambda item: item[1], reverse=True)
    return items[:limit]

def analyze_single_image(image_path: str) -> Dict:
    visual_string = image_to_visual_string(image_path)
    scores = calculate_scores(visual_string)
    confidence = calculate_confidence(scores["ai_score"], scores["real_score"])
    result = determine_tendency(scores["ai_score"], scores["real_score"], confidence)

    analysis = {
        "image_path": image_path,
        "visual_string": visual_string,
        "visual_string_length": len(visual_string),
        "confidence": confidence,
        "result": result,
    }
    analysis.update(scores)
    return analysis

def build_comparison_summary(ai_analysis: Dict, real_analysis: Dict) -> str:
    lines: List[str] = []

    if ai_analysis["ai_score"] > real_analysis["ai_score"]:
        stronger_ai = "the AI-generated image"
    elif real_analysis["ai_score"] > ai_analysis["ai_score"]:
        stronger_ai = "the real image"
    else:
        stronger_ai = "both images equally"
    lines.append(f"Stronger AI-like visual patterns appear in {stronger_ai}.")

    if ai_analysis["real_score"] > real_analysis["real_score"]:
        stronger_real = "the AI-generated image"
    elif real_analysis["real_score"] > ai_analysis["real_score"]:
        stronger_real = "the real image"
    else:
        stronger_real = "both images equally"
    lines.append(f"Stronger real-like visual patterns appear in {stronger_real}.")

    ai_top_exact = _most_frequent_patterns(ai_analysis["ai_exact_results"]["per_pattern"], "kmp_count")
    real_top_exact = _most_frequent_patterns(real_analysis["real_exact_results"]["per_pattern"], "kmp_count")
    lines.append(
        "Most frequent AI-like exact patterns in the AI image: "
        + (", ".join(f"{name}({value})" for name, value in ai_top_exact) if ai_top_exact else "none")
        + "."
    )
    lines.append(
        "Most frequent real-like exact patterns in the real image: "
        + (", ".join(f"{name}({value})" for name, value in real_top_exact) if real_top_exact else "none")
        + "."
    )

    ai_top_regex = _most_frequent_patterns(ai_analysis["ai_regex_results"]["per_pattern"], "count")
    real_top_regex = _most_frequent_patterns(real_analysis["real_regex_results"]["per_pattern"], "count")
    lines.append(
        "Most frequent AI-like regex patterns in the AI image: "
        + (", ".join(f"{name}({value})" for name, value in ai_top_regex) if ai_top_regex else "none")
        + "."
    )
    lines.append(
        "Most frequent real-like regex patterns in the real image: "
        + (", ".join(f"{name}({value})" for name, value in real_top_regex) if real_top_regex else "none")
        + "."
    )

    lines.append(
        "Interpretation: the AI image tendency is "
        + f"'{ai_analysis['result']}' (confidence {ai_analysis['confidence']:.4f}) "
        + "and the real image tendency is "
        + f"'{real_analysis['result']}' (confidence {real_analysis['confidence']:.4f}). "
        + "These are rule-based tendency scores derived from visual pattern strings, not absolute forensic detection results."
    )

    return " ".join(lines)

def compare_two_images(ai_image_path: str, real_image_path: str) -> Dict:
    ai_analysis = analyze_single_image(ai_image_path)
    real_analysis = analyze_single_image(real_image_path)
    summary = build_comparison_summary(ai_analysis, real_analysis)
    return {
        "ai_analysis": ai_analysis,
        "real_analysis": real_analysis,
        "summary": summary,
    }