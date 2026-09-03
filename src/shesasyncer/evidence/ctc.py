from typing import Sequence
import math

from .acoustic import AcousticFrame


def ctc_viterbi_alignment(
    phonemes: Sequence[str],
    frames: Sequence[AcousticFrame],
    *,
    blank_token: str = "<blank>",
) -> tuple[dict, ...]:
    """Find the highest-scoring CTC path for trusted phonemes.

    The decoder uses the CTC blank explicitly, so silence can remain
    unassigned and repeated phonemes require the blank separation mandated by
    CTC. Scores are expected to be log-probabilities or another additive score.
    """
    tokens = [str(p).strip() for p in phonemes if str(p).strip()]
    if not tokens or not frames:
        return ()

    labels = [blank_token]
    for token in tokens:
        labels.extend((token, blank_token))

    n_states = len(labels)
    n_frames = len(frames)
    neg_inf = float("-inf")
    dp = [[neg_inf] * n_states for _ in range(n_frames)]
    back = [[-1] * n_states for _ in range(n_frames)]

    dp[0][0] = float(frames[0].scores.get(blank_token, neg_inf))
    if n_states > 1:
        dp[0][1] = float(frames[0].scores.get(tokens[0], neg_inf))

    for t in range(1, n_frames):
        scores = frames[t].scores
        for state, label in enumerate(labels):
            emit = float(scores.get(label, neg_inf))
            if emit == neg_inf:
                continue

            best_score = dp[t - 1][state]
            best_prev = state

            if state > 0 and dp[t - 1][state - 1] > best_score:
                best_score = dp[t - 1][state - 1]
                best_prev = state - 1

            if (
                state > 1
                and label != blank_token
                and label != labels[state - 2]
                and dp[t - 1][state - 2] > best_score
            ):
                best_score = dp[t - 1][state - 2]
                best_prev = state - 2

            if best_score != neg_inf:
                dp[t][state] = best_score + emit
                back[t][state] = best_prev

    final_candidates = [n_states - 1]
    if n_states > 1:
        final_candidates.append(n_states - 2)
    final_state = max(final_candidates, key=lambda state: dp[-1][state])
    if dp[-1][final_state] == neg_inf:
        return ()

    states = [final_state]
    for t in range(n_frames - 1, 0, -1):
        previous = back[t][states[-1]]
        if previous < 0:
            return ()
        states.append(previous)
    states.reverse()

    if len(frames) > 1:
        deltas = [max(0.0, frames[i + 1].time - frames[i].time) for i in range(n_frames - 1)]
        hop = sorted(deltas)[len(deltas) // 2] or 0.01
    else:
        hop = 0.01

    spans = []
    start = None
    current_state = None
    for i, state in enumerate(states + [-1]):
        label = labels[current_state] if current_state is not None else None
        if state != current_state:
            if current_state is not None and label != blank_token and start is not None:
                frame_scores = [
                    float(frames[k].scores.get(label, neg_inf))
                    for k in range(start, i)
                ]
                finite_scores = [score for score in frame_scores if score != neg_inf]
                if finite_scores:
                    mean_score = sum(finite_scores) / len(finite_scores)
                    confidence = math.exp(mean_score) if mean_score <= 0 else 1.0 - math.exp(-mean_score)
                    end_time = frames[i].time if i < n_frames else frames[-1].time + hop
                    spans.append({
                        "token_index": current_state // 2,
                        "phoneme": label,
                        "start": frames[start].time,
                        "end": end_time,
                        "confidence": max(0.0, min(1.0, confidence)),
                    })
            start = i if state >= 0 else None
            current_state = state if state >= 0 else None

    return tuple(spans)
