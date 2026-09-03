from shesasyncer import AlignmentPipeline


def test_trusted_lyrics_are_preserved():
    lyrics = ["Hello world", "We are here"]
    segments = [
        {"start": 1.0, "end": 2.5, "text": "hello wurld"},
        {"start": 3.0, "end": 4.2, "text": "we are hear"},
    ]
    result = AlignmentPipeline().run(lyrics, segments)
    assert [x["text"] for x in result.lines] == lyrics
    assert result.lines[0]["start"] == 1.0
    assert result.lines[1]["start"] == 3.0
    assert result.confidence > 0.4


def test_missing_evidence_is_explicit():
    result = AlignmentPipeline().run(["Unmatched line"], [])
    assert result.lines[0]["start"] is None
    assert result.lines[0]["end"] is None
    assert result.lines[0]["confidence"] == 0.0
    assert result.warnings
