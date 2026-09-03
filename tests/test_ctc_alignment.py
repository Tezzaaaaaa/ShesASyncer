from shesasyncer import AcousticFrame, G2PEngine
from shesasyncer.engines.ctc import CtcSingingEngine
from shesasyncer.evidence.ctc import ctc_viterbi_alignment


def test_ctc_decoder_allows_silence_and_repeated_phonemes():
    frames = (
        AcousticFrame(0.0, {"<blank>": 0.0, "a": -4.0}),
        AcousticFrame(0.1, {"<blank>": -2.0, "a": -0.1}),
        AcousticFrame(0.2, {"<blank>": 0.0, "a": -0.2}),
        AcousticFrame(0.3, {"<blank>": -2.0, "a": -0.1}),
        AcousticFrame(0.4, {"<blank>": 0.0, "a": -4.0}),
    )

    spans = ctc_viterbi_alignment(("a", "a"), frames)

    assert [span["token_index"] for span in spans] == [0, 1]
    assert spans[0]["start"] == 0.1
    assert spans[0]["end"] == 0.2
    assert spans[1]["start"] == 0.3
    assert spans[1]["end"] == 0.5


def test_ctc_engine_reconstructs_trusted_lines():
    g2p = G2PEngine(lambda text, language: ("a", "b") if text == "one" else ("c",))

    def acoustic(_audio, _phonemes, _language):
        return (
            AcousticFrame(0.0, {"<blank>": 0.0, "a": -0.1, "b": -4.0, "c": -4.0}),
            AcousticFrame(0.1, {"<blank>": -2.0, "a": -0.1, "b": -4.0, "c": -4.0}),
            AcousticFrame(0.2, {"<blank>": -2.0, "a": -4.0, "b": -0.1, "c": -4.0}),
            AcousticFrame(0.3, {"<blank>": 0.0, "a": -4.0, "b": -0.2, "c": -4.0}),
            AcousticFrame(0.4, {"<blank>": -2.0, "a": -4.0, "b": -4.0, "c": -0.1}),
            AcousticFrame(0.5, {"<blank>": 0.0, "a": -4.0, "b": -4.0, "c": -0.1}),
        )

    segments = CtcSingingEngine(g2p, acoustic).align("song.wav", ["one", "two"], "en")

    assert [(segment.text, segment.start, segment.end) for segment in segments] == [
        ("one", 0.0, 0.4),
        ("two", 0.4, 0.6),
    ]
