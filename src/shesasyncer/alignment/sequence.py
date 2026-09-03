from difflib import SequenceMatcher

from ..lyrics.normalize import normalize_lyric


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_lyric(a), normalize_lyric(b)).ratio()


def monotonic_match(lyrics: list[str], segments: list[dict], *, skip_penalty: float = 0.18) -> list[tuple[int, int, float]]:
    """Globally align lyric lines to timed segments while preserving order.

    Unlike greedy matching, repeated choruses and locally similar lines can be
    resolved using surrounding context. The result contains only matched pairs.
    """
    n, m = len(lyrics), len(segments)
    if not n or not m:
        return []
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    move = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = similarity(lyrics[i - 1], str(segments[j - 1].get("text", "")))
            diag = dp[i - 1][j - 1] + s
            up = dp[i - 1][j] - skip_penalty
            left = dp[i][j - 1] - skip_penalty
            best = max((diag, "diag"), (up, "up"), (left, "left"))
            dp[i][j], move[i][j] = best
    out = []
    i, j = n, m
    while i and j:
        if move[i][j] == "diag":
            s = similarity(lyrics[i - 1], str(segments[j - 1].get("text", "")))
            if s > 0:
                out.append((i - 1, j - 1, s))
            i -= 1; j -= 1
        elif move[i][j] == "up":
            i -= 1
        else:
            j -= 1
    return list(reversed(out))
