"""Optional WhisperX adapter.

WhisperX is used only as timing evidence. ShesASyncer never accepts its
transcription as the canonical lyric text.
"""

from .adapters import TimedSegment


class WhisperXEngine:
    name = "whisperx"

    def available(self) -> bool:
        try:
            import whisperx  # type: ignore
            return True
        except ImportError:
            return False

    def align(self, audio_path: str, language: str | None = None):
        if not self.available():
            return ()
        raise NotImplementedError("WhisperX runtime adapter is intentionally isolated; configure model/device before inference")
