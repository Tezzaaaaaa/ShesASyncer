"""Optional WhisperX timing-evidence adapter.

WhisperX supplies ASR plus forced-alignment timestamps. Its transcription is
never treated as canonical lyrics; ShesASyncer matches it back to trusted
lyrics before producing the final timeline.
"""

from .adapters import TimedSegment


class WhisperXEngine:
    name = "whisperx"

    def __init__(self, model: str = "small", device: str = "cpu", compute_type: str = "int8"):
        self.model_name = model
        self.device = device
        self.compute_type = compute_type
        self._whisperx = None
        self._model = None
        self._align_models: dict[str, tuple[object, object]] = {}

    def available(self) -> bool:
        try:
            import whisperx  # type: ignore
            self._whisperx = whisperx
            return True
        except ImportError:
            return False

    def _load_model(self):
        if self._model is None:
            if self._whisperx is None and not self.available():
                return None
            self._model = self._whisperx.load_model(
                self.model_name,
                self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def _alignment_model(self, language: str):
        if language not in self._align_models:
            model_a, metadata = self._whisperx.load_align_model(
                language_code=language,
                device=self.device,
            )
            self._align_models[language] = (model_a, metadata)
        return self._align_models[language]

    @staticmethod
    def _confidence(segment: dict) -> float:
        words = segment.get("words") or ()
        values = [
            float(w["score"])
            for w in words
            if isinstance(w, dict) and w.get("score") is not None
        ]
        if values:
            return max(0.0, min(1.0, sum(values) / len(values)))
        return max(0.0, min(1.0, float(segment.get("score", 0.0) or 0.0)))

    def align(
        self,
        audio_path: str,
        lyrics=None,
        language: str | None = None,
    ) -> tuple[TimedSegment, ...]:
        """Return word/segment timing evidence from WhisperX.

        ``lyrics`` is accepted deliberately so all timing engines share one
        contract. WhisperX itself still transcribes the audio; the caller is
        responsible for matching that evidence against trusted lyrics.
        """
        if not self.available():
            return ()

        model = self._load_model()
        result = model.transcribe(audio_path, language=language)
        detected_language = language or result.get("language")
        segments = result.get("segments") or ()

        if detected_language:
            try:
                model_a, metadata = self._alignment_model(detected_language)
                result = self._whisperx.align(
                    segments,
                    model_a,
                    metadata,
                    audio_path,
                    self.device,
                    return_char_alignments=True,
                )
                segments = result.get("segments") or segments
            except Exception:
                # Segment-level ASR timing is still useful evidence if the
                # language has no compatible forced-alignment model.
                pass

        output: list[TimedSegment] = []
        for segment in segments:
            if segment.get("start") is None or segment.get("end") is None:
                continue
            words = tuple(segment.get("words") or ())
            output.append(
                TimedSegment(
                    start=float(segment["start"]),
                    end=float(segment["end"]),
                    text=str(segment.get("text", "")).strip(),
                    confidence=self._confidence(segment),
                    words=words,
                )
            )
        return tuple(output)
