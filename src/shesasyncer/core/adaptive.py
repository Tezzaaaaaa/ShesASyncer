from dataclasses import dataclass
from typing import Callable, Sequence

from ..alignment.sequence import monotonic_match
from ..consensus.merge import Candidate, merge_candidates
from ..engines.adapters import TimedSegment, TimingEngine
from .models import AlignmentEvidence, AlignmentResult, LyricLine, Timing


@dataclass(frozen=True)
class EngineEvidence:
    engine: str
    segments: tuple[TimedSegment, ...]


class AdaptiveAligner:
    """Run only the timing engines needed and merge their evidence.

    Trusted lyrics remain canonical. Engines may disagree about recognition or
    timing; only their timing evidence is allowed into the consensus layer.
    """

    def __init__(self, engines: Sequence[TimingEngine] = ()):
        self.engines = tuple(engines)

    def collect(
        self,
        audio_path: str,
        lyrics: Sequence[str] | Sequence[LyricLine],
        *,
        language: str | None = None,
    ) -> tuple[EngineEvidence, ...]:
        lines = [x if isinstance(x, LyricLine) else LyricLine(i, x) for i, x in enumerate(lyrics)]
        collected: list[EngineEvidence] = []
        for engine in self.engines:
            if not engine.available():
                continue
            segments = tuple(engine.align(audio_path, [x.text for x in lines], language))
            if segments:
                collected.append(EngineEvidence(engine.name, segments))
        return tuple(collected)

    def run(
        self,
        audio_path: str,
        lyrics: Sequence[str] | Sequence[LyricLine],
        *,
        language: str | None = None,
        retry: Callable[[str, Sequence[int]], Sequence[EngineEvidence]] | None = None,
    ) -> AlignmentResult:
        lines = [x if isinstance(x, LyricLine) else LyricLine(i, x) for i, x in enumerate(lyrics)]
        evidence_runs = list(self.collect(audio_path, lines, language=language))
        evidence = self._match(lines, evidence_runs)

        unresolved = self._unresolved_lines(lines, evidence)
        if unresolved and retry:
            for run in retry(audio_path, unresolved):
                evidence_runs.append(run)
            evidence = self._match(lines, evidence_runs)
            unresolved = self._unresolved_lines(lines, evidence)

        output = []
        warnings = []
        by_line: dict[int, AlignmentEvidence] = {}
        for item in evidence:
            by_line.setdefault(item.line_index, item)

        for line in lines:
            item = by_line.get(line.index)
            if item is None:
                output.append({"index": line.index, "text": line.text, "start": None, "end": None, "confidence": 0.0, "source": None})
                warnings.append(f"No reliable timing evidence for lyric line {line.index}")
            else:
                output.append({
                    "index": line.index,
                    "text": line.text,
                    "start": item.timing.start,
                    "end": item.timing.end,
                    "confidence": item.timing.confidence,
                    "source": item.source,
                    "words": item.metadata.get("words", []),
                })

        if unresolved:
            warnings.append("Unresolved lines remain after evidence merge: " + ", ".join(map(str, unresolved)))

        return AlignmentResult(output, self._confidence(evidence), warnings, evidence)

    @staticmethod
    def _match(lines: Sequence[LyricLine], runs: Sequence[EngineEvidence]) -> list[AlignmentEvidence]:
        candidates: dict[int, list[Candidate]] = {line.index: [] for line in lines}
        metadata: dict[tuple[int, str], dict] = {}

        for run in runs:
            segments = [
                {"start": s.start, "end": s.end, "text": s.text, "confidence": s.confidence}
                for s in run.segments
            ]
            pairs = monotonic_match([line.text for line in lines], segments)
            for line_index, segment_index, similarity in pairs:
                segment = run.segments[segment_index]
                score = max(0.0, min(1.0, similarity * max(segment.confidence, 0.01)))
                candidates[line_index].append(Candidate(segment.start, segment.end, score, run.engine))
                metadata[(line_index, run.engine)] = {
                    "words": list(segment.words),
                    "similarity": similarity,
                    "engine_confidence": segment.confidence,
                }

        output: list[AlignmentEvidence] = []
        for line in lines:
            merged = merge_candidates(candidates[line.index])
            if merged is None:
                continue
            sources = [c.source for c in candidates[line.index] if abs(c.start - merged.start) <= 0.45 and abs(c.end - merged.end) <= 0.45]
            source = merged.source if len(sources) > 1 else sources[0]
            source_meta = metadata.get((line.index, source), {})
            output.append(AlignmentEvidence(
                line_index=line.index,
                timing=Timing(merged.start, merged.end, merged.confidence, "consensus" if len(sources) > 1 else "asr"),
                matched_text=line.text,
                score=merged.confidence,
                source=source,  # type: ignore[arg-type]
                metadata={"sources": sources, **source_meta},
            ))
        return output

    @staticmethod
    def _unresolved_lines(lines: Sequence[LyricLine], evidence: Sequence[AlignmentEvidence]) -> list[int]:
        matched = {e.line_index for e in evidence}
        return [line.index for line in lines if line.index not in matched]

    @staticmethod
    def _confidence(evidence: Sequence[AlignmentEvidence]) -> float:
        if not evidence:
            return 0.0
        return sum(e.timing.confidence for e in evidence) / len(evidence)
