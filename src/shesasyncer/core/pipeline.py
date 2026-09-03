from ..alignment.anchor import anchor_lines
from ..alignment.sequence import monotonic_match
from ..consensus.confidence import confidence, conflicts
from ..core.adaptive import AdaptiveAligner
from ..core.models import AlignmentEvidence, AlignmentResult, LyricLine, Timing
from ..engines.adapters import TimingEngine


class AlignmentPipeline:
    """Public pipeline with a lightweight path and an adaptive audio path."""

    def __init__(self, engines: tuple[TimingEngine, ...] = ()):
        self.engines = engines

    def run(self, lyrics: list[str] | list[LyricLine], timed_segments: list[dict]) -> AlignmentResult:
        lines = [x if isinstance(x, LyricLine) else LyricLine(i, x) for i, x in enumerate(lyrics)]
        evidence = anchor_lines(lines, timed_segments, min_score=0.45)

        matched = {e.line_index for e in evidence}
        if len(matched) < len(lines) and timed_segments:
            pairs = monotonic_match([x.text for x in lines], timed_segments)
            existing = {e.line_index for e in evidence}
            for li, si, score in pairs:
                if li in existing or score < 0.35:
                    continue
                seg = timed_segments[si]
                evidence.append(AlignmentEvidence(
                    line_index=li,
                    timing=Timing(float(seg["start"]), float(seg["end"]), score, "asr"),
                    matched_text=str(seg.get("text", "")),
                    score=score,
                    source="asr",
                    metadata={"matcher": "monotonic_sequence"},
                ))

        evidence.sort(key=lambda e: e.line_index)
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

    def run_audio(
        self,
        audio_path: str,
        lyrics: list[str] | list[LyricLine],
        *,
        language: str | None = None,
    ) -> AlignmentResult:
        """Align trusted lyrics to an audio file using configured engines."""
        return AdaptiveAligner(self.engines).run(audio_path, lyrics, language=language)
