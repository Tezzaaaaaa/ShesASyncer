from __future__ import annotations

from difflib import SequenceMatcher
import re

from ..core.models import AlignmentEvidence

_TOKEN_RE = re.compile(r"\S+")


def refine_evidence(evidence: list[AlignmentEvidence]) -> list[AlignmentEvidence]:
    """Add word/character timing without changing accepted line boundaries.

    Word timings supplied by an alignment engine are treated as evidence. The
    lyric text remains canonical; character spans are derived only inside the
    matched word intervals. Lines without usable word evidence are left alone.
    """
    refined: list[AlignmentEvidence] = []
    for item in evidence:
        words = _clean_words(item.metadata.get("words", []))
        if not words:
            refined.append(item)
            continue

        mapped = _map_words(item.matched_text, words)
        if not mapped:
            refined.append(item)
            continue

        char_timings = _character_timings(item.matched_text, mapped)
        metadata = dict(item.metadata)
        metadata["words"] = mapped
        metadata["characters"] = char_timings
        metadata["refinement"] = "word-to-character"
        refined.append(
            AlignmentEvidence(
                line_index=item.line_index,
                timing=item.timing,
                matched_text=item.matched_text,
                score=item.score,
                source=item.source,
                metadata=metadata,
            )
        )
    return refined


def _clean_words(words: object) -> list[dict]:
    if not isinstance(words, (list, tuple)):
        return []
    result = []
    for word in words:
        if not isinstance(word, dict):
            continue
        try:
            start = float(word["start"])
            end = float(word["end"])
            text = str(word.get("word", word.get("text", ""))).strip()
        except (KeyError, TypeError, ValueError):
            continue
        if text and end > start >= 0:
            result.append({"text": text, "start": start, "end": end, "confidence": float(word.get("confidence", 0.0) or 0.0)})
    return result


def _map_words(lyric: str, words: list[dict]) -> list[dict]:
    lyric_tokens = [(m.start(), m.end(), m.group()) for m in _TOKEN_RE.finditer(lyric)]
    if not lyric_tokens:
        return []
    engine_text = [w["text"] for w in words]
    lyric_text = [x[2] for x in lyric_tokens]
    matcher = SequenceMatcher(None, [x.casefold() for x in lyric_text], [x.casefold() for x in engine_text])
    mapped = []
    for match in matcher.get_matching_blocks():
        a0, b0, size = match.a, match.b, match.size
        for offset in range(size):
            lyric_start, lyric_end, text = lyric_tokens[a0 + offset]
            word = words[b0 + offset]
            mapped.append({
                "text": text,
                "start": word["start"],
                "end": word["end"],
                "confidence": word["confidence"],
                "lyric_start": lyric_start,
                "lyric_end": lyric_end,
            })
    return mapped


def _character_timings(lyric: str, words: list[dict]) -> list[dict]:
    result = []
    for word in words:
        chars = [c for c in lyric[word["lyric_start"] : word["lyric_end"]] if not c.isspace()]
        if not chars:
            continue
        duration = word["end"] - word["start"]
        step = duration / len(chars)
        for index, char in enumerate(chars):
            start = word["start"] + step * index
            end = word["end"] if index == len(chars) - 1 else word["start"] + step * (index + 1)
            result.append({
                "char": char,
                "start": start,
                "end": end,
                "confidence": word["confidence"],
            })
    return result
