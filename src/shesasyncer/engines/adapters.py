from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class TimedSegment:
    start: float
    end: float
    text: str
    confidence: float = 0.0
    words: tuple[dict, ...] = ()
    phonemes: tuple[dict, ...] = ()


class TimingEngine(Protocol):
    name: str

    def available(self) -> bool: ...

    def align(
        self,
        audio_path: str,
        lyrics: Sequence[str] | None = None,
        language: str | None = None,
    ) -> Sequence[TimedSegment]: ...


class NullEngine:
    """Safe adapter used when an optional heavy engine is not installed."""

    name = "none"

    def available(self) -> bool:
        return False

    def align(
        self,
        audio_path: str,
        lyrics: Sequence[str] | None = None,
        language: str | None = None,
    ) -> Sequence[TimedSegment]:
        return ()
