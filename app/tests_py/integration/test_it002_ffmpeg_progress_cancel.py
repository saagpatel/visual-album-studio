from vas_studio import FFmpegAdapter


def test_it002_ffmpeg_progress_parse_smoke(tmp_path):
    ff = FFmpegAdapter("ffmpeg")
    out = tmp_path / "out.mp4"
    progress_seen = {"frame": False, "progress": False}

    def on_progress(data):
        if "frame" in data:
            progress_seen["frame"] = True
        if "progress" in data:
            progress_seen["progress"] = True

    ff.run(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=320x240:rate=30",
            "-t",
            "1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(out),
        ],
        on_progress=on_progress,
    )

    assert out.exists()
    assert progress_seen["progress"]
