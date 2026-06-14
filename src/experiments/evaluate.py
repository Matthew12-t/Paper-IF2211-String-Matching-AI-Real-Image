import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

AI_RESULT = "tends to have AI-generated visual characteristics"
REAL_RESULT = "tends to have real image visual characteristics"

def category_of(image_path: str) -> str:
    parts = image_path.replace("\\", "/").split("/")
    return parts[-2] if len(parts) >= 2 else "unknown"

def load_rows(csv_path: str) -> List[Dict]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    rows: List[Dict] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for record in reader:
            rows.append(
                {
                    "label": record["label"],
                    "ai_score": float(record["ai_score"]),
                    "real_score": float(record["real_score"]),
                    "result": record["predicted_tendency"],
                    "category": category_of(record["image_path"]),
                    "bf_time": float(record["brute_force_time"]),
                    "kmp_time": float(record["kmp_time"]),
                    "bm_time": float(record["boyer_moore_time"]),
                }
            )
    if len(rows) == 0:
        raise ValueError(f"No data rows in: {csv_path}")
    return rows

def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0

def direction_prediction(row: Dict) -> str:
    if row["ai_score"] > row["real_score"]:
        return "ai"
    if row["real_score"] > row["ai_score"]:
        return "real"
    return "tie"

def confusion(rows: List[Dict]) -> Tuple[int, int, int, int, int]:
    true_positive = false_positive = false_negative = true_negative = tie = 0
    for row in rows:
        prediction = direction_prediction(row)
        if prediction == "tie":
            tie += 1
            continue
        if row["label"] == "ai":
            if prediction == "ai":
                true_positive += 1
            else:
                false_negative += 1
        else:
            if prediction == "ai":
                false_positive += 1
            else:
                true_negative += 1
    return true_positive, false_positive, false_negative, true_negative, tie

def print_classification(rows: List[Dict]) -> None:
    tp, fp, fn, tn, tie = confusion(rows)
    print("Confusion matrix (direction-based, ties excluded)")
    print(f"  {'':12}{'pred AI':>10}{'pred real':>12}")
    print(f"  {'true AI':12}{tp:>10}{fn:>12}")
    print(f"  {'true real':12}{fp:>10}{tn:>12}")
    print(f"  ties (ai score == real score): {tie}")
    print()

    ai_recall = safe_div(tp, tp + fn)
    real_recall = safe_div(tn, tn + fp)
    ai_precision = safe_div(tp, tp + fp)
    real_precision = safe_div(tn, tn + fn)
    ai_f1 = safe_div(2 * ai_precision * ai_recall, ai_precision + ai_recall)
    real_f1 = safe_div(2 * real_precision * real_recall, real_precision + real_recall)
    balanced = (ai_recall + real_recall) / 2.0
    decided = tp + fp + fn + tn
    simple = safe_div(tp + tn, decided)

    print("Per-class metrics")
    print(f"  {'class':8}{'precision':>11}{'recall':>9}{'f1':>8}")
    print(f"  {'AI':8}{ai_precision * 100:>10.1f}%{ai_recall * 100:>8.1f}%{ai_f1 * 100:>7.1f}%")
    print(f"  {'real':8}{real_precision * 100:>10.1f}%{real_recall * 100:>8.1f}%{real_f1 * 100:>7.1f}%")
    print()
    print(f"Balanced accuracy: {balanced * 100:.1f}%")
    print(f"Simple accuracy:   {simple * 100:.1f}% ({tp + tn}/{decided})")
    print()

def print_decision_coverage(rows: List[Dict]) -> None:
    total = len(rows)
    inconclusive = sum(1 for row in rows if row["result"] == "inconclusive")
    decided = total - inconclusive
    correct = 0
    for row in rows:
        if row["result"] == "inconclusive":
            continue
        prediction = "ai" if row["result"] == AI_RESULT else "real"
        if prediction == row["label"]:
            correct += 1
    print("Decision-based metrics (using the program tendency, with abstention)")
    print(f"  inconclusive: {inconclusive}/{total} ({safe_div(inconclusive, total) * 100:.1f}%)")
    print(f"  coverage (decided): {decided}/{total} ({safe_div(decided, total) * 100:.1f}%)")
    print(f"  accuracy on decided: {safe_div(correct, decided) * 100:.1f}% ({correct}/{decided})")
    print()

def print_per_category(rows: List[Dict]) -> None:
    categories: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    for row in rows:
        prediction = direction_prediction(row)
        if prediction == "tie":
            continue
        bucket = categories[row["category"]]
        bucket[1] += 1
        if prediction == row["label"]:
            bucket[0] += 1
    print("Accuracy per category (direction-based)")
    for category in sorted(categories):
        correct, total = categories[category]
        print(f"  {category:12}{safe_div(correct, total) * 100:6.1f}% ({correct}/{total})")
    print()

def print_timing(rows: List[Dict]) -> None:
    brute_force = sum(row["bf_time"] for row in rows)
    kmp = sum(row["kmp_time"] for row in rows)
    boyer_moore = sum(row["bm_time"] for row in rows)
    count = len(rows)
    print("Average exact-match execution time per image (seconds)")
    print(f"  Brute Force : {safe_div(brute_force, count):.8f}")
    print(f"  KMP         : {safe_div(kmp, count):.8f}")
    print(f"  Boyer-Moore : {safe_div(boyer_moore, count):.8f}")
    print()

def run(csv_path: str) -> None:
    rows = load_rows(csv_path)
    ai_count = sum(1 for row in rows if row["label"] == "ai")
    real_count = len(rows) - ai_count
    print("=" * 60)
    print("Evaluation report")
    print("=" * 60)
    print(f"source: {csv_path}")
    print(f"images: {len(rows)} (AI {ai_count}, real {real_count})")
    print()
    print_classification(rows)
    print_decision_coverage(rows)
    print_per_category(rows)
    print_timing(rows)

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluation report computed from a batch CSV")
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    try:
        run(args.csv)
    except (FileNotFoundError, ValueError, KeyError) as error:
        print(f"Error: {error}")

if __name__ == "__main__":
    main()