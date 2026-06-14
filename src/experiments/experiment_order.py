import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from analysis.scoring import calculate_scores
from imaging.image_to_string import (
    calculate_block_features,
    load_image,
    preprocess_image,
    split_into_blocks,
)

CANDIDATE_ORDERS = [
    ("baseline", ["G", "L", "E", "V", "C", "T", "D", "S"]),
    ("swap V and C", ["G", "L", "E", "C", "V", "T", "D", "S"]),
    ("E after V", ["G", "L", "V", "E", "C", "T", "D", "S"]),
    ("texture first", ["V", "C", "E", "G", "L", "T", "D", "S"]),
    ("glow and line last", ["E", "V", "C", "T", "D", "S", "G", "L"]),
    ("swap G and L", ["L", "G", "E", "V", "C", "T", "D", "S"]),
    ("contrast first", ["C", "V", "E", "G", "L", "T", "D", "S"]),
]

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

def load_block_features(ai_dir: str, real_dir: str) -> List[Tuple[List[Dict[str, float]], str]]:
    samples: List[Tuple[List[Dict[str, float]], str]] = []
    for directory, label in [(ai_dir, "ai"), (real_dir, "real")]:
        for path in collect_images(directory):
            try:
                image = load_image(path)
            except (FileNotFoundError, ValueError):
                continue
            gray, hsv, edges = preprocess_image(image)
            saturation = hsv[:, :, 1]
            gray_blocks = split_into_blocks(gray)
            saturation_blocks = split_into_blocks(saturation)
            edge_blocks = split_into_blocks(edges)
            features = [
                calculate_block_features(gray_blocks[i], saturation_blocks[i], edge_blocks[i])
                for i in range(len(gray_blocks))
            ]
            samples.append((features, label))
    return samples

def rule_conditions(feature: Dict[str, float]) -> Dict[str, bool]:
    return {
        "G": feature["glow_score"] > config.GLOW_THRESHOLD,
        "L": feature["line_score"] > config.LINE_SCORE_THRESHOLD,
        "E": feature["edge_density"] > config.EDGE_DENSITY_THRESHOLD
        and feature["contrast"] > config.CONTRAST_THRESHOLD,
        "V": feature["texture"] > config.TEXTURE_THRESHOLD,
        "C": feature["contrast"] > config.CONTRAST_THRESHOLD,
        "T": feature["brightness"] > config.BRIGHTNESS_THRESHOLD
        and feature["texture"] < config.TEXTURE_THRESHOLD,
        "D": feature["brightness"] < config.DARK_BRIGHTNESS_THRESHOLD
        and feature["texture"] < config.TEXTURE_THRESHOLD,
        "S": feature["texture"] < config.VERY_LOW_TEXTURE_THRESHOLD,
    }

def encode_with_order(feature: Dict[str, float], order: List[str]) -> str:
    conditions = rule_conditions(feature)
    for symbol in order:
        if conditions[symbol]:
            return symbol
    return "H"

def balanced_accuracy(samples: List[Tuple[List[Dict[str, float]], str]], order: List[str]) -> Tuple[float, float, float]:
    ai_correct = ai_total = real_correct = real_total = 0
    for features, label in samples:
        visual_string = "".join(encode_with_order(feature, order) for feature in features)
        scores = calculate_scores(visual_string)
        prediction = "ai" if scores["ai_score"] > scores["real_score"] else "real"
        if label == "ai":
            ai_total += 1
            ai_correct += 1 if prediction == "ai" else 0
        else:
            real_total += 1
            real_correct += 1 if prediction == "real" else 0
    ai_recall = ai_correct / ai_total if ai_total else 0.0
    real_recall = real_correct / real_total if real_total else 0.0
    return ai_recall, real_recall, (ai_recall + real_recall) / 2.0

def run(ai_dir: str, real_dir: str) -> None:
    samples = load_block_features(ai_dir, real_dir)
    print("Rule order experiment")
    print(f"images: {len(samples)}")
    print()
    results = []
    for name, order in CANDIDATE_ORDERS:
        ai_recall, real_recall, balanced = balanced_accuracy(samples, order)
        results.append((name, order, balanced, ai_recall, real_recall))
        print(
            f"{name:22} {' '.join(order)}  balanced = {balanced * 100:5.1f}%"
            f"  (AI {ai_recall * 100:4.1f}%, real {real_recall * 100:4.1f}%)"
        )
    print()
    best = max(results, key=lambda item: item[2])
    print(f"best order: {best[0]} ({' '.join(best[1])}) -> {best[2] * 100:.1f}%")

def main() -> None:
    parser = argparse.ArgumentParser(description="Rule order experiment")
    parser.add_argument("--ai-dir", required=True)
    parser.add_argument("--real-dir", required=True)
    args = parser.parse_args()
    try:
        run(args.ai_dir, args.real_dir)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}")

if __name__ == "__main__":
    main()