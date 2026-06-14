import csv
from pathlib import Path
from typing import Dict, List

def ensure_output_directory(output_path: str) -> None:
    parent = Path(output_path).parent
    if str(parent) != "":
        parent.mkdir(parents=True, exist_ok=True)

def write_single_result(output_path: str, analysis: Dict) -> None:
    ensure_output_directory(output_path)
    header = [
        "image_path",
        "visual_string",
        "visual_string_length",
        "ai_exact_score",
        "real_exact_score",
        "ai_regex_score",
        "real_regex_score",
        "ai_score",
        "real_score",
        "confidence",
        "final_result",
        "brute_force_ai_pattern_count",
        "brute_force_real_pattern_count",
        "kmp_ai_pattern_count",
        "kmp_real_pattern_count",
        "boyer_moore_ai_pattern_count",
        "boyer_moore_real_pattern_count",
        "regex_ai_pattern_count",
        "regex_real_pattern_count",
        "brute_force_total_time",
        "kmp_total_time",
        "boyer_moore_total_time",
    ]
    row = [
        analysis["image_path"],
        analysis["visual_string"],
        analysis["visual_string_length"],
        analysis["ai_exact_score"],
        analysis["real_exact_score"],
        analysis["ai_regex_score"],
        analysis["real_regex_score"],
        analysis["ai_score"],
        analysis["real_score"],
        f"{analysis['confidence']:.6f}",
        analysis["result"],
        analysis["ai_exact_results"]["bf_total_count"],
        analysis["real_exact_results"]["bf_total_count"],
        analysis["ai_exact_results"]["kmp_total_count"],
        analysis["real_exact_results"]["kmp_total_count"],
        analysis["ai_exact_results"]["bm_total_count"],
        analysis["real_exact_results"]["bm_total_count"],
        analysis["ai_regex_score"],
        analysis["real_regex_score"],
        f"{analysis['ai_exact_results']['bf_total_time'] + analysis['real_exact_results']['bf_total_time']:.8f}",
        f"{analysis['ai_exact_results']['kmp_total_time'] + analysis['real_exact_results']['kmp_total_time']:.8f}",
        f"{analysis['ai_exact_results']['bm_total_time'] + analysis['real_exact_results']['bm_total_time']:.8f}",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerow(row)

def write_compare_result(output_path: str, comparison: Dict) -> None:
    ensure_output_directory(output_path)
    ai = comparison["ai_analysis"]
    real = comparison["real_analysis"]
    header = [
        "ai_image_path",
        "real_image_path",
        "ai_image_visual_string",
        "real_image_visual_string",
        "ai_image_ai_exact_score",
        "ai_image_real_exact_score",
        "ai_image_ai_regex_score",
        "ai_image_real_regex_score",
        "ai_image_ai_score",
        "ai_image_real_score",
        "ai_image_confidence",
        "ai_image_result",
        "real_image_ai_exact_score",
        "real_image_real_exact_score",
        "real_image_ai_regex_score",
        "real_image_real_regex_score",
        "real_image_ai_score",
        "real_image_real_score",
        "real_image_confidence",
        "real_image_result",
        "comparison_summary",
    ]
    row = [
        ai["image_path"],
        real["image_path"],
        ai["visual_string"],
        real["visual_string"],
        ai["ai_exact_score"],
        ai["real_exact_score"],
        ai["ai_regex_score"],
        ai["real_regex_score"],
        ai["ai_score"],
        ai["real_score"],
        f"{ai['confidence']:.6f}",
        ai["result"],
        real["ai_exact_score"],
        real["real_exact_score"],
        real["ai_regex_score"],
        real["real_regex_score"],
        real["ai_score"],
        real["real_score"],
        f"{real['confidence']:.6f}",
        real["result"],
        comparison["summary"],
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerow(row)

def write_batch_result(output_path: str, rows: List[Dict]) -> None:
    ensure_output_directory(output_path)
    header = [
        "image_path",
        "label",
        "visual_string",
        "visual_string_length",
        "ai_exact_score",
        "real_exact_score",
        "ai_regex_score",
        "real_regex_score",
        "ai_score",
        "real_score",
        "confidence",
        "predicted_tendency",
        "prediction_matches_label",
        "brute_force_time",
        "kmp_time",
        "boyer_moore_time",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for analysis in rows:
            bf_time = analysis["ai_exact_results"]["bf_total_time"] + analysis["real_exact_results"]["bf_total_time"]
            kmp_time = analysis["ai_exact_results"]["kmp_total_time"] + analysis["real_exact_results"]["kmp_total_time"]
            bm_time = analysis["ai_exact_results"]["bm_total_time"] + analysis["real_exact_results"]["bm_total_time"]
            writer.writerow([
                analysis["image_path"],
                analysis["label"],
                analysis["visual_string"],
                analysis["visual_string_length"],
                analysis["ai_exact_score"],
                analysis["real_exact_score"],
                analysis["ai_regex_score"],
                analysis["real_regex_score"],
                analysis["ai_score"],
                analysis["real_score"],
                f"{analysis['confidence']:.6f}",
                analysis["result"],
                analysis["prediction_matches_label"],
                f"{bf_time:.8f}",
                f"{kmp_time:.8f}",
                f"{bm_time:.8f}",
            ])