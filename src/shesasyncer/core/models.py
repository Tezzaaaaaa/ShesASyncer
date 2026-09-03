from dataclasses import dataclass, field
from typing import Literal

EvidenceKind = Literal["asr", "phoneme", "vocal", "consensus"]

@dataclass(frozen=True)
class LyricLine:
    index: int
    text: str

@dataclass(frozen=True)
class Timing:
    start: float
    end: float
    confidence: float = 0.0
    source: EvidenceKind = "consensus"

@dataclass
class AlignmentEvidence:
    line_index: int
    timing: Timing
    matched_text: str = ""
    score: float = 0.0
    source: EvidenceKind = "asr"
    metadata: dict = field(default_factory=dict)

@dataclass
class AlignmentResult:
    lines: list[dict]
    confidence: float
    warnings: list[str] = field(default_factory=list)
    evidence: list[AlignmentEvidence] = field(default_factory=list)
