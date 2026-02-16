extends RefCounted
class_name MixerService

const VasIds = preload("res://src/shared/ids.gd")

var ffmpeg
var projects = {}

func _init(p_ffmpeg = null) -> void:
	ffmpeg = p_ffmpeg

func add_track(project_id: String, wav_path: String) -> String:
	if not projects.has(project_id):
		projects[project_id] = []
	var track_id = VasIds.new_id("track")
	projects[project_id].append({
		"track_id": track_id,
		"wav_path": wav_path,
		"volume_db": 0.0,
		"pan": 0.0,
		"start_offset_ms": 0,
		"loop_enabled": false,
		"loop_start_ms": null,
		"loop_end_ms": null,
		"fade_in_ms": 0,
		"fade_out_ms": 0,
	})
	return track_id

func set_track_params(project_id: String, track_id: String, params: Dictionary) -> bool:
	if not projects.has(project_id):
		return false
	for track in projects[project_id]:
		if String(track.get("track_id", "")) == track_id:
			for key in params.keys():
				track[key] = params[key]
			return true
	return false

func bounce(project_id: String, out_wav: String) -> Dictionary:
	if not projects.has(project_id):
		return {"error": "E_MIXER_INVALID_STATE", "message": "Unknown project"}
	var tracks: Array = projects[project_id]
	if tracks.is_empty():
		return {"error": "E_MIXER_INVALID_STATE", "message": "No tracks"}

	var args = PackedStringArray(["-y"])
	var filter_parts: Array[String] = []
	var mix_inputs: Array[String] = []

	for i in tracks.size():
		var track: Dictionary = tracks[i]
		args.append_array(["-i", String(track.get("wav_path", ""))])
		filter_parts.append("[%d:a]volume=%sdB[a%d]" % [i, str(track.get("volume_db", 0.0)), i])
		mix_inputs.append("[a%d]" % i)

	var filter_complex = ""
	if not filter_parts.is_empty():
		filter_complex = ";".join(filter_parts) + ";"
	filter_complex += "".join(mix_inputs) + "amix=inputs=%d:normalize=0[m]" % tracks.size()

	args.append_array([
		"-filter_complex", filter_complex,
		"-map", "[m]",
		"-ac", "2",
		"-ar", "48000",
		"-sample_fmt", "s16",
		out_wav,
	])

	var res = ffmpeg.run(args)
	if not res.get("ok", false):
		return {"error": "E_FFMPEG_FAILED", "message": "Bounce failed", "details": res}

	var digest = _hash_file(out_wav)
	return {
		"bounce_id": VasIds.new_id("bounce"),
		"sha256": digest,
		"created_at": int(Time.get_unix_time_from_system()),
		"manifest": {
			"project_id": project_id,
			"tracks": tracks.map(func(t): return t["track_id"]),
		},
	}

func loop_boundary_diff(samples_a: PackedByteArray, samples_b: PackedByteArray) -> float:
	if samples_a.is_empty() or samples_b.is_empty():
		return 0.0
	var length = mini(samples_a.size(), samples_b.size())
	if length <= 0:
		return 0.0
	var total = 0.0
	for i in length:
		total += abs(float(samples_a[i]) - float(samples_b[i]))
	return total / float(length)

func _hash_file(path: String) -> String:
	var file = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return ""
	var hash = HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	while not file.eof_reached():
		hash.update(file.get_buffer(1024 * 1024))
	file.close()
	return hash.finish().hex_encode()
