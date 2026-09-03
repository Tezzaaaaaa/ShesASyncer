from shesasyncer import AcousticFrame, G2PEngine, NativeSingingEngine


def test_native_engine_aligns_phonemes_to_acoustic_frames():
    g2p = G2PEngine(lambda text, language: ("h", "e", "l", "o"))

    def acoustic(audio_path, phonemes, language):
        assert audio_path == "song.wav"
        assert phonemes == ["h", "e", "l", "o"]
        assert language == "en"
        return tuple(
            AcousticFrame(i * 0.1, {phoneme: 3.0})
            for i, phoneme in enumerate(("h", "e", "l", "o"))
        )

    segments = NativeSingingEngine(g2p, acoustic).align("song.wav", ["Hello"], "en")
    assert len(segments) == 1
    assert segments[0].text == "Hello"
    assert segments[0].start == 0.0
    assert segments[0].end == 0.4
    assert [p["phoneme"] for p in segments[0].phonemes] == ["h", "e", "l", "o"]
    assert all(p["end"] > p["start"] for p in segments[0].phonemes)


def test_native_engine_reconstructs_multiple_lines_from_one_alignment():
    calls = []
    g2p = G2PEngine(lambda text, language: (calls.append(text) or (("a", "b") if text == "one" else ("c", "d"))))

    def acoustic(_audio, phonemes, _language):
        assert phonemes == ["a", "b", "c", "d"]
        return tuple(AcousticFrame(i * 0.1, {p: 4.0}) for i, p in enumerate(phonemes))

    segments = NativeSingingEngine(g2p, acoustic).align("song.wav", ["one", "two"], "en")
    assert calls == ["one", "two"]
    assert [(s.text, s.start, s.end) for s in segments] == [
        ("one", 0.0, 0.2),
        ("two", 0.2, 0.4),
    ]
