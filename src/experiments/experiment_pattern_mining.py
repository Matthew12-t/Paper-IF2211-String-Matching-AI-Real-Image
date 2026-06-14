import argparse
import itertools
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from algorithms.string_matching import kmp_search
from imaging.image_to_string import image_to_visual_string

ALPHABET = "HSEVTDCGL"
MIN_AVERAGE = 0.10
TOP_COUNT = 16

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

def visual_strings(directory: str) -> List[str]:
    result: List[str] = []
    for path in collect_images(directory):
        try:
            result.append(image_to_visual_string(path))
        except (FileNotFoundError, ValueError):
            continue
    return result

def generate_candidates(lengths: List[int]) -> List[str]:
    candidates: List[str] = []
    for length in lengths:
        for combination in itertools.product(ALPHABET, repeat=length):
            candidates.append("".join(combination))
    return candidates

def average_occurrence(pattern: str, strings: List[str]) -> float:
    total = 0
    for text in strings:
        total += kmp_search(text, pattern)[1]
    return total / len(strings) if strings else 0.0

def score_candidates(candidates: List[str], ai_strings: List[str], real_strings: List[str]) -> List[Tuple[str, float, float, float]]:
    scored: List[Tuple[str, float, float, float]] = []
    for pattern in candidates:
        avg_ai = average_occurrence(pattern, ai_strings)
        avg_real = average_occurrence(pattern, real_strings)
        if avg_ai < MIN_AVERAGE and avg_real < MIN_AVERAGE:
            continue
        scored.append((pattern, avg_ai, avg_real, avg_ai - avg_real))
    return scored

def print_table(title: str, rows: List[Tuple[str, float, float, float]]) -> None:
    print(title)
    print(f"  {'pattern':10}{'avg in AI':>12}{'avg in real':>14}{'difference':>13}")
    for pattern, avg_ai, avg_real, difference in rows:
        print(f"  {pattern:10}{avg_ai:12.3f}{avg_real:14.3f}{difference:13.3f}")
    print()

def run(ai_dir: str, real_dir: str) -> None:
    ai_strings = visual_strings(ai_dir)
    real_strings = visual_strings(real_dir)
    print("Pattern mining experiment")
    print(f"AI images: {len(ai_strings)}  real images: {len(real_strings)}")
    print(f"alphabet: {ALPHABET}  candidate lengths: 2 and 3")
    print()

    candidates = generate_candidates([2, 3])
    scored = score_candidates(candidates, ai_strings, real_strings)

    ai_ranked = sorted(scored, key=lambda item: item[3], reverse=True)[:TOP_COUNT]
    real_ranked = sorted(scored, key=lambda item: item[3])[:TOP_COUNT]

    print_table("Top AI-leaning patterns (most frequent in AI relative to real)", ai_ranked)
    print_table("Top real-leaning patterns (most frequent in real relative to AI)", real_ranked)

    print("Suggested config lists derived from the data:")
    print("AI_EXACT_PATTERNS  = " + str([pattern for pattern, _, _, _ in ai_ranked]))
    print("REAL_EXACT_PATTERNS = " + str([pattern for pattern, _, _, _ in real_ranked]))

def main() -> None:
    parser = argparse.ArgumentParser(description="Pattern mining experiment")
    parser.add_argument("--ai-dir", required=True)
    parser.add_argument("--real-dir", required=True)
    args = parser.parse_args()
    try:
        run(args.ai_dir, args.real_dir)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}")

if __name__ == "__main__":
    main()