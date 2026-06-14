import time
from typing import Dict, List, Tuple

def brute_force_search(text: str, pattern: str) -> Tuple[List[int], int, float]:
    start = time.perf_counter()
    positions: List[int] = []
    n = len(text)
    m = len(pattern)
    if m == 0 or m > n:
        return positions, 0, time.perf_counter() - start
    for i in range(n - m + 1):
        j = 0
        while j < m and text[i + j] == pattern[j]:
            j += 1
        if j == m:
            positions.append(i)
    elapsed = time.perf_counter() - start
    return positions, len(positions), elapsed

def build_lps(pattern: str) -> List[int]:
    m = len(pattern)
    lps = [0] * m
    length = 0
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length != 0:
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1
    return lps

def kmp_search(text: str, pattern: str) -> Tuple[List[int], int, float]:
    start = time.perf_counter()
    positions: List[int] = []
    n = len(text)
    m = len(pattern)
    if m == 0 or m > n:
        return positions, 0, time.perf_counter() - start
    lps = build_lps(pattern)
    i = 0
    j = 0
    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
            if j == m:
                positions.append(i - j)
                j = lps[j - 1]
        elif j != 0:
            j = lps[j - 1]
        else:
            i += 1
    elapsed = time.perf_counter() - start
    return positions, len(positions), elapsed

def build_bad_character_table(pattern: str) -> Dict[str, int]:
    table: Dict[str, int] = {}
    for index in range(len(pattern)):
        table[pattern[index]] = index
    return table

def boyer_moore_search(text: str, pattern: str) -> Tuple[List[int], int, float]:
    start = time.perf_counter()
    positions: List[int] = []
    n = len(text)
    m = len(pattern)
    if m == 0 or m > n:
        return positions, 0, time.perf_counter() - start
    bad_character = build_bad_character_table(pattern)
    s = 0
    while s <= n - m:
        j = m - 1
        while j >= 0 and pattern[j] == text[s + j]:
            j -= 1
        if j < 0:
            positions.append(s)
            s += 1
        else:
            last_occurrence = bad_character.get(text[s + j], -1)
            shift = j - last_occurrence
            if shift < 1:
                shift = 1
            s += shift
    elapsed = time.perf_counter() - start
    return positions, len(positions), elapsed

def analyze_patterns_with_all_algorithms(text: str, patterns: List[str]) -> Dict:
    per_pattern: Dict[str, Dict] = {}
    bf_total_count = 0
    kmp_total_count = 0
    bm_total_count = 0
    bf_total_time = 0.0
    kmp_total_time = 0.0
    bm_total_time = 0.0

    for pattern in patterns:
        bf_positions, bf_count, bf_time = brute_force_search(text, pattern)
        kmp_positions, kmp_count, kmp_time = kmp_search(text, pattern)
        bm_positions, bm_count, bm_time = boyer_moore_search(text, pattern)

        per_pattern[pattern] = {
            "pattern": pattern,
            "bf_count": bf_count,
            "kmp_count": kmp_count,
            "bm_count": bm_count,
            "bf_positions": bf_positions,
            "kmp_positions": kmp_positions,
            "bm_positions": bm_positions,
            "bf_time": bf_time,
            "kmp_time": kmp_time,
            "bm_time": bm_time,
        }

        bf_total_count += bf_count
        kmp_total_count += kmp_count
        bm_total_count += bm_count
        bf_total_time += bf_time
        kmp_total_time += kmp_time
        bm_total_time += bm_time

    return {
        "per_pattern": per_pattern,
        "bf_total_count": bf_total_count,
        "kmp_total_count": kmp_total_count,
        "bm_total_count": bm_total_count,
        "bf_total_time": bf_total_time,
        "kmp_total_time": kmp_total_time,
        "bm_total_time": bm_total_time,
    }