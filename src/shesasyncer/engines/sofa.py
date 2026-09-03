"""Optional SOFA singing-oriented forced-alignment adapter.

SOFA is kept behind a callable runtime boundary so the core package does not
need PyTorch, model weights, or SOFA-specific dependencies installed. A host
application can inject its configured SOFA runner and receive normalized
TimedSegment objects containing phoneme boundaries.
"""

from collections.abc import Callable, Sequence

from .adapters import TimedSegment


class SofaEngine:
    name = "sofa"

    def __init__(self, runner: Callable | None = None):
        self.runner = runner

    def available(self) -> bool:
        return callable(self.runner)

    def align(
        self,
        audio_path: str,
        lyrics: Sequence[str] | None = None,
        language: str | None = None,
    ) -> tuple[TimedSegment, ...]:
        if not self.available():
            return ()

        raw = self.runner(audio_path, list(lyrics or ()), language)
        result: list[TimedSegment] = []
        for segment in raw or ():
            if isinstance(segment, TimedSegment):
                result.append(segment)
                continue
            if not isinstance(segment, dict):
                continue
            try:
                start = float(segment["start"])
                end = float(segment["end"])
                text = str(segment.get("text", ""))
            except (KeyError, TypeError, ValueError):
                continue
            words = tuple(segment.get("words", ()) or ())
            result.append(
                TimedSegment(
                    start=start,
                    end=end,
                    text=text,
                    confidence=float(segment.get("confidence", 0.0) or 0.0),
                    words=words,
                )
            )
        return tuple(result)
