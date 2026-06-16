# Application of String Matching Algorithms and Regular Expressions Using Visual Pattern Representation for AI-Generated and Real Image Analysis

## Overview

This program analyzes AI-generated images and real images **without using any machine
learning model**. Each image is converted into a 64-symbol *visual pattern string*, and the
analysis is performed entirely with classical string matching algorithms (Brute Force,
Knuth-Morris-Pratt, Boyer-Moore) and regular expressions. The final output is a rule-based
**tendency score** (AI-like / real-like / inconclusive), not an absolute forensic decision.

It contains no neural networks, classifiers, or pretrained detectors, and does not use
`torch`, `tensorflow`, `keras`, or `sklearn`. OpenCV and NumPy are used only to read an image
and compute simple per-block features; every decision after that is made by fixed,
human-written rules and deterministic algorithms.

The program offers three command-line modes (single, compare, batch) and a desktop GUI for
the single and compare modes.

## Algorithms (Core)

### 1. Image to visual string

For each image:

1. Read the image and resize to 256 x 256.
2. Build grayscale, HSV, and Canny-edge versions.
3. Split into 32 x 32 blocks, giving 8 x 8 = **64 blocks**.
4. For each block compute 7 features: brightness, texture (std), edge density, contrast,
   saturation, glow score, and line score.
5. Encode each block into one symbol, then concatenate left-to-right, top-to-bottom into a
   **64-symbol visual string**.

Symbols and their tendency group:

| Symbol | Meaning | Group |
| ------ | ------- | ----- |
| V | high texture variation | AI-like |
| C | high contrast | AI-like |
| L | digital line / line-art | AI-like |
| H | smooth | real-like |
| S | uniform | real-like |
| T | bright smooth | real-like |
| D | dark smooth | real-like |
| E | high edge density | real-like |
| G | glow / highly saturated | neutral |

Encoding rules (checked in this fixed priority order, first match wins):

```
glow high                         -> G
line score high                   -> L
edge density high and contrast high -> E
texture high                      -> V
contrast high                     -> C
bright and low texture            -> T
dark and low texture              -> D
texture very low                  -> S
otherwise                         -> H
```

All thresholds live in `src/config.py`. The encoding logic lives in
`src/imaging/image_to_string.py`.

### 2. String matching (Brute Force, KMP, Boyer-Moore)

Each algorithm is implemented manually in `src/algorithms/string_matching.py` and returns the
list of starting indices, the match count, and the execution time. They do **not** use
Python's `find` or the `in` operator.

- **Brute Force** slides the pattern across the text one position at a time.
- **KMP** builds a longest-proper-prefix-suffix (LPS) table to skip work after a mismatch.
- **Boyer-Moore** uses a bad-character table and compares the pattern from right to left.

All three solve the same problem, so they return identical counts and positions; only their
execution times differ. To avoid triple-counting the same evidence, only the **KMP** counts
feed the scores; Brute Force and Boyer-Moore are kept for speed comparison.

### 3. Regular expressions

Python's `re` module scans the visual string for flexible patterns that exact matching cannot
express compactly: long runs (`V{3,}`), repetitions (`(VC){2,}`), and transitions (`V+C+`).
Implemented in `src/regex_analysis/regex_analyzer.py`.

### 4. Rule-based scoring

```
AI score   = (AI exact matches via KMP)   + (AI regex matches)
Real score = (real exact matches via KMP) + (real regex matches)
confidence = abs(AI score - Real score) / (AI score + Real score)
```

Decision (default confidence threshold 0.20):

- AI score > Real score and confidence >= 0.20 -> tends to be AI-generated
- Real score > AI score and confidence >= 0.20 -> tends to be a real image
- confidence < 0.20 or AI score == Real score -> inconclusive

Implemented in `src/analysis/scoring.py`; results are saved to CSV by
`src/results/csv_writer.py`.

## Supporting Algorithms (Experiments)

These scripts in `src/experiments/` are research/calibration tools (run once, not part of the
runtime program). They were used to derive and validate the settings in `config.py`.

- **`calibrate.py`** — measures the average block features per class (the evidence for the
  symbol design) and selects the best AI/real **symbol grouping**, validated with a
  train/test split.
- **`experiment_order.py`** — tests different rule orders in `encode_block` and reports the
  best one by balanced accuracy.
- **`experiment_threshold.py`** — sweeps each threshold value and reports its sensitivity and
  best value.
- **`experiment_pattern_mining.py`** — scans every length-2 and length-3 symbol sequence and
  ranks them by how much more often they appear in one class, suggesting data-driven patterns.
- **`evaluate.py`** — reads the batch CSV and prints the full evaluation report (confusion
  matrix, precision / recall / F1, balanced accuracy, inconclusive coverage, per-category
  accuracy, and average BF/KMP/BM execution time).

Key results on a 995-image dataset (250 AI, 745 real): balanced accuracy about **80%**, real
F1 about 0.89, AI F1 about 0.70, with roughly 13% of images returned as inconclusive. The
three string-matching algorithms run in nearly the same time because the strings are short
(64 symbols), which cancels the theoretical skipping advantage of KMP and Boyer-Moore.

## Requirements & Installation

Requirements:

- Python 3.8+
- `opencv-python`
- `numpy`
- `tkinter` (bundled with the standard CPython installer; needed only for the GUI)

Install:

```
pip install -r requirements.txt
```

## Dataset

The dataset can be obtained from Kaggle:

> AI vs Real Images Dataset — https://www.kaggle.com/datasets/rhythmghai/ai-vs-real-images-dataset/data

The image files are **not committed** to this repository (large and licensed). After
downloading, arrange them as:

```
dataset/
  Ai_generated_dataset/
    animals/  city/  food/  nature/  people/
  real_dataset/
    animals/  city/  food/  nature/  people/
```

The category subfolders are optional but enable the per-category evaluation. Supported
extensions: `jpg`, `jpeg`, `png`, `bmp`, `webp`.

## How to Run (Step by Step)

Run everything from the project root:

```
cd Paper-IF2211-String-Matching-AI-Real-Image
pip install -r requirements.txt
```

### Main program

1. Single image:

```
python src/main.py single --image dataset/Ai_generated_dataset/people/image.png --output output/single_result.csv
```

2. Compare two images:

```
python src/main.py compare --ai dataset/Ai_generated_dataset/animals/ai_1.jpg --real dataset/real_dataset/animals/real_1.jpg --output output/compare_result.csv
```

3. Batch (analyze whole folders, compute accuracy, save CSV):

```
python src/main.py batch --ai-dir dataset/Ai_generated_dataset --real-dir dataset/real_dataset --output output/batch_calibrated.csv
```

4. GUI (single and compare):

```
python src/gui_app.py
```

### Experiments

5. Calibration (feature evidence + symbol grouping):

```
python src/experiments/calibrate.py --ai-dir dataset/Ai_generated_dataset --real-dir dataset/real_dataset
```

6. Rule-order experiment:

```
python src/experiments/experiment_order.py --ai-dir dataset/Ai_generated_dataset --real-dir dataset/real_dataset
```

7. Threshold sensitivity experiment:

```
python src/experiments/experiment_threshold.py --ai-dir dataset/Ai_generated_dataset --real-dir dataset/real_dataset
```

8. Pattern mining:

```
python src/experiments/experiment_pattern_mining.py --ai-dir dataset/Ai_generated_dataset --real-dir dataset/real_dataset
```

9. Full evaluation report (reads the CSV produced by batch in step 3):

```
python src/experiments/evaluate.py --csv output/batch_calibrated.csv
```

Note: `evaluate.py` reads the batch CSV instead of re-processing images, so run step 3 first.

## Project Structure

```
src/
  main.py
  gui_app.py
  config.py
  imaging/image_to_string.py
  algorithms/string_matching.py
  regex_analysis/regex_analyzer.py
  analysis/scoring.py
  results/csv_writer.py
  gui/  (app.py, single_tab.py, compare_tab.py, preview.py)
  experiments/  (calibrate.py, experiment_order.py, experiment_threshold.py,
                 experiment_pattern_mining.py, evaluate.py)
dataset/
output/
requirements.txt
README.md
```

## Author

- **Name:** Matthew Sebastian Kurniawan
- **NIM:** 18223096