extends RefCounted
class_name ExportService

const VasIds = preload("res://src/shared/ids.gd")

var db
var paths: Dictionary
var ffmpeg
var asset_service

func _init(p_db = null, p_paths: Dictionary = {}, p_ffmpeg = null, p_asset_service = null) -> void:
	db = p_db
	paths = p_paths
	ffmpeg = p_ffmpeg
	asset_service = p_asset_service

func plan_export(project_id: String, _export_preset_id: String = "") -> Dictionary:
	var rows = db.query("SELECT id, fps, width, height, duration_frames FROM projects WHERE id = %s LIMIT 1;" % db.quote(project_id))
	if rows.is_empty():
		return {}
	var project: Dictionary = rows[0]
	var fps = int(project.get("fps", 30))
	var total_frames = int(project.get("duration_frames", 0))
	var segment_frames = fps * 60
	return {
		"project_id": String(project.get("id", project_id)),
		"fps": fps,
		"width": int(project.get("width", 1920)),
		"height": int(project.get("height", 1080)),
		"duration_frames": total_frames,
		"segment_plan": {
			"segment_frames": segment_frames,
			"segments": plan_segments(total_frames, segment_frames),
		},
	}

func export_project(
	project: Dictionary,
	audio_asset_id: String,
	analysis: Dictionary,
	template: Dictionary,
	draft: bool,
	simulate_only: bool = false
) -> Dictionary:
	var license_check = asset_service.validate_production_allowed(audio_asset_id)
	if not draft and not bool(license_check.get("allowed", false)):
		return {
			"error": "E_LICENSE_INCOMPLETE",
			"message": String(license_check.get("reason", "Audio license metadata is incomplete")),
		}

	var export_id = VasIds.new_id("export")
	var job_id = VasIds.new_id("job")

	var fps = int(project.get("fps", 30))
	var width = int(project.get("width", 1920))
	var height = int(project.get("height", 1080))
	var duration_frames = int(project.get("duration_frames", 0))
	var segment_frames = fps * 60
	var segments = plan_segments(duration_frames, segment_frames)

	var workspace = String(paths.get("tmp_dir", "out/tmp")).path_join("jobs").path_join(job_id)
	var seg_dir = workspace.path_join("segments")
	var concat_dir = workspace.path_join("concat")
	var final_dir = workspace.path_join("final")
	var exports_dir = String(paths.get("exports_dir", "out/exports"))
	var bundle_tmp = exports_dir.path_join("%s.tmp" % export_id)
	var bundle_dir = exports_dir.path_join(export_id)

	for p in [workspace, seg_dir, concat_dir, final_dir, bundle_tmp]:
		DirAccess.make_dir_recursive_absolute(p)

	_write_json(
		workspace.path_join("job_manifest.json"),
		{
			"job_id": job_id,
			"project_id": project.get("id", ""),
			"export_id": export_id,
			"segments": segments,
			"fps": fps,
			"resolution": [width, height],
			"created_at": int(Time.get_unix_time_from_system()),
		},
	)

	var audio_rows = db.query("SELECT library_relpath, sha256 FROM assets WHERE id = %s LIMIT 1;" % db.quote(audio_asset_id))
	if audio_rows.is_empty():
		return {
			"error": "E_ASSET_NOT_FOUND",
			"message": "Missing audio asset %s" % audio_asset_id,
		}
	var audio_row: Dictionary = audio_rows[0]
	var out_dir = String(paths.get("out_dir", "out"))
	var audio_path = out_dir.path_join(String(audio_row.get("library_relpath", "")))

	var seg_mp4s: Array[String] = []
	var encoder = ffmpeg.preferred_h264_encoder()

	if not simulate_only:
		for segment in segments:
			var idx = int(segment.get("index", 0))
			var seg_path = seg_dir.path_join("%03d" % idx)
			var frames_path = seg_path.path_join("frames")
			var seg_mp4 = seg_path.path_join("segment.mp4")
			var seg_manifest_path = seg_path.path_join("segment.manifest.json")
			DirAccess.make_dir_recursive_absolute(seg_path)

			var reuse_ok = false
			if FileAccess.file_exists(seg_mp4) and FileAccess.file_exists(seg_manifest_path):
				var existing_manifest: Variant = JSON.parse_string(FileAccess.get_file_as_string(seg_manifest_path))
				if typeof(existing_manifest) == TYPE_DICTIONARY:
					var m: Dictionary = existing_manifest
					var file_hash = _hash_file(seg_mp4)
					if String(m.get("sha256", "")) == file_hash:
						reuse_ok = true

			if not reuse_ok:
				_safe_remove_tree(frames_path)
				DirAccess.make_dir_recursive_absolute(frames_path)
				_render_segment_frames(frames_path, segment, project, analysis)

				var start_sec = float(segment.get("start_frame", 0)) / max(float(fps), 1.0)
				var dur_sec = float(segment.get("frame_count", 0)) / max(float(fps), 1.0)
				var encode = ffmpeg.run(PackedStringArray([
					"-y",
					"-framerate", str(fps),
					"-i", frames_path.path_join("frame_%06d.png"),
					"-ss", "%.6f" % start_sec,
					"-t", "%.6f" % dur_sec,
					"-i", audio_path,
					"-c:v", encoder,
					"-pix_fmt", "yuv420p",
					"-c:a", "aac",
					"-b:a", "192k",
					"-shortest",
					"-movflags", "+faststart",
					seg_mp4,
				]))
				if not encode["ok"]:
					return {
						"error": "E_FFMPEG_FAILED",
						"message": "Segment encode failed",
						"details": encode,
					}
				var seg_hash = _hash_file(seg_mp4)
				_write_json(seg_manifest_path, {
					"index": idx,
					"start_frame": int(segment.get("start_frame", 0)),
					"frame_count": int(segment.get("frame_count", 0)),
					"sha256": seg_hash,
				})
				_safe_remove_tree(frames_path)

			seg_mp4s.append(seg_mp4)

		var concat_list = concat_dir.path_join("concat_list.txt")
		var lines: Array[String] = []
		for p in seg_mp4s:
			lines.append("file '%s'" % p)
		var concat_file = FileAccess.open(concat_list, FileAccess.WRITE)
		concat_file.store_string("\n".join(lines) + "\n")
		concat_file.close()

		var final_video = final_dir.path_join("video.mp4")
		var concat_res = ffmpeg.run(PackedStringArray([
			"-y",
			"-f", "concat",
			"-safe", "0",
			"-i", concat_list,
			"-c", "copy",
			final_video,
		]))
		if not concat_res["ok"]:
			return {
				"error": "E_FFMPEG_FAILED",
				"message": "Segment concat failed",
				"details": concat_res,
			}

		var thumb = final_dir.path_join("thumbnail.png")
		var thumb_res = ffmpeg.run(PackedStringArray([
			"-y",
			"-ss", "0",
			"-i", final_video,
			"-vframes", "1",
			"-vf", "scale=1280:720",
			thumb,
		]))
		if not thumb_res["ok"]:
			return {
				"error": "E_FFMPEG_FAILED",
				"message": "Thumbnail generation failed",
				"details": thumb_res,
			}

		if _file_size(thumb) > 2_000_000:
			ffmpeg.run(PackedStringArray([
				"-y",
				"-i", thumb,
				"-vf", "scale=1280:720",
				"-compression_level", "9",
				thumb,
			]))

		var checkpoint_frames: Array[int] = [0]
		if duration_frames > 1:
			checkpoint_frames = [0, mini(duration_frames - 1, 900), mini(duration_frames - 1, 1800)]
		var checkpoints = {}
		for frame_idx in checkpoint_frames:
			checkpoints[str(frame_idx)] = _checkpoint_hash(final_video, fps, frame_idx)

		var export_files = _finalize_bundle(
			bundle_tmp,
			bundle_dir,
			project,
			audio_asset_id,
			audio_row,
			template,
			analysis,
			export_id,
			encoder,
			checkpoints,
			segments,
			duration_frames,
			fps,
			width,
			height,
			final_video,
			thumb,
		)
		if not export_files["ok"]:
			return export_files
	else:
		var final_video = final_dir.path_join("video.mp4")
		var thumb = final_dir.path_join("thumbnail.png")
		var simulated_image = Image.create(1280, 720, false, Image.FORMAT_RGB8)
		simulated_image.fill(Color(0.1, 0.1, 0.1, 1.0))
		simulated_image.save_png(thumb)
		var simulated_video = FileAccess.open(final_video, FileAccess.WRITE)
		simulated_video.store_string("SIMULATED")
		simulated_video.close()
		var checkpoints = {"0": _hash_file(final_video)}
		var export_files = _finalize_bundle(
			bundle_tmp,
			bundle_dir,
			project,
			audio_asset_id,
			audio_row,
			template,
			analysis,
			export_id,
			encoder,
			checkpoints,
			segments,
			duration_frames,
			fps,
			width,
			height,
			final_video,
			thumb,
		)
		if not export_files["ok"]:
			return export_files

	var now = int(Time.get_unix_time_from_system())
	var insert_export = """
		INSERT INTO exports(
			id, job_id, project_id, created_at, bundle_relpath, video_relpath,
			thumbnail_relpath, metadata_relpath, provenance_relpath, build_manifest_relpath
		) VALUES (
			%s, %s, %s, %d, %s, %s, %s, %s, %s, %s
		);
	""" % [
		db.quote(export_id),
		db.quote(job_id),
		db.quote(String(project.get("id", ""))),
		now,
		db.quote(_relative_to(String(paths.get("root", "")), bundle_dir)),
		db.quote(_relative_to(String(paths.get("root", "")), bundle_dir.path_join("video.mp4"))),
		db.quote(_relative_to(String(paths.get("root", "")), bundle_dir.path_join("thumbnail.png"))),
		db.quote(_relative_to(String(paths.get("root", "")), bundle_dir.path_join("metadata.json"))),
		db.quote(_relative_to(String(paths.get("root", "")), bundle_dir.path_join("provenance.json"))),
		db.quote(_relative_to(String(paths.get("root", "")), bundle_dir.path_join("build_manifest.json"))),
	]
	db.exec(insert_export)

	return {
		"export_id": export_id,
		"job_id": job_id,
		"bundle_dir": bundle_dir,
		"segments": segments,
	}

func _finalize_bundle(
	bundle_tmp: String,
	bundle_dir: String,
	project: Dictionary,
	audio_asset_id: String,
	audio_row: Dictionary,
	template: Dictionary,
	analysis: Dictionary,
	export_id: String,
	encoder: String,
	checkpoints: Dictionary,
	segments: Array,
	duration_frames: int,
	fps: int,
	width: int,
	height: int,
	final_video: String,
	thumbnail: String
) -> Dictionary:
	var provenance = asset_service.provenance_json(
		audio_asset_id,
		String(project.get("template_id", "")),
		String(project.get("preset_id", "")),
		String(project.get("mapping_id", "")),
		int(project.get("seed", 0))
	)

	var metadata = _render_metadata(template, project, analysis, duration_frames, fps, provenance)
	var build_manifest = {
		"schema_version": 1,
		"toolchain": {
			"godot_version": _godot_version_string(),
			"render_graph_hash": _sha256_text("%s:%s" % [String(project.get("visual_mode", "motion_poster")), String(project.get("preset_id", ""))]),
			"ffmpeg_version": ffmpeg.ffmpeg_version(),
			"ffmpeg_license_mode": "lgpl",
			"analysis_worker_version": String(analysis.get("analysis_version", "worker-v1")),
		},
		"snapshot": {
			"export_id": export_id,
			"project_id": String(project.get("id", "")),
			"inputs": {
				"audio_asset_id": audio_asset_id,
				"audio_sha256": String(audio_row.get("sha256", "")),
				"album_art_asset_id": String(project.get("album_art_asset_id", "")),
				"album_art_sha256": String(project.get("album_art_sha256", "")),
				"fonts": [],
			},
			"preset_id": String(project.get("preset_id", "")),
			"mapping_id": String(project.get("mapping_id", "")),
			"template_id": String(project.get("template_id", "")),
			"seed": int(project.get("seed", 0)),
			"fps": fps,
			"width": width,
			"height": height,
			"duration_frames": duration_frames,
			"segment_plan": {
				"segment_frames": fps * 60,
				"segments": segments,
			},
			"checkpoints": checkpoints,
		},
		"outputs": {
			"video": {"container": "mp4", "codec": "h264", "encoder": encoder, "settings": {}},
			"audio": {"codec": "aac", "bitrate": 192000},
			"thumbnail": {"width": 1280, "height": 720, "time_sec": 0.0},
		},
	}

	DirAccess.copy_absolute(final_video, bundle_tmp.path_join("video.mp4"))
	DirAccess.copy_absolute(thumbnail, bundle_tmp.path_join("thumbnail.png"))
	_write_json(bundle_tmp.path_join("metadata.json"), metadata)
	_write_json(bundle_tmp.path_join("provenance.json"), provenance)
	_write_json(bundle_tmp.path_join("build_manifest.json"), build_manifest)

	if DirAccess.dir_exists_absolute(bundle_dir):
		_safe_remove_tree(bundle_dir)
	var rename_err = DirAccess.rename_absolute(bundle_tmp, bundle_dir)
	if rename_err != OK:
		return {
			"ok": false,
			"error": "E_BUNDLE_WRITE_FAILED",
			"message": "Failed to finalize bundle (rename %s -> %s, err=%d)" % [bundle_tmp, bundle_dir, rename_err],
		}
	return {"ok": true}

func _render_metadata(template: Dictionary, project: Dictionary, analysis: Dictionary, duration_frames: int, fps: int, provenance: Dictionary) -> Dictionary:
	var metadata = {}
	if typeof(template.get("metadata", {})) == TYPE_DICTIONARY:
		metadata = template.get("metadata", {}).duplicate(true)

	var duration_sec = float(duration_frames) / max(float(fps), 1.0)
	var duration_hms = "%.3fs" % duration_sec
	var vars = {
		"{project.title}": String(project.get("name", "")),
		"{project.artist}": String(project.get("artist", "")),
		"{project.series}": String(project.get("series", "")),
		"{project.genre}": String(project.get("genre", "")),
		"{audio.bpm}": str(analysis.get("tempo_bpm", 0.0)),
		"{audio.duration_sec}": str(duration_sec),
		"{export.fps}": str(fps),
		"{export.width}": str(project.get("width", 1920)),
		"{export.height}": str(project.get("height", 1080)),
		"{export.duration_hms}": duration_hms,
		"{provenance.attribution_block}": String(provenance.get("attribution_block", "")),
		"{now.iso_date}": Time.get_datetime_string_from_system(false, true).substr(0, 10),
	}

	metadata["title"] = _resolve_template_string(String(metadata.get("title", "")), vars)
	metadata["description"] = _resolve_template_string(String(metadata.get("description", "")), vars)

	var tags_out: Array = []
	var tags_in: Array = metadata.get("tags", [])
	for tag in tags_in:
		tags_out.append(_resolve_template_string(String(tag), vars))
	metadata["tags"] = tags_out

	metadata["categoryId"] = String(metadata.get("categoryId", "10"))
	metadata["privacyStatus"] = String(metadata.get("privacyStatus", "private"))
	if not metadata.has("publishAt"):
		metadata["publishAt"] = null
	if not metadata.has("playlistIds"):
		metadata["playlistIds"] = []
	if not metadata.has("chapters"):
		metadata["chapters"] = []

	metadata["schema_version"] = 1
	return metadata

func _resolve_template_string(source: String, vars: Dictionary) -> String:
	var out = source
	for key in vars.keys():
		out = out.replace(String(key), String(vars[key]))
	return out

func _render_segment_frames(frames_path: String, segment: Dictionary, project: Dictionary, analysis: Dictionary) -> void:
	var start_frame = int(segment.get("start_frame", 0))
	var frame_count = int(segment.get("frame_count", 0))
	var fps = max(int(project.get("fps", 30)), 1)
	var width = max(int(project.get("width", 1920)), 2)
	var height = max(int(project.get("height", 1080)), 2)
	var seed = int(project.get("seed", 101))
	var tempo = float(analysis.get("tempo_bpm", 120.0))

	for local_idx in frame_count:
		var global_idx = start_frame + local_idx
		var time_sec = float(global_idx) / float(fps)
		var beat_phase = fposmod((time_sec * tempo / 60.0), 1.0)
		var png_path = frames_path.path_join("frame_%06d.png" % local_idx)
		_render_motion_poster_frame(png_path, width, height, time_sec, beat_phase, seed, global_idx)

func _render_motion_poster_frame(path: String, width: int, height: int, time_sec: float, beat_phase: float, seed: int, frame_index: int) -> void:
	var img = Image.create(width, height, false, Image.FORMAT_RGB8)
	var wave = 0.5 + 0.5 * sin(time_sec * 1.2 + float(seed) * 0.001)
	var pulse = 0.5 + 0.5 * sin(TAU * beat_phase)
	var r = clampf(0.2 + 0.6 * wave, 0.0, 1.0)
	var g = clampf(0.2 + 0.7 * pulse, 0.0, 1.0)
	var b = clampf(0.2 + 0.6 * (1.0 - wave), 0.0, 1.0)
	img.fill(Color(r, g, b, 1.0))

	var bar_h = maxi(8, int(float(height) * (0.08 + 0.18 * pulse)))
	img.fill_rect(Rect2i(0, height - bar_h, width, bar_h), Color(1.0 - pulse, pulse, 0.35 + 0.4 * wave, 1.0))

	var marker_x = int(float(width) * fposmod(time_sec * 0.05 + float(seed % 17) * 0.01, 1.0))
	img.fill_rect(Rect2i(marker_x, 0, 6, height), Color(0.95, 0.95, 0.95, 1.0))

	var grain = float((frame_index + seed) % 13) / 13.0
	img.fill_rect(Rect2i(0, 0, width, 6), Color(grain, grain, grain, 1.0))
	img.save_png(path)

func _write_json(path: String, payload: Dictionary) -> void:
	var f = FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		push_error("Failed to write JSON: %s" % path)
		return
	f.store_string(JSON.stringify(payload, "\t"))
	f.close()

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

func _sha256_text(text: String) -> String:
	var hash = HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(text.to_utf8_buffer())
	return hash.finish().hex_encode()

func _checkpoint_hash(video_path: String, fps: int, frame_index: int) -> String:
	var tmp_png = String(paths.get("tmp_dir", "out/tmp")).path_join("checkpoint_%s_%d.png" % [VasIds.new_id("cp"), frame_index])
	var t = float(frame_index) / max(float(fps), 1.0)
	var capture = ffmpeg.run(PackedStringArray([
		"-y",
		"-ss", "%.6f" % t,
		"-i", video_path,
		"-vframes", "1",
		tmp_png,
	]))
	if not capture["ok"]:
		return ""
	var digest = _hash_file(tmp_png)
	DirAccess.remove_absolute(tmp_png)
	return digest

func _file_size(path: String) -> int:
	var file = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return 0
	var size = int(file.get_length())
	file.close()
	return size

func _safe_remove_tree(path: String) -> void:
	if path.strip_edges() == "" or path == "/":
		return
	OS.execute("rm", PackedStringArray(["-rf", path]), [], true)

func _relative_to(root: String, abs_path: String) -> String:
	var normalized_root = root
	if normalized_root != "" and not normalized_root.ends_with("/"):
		normalized_root += "/"
	if normalized_root != "" and abs_path.begins_with(normalized_root):
		return abs_path.substr(normalized_root.length())
	return abs_path

func _godot_version_string() -> String:
	var info: Dictionary = Engine.get_version_info()
	return "%s.%s.%s-%s" % [
		str(info.get("major", "?")),
		str(info.get("minor", "?")),
		str(info.get("patch", "?")),
		str(info.get("status", "")),
	]

static func plan_segments(total_frames: int, segment_frames: int) -> Array:
	var segments: Array = []
	var i = 0
	while i * segment_frames < total_frames:
		var start_frame = i * segment_frames
		var frame_count = mini(segment_frames, total_frames - start_frame)
		segments.append({
			"index": i,
			"start_frame": start_frame,
			"frame_count": frame_count,
		})
		i += 1
	return segments
