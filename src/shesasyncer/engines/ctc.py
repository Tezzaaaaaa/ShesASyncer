"""CTC-based singing alignment engine.

This is the model-facing layer for a Wav2Vec2/CTC-style acoustic model. The
acoustic model is injected, while ShesASyncer owns G2P, CTC decoding, and the
reconstruction of trusted lyric lines.
"""

from collections.abc import Callable, Sequence

from ..evidence.acoustic import AcousticFrame
from ..evidence.ctc import ctc_viterbi_alignment
from ..lyrics.g2p import G2PEngine
from .adapters import TimedSegment


class CtcSingingEngine:
    name = "shesasyncer-ctc"

    def __init__(
        self,
        g2p: G2PEngine,
        acoustic_runner: Callable[[str, Sequence[str], str | None], Sequence[AcousticFrame]] | None = None,
        *,
        blank_token: str = "<blank>",
    ):
        self.g2p = g2p
        self.acoustic_runner = acoustic_runner
        self.blank_token = blank_token

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
        spans = ctc_viterbi_alignment(flat, frames, blank_token=self.blank_token)
        if not spans:
            return ()

        by_index = {span["token_index"]: span for span in spans}
        result: list[TimedSegment] = []
        offset = 0
        for line, phonemes in zip(lines, line_phonemes):
            indices = range(offset, offset + len(phonemes))
            line_spans = [by_index[index] for index in indices if index in by_index]
            offset += len(phonemes)
            if not line_spans:
                continue

            result.append(
                TimedSegment(
                    start=float(line_spans[0]["start"]),
                    end=float(line_spans[-1]["end"]),
                    text=line,
                    confidence=sum(float(x["confidence"]) for x in line_spans) / len(line_spans),
                    phonemes=tuple({k: v for k, v in span.items() if k != "token_index"} for span in line_spans),
                )
            )
        return tuple(result)
