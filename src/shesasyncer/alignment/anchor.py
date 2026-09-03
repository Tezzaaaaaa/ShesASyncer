from difflib import SequenceMatcher
from ..core.models import AlignmentEvidence, LyricLine, Timing
from ..lyrics.normalize import normalize_lyric


def anchor_lines(lyrics: list[LyricLine], segments: list[dict], min_score: float = 0.45) -> list[AlignmentEvidence]:
    """Map trusted lyric lines onto externally supplied timed ASR segments.

    The segment text is only timing evidence; the returned match never replaces
    the trusted lyric text.
    """
    evidence = []
    cursor = 0
    for line in lyrics:
        target = normalize_lyric(line.text)
        best = None
        best_score = 0.0
        for i in range(cursor, len(segments)):
            seg = segments[i]
            candidate = normalize_lyric(str(seg.get("text", "")))
            if not candidate:
                continue
            score = SequenceMatcher(None, target, candidate).ratio()
            if score > best_score:
                best_score, best = score, (i, seg)
            if score >= 0.90:
                break
        if best and best_score >= min_score:
            i, seg = best
            start, end = float(seg["start"]), float(seg["end"])
            evidence.append(AlignmentEvidence(
                line_index=line.index,
                timing=Timing(start, end, min(1.0, best_score), "asr"),
                matched_text=str(seg.get("text", "")),
                score=best_score,
                source="asr",
            ))
            cursor = i + 1
    return evidence
