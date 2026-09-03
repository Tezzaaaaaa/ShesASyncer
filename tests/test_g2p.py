from shesasyncer.lyrics.g2p import EspeakG2P, _tokenize_ipa


def test_tokenize_ipa_removes_stress_and_ties():
    assert _tokenize_ipa("h əʊ ˈl aɪ tʃ", strip_stress=True) == (
        "h", "əʊ", "l", "aɪ", "tʃ"
    )


def test_espeak_g2p_unavailable_without_executable():
    engine = EspeakG2P(executable="/definitely/not/espeak-ng")
    assert not engine.available()
    assert engine.convert("hello", "en") == ()
