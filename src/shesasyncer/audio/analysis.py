from dataclasses import dataclass
from math import isfinite
from pathlib import Path


@dataclass(frozen=True)
class AudioProfile:
    duration: float | None = None
    sample_rate: int | None = None
    channels: int | None = None
    rms: float | None = None
    dynamic_range: float | None = None
    likely_vocal: bool | None = None


def profile_from_samples(samples: list[float], sample_rate: int, channels: int = 1) -> AudioProfile:
    """Cheap, dependency-free audio quality signal for routing.

    This intentionally does not try to recognise lyrics. It only helps decide
    whether expensive vocal/alignment stages are worth invoking.
    """
    if not samples or sample_rate <= 0:
        return AudioProfile(sample_rate=sample_rate, channels=channels)
    finite = [abs(float(x)) for x in samples if isfinite(float(x))]
    if not finite:
        return AudioProfile(sample_rate=sample_rate, channels=channels)
    rms = (sum(x * x for x in finite) / len(finite)) ** 0.5
    peak = max(finite)
    floor = min(finite)
    dynamic = peak / max(floor, 1e-9)
    return AudioProfile(
        sample_rate=sample_rate,
        channels=channels,
        rms=rms,
        dynamic_range=dynamic,
        likely_vocal=rms > 1e-4,
    )


def choose_route(*, has_word_timing: bool, has_phoneme_engine: bool, audio_is_clean: bool) -> str:
    """Select the cheapest route that can provide useful timing evidence."""
    if has_word_timing:
        return "anchor"
    if audio_is_clean and has_phoneme_engine:
        return "phoneme"
    if has_phoneme_engine:
        return "separate_then_phoneme"
    return "timing_evidence"
