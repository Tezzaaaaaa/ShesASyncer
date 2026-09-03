from shesasyncer import AdaptiveAligner, TimedSegment
from shesasyncer.core.adaptive import EngineEvidence


class FakeEngine:
    def __init__(self, name, segments):
        self.name = name
        self.segments = tuple(segments)
        self.calls = 0

    def available(self):
        return True

    def align(self, audio_path, lyrics=None, language=None):
        self.calls += 1
        return self.segments


def test_multiple_engines_consensus():
    first = FakeEngine("word", [TimedSegment(1.0, 2.0, "hello world", 0.9)])
    second = FakeEngine("phoneme", [TimedSegment(1.08, 2.04, "hello world", 0.95)])

    result = AdaptiveAligner([first, second]).run("song.wav", ["Hello world"])

    assert result.lines[0]["text"] == "Hello world"
    assert 1.0 <= result.lines[0]["start"] <= 1.08
    assert result.lines[0]["source"] == "consensus"
    assert result.lines[0]["confidence"] > 0.8


def test_disagreement_does_not_silently_pick_one_engine():
    first = FakeEngine("word", [TimedSegment(1.0, 2.0, "hello world", 0.95)])
    second = FakeEngine("phoneme", [TimedSegment(4.0, 5.0, "hello world", 0.95)])

    result = AdaptiveAligner([first, second]).run("song.wav", ["Hello world"])

    assert result.lines[0]["start"] is None
    assert result.lines[0]["end"] is None
    assert result.warnings


def test_targeted_retry_can_supply_missing_evidence():
    primary = FakeEngine("word", [])
    retry_engine = FakeEngine("retry", [TimedSegment(2.0, 3.0, "second line", 0.9)])

    def retry(audio_path, unresolved):
        assert unresolved == [1]
        return [EngineEvidence("retry", retry_engine.segments)]

    result = AdaptiveAligner([primary]).run(
        "song.wav",
        ["first line", "second line"],
        retry=retry,
    )

    assert result.lines[0]["start"] is None
    assert result.lines[1]["start"] == 2.0
