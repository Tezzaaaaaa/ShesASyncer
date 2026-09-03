from dataclasses import dataclass
from typing import Callable, Sequence

from ..alignment.refinement import refine_evidence
from ..alignment.sequence import monotonic_match
from ..consensus.merge import Candidate, merge_candidates
from ..engines.adapters import TimedSegment, TimingEngine
from ..validation.timeline import validate_timeline
from .models import AlignmentEvidence, AlignmentResult, LyricLine, Timing


@dataclass(frozen=True)
class EngineEvidence:
    engine: str
    segments: tuple[TimedSegment, ...]


class AdaptiveAligner:
    """Run timing engines adaptively and arbitrate their evidence safely."""

    def __init__(self, engines: Sequence[TimingEngine] = ()):
        self.engines = tuple(engines)

    def collect(self, audio_path: str, lyrics: Sequence[str] | Sequence[LyricLine], *, language: str | None = None) -> tuple[EngineEvidence, ...]:
        lines = [x if isinstance(x, LyricLine) else LyricLine(i, x) for i, x in enumerate(lyrics)]
        collected: list[EngineEvidence] = []
        for engine in self.engines:
            if not engine.available():
                continue
            try:
                segments = tuple(engine.align(audio_path, [x.text for x in lines], language))
            except Exception:
                continue
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
            evidence_runs.extend(self._targeted_retry(audio_path, unresolved, retry))
            evidence = self._match(lines, evidence_runs)
            unresolved = self._unresolved_lines(lines, evidence)

        validation = validate_timeline(evidence)
        invalid_lines = {issue.line_index for issue in validation.issues if issue.severity == "error"}
        if invalid_lines and retry:
            evidence_runs.extend(self._targeted_retry(audio_path, sorted(invalid_lines), retry))
            evidence = self._match(lines, evidence_runs)
            validation = validate_timeline(evidence)

        invalid_lines = {issue.line_index for issue in validation.issues if issue.severity == "error"}
        evidence = [item for item in evidence if item.line_index not in invalid_lines]
        evidence = refine_evidence(evidence)
        unresolved = self._unresolved_lines(lines, evidence)

        warnings = [f"Timeline {issue.severity}: line {issue.line_index}: {issue.message}" for issue in validation.issues]
        by_line = {item.line_index: item for item in evidence}
        output = []
        for line in lines:
            item = by_line.get(line.index)
            if item is None:
                output.append({"index": line.index, "text": line.text, "start": None, "end": None, "confidence": 0.0, "source": None, "words": [], "characters": [], "phonemes": []})
                if line.index not in invalid_lines:
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
                    "characters": item.metadata.get("characters", []),
                    "phonemes": item.metadata.get("phonemes", []),
                })
        if unresolved:
            warnings.append("Unresolved lines remain after validation: " + ", ".join(map(str, unresolved)))
        return AlignmentResult(output, self._confidence(evidence), warnings, evidence)

    @staticmethod
    def _targeted_retry(
        audio_path: str,
        line_indices: Sequence[int],
        retry: Callable[[str, Sequence[int]], Sequence[EngineEvidence]],
    ) -> list[EngineEvidence]:
        collected: list[EngineEvidence] = []
        for line_index in line_indices:
            try:
                runs = retry(audio_path, [line_index])
            except Exception:
                continue
            if runs:
                collected.extend(runs)
        return collected

    @staticmethod
    def _match(lines: Sequence[LyricLine], runs: Sequence[EngineEvidence]) -> list[AlignmentEvidence]:
        candidates: dict[int, list[Candidate]] = {line.index: [] for line in lines}
        metadata: dict[tuple[int, str], dict] = {}
        for run in runs:
            segments = [{"start": s.start, "end": s.end, "text": s.text, "confidence": s.confidence} for s in run.segments]
            for line_index, segment_index, similarity in monotonic_match([line.text for line in lines], segments):
                segment = run.segments[segment_index]
                score = max(0.0, min(1.0, similarity * max(segment.confidence, 0.01)))
                candidates[line_index].append(Candidate(segment.start, segment.end, score, run.engine))
                metadata[(line_index, run.engine)] = {
                    "words": list(segment.words),
                    "phonemes": list(segment.phonemes),
                    "similarity": similarity,
                    "engine_confidence": segment.confidence,
                }

        output: list[AlignmentEvidence] = []
        for line in lines:
            merged = merge_candidates(candidates[line.index])
            if merged is None:
                continue
            agreeing = [c for c in candidates[line.index] if abs(c.start - merged.start) <= 0.45 and abs(c.end - merged.end) <= 0.45]
            sources = [c.source for c in agreeing]
            if not sources:
                continue
            source = merged.source if len(sources) > 1 else sources[0]
            merged_metadata = {"sources": sources, "agreement": len(sources) > 1}
            for engine_name in sources:
                source_metadata = metadata.get((line.index, engine_name), {})
                for key in ("words", "phonemes"):
                    if source_metadata.get(key):
                        merged_metadata[key] = source_metadata[key]
                        break
                if "similarity" not in merged_metadata and source_metadata.get("similarity") is not None:
                    merged_metadata["similarity"] = source_metadata["similarity"]
                if "engine_confidence" not in merged_metadata and source_metadata.get("engine_confidence") is not None:
                    merged_metadata["engine_confidence"] = source_metadata["engine_confidence"]
            output.append(AlignmentEvidence(
                line_index=line.index,
                timing=Timing(merged.start, merged.end, merged.confidence, "consensus" if len(sources) > 1 else source),
                matched_text=line.text,
                score=merged.confidence,
                source=source,
                metadata=merged_metadata,
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
