"""Optional ONNX CTC acoustic runner for ShesASyncer.

The runner is deliberately separate from the alignment logic. It turns a
16 kHz mono waveform into frame-wise log probabilities from an ONNX CTC model,
then exposes only the phoneme scores requested by the trusted lyric path.
"""

from collections.abc import Callable, Sequence
import json
import math
import wave

from ..evidence.acoustic import AcousticFrame


class OnnxCtcRunner:
    """Run a CTC phoneme model through ONNX Runtime.

    ``model_path`` and ``vocab_path`` point to externally managed model assets;
    ShesASyncer does not bundle model weights. The default waveform loader
    accepts PCM WAV and normalizes/resamples it to mono 16 kHz.
    """

    def __init__(
        self,
        model_path: str,
        vocab_path: str,
        *,
        blank_token: str = "<blank>",
        sample_rate: int = 16_000,
        waveform_loader: Callable[[str, int], Sequence[float]] | None = None,
        ort_module=None,
        numpy_module=None,
    ):
        self.model_path = model_path
        self.vocab_path = vocab_path
        self.blank_token = blank_token
        self.sample_rate = sample_rate
        self.waveform_loader = waveform_loader or _load_wav_mono_16k
        self._ort = ort_module
        self._np = numpy_module
        self._session = None
        self._vocab = None

    def available(self) -> bool:
        try:
            ort = self._ort or __import__("onnxruntime")
            np = self._np or __import__("numpy")
            self._ort = ort
            self._np = np
            return True
        except ImportError:
            return False

    def _load(self):
        if not self.available():
            return False
        if self._session is None:
            self._session = self._ort.InferenceSession(self.model_path, providers=["CPUExecutionProvider"])
        if self._vocab is None:
            with open(self.vocab_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
            self._vocab = _normalize_vocab(raw)
        return True

    def __call__(
        self,
        audio_path: str,
        phonemes: Sequence[str],
        language: str | None = None,
    ) -> tuple[AcousticFrame, ...]:
        del language
        if not self._load():
            return ()

        waveform = self.waveform_loader(audio_path, self.sample_rate)
        array = self._np.asarray(tuple(waveform), dtype="float32")
        if array.size == 0:
            return ()
        array = array - float(array.mean())
        std = float(array.std())
        if std > 1e-6:
            array = array / std
        array = array.reshape(1, -1)

        input_name = self._session.get_inputs()[0].name
        outputs = self._session.run(None, {input_name: array})
        if not outputs:
            return ()
        logits = self._np.asarray(outputs[0])
        if logits.ndim == 3:
            logits = logits[0]
        if logits.ndim != 2:
            raise ValueError("CTC ONNX model must return [frames, vocabulary] logits")

        log_probs = _log_softmax(logits, self._np)
        requested = set(str(item).strip() for item in phonemes if str(item).strip())
        requested.add(self.blank_token)

        ids = {}
        for token in requested:
            if token in self._vocab:
                ids[token] = self._vocab[token]

        if self.blank_token not in ids:
            raise ValueError(f"CTC vocabulary does not contain blank token {self.blank_token!r}")
        missing = requested.difference(ids)
        if missing:
            raise ValueError(f"CTC vocabulary is missing phonemes: {sorted(missing)}")

        # CTC/Wav2Vec2 emits at a fixed frame rate; infer the time scale from
        # the input duration rather than hard-coding a model-specific stride.
        duration = len(waveform) / float(self.sample_rate)
        hop = duration / max(1, log_probs.shape[0])
        frames = []
        for index, row in enumerate(log_probs):
            frames.append(
                AcousticFrame(
                    time=index * hop,
                    scores={token: float(row[token_id]) for token, token_id in ids.items()},
                )
            )
        return tuple(frames)


def _normalize_vocab(raw: object) -> dict[str, int]:
    if not isinstance(raw, dict):
        raise ValueError("CTC vocabulary must be a JSON object")
    result: dict[str, int] = {}
    for key, value in raw.items():
        try:
            if isinstance(value, int):
                result[str(key)] = value
            elif isinstance(key, str) and str(key).isdigit():
                result[str(value)] = int(key)
        except (TypeError, ValueError):
            continue
    return result


def _log_softmax(logits, np):
    maximum = np.max(logits, axis=-1, keepdims=True)
    shifted = logits - maximum
    return shifted - np.log(np.sum(np.exp(shifted), axis=-1, keepdims=True))


def _load_wav_mono_16k(path: str, target_rate: int) -> tuple[float, ...]:
    with wave.open(path, "rb") as handle:
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        source_rate = handle.getframerate()
        frame_count = handle.getnframes()
        raw = handle.readframes(frame_count)

    if sample_width != 2:
        raise ValueError("ONNX CTC WAV loader requires 16-bit PCM audio")

    import struct

    samples = struct.unpack("<" + "h" * (len(raw) // 2), raw)
    if channels > 1:
        mono = [
            sum(samples[index:index + channels]) / channels
            for index in range(0, len(samples), channels)
        ]
    else:
        mono = list(samples)
    normalized = [sample / 32768.0 for sample in mono]

    if source_rate == target_rate:
        return tuple(normalized)
    if not normalized:
        return ()

    output_length = max(1, round(len(normalized) * target_rate / source_rate))
    result = []
    scale = source_rate / target_rate
    for index in range(output_length):
        position = index * scale
        left = min(len(normalized) - 1, int(math.floor(position)))
        right = min(len(normalized) - 1, left + 1)
        fraction = position - left
        result.append(normalized[left] * (1.0 - fraction) + normalized[right] * fraction)
    return tuple(result)
