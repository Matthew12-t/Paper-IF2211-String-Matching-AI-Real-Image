import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from analysis.scoring import calculate_scores
from imaging.image_to_string import (
    calculate_block_features,
    encode_block,
    load_image,
    preprocess_image,
    split_into_blocks,
)

SWEEP = [
    ("TEXTURE_THRESHOLD", [24, 28, 32, 36, 40]),
    ("CONTRAST_THRESHOLD", [100, 110, 120, 130, 140]),
    ("GLOW_THRESHOLD", [0.25, 0.30, 0.35, 0.40]),
    ("EDGE_DENSITY_THRESHOLD", [0.08, 0.10, 0.12, 0.15]),
    ("LINE_SCORE_THRESHOLD", [0.50, 0.60, 0.70]),
    ("BRIGHTNESS_THRESHOLD", [130, 140, 150, 160]),
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

def balanced_accuracy(samples: List[Tuple[List[Dict[str, float]], str]]) -> Tuple[float, float, float]:
    ai_correct = ai_total = real_correct = real_total = 0
    for features, label in samples:
        visual_string = "".join(encode_block(feature) for feature in features)
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
    base_ai, base_real, base_balanced = balanced_accuracy(samples)
    print("Threshold sensitivity experiment")
    print(f"images: {len(samples)}")
    print(f"baseline balanced accuracy: {base_balanced * 100:.1f}% (AI {base_ai * 100:.1f}%, real {base_real * 100:.1f}%)")
    print()

    for name, values in SWEEP:
        original = getattr(config, name)
        print(f"{name} (current = {original})")
        best_value = original
        best_balanced = -1.0
        for value in values:
            setattr(config, name, value)
            ai_recall, real_recall, balanced = balanced_accuracy(samples)
            marker = " <= current" if value == original else ""
            print(
                f"  {name} = {value:<6} balanced = {balanced * 100:5.1f}%"
                f"  (AI {ai_recall * 100:4.1f}%, real {real_recall * 100:4.1f}%){marker}"
            )
            if balanced > best_balanced:
                best_balanced = balanced
                best_value = value
        setattr(config, name, original)
        print(f"  best: {name} = {best_value} -> {best_balanced * 100:.1f}%")
        print()

def main() -> None:
    parser = argparse.ArgumentParser(description="Threshold sensitivity experiment")
    parser.add_argument("--ai-dir", required=True)
    parser.add_argument("--real-dir", required=True)
    args = parser.parse_args()
    try:
        run(args.ai_dir, args.real_dir)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}")

if __name__ == "__main__":
    main()