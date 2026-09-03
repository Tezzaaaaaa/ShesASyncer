from shesasyncer.core.models import AlignmentEvidence, Timing
from shesasyncer.validation.timeline import validate_timeline


def evidence(index, start, end):
    return AlignmentEvidence(index, Timing(start, end, 0.9, "test"))


def test_valid_timeline():
    result = validate_timeline([evidence(0, 0.5, 2.0), evidence(1, 2.1, 3.0)])
    assert result.valid
    assert not result.issues


def test_overlap_is_error():
    result = validate_timeline([evidence(0, 0.5, 2.0), evidence(1, 1.8, 3.0)])
    assert not result.valid
    assert any(issue.code == "overlap" for issue in result.issues)


def test_invalid_direction_is_error():
    result = validate_timeline([evidence(0, 2.0, 1.0)])
    assert not result.valid
    assert any(issue.code == "non-positive-duration" for issue in result.issues)


def test_audio_boundary_is_error():
    result = validate_timeline([evidence(0, 1.0, 11.0)], duration=10.0)
    assert not result.valid
    assert any(issue.code == "past-duration" for issue in result.issues)
