from shesasyncer import AdaptiveAligner, PhonemeBoundary, SofaEngine, TimedSegment, normalize_phonemes


def test_normalize_phonemes_rejects_invalid_and_sorts():
    result = normalize_phonemes([
        {"phoneme": "b", "start": 1.2, "end": 1.4, "confidence": 0.8},
        {"symbol": "a", "start": 1.0, "end": 1.2},
        {"phoneme": "bad", "start": 2.0, "end": 1.0},
    ])

    assert result == (
        PhonemeBoundary("a", 1.0, 1.2, 0.0),
        PhonemeBoundary("b", 1.2, 1.4, 0.8),
    )


def test_sofa_adapter_normalizes_phoneme_output():
    def runner(audio_path, lyrics, language):
        assert audio_path == "song.wav"
        assert lyrics == ["Hello"]
        assert language == "en"
        return [{
            "start": 1.0,
            "end": 2.0,
            "text": "hello",
            "confidence": 0.9,
            "phonemes": [
                {"phoneme": "h", "start": 1.0, "end": 1.2, "confidence": 0.8},
                {"phoneme": "ə", "start": 1.2, "end": 1.5, "confidence": 0.7},
            ],
        }]

    segments = SofaEngine(runner).align("song.wav", ["Hello"], "en")

    assert len(segments) == 1
    assert segments[0].phonemes == (
        {"phoneme": "h", "start": 1.0, "end": 1.2, "confidence": 0.8},
        {"phoneme": "ə", "start": 1.2, "end": 1.5, "confidence": 0.7},
    )


def test_sofa_without_runtime_is_safe():
    engine = SofaEngine()
    assert not engine.available()
    assert engine.align("song.wav", ["Hello"]) == ()


def test_adaptive_result_preserves_phoneme_evidence():
    engine = SofaEngine(lambda *_: [
        TimedSegment(
            1.0,
            2.0,
            "hello",
            0.95,
            phonemes=({"phoneme": "h", "start": 1.0, "end": 1.2, "confidence": 0.9},),
        )
    ])

    result = AdaptiveAligner([engine]).run("song.wav", ["Hello"])

    assert result.lines[0]["phonemes"] == [
        {"phoneme": "h", "start": 1.0, "end": 1.2, "confidence": 0.9}
    ]
