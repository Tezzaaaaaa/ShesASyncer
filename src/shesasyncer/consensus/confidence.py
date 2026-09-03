from statistics import mean
from ..core.models import AlignmentEvidence


def confidence(evidence: list[AlignmentEvidence]) -> float:
    if not evidence:
        return 0.0
    return round(mean(max(0.0, min(1.0, e.timing.confidence)) for e in evidence), 4)


def conflicts(evidence: list[AlignmentEvidence], tolerance: float = 0.75) -> list[int]:
    """Return line indexes where independent evidence sources disagree."""
    by_line: dict[int, list[AlignmentEvidence]] = {}
    for item in evidence:
        by_line.setdefault(item.line_index, []).append(item)
    result = []
    for index, items in by_line.items():
        starts = [x.timing.start for x in items]
        ends = [x.timing.end for x in items]
        if len(items) > 1 and (max(starts) - min(starts) > tolerance or max(ends) - min(ends) > tolerance):
            result.append(index)
    return result
