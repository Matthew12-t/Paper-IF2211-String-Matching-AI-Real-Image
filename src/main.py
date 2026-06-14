import argparse
import sys
from pathlib import Path
from typing import Dict, List
import config
from results.csv_writer import write_batch_result, write_compare_result, write_single_result
from analysis.scoring import analyze_single_image, compare_two_images

def print_visual_string(label: str, analysis: Dict) -> None:
    print(f"{label} visual string ({analysis['visual_string_length']} symbols):")
    print(analysis["visual_string"])
    print("")

def print_exact_algorithm_report(title: str, exact_results: Dict) -> None:
    print(title)
    per_pattern = exact_results["per_pattern"]
    for pattern, data in per_pattern.items():
        print(
            f"  pattern={data['pattern']} "
            f"BF={data['bf_count']} KMP={data['kmp_count']} BM={data['bm_count']} "
            f"BF_pos={data['bf_positions']} KMP_pos={data['kmp_positions']} BM_pos={data['bm_positions']} "
            f"BF_time={data['bf_time']:.8f} KMP_time={data['kmp_time']:.8f} BM_time={data['bm_time']:.8f}"
        )
    print(
        f"  totals BF={exact_results['bf_total_count']} "
        f"KMP={exact_results['kmp_total_count']} BM={exact_results['bm_total_count']} "
        f"BF_time={exact_results['bf_total_time']:.8f} "
        f"KMP_time={exact_results['kmp_total_time']:.8f} "
        f"BM_time={exact_results['bm_total_time']:.8f}"
    )
    print("")

def print_regex_report(title: str, regex_results: Dict) -> None:
    print(title)
    for name, data in regex_results["per_pattern"].items():
        print(
            f"  regex={data['name']} count={data['count']} "
            f"matches={data['matches']} positions={data['positions']}"
        )
    print(f"  total regex matches={regex_results['total_matches']}")
    print("")

def print_analysis(label: str, analysis: Dict) -> None:
    print("=" * 70)
    print(f"{label}: {analysis['image_path']}")
    print("=" * 70)
    print_visual_string(label, analysis)
    print_exact_algorithm_report("AI-like exact pattern matching:", analysis["ai_exact_results"])
    print_exact_algorithm_report("Real-like exact pattern matching:", analysis["real_exact_results"])
    print_regex_report("AI-like regex analysis:", analysis["ai_regex_results"])
    print_regex_report("Real-like regex analysis:", analysis["real_regex_results"])
    print(f"AI exact score: {analysis['ai_exact_score']}")
    print(f"Real exact score: {analysis['real_exact_score']}")
    print(f"AI regex score: {analysis['ai_regex_score']}")
    print(f"Real regex score: {analysis['real_regex_score']}")
    print(f"AI score: {analysis['ai_score']}")
    print(f"Real score: {analysis['real_score']}")
    print(f"Confidence: {analysis['confidence']:.6f}")
    print(f"Result: {analysis['result']}")
    print("")

def run_single(image_path: str, output_path: str) -> int:
    analysis = analyze_single_image(image_path)
    print_analysis("Single image", analysis)
    write_single_result(output_path, analysis)
    print(f"Result saved to: {output_path}")
    return 0

def run_compare(ai_image_path: str, real_image_path: str, output_path: str) -> int:
    comparison = compare_two_images(ai_image_path, real_image_path)
    print_analysis("AI-generated image", comparison["ai_analysis"])
    print_analysis("Real image", comparison["real_analysis"])
    print("=" * 70)
    print("Comparison summary")
    print("=" * 70)
    print(comparison["summary"])
    print("")
    write_compare_result(output_path, comparison)
    print(f"Result saved to: {output_path}")
    return 0

def collect_images(directory: str) -> List[str]:
    folder = Path(directory)
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {directory}")
    images: List[str] = []
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix.lower() in config.SUPPORTED_EXTENSIONS:
            images.append(str(path))
    if len(images) == 0:
        raise ValueError(f"Empty folder or no supported images in: {directory}")
    return images

def analyze_folder(directory: str, label: str) -> List[Dict]:
    rows: List[Dict] = []
    for image_path in collect_images(directory):
        try:
            analysis = analyze_single_image(image_path)
        except (FileNotFoundError, ValueError) as error:
            print(f"Skipping {image_path}: {error}")
            continue
        analysis["label"] = label
        matches = (
            (label == "ai" and analysis["result"] == "tends to have AI-generated visual characteristics")
            or (label == "real" and analysis["result"] == "tends to have real image visual characteristics")
        )
        analysis["prediction_matches_label"] = matches
        rows.append(analysis)
    return rows

def average(values: List[float]) -> float:
    if len(values) == 0:
        return 0.0
    return sum(values) / len(values)

def print_batch_summary(ai_rows: List[Dict], real_rows: List[Dict]) -> None:
    print("=" * 70)
    print("Batch summary statistics")
    print("=" * 70)
    print(f"Number of AI-generated images: {len(ai_rows)}")
    print(f"Number of real images: {len(real_rows)}")
    print(f"Average AI score for AI-generated images: {average([row['ai_score'] for row in ai_rows]):.4f}")
    print(f"Average real score for AI-generated images: {average([row['real_score'] for row in ai_rows]):.4f}")
    print(f"Average confidence for AI-generated images: {average([row['confidence'] for row in ai_rows]):.4f}")
    print(f"Average AI score for real images: {average([row['ai_score'] for row in real_rows]):.4f}")
    print(f"Average real score for real images: {average([row['real_score'] for row in real_rows]):.4f}")
    print(f"Average confidence for real images: {average([row['confidence'] for row in real_rows]):.4f}")
    all_rows = ai_rows + real_rows
    correct = sum(1 for row in all_rows if row["prediction_matches_label"])
    total = len(all_rows)
    accuracy = (correct / total) if total > 0 else 0.0
    print(f"Simple tendency accuracy: {accuracy:.4f} ({correct}/{total})")
    print("")

def run_batch(ai_dir: str, real_dir: str, output_path: str) -> int:
    ai_rows = analyze_folder(ai_dir, "ai")
    real_rows = analyze_folder(real_dir, "real")
    all_rows = ai_rows + real_rows
    write_batch_result(output_path, all_rows)
    print_batch_summary(ai_rows, real_rows)
    print(f"Result saved to: {output_path}")
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Visual pattern string matching and regex analysis for AI-generated and real images"
    )
    subparsers = parser.add_subparsers(dest="mode")

    single_parser = subparsers.add_parser("single")
    single_parser.add_argument("--image", required=True)
    single_parser.add_argument("--output", required=True)

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--ai", required=True)
    compare_parser.add_argument("--real", required=True)
    compare_parser.add_argument("--output", required=True)

    batch_parser = subparsers.add_parser("batch")
    batch_parser.add_argument("--ai-dir", required=True)
    batch_parser.add_argument("--real-dir", required=True)
    batch_parser.add_argument("--output", required=True)

    return parser

def main(argv: List[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.mode is None:
        parser.print_help()
        return 2
    try:
        if args.mode == "single":
            return run_single(args.image, args.output)
        if args.mode == "compare":
            return run_compare(args.ai, args.real, args.output)
        if args.mode == "batch":
            return run_batch(args.ai_dir, args.real_dir, args.output)
        print(f"Unsupported mode: {args.mode}")
        return 2
    except FileNotFoundError as error:
        print(f"Error: {error}")
        return 1
    except ValueError as error:
        print(f"Error: {error}")
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))