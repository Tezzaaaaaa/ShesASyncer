from shesasyncer.alignment.refinement import refine_evidence
from shesasyncer.core.models import AlignmentEvidence, Timing


def test_word_and_character_timing_stays_inside_word_boundaries():
    evidence = [AlignmentEvidence(
        line_index=0,
        timing=Timing(1.0, 3.0, 0.9, "consensus"),
        matched_text="Hello world",
        source="consensus",
        metadata={"words": [
            {"word": "Hello", "start": 1.0, "end": 1.8, "confidence": 0.95},
            {"word": "world", "start": 2.0, "end": 3.0, "confidence": 0.9},
        ]},
    )]

    result = refine_evidence(evidence)[0]
    assert len(result.metadata["words"]) == 2
    assert "characters" in result.metadata
    assert result.metadata["characters"][0]["start"] == 1.0
    assert result.metadata["characters"][4]["end"] <= 1.8
    assert result.metadata["characters"][-1]["end"] == 3.0


def test_missing_word_evidence_is_not_invented():
    evidence = [AlignmentEvidence(
        line_index=0,
        timing=Timing(1.0, 3.0, 0.9, "consensus"),
        matched_text="Hello world",
        source="consensus",
    )]

    result = refine_evidence(evidence)[0]
    assert "characters" not in result.metadata
