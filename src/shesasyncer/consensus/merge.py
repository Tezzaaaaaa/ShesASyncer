from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    start: float
    end: float
    confidence: float
    source: str


def merge_candidates(candidates: list[Candidate], *, tolerance: float = 0.45) -> Candidate | None:
    """Return a timing only when evidence forms a compatible cluster.

    A single engine can establish a provisional timing, but contradictory
    engines cannot cancel each other out or be averaged into a fake answer.
    """
    if not candidates:
        return None
    ranked = sorted(candidates, key=lambda c: c.confidence, reverse=True)
    best = ranked[0]
    agreeing = [c for c in ranked if abs(c.start - best.start) <= tolerance and abs(c.end - best.end) <= tolerance]
    if len(agreeing) == 1 and len(ranked) > 1:
        return None
    weight = sum(max(c.confidence, 0.01) for c in agreeing)
    start = sum(c.start * max(c.confidence, 0.01) for c in agreeing) / weight
    end = sum(c.end * max(c.confidence, 0.01) for c in agreeing) / weight
    confidence = min(1.0, sum(c.confidence for c in agreeing) / len(agreeing) + 0.05 * (len(agreeing) - 1))
    return Candidate(start, end, confidence, "consensus" if len(agreeing) > 1 else best.source)
