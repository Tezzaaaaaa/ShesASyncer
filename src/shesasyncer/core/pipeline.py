from ..alignment.anchor import anchor_lines
from ..consensus.confidence import confidence, conflicts
from .models import AlignmentResult, LyricLine


class AlignmentPipeline:
    """Small orchestration layer; heavyweight engines plug in later."""

    def run(self, lyrics: list[str] | list[LyricLine], timed_segments: list[dict]) -> AlignmentResult:
        lines = [x if isinstance(x, LyricLine) else LyricLine(i, x) for i, x in enumerate(lyrics)]
        evidence = anchor_lines(lines, timed_segments)
        conflict_lines = conflicts(evidence)
        by_index = {e.line_index: e for e in evidence}
        output = []
        warnings = []
        for line in lines:
            item = by_index.get(line.index)
            if item:
                output.append({"index": line.index, "text": line.text, "start": item.timing.start, "end": item.timing.end, "confidence": item.timing.confidence, "source": item.source})
            else:
                output.append({"index": line.index, "text": line.text, "start": None, "end": None, "confidence": 0.0, "source": None})
                warnings.append(f"No reliable timing evidence for lyric line {line.index}")
        if conflict_lines:
            warnings.append("Conflicting alignment evidence requires targeted refinement: " + ", ".join(map(str, conflict_lines)))
        return AlignmentResult(output, confidence(evidence), warnings, evidence)
