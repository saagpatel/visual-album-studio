from vas_audio_worker import analyze_audio


def test_analyze_audio_returns_expected_shape():
    result = analyze_audio("dummy.wav")
    assert "tempo_bpm" in result
    assert "beat_times_sec" in result
