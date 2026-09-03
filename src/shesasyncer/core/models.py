from dataclasses import dataclass, field


@dataclass(frozen=True)
class LyricLine:
    index: int
    text: str


@dataclass(frozen=True)
class Timing:
    start: float
    end: float
    confidence: float = 0.0
    source: str = "consensus"


@dataclass
class AlignmentEvidence:
    line_index: int
    timing: Timing
    matched_text: str = ""
    score: float = 0.0
    source: str = "asr"
    metadata: dict = field(default_factory=dict)


@dataclass
class AlignmentResult:
    lines: list[dict]
    confidence: float
    warnings: list[str] = field(default_factory=list)
    evidence: list[AlignmentEvidence] = field(default_factory=list)
