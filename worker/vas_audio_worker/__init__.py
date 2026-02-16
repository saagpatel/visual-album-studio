__all__ = ["analyze_audio"]


def analyze_audio(path: str) -> dict:
    return {
        "path": path,
        "tempo_bpm": 120.0,
        "beat_times_sec": [0.0],
        "analysis_version": "phase0-placeholder",
    }
