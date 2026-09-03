from shesasyncer.engines.ctc import CtcSingingEngine
from shesasyncer.evidence.acoustic import AcousticFrame
from shesasyncer.lyrics.g2p import G2PEngine


def test_ctc_engine_fills_gaps_between_lines():
    g2p = G2PEngine(lambda text, language: tuple(text.split()))

    def runner(audio_path, phonemes, language):
        return [
            AcousticFrame(0.00, {"<blank>": -1.0, "one": -0.1}),
            AcousticFrame(0.02, {"<blank>": -1.0, "one": -0.1}),
            AcousticFrame(0.04, {"<blank>": -0.1, "two": -1.0}),
            AcousticFrame(0.06, {"<blank>": -1.0, "two": -0.1}),
        ]

    engine = CtcSingingEngine(g2p, runner)
    result = engine.align("song.wav", ["one", "two"])

    assert len(result) == 2
    assert result[0].start == 0.0
    assert result[0].end == result[1].start
