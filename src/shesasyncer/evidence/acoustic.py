from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class AcousticFrame:
    """A single acoustic frame with scores for candidate phonemes.

    Scores are expected to be log-likelihood-like values. The aligner does not
    prescribe how they were produced, so a host may supply a neural encoder,
    CTC model, or another acoustic front end.
    """
    time: float
    scores: dict[str, float]


def viterbi_phoneme_alignment(
    phonemes: Sequence[str],
    frames: Sequence[AcousticFrame],
    *,
    stay_bonus: float = 0.15,
    skip_penalty: float = 2.0,
) -> tuple[dict, ...]:
    """Monotonically align a trusted phoneme sequence to acoustic frames.

    This is deliberately model-agnostic: the acoustic scorer is replaceable,
    while the temporal decoder remains owned by ShesASyncer.
    """
    tokens = [str(p).strip() for p in phonemes if str(p).strip()]
    if not tokens or not frames:
        return ()

    n, m = len(tokens), len(frames)
    neg_inf = float("-inf")
    dp = [[neg_inf] * n for _ in range(m)]
    back = [[-1] * n for _ in range(m)]

    for j in range(min(n, m)):
        dp[0][j] = frames[0].scores.get(tokens[j], -skip_penalty * j)

    for i in range(1, m):
        for j in range(n):
            emit = frames[i].scores.get(tokens[j], -skip_penalty)
            best = dp[i - 1][j] + stay_bonus
            prev = j
            if j > 0 and dp[i - 1][j - 1] > best:
                best = dp[i - 1][j - 1]
                prev = j - 1
            dp[i][j] = best + emit
            back[i][j] = prev

    if dp[-1][n - 1] == neg_inf:
        return ()

    states = [n - 1]
    for i in range(m - 1, 0, -1):
        states.append(back[i][states[-1]])
    states.reverse()

    if len(frames) > 1:
        deltas = [max(0.0, frames[i + 1].time - frames[i].time) for i in range(len(frames) - 1)]
        hop = sorted(deltas)[len(deltas) // 2] or 0.01
    else:
        hop = 0.01

    spans = []
    start = 0
    current = states[0]
    for i in range(1, m + 1):
        if i == m or states[i] != current:
            end = i
            frame_scores = [frames[k].scores.get(tokens[current], -skip_penalty) for k in range(start, end)]
            mean_score = sum(frame_scores) / len(frame_scores)
            confidence = 1.0 / (1.0 + math.exp(-mean_score))
            spans.append({
                "token_index": current,
                "phoneme": tokens[current],
                "start": frames[start].time,
                "end": frames[end - 1].time + hop,
                "confidence": max(0.0, min(1.0, confidence)),
            })
            if i < m:
                start = i
                current = states[i]

    return tuple(spans)
