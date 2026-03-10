from __future__ import annotations


DEFAULT_THRESHOLD = 5  # para MVP demo


def compute_score(*, likes: int, comments: int, shares: int, clicks: int) -> int:
    return int(likes + 2 * comments + 3 * shares + 2 * clicks)


def compute_fitness(*, likes: int, comments: int, shares: int, clicks: int, threshold: int = DEFAULT_THRESHOLD) -> float:
    score = compute_score(likes=likes, comments=comments, shares=shares, clicks=clicks)
    return float(score - threshold)