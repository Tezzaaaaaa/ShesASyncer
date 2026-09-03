"""ShesASyncer's native, model-agnostic singing alignment engine.

Unlike a SOFA wrapper, this engine owns the decoding contract. A host supplies
an acoustic scorer; ShesASyncer performs G2P, monotonic phoneme decoding, and
reconstruction of line evidence.
"""

from collections.abc import Callable, Sequence

from ..evidence.acoustic import AcousticFrame, viterbi_phoneme_alignment
from ..lyrics.g2p import G2PEngine
from .adapters import TimedSegment


class NativeSingingEngine:
    name = "shesasyncer-native"

    def __init__(
        self,
        g2p: G2PEngine,
        acoustic_runner: Callable[[str, Sequence[str], str | None], Sequence[AcousticFrame]] | None = None,
    ):
        self.g2p = g2p
        self.acoustic_runner = acoustic_runner

    def available(self) -> bool:
        return self.g2p.available() and callable(self.acoustic_runner)

    def align(
        self,
        audio_path: str,
        lyrics: Sequence[str] | None = None,
        language: str | None = None,
    ) -> tuple[TimedSegment, ...]:
        if not self.available():
            return ()

        lines = list(lyrics or ())
        line_phonemes = [self.g2p.convert(line, language) for line in lines]
        flat = [phoneme for line in line_phonemes for phoneme in line]
        if not flat:
            return ()

        frames = tuple(self.acoustic_runner(audio_path, flat, language))
        spans = viterbi_phoneme_alignment(flat, frames)
        if not spans:
            return ()

        result: list[TimedSegment] = []
        offset = 0
        for line, phonemes in zip(lines, line_phonemes):
            indices = set(range(offset, offset + len(phonemes)))
            line_spans = [span for span in spans if span["token_index"] in indices]
            offset += len(phonemes)
            if not line_spans:
                continue
            result.append(TimedSegment(
                start=float(line_spans[0]["start"]),
                end=float(line_spans[-1]["end"]),
                text=line,
                confidence=sum(float(x["confidence"]) for x in line_spans) / len(line_spans),
                phonemes=tuple({k: v for k, v in span.items() if k != "token_index"} for span in line_spans),
            ))
        return tuple(result)
