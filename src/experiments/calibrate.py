import argparse
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import config

from imaging.image_to_string import (
    calculate_block_features,
    image_to_visual_string,
    load_image,
    preprocess_image,
    split_into_blocks,
)

FEATURE_KEYS = [
    "brightness",
    "texture",
    "edge_density",
    "contrast",
    "saturation",
    "glow_score",
    "line_score",
]

CANDIDATE_GROUPINGS = [
    ("VCL", "HSTDE"),
    ("VCLG", "HSTDE"),
    ("VCL", "HSTD"),
    ("VCLG", "HSTD"),
    ("VC", "HSTDE"),
    ("VCLGE", "HSTD"),
    ("VCLG", "HSTDEH"),
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

def average_features(image_paths: List[str]) -> Dict[str, float]:
    totals: Dict[str, List[float]] = {key: [] for key in FEATURE_KEYS}
    for path in image_paths:
        try:
            image = load_image(path)
        except (FileNotFoundError, ValueError):
            continue
        gray, hsv, edges = preprocess_image(image)
        saturation = hsv[:, :, 1]
        gray_blocks = split_into_blocks(gray)
        saturation_blocks = split_into_blocks(saturation)
        edge_blocks = split_into_blocks(edges)
        for index in range(len(gray_blocks)):
            features = calculate_block_features(
                gray_blocks[index],
                saturation_blocks[index],
                edge_blocks[index],
            )
            for key in FEATURE_KEYS:
                totals[key].append(features[key])
    return {key: float(np.mean(values)) for key, values in totals.items()}

def visual_strings(image_paths: List[str]) -> List[str]:
    result: List[str] = []
    for path in image_paths:
        try:
            result.append(image_to_visual_string(path))
        except (FileNotFoundError, ValueError):
            continue
    return result

def predict_by_symbols(visual_string: str, ai_symbols: set, real_symbols: set) -> str:
    ai = sum(visual_string.count(symbol) for symbol in ai_symbols)
    real = sum(visual_string.count(symbol) for symbol in real_symbols)
    if ai > real:
        return "ai"
    if real > ai:
        return "real"
    return "tie"

def balanced_accuracy(
    ai_strings: List[str],
    real_strings: List[str],
    ai_symbols: set,
    real_symbols: set,
) -> Tuple[float, float, float]:
    ai_recall = sum(
        1 for item in ai_strings if predict_by_symbols(item, ai_symbols, real_symbols) == "ai"
    ) / len(ai_strings)
    real_recall = sum(
        1 for item in real_strings if predict_by_symbols(item, ai_symbols, real_symbols) == "real"
    ) / len(real_strings)
    return ai_recall, real_recall, (ai_recall + real_recall) / 2.0

def select_grouping(ai_strings: List[str], real_strings: List[str]) -> Tuple[str, str, float]:
    best: Tuple[str, str, float] = ("", "", -1.0)
    for ai_symbols, real_symbols in CANDIDATE_GROUPINGS:
        _, _, score = balanced_accuracy(ai_strings, real_strings, set(ai_symbols), set(real_symbols))
        if score > best[2]:
            best = (ai_symbols, real_symbols, score)
    return best

def split_halves(items: List[str], seed: int) -> Tuple[List[str], List[str]]:
    shuffled = list(items)
    random.Random(seed).shuffle(shuffled)
    half = len(shuffled) // 2
    return shuffled[:half], shuffled[half:]

def run(ai_dir: str, real_dir: str, seed: int) -> None:
    ai_paths = collect_images(ai_dir)
    real_paths = collect_images(real_dir)

    ai_features = average_features(ai_paths)
    real_features = average_features(real_paths)

    print("Average block features per class")
    print(f"{'feature':13}{'AI':>10}{'REAL':>10}{'diff':>10}")
    for key in FEATURE_KEYS:
        difference = ai_features[key] - real_features[key]
        print(f"{key:13}{ai_features[key]:10.3f}{real_features[key]:10.3f}{difference:10.3f}")
    print()

    ai_strings = visual_strings(ai_paths)
    real_strings = visual_strings(real_paths)

    ai_symbols, real_symbols, full_score = select_grouping(ai_strings, real_strings)
    ai_recall, real_recall, _ = balanced_accuracy(
        ai_strings, real_strings, set(ai_symbols), set(real_symbols)
    )
    print("Symbol grouping with highest balanced accuracy on full data")
    print(f"  AI-like symbols   : {', '.join(ai_symbols)}")
    print(f"  real-like symbols : {', '.join(real_symbols)}")
    print(f"  AI recall         : {ai_recall * 100:.1f}%")
    print(f"  real recall       : {real_recall * 100:.1f}%")
    print(f"  balanced accuracy : {full_score * 100:.1f}%")
    print()

    ai_train, ai_test = split_halves(ai_strings, seed)
    real_train, real_test = split_halves(real_strings, seed)
    train_ai, train_real, _ = select_grouping(ai_train, real_train)
    train_score = balanced_accuracy(ai_train, real_train, set(train_ai), set(train_real))[2]
    test_score = balanced_accuracy(ai_test, real_test, set(train_ai), set(train_real))[2]
    print("Train/test validation (grouping chosen on train, evaluated on test)")
    print(f"  grouping from train : AI={train_ai} REAL={train_real}")
    print(f"  balanced on train   : {train_score * 100:.1f}%")
    print(f"  balanced on test    : {test_score * 100:.1f}%")
    print()

def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate symbol grouping from a dataset")
    parser.add_argument("--ai-dir", required=True)
    parser.add_argument("--real-dir", required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    try:
        run(args.ai_dir, args.real_dir, args.seed)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}")

if __name__ == "__main__":
    main()