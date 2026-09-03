from shesasyncer.evidence.acoustic import AcousticFrame
from shesasyncer.evidence.ctc import ctc_viterbi_alignment


def frame(time, blank=-0.1, **scores):
    values = {"<blank>": blank}
    values.update(scores)
    return AcousticFrame(time=time, scores=values)


def test_ctc_alignment_handles_token_ending_on_final_frame():
    result = ctc_viterbi_alignment(
        ["a"],
        [frame(0.00, a=-4), frame(0.02, a=-0.1), frame(0.04, a=-0.1)],
    )

    assert len(result) == 1
    assert result[0]["phoneme"] == "a"
    assert result[0]["start"] == 0.02
    assert result[0]["end"] == 0.06


def test_ctc_repeated_phonemes_require_blank_separation():
    result = ctc_viterbi_alignment(
        ["a", "a"],
        [
            frame(0.00, a=-0.1),
            frame(0.02, a=-4),
            frame(0.04, a=-0.1),
            frame(0.06, a=-0.1),
        ],
    )

    assert [item["phoneme"] for item in result] == ["a", "a"]
    assert result[0]["end"] <= result[1]["start"]


def test_ctc_empty_input_is_safe():
    assert ctc_viterbi_alignment([], []) == ()
