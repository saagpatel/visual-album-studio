extends RefCounted
class_name FfmpegAdapter

var ffmpeg_bin: String = "ffmpeg"

func _init(p_ffmpeg_bin: String = "ffmpeg") -> void:
	ffmpeg_bin = p_ffmpeg_bin

func run(args: PackedStringArray) -> Dictionary:
	var full = args.duplicate()
	full.append_array(["-progress", "pipe:1", "-nostats", "-hide_banner"])

	var out: Array = []
	var code = OS.execute(ffmpeg_bin, full, out, true)
	var output_text = "\n".join(out)
	var progress = _parse_progress(output_text)

	return {
		"ok": code == 0,
		"code": code,
		"output": output_text,
		"progress": progress,
	}

func ffmpeg_version() -> String:
	var out: Array = []
	var code = OS.execute(ffmpeg_bin, PackedStringArray(["-version"]), out, true)
	if code != 0 or out.is_empty():
		return "unknown"
	var first = String(out[0]).strip_edges()
	return first

func preferred_h264_encoder() -> String:
	var out: Array = []
	var code = OS.execute(ffmpeg_bin, PackedStringArray(["-encoders"]), out, true)
	if code != 0:
		return "libx264"
	var text = "\n".join(out)
	if text.contains(" h264_videotoolbox"):
		return "h264_videotoolbox"
	if text.contains(" libx264"):
		return "libx264"
	return "mpeg4"

func _parse_progress(output_text: String) -> Dictionary:
	var progress = {
		"frame": 0,
		"out_time_ms": 0,
		"progress": "continue",
	}
	for raw_line in output_text.split("\n"):
		var line = raw_line.strip_edges()
		if line == "" or line.find("=") == -1:
			continue
		var kv = line.split("=", false, 1)
		if kv.size() != 2:
			continue
		var key = kv[0]
		var value = kv[1]
		match key:
			"frame":
				progress["frame"] = int(value)
			"out_time_ms":
				progress["out_time_ms"] = int(value)
			"progress":
				progress["progress"] = value
			_:
				pass
	return progress
