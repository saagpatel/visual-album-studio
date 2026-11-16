extends RefCounted
class_name ExportService

const VasIds = preload("res://src/shared/ids.gd")

var db
var paths: Dictionary
var ffmpeg
var asset_service
var _atomic_write_after_stage: Callable

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
	var job_id = VasIds.new_id("job")
	var lock_result = _acquire_job_lock(job_id)
	if not bool(lock_result.get("ok", false)):
		return lock_result
	var result = _run_export(project, audio_asset_id, analysis, template, draft, simulate_only, job_id, false)
	if not _release_job_lock(job_id):
		result["lock_release_error"] = "Export lock could not be released; reconcile its owner record before another attempt"
	return result

func resume_export(
	job_id: String,
	project: Dictionary,
	audio_asset_id: String,
	analysis: Dictionary,
	template: Dictionary,
	draft: bool,
	simulate_only: bool = false
) -> Dictionary:
	if not _is_safe_job_id(job_id):
		return {"error": "E_RESUME_INVALID_JOB", "message": "Invalid export job id"}
	var lock_result = _acquire_job_lock(job_id)
	if not bool(lock_result.get("ok", false)):
		return lock_result
	var result = _run_export(project, audio_asset_id, analysis, template, draft, simulate_only, job_id, true)
	if not _release_job_lock(job_id):
		result["lock_release_error"] = "Export lock could not be released; reconcile its owner record before another attempt"
	return result

func _run_export(
	project: Dictionary,
	audio_asset_id: String,
	analysis: Dictionary,
	template: Dictionary,
	draft: bool,
	simulate_only: bool,
	job_id: String = "",
	resume_existing: bool = false
) -> Dictionary:
	var license_check = asset_service.validate_production_allowed(audio_asset_id)
	if not draft and not bool(license_check.get("allowed", false)):
		return {
			"error": "E_LICENSE_INCOMPLETE",
			"message": String(license_check.get("reason", "Audio license metadata is incomplete")),
		}

	if job_id == "":
		job_id = VasIds.new_id("job")
	var export_id = ""

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

	var audio_rows = db.query("SELECT library_relpath, sha256 FROM assets WHERE id = %s LIMIT 1;" % db.quote(audio_asset_id))
	if audio_rows.is_empty():
		return {
			"error": "E_ASSET_NOT_FOUND",
			"message": "Missing audio asset %s" % audio_asset_id,
		}
	var audio_row: Dictionary = audio_rows[0]
	var out_dir = String(paths.get("out_dir", "out"))
	var audio_path = out_dir.path_join(String(audio_row.get("library_relpath", "")))
	if _path_has_symlink_component(workspace) or _path_has_symlink_component(exports_dir) or _path_has_symlink_component(audio_path):
		return {"error": "E_RESUME_UNSAFE_PATH", "message": "Export path contains a symlink", "job_id": job_id}
	var actual_audio_hash = _hash_file(audio_path)
	if actual_audio_hash == "":
		return {"error": "E_AUDIO_HASH_FAILED", "message": "Could not hash the export audio input", "job_id": job_id}
	audio_row["sha256"] = actual_audio_hash
	var binding = _resume_binding(project, audio_asset_id, actual_audio_hash, analysis, template, draft, simulate_only, fps, width, height, duration_frames, segments)
	if binding == "":
		return {"error": "E_RESUME_BINDING_UNAVAILABLE", "message": "Could not identify the renderer source and toolchain; refusing to create or resume a reusable job", "job_id": job_id}
	var job_manifest_path = workspace.path_join("job_manifest.json")
	if _path_has_symlink_component(job_manifest_path):
		return {"error": "E_RESUME_UNSAFE_PATH", "message": "Job manifest path contains a symlink", "job_id": job_id}
	if resume_existing:
		if not FileAccess.file_exists(job_manifest_path):
			return {"error": "E_RESUME_JOB_NOT_FOUND", "message": "Export job manifest is missing", "job_id": job_id}
		var stored_value: Variant = JSON.parse_string(FileAccess.get_file_as_string(job_manifest_path))
		if typeof(stored_value) != TYPE_DICTIONARY:
			return {"error": "E_RESUME_INVALID_JOB", "message": "Export job manifest is invalid", "job_id": job_id}
		var stored: Dictionary = stored_value
		if String(stored.get("job_id", "")) != job_id or not _is_safe_export_id(String(stored.get("export_id", ""))):
			return {"error": "E_RESUME_INVALID_JOB", "message": "Export job identity is invalid", "job_id": job_id}
		export_id = String(stored.get("export_id", ""))
		if String(stored.get("resume_binding", "")) == "" or String(stored.get("resume_binding", "")) != binding:
			return _with_export_context({"error": "E_RESUME_INPUT_MISMATCH", "message": "Export inputs or toolchain differ from the original job"}, job_id, export_id)
	else:
		export_id = VasIds.new_id("export")
	var bundle_tmp = exports_dir.path_join("%s.tmp.%s" % [export_id, VasIds.new_id("stage")])
	var bundle_dir = exports_dir.path_join(export_id)
	if _path_has_symlink_component(bundle_tmp) or _path_has_symlink_component(bundle_dir):
		return _with_export_context({"error": "E_RESUME_UNSAFE_PATH", "message": "Export bundle path contains a symlink"}, job_id, export_id)
	for output_path in [
		bundle_tmp.path_join("video.mp4"), bundle_tmp.path_join("thumbnail.png"),
		bundle_tmp.path_join("metadata.json"), bundle_tmp.path_join("provenance.json"),
		bundle_tmp.path_join("build_manifest.json"), final_dir.path_join("video.mp4"),
		final_dir.path_join("thumbnail.png"),
	]:
		if _path_has_symlink_component(output_path):
			return _with_export_context({"error": "E_RESUME_UNSAFE_PATH", "message": "Export output path contains a symlink"}, job_id, export_id)
	if resume_existing and DirAccess.dir_exists_absolute(bundle_dir):
		if not _is_complete_bundle(bundle_dir, export_id, String(project.get("id", "")), job_manifest_path, binding):
			return _with_export_context({"error": "E_RESUME_BUNDLE_INCOMPLETE", "message": "Finalized export directory is incomplete or does not match this job"}, job_id, export_id)
		if not _register_export(export_id, job_id, String(project.get("id", "")), bundle_dir):
			return _with_export_context({"error": "E_EXPORT_REGISTRATION_FAILED", "message": "Could not reconcile the finalized export record"}, job_id, export_id)
		return {"export_id": export_id, "job_id": job_id, "bundle_dir": bundle_dir, "segments": segments}
	for p in [workspace, seg_dir, concat_dir, final_dir, bundle_tmp]:
		DirAccess.make_dir_recursive_absolute(p)
	if not resume_existing:
		var manifest_write = _write_json_atomic(job_manifest_path, {
			"schema_version": 2,
			"job_id": job_id,
			"project_id": project.get("id", ""),
			"export_id": export_id,
			"segments": segments,
			"fps": fps,
			"resolution": [width, height],
			"resume_binding": binding,
			"created_at": int(Time.get_unix_time_from_system()),
		})
		if not manifest_write:
			return _with_export_context({"error": "E_JOB_MANIFEST_WRITE_FAILED", "message": "Could not persist export job manifest"}, job_id, export_id)
	var seg_mp4s: Array[String] = []
	var encoder = ffmpeg.preferred_h264_encoder()

	if not simulate_only:
		var concat_list_path = concat_dir.path_join("concat_list.txt")
		for segment in segments:
			var idx = int(segment.get("index", 0))
			var seg_path = seg_dir.path_join("%03d" % idx)
			if _path_has_symlink_component(seg_path):
				return _with_export_context({"error": "E_RESUME_UNSAFE_PATH", "message": "Segment path contains a symlink"}, job_id, export_id)
			var frames_path = seg_path.path_join("frames")
			var seg_mp4 = seg_path.path_join("segment.mp4")
			var seg_manifest_path = seg_path.path_join("segment.manifest.json")
			if _path_has_symlink_component(frames_path) or _path_has_symlink_component(seg_mp4) or _path_has_symlink_component(seg_manifest_path) or _path_has_symlink_component(concat_list_path):
				return _with_export_context({"error": "E_RESUME_UNSAFE_PATH", "message": "Segment artifact path contains a symlink"}, job_id, export_id)
			DirAccess.make_dir_recursive_absolute(seg_path)

			var reuse_ok = _segment_is_reusable(seg_mp4, seg_manifest_path, segment)

			if not reuse_ok:
				_safe_remove_tree(frames_path)
				DirAccess.make_dir_recursive_absolute(frames_path)
				_render_segment_frames(frames_path, segment, project, analysis)

				var start_sec = float(segment.get("start_frame", 0)) / max(float(fps), 1.0)
				var dur_sec = float(segment.get("frame_count", 0)) / max(float(fps), 1.0)
				var partial_mp4 = seg_path.path_join("segment.%s.partial.mp4" % VasIds.new_id("attempt"))
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
					partial_mp4,
				]))
				if not encode["ok"] or not FileAccess.file_exists(partial_mp4) or _hash_file(partial_mp4) == "":
					return _with_export_context({
						"error": "E_FFMPEG_FAILED",
						"message": "Segment encode failed",
						"details": encode,
					}, job_id, export_id)
				var seg_hash = _hash_file(partial_mp4)
				var promote_err = DirAccess.rename_absolute(partial_mp4, seg_mp4)
				if promote_err != OK:
					return _with_export_context({"error": "E_SEGMENT_PROMOTE_FAILED", "message": "Could not promote completed segment"}, job_id, export_id)
				if not _write_json_atomic(seg_manifest_path, {
					"index": idx,
					"start_frame": int(segment.get("start_frame", 0)),
					"frame_count": int(segment.get("frame_count", 0)),
					"sha256": seg_hash,
				}):
					DirAccess.remove_absolute(seg_mp4)
					return _with_export_context({"error": "E_SEGMENT_MANIFEST_WRITE_FAILED", "message": "Could not persist completed segment manifest"}, job_id, export_id)
				_safe_remove_tree(frames_path)

			seg_mp4s.append(seg_mp4)

		var concat_list = concat_list_path
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
			return _with_export_context({
				"error": "E_FFMPEG_FAILED",
				"message": "Segment concat failed",
				"details": concat_res,
			}, job_id, export_id)

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
			return _with_export_context({
				"error": "E_FFMPEG_FAILED",
				"message": "Thumbnail generation failed",
				"details": thumb_res,
			}, job_id, export_id)

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
			job_manifest_path,
			binding,
		)
		if not export_files["ok"]:
			return _with_export_context(export_files, job_id, export_id)
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
			job_manifest_path,
			binding,
		)
		if not export_files["ok"]:
			return _with_export_context(export_files, job_id, export_id)

	if not _register_export(export_id, job_id, String(project.get("id", "")), bundle_dir):
		return _with_export_context({"error": "E_EXPORT_REGISTRATION_FAILED", "message": "Could not register the finalized export"}, job_id, export_id)

	return {
		"export_id": export_id,
		"job_id": job_id,
		"bundle_dir": bundle_dir,
		"segments": segments,
	}

func _with_export_context(result: Dictionary, job_id: String, export_id: String) -> Dictionary:
	var contextual = result.duplicate(true)
	contextual["job_id"] = job_id
	if export_id != "":
		contextual["export_id"] = export_id
	return contextual

func _acquire_job_lock(job_id: String) -> Dictionary:
	var jobs_root = String(paths.get("tmp_dir", "out/tmp")).path_join("jobs")
	if _path_has_symlink_component(jobs_root):
		return {"error": "E_RESUME_UNSAFE_PATH", "message": "Export job path contains a symlink", "job_id": job_id}
	DirAccess.make_dir_recursive_absolute(jobs_root)
	var lock_path = jobs_root.path_join(job_id + ".lock")
	if _path_has_symlink_component(lock_path):
		return {"error": "E_RESUME_UNSAFE_PATH", "message": "Export lock path contains a symlink", "job_id": job_id}
	if DirAccess.make_dir_absolute(lock_path) != OK:
		return {"error": "E_RESUME_LOCKED", "message": "Export job has an active or unreconciled lock. Manual recovery requires stopping every Visual Album Studio exporter process and reaping all descendants (including FFmpeg), confirming no app instance can start another export, using one exclusive operator with no concurrent resume attempts, preserving the workspace and lock contents, and inspecting the owner record (or treating a missing record as unknown) before removing only this job lock.", "job_id": job_id}
	var owner_path = lock_path.path_join("owner.json")
	if not _write_json_atomic(owner_path, {
		"job_id": job_id,
		"pid": OS.get_process_id(),
		"lock_created_at": int(Time.get_unix_time_from_system()),
	}):
		_safe_remove_tree(lock_path)
		if DirAccess.dir_exists_absolute(lock_path):
			return {"error": "E_RESUME_LOCK_WRITE_FAILED", "message": "Could not persist owner metadata and the lock directory remains; treat it as unreconciled and follow the supervised lock recovery procedure", "job_id": job_id}
		return {"error": "E_RESUME_LOCK_WRITE_FAILED", "message": "Could not persist export lock owner", "job_id": job_id}
	return {"ok": true, "lock_path": lock_path}

func _release_job_lock(job_id: String) -> bool:
	var lock_path = String(paths.get("tmp_dir", "out/tmp")).path_join("jobs").path_join(job_id + ".lock")
	var owner_path = lock_path.path_join("owner.json")
	if _path_has_symlink_component(lock_path) or _path_has_symlink_component(owner_path):
		return false
	if not FileAccess.file_exists(owner_path):
		return false
	var owner: Variant = JSON.parse_string(FileAccess.get_file_as_string(owner_path))
	if typeof(owner) != TYPE_DICTIONARY or int(owner.get("pid", -1)) != OS.get_process_id():
		return false
	if DirAccess.remove_absolute(owner_path) != OK:
		return false
	return DirAccess.remove_absolute(lock_path) == OK

func _register_export(export_id: String, job_id: String, project_id: String, bundle_dir: String) -> bool:
	var expected_paths = _expected_export_paths(bundle_dir)
	var existing_rows = db.query("SELECT id, job_id, project_id, bundle_relpath, video_relpath, thumbnail_relpath, metadata_relpath, provenance_relpath, build_manifest_relpath FROM exports WHERE id = %s LIMIT 1;" % db.quote(export_id))
	if not existing_rows.is_empty():
		var existing: Dictionary = existing_rows[0]
		if String(existing.get("job_id", "")) != job_id or String(existing.get("project_id", "")) != project_id:
			return false
		for key in expected_paths:
			if String(existing.get(key, "")) != String(expected_paths[key]):
				return false
		return true
	var now = int(Time.get_unix_time_from_system())
	var result = db.exec("""
		INSERT OR IGNORE INTO exports(
			id, job_id, project_id, created_at, bundle_relpath, video_relpath,
			thumbnail_relpath, metadata_relpath, provenance_relpath, build_manifest_relpath
		) VALUES (
			%s, %s, %s, %d, %s, %s, %s, %s, %s, %s
		);
	""" % [
		db.quote(export_id), db.quote(job_id), db.quote(project_id), now,
		db.quote(expected_paths["bundle_relpath"]),
		db.quote(expected_paths["video_relpath"]),
		db.quote(expected_paths["thumbnail_relpath"]),
		db.quote(expected_paths["metadata_relpath"]),
		db.quote(expected_paths["provenance_relpath"]),
		db.quote(expected_paths["build_manifest_relpath"]),
	])
	if not bool(result.get("ok", false)):
		return false
	var rows = db.query("SELECT id, job_id, project_id, bundle_relpath, video_relpath, thumbnail_relpath, metadata_relpath, provenance_relpath, build_manifest_relpath FROM exports WHERE id = %s LIMIT 1;" % db.quote(export_id))
	if rows.is_empty() or String(rows[0].get("job_id", "")) != job_id or String(rows[0].get("project_id", "")) != project_id:
		return false
	for key in expected_paths:
		if String(rows[0].get(key, "")) != String(expected_paths[key]):
			return false
	return true

func _expected_export_paths(bundle_dir: String) -> Dictionary:
	var root = String(paths.get("root", ""))
	return {
		"bundle_relpath": _relative_to(root, bundle_dir),
		"video_relpath": _relative_to(root, bundle_dir.path_join("video.mp4")),
		"thumbnail_relpath": _relative_to(root, bundle_dir.path_join("thumbnail.png")),
		"metadata_relpath": _relative_to(root, bundle_dir.path_join("metadata.json")),
		"provenance_relpath": _relative_to(root, bundle_dir.path_join("provenance.json")),
		"build_manifest_relpath": _relative_to(root, bundle_dir.path_join("build_manifest.json")),
	}

func _is_complete_bundle(bundle_dir: String, export_id: String, project_id: String, job_manifest_path: String, binding: String) -> bool:
	var required_paths = ["video.mp4", "thumbnail.png", "metadata.json", "provenance.json", "build_manifest.json"]
	for relative_path in required_paths:
		var path = bundle_dir.path_join(relative_path)
		if _path_has_symlink_component(path) or not FileAccess.file_exists(path) or _file_size(path) <= 0:
			return false
	var manifest: Variant = JSON.parse_string(FileAccess.get_file_as_string(bundle_dir.path_join("build_manifest.json")))
	if typeof(manifest) != TYPE_DICTIONARY:
		return false
	var snapshot_value: Variant = manifest.get("snapshot", {})
	if typeof(snapshot_value) != TYPE_DICTIONARY:
		return false
	var snapshot: Dictionary = snapshot_value
	if String(snapshot.get("export_id", "")) != export_id or String(snapshot.get("project_id", "")) != project_id:
		return false
	var job_manifest: Variant = JSON.parse_string(FileAccess.get_file_as_string(job_manifest_path))
	if typeof(job_manifest) != TYPE_DICTIONARY:
		return false
	var receipt_value: Variant = job_manifest.get("published_bundle", {})
	if typeof(receipt_value) != TYPE_DICTIONARY:
		return false
	var receipt: Dictionary = receipt_value
	if String(receipt.get("export_id", "")) != export_id or String(receipt.get("project_id", "")) != project_id or String(receipt.get("resume_binding", "")) != binding:
		return false
	var hashes_value: Variant = receipt.get("files", {})
	var outputs_value: Variant = manifest.get("outputs", {})
	if typeof(hashes_value) != TYPE_DICTIONARY or typeof(outputs_value) != TYPE_DICTIONARY:
		return false
	var outputs: Dictionary = outputs_value
	var manifest_integrity_value: Variant = outputs.get("integrity", {})
	if typeof(manifest_integrity_value) != TYPE_DICTIONARY:
		return false
	var hashes: Dictionary = hashes_value
	var manifest_integrity: Dictionary = manifest_integrity_value
	for relative_path in required_paths:
		var expected_hash = String(hashes.get(relative_path, ""))
		if expected_hash.length() != 64 or not expected_hash.is_valid_hex_number(false):
			return false
		if _hash_file(bundle_dir.path_join(relative_path)) != expected_hash:
			return false
		if relative_path != "build_manifest.json" and String(manifest_integrity.get(relative_path, "")) != expected_hash:
			return false
	return true

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
	thumbnail: String,
	job_manifest_path: String,
	binding: String
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

	var source_video_hash = _hash_file(final_video)
	var source_thumbnail_hash = _hash_file(thumbnail)
	if source_video_hash == "" or source_thumbnail_hash == "":
		return {"ok": false, "error": "E_BUNDLE_WRITE_FAILED", "message": "Could not verify source export outputs"}
	if DirAccess.copy_absolute(final_video, bundle_tmp.path_join("video.mp4")) != OK:
		return {"ok": false, "error": "E_BUNDLE_WRITE_FAILED", "message": "Could not stage video in export bundle"}
	if _hash_file(bundle_tmp.path_join("video.mp4")) != source_video_hash:
		return {"ok": false, "error": "E_BUNDLE_WRITE_FAILED", "message": "Staged video hash differs from source output"}
	if DirAccess.copy_absolute(thumbnail, bundle_tmp.path_join("thumbnail.png")) != OK:
		return {"ok": false, "error": "E_BUNDLE_WRITE_FAILED", "message": "Could not stage thumbnail in export bundle"}
	if _hash_file(bundle_tmp.path_join("thumbnail.png")) != source_thumbnail_hash:
		return {"ok": false, "error": "E_BUNDLE_WRITE_FAILED", "message": "Staged thumbnail hash differs from source output"}
	if not _write_json_atomic(bundle_tmp.path_join("metadata.json"), metadata):
		return {"ok": false, "error": "E_BUNDLE_WRITE_FAILED", "message": "Could not stage export metadata"}
	if not _write_json_atomic(bundle_tmp.path_join("provenance.json"), provenance):
		return {"ok": false, "error": "E_BUNDLE_WRITE_FAILED", "message": "Could not stage export provenance"}
	var hashes = {}
	for relative_path in ["video.mp4", "thumbnail.png", "metadata.json", "provenance.json"]:
		var path = bundle_tmp.path_join(relative_path)
		var digest = _hash_file(path)
		if digest == "":
			return {"ok": false, "error": "E_BUNDLE_WRITE_FAILED", "message": "Could not hash staged export content"}
		hashes[relative_path] = digest
	build_manifest["outputs"]["integrity"] = hashes
	if not _write_json_atomic(bundle_tmp.path_join("build_manifest.json"), build_manifest):
		return {"ok": false, "error": "E_BUNDLE_WRITE_FAILED", "message": "Could not stage build manifest"}
	hashes["build_manifest.json"] = _hash_file(bundle_tmp.path_join("build_manifest.json"))
	if hashes["build_manifest.json"] == "":
		return {"ok": false, "error": "E_BUNDLE_WRITE_FAILED", "message": "Could not hash build manifest"}
	var job_manifest: Variant = JSON.parse_string(FileAccess.get_file_as_string(job_manifest_path))
	if typeof(job_manifest) != TYPE_DICTIONARY or String(job_manifest.get("resume_binding", "")) != binding:
		return {"ok": false, "error": "E_JOB_MANIFEST_INVALID", "message": "Job manifest changed before bundle publication"}
	job_manifest["published_bundle"] = {
		"export_id": export_id,
		"project_id": String(project.get("id", "")),
		"resume_binding": binding,
		"files": hashes,
	}
	if not _write_json_atomic(job_manifest_path, job_manifest):
		return {"ok": false, "error": "E_JOB_MANIFEST_WRITE_FAILED", "message": "Could not persist bundle integrity receipt"}

	if DirAccess.dir_exists_absolute(bundle_dir):
		return {"ok": false, "error": "E_BUNDLE_ALREADY_EXISTS", "message": "Refusing to replace an existing export bundle"}
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

func _write_json_atomic(path: String, payload: Dictionary) -> bool:
	var temporary_path = path + ".%s.partial" % VasIds.new_id("write")
	var serialized = JSON.stringify(payload, "\t")
	var expected_bytes = serialized.to_utf8_buffer()
	var file = FileAccess.open(temporary_path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(serialized)
	var store_error = file.get_error()
	file.flush()
	var flush_error = file.get_error()
	file.close()
	if store_error != OK or flush_error != OK:
		DirAccess.remove_absolute(temporary_path)
		return false
	if _atomic_write_after_stage.is_valid():
		_atomic_write_after_stage.call(temporary_path)

	var readback = FileAccess.open(temporary_path, FileAccess.READ)
	if readback == null:
		DirAccess.remove_absolute(temporary_path)
		return false
	var actual_bytes = readback.get_buffer(expected_bytes.size())
	var read_error = readback.get_error()
	var exact_size = readback.get_length() == expected_bytes.size()
	readback.close()
	if read_error != OK or not exact_size or actual_bytes != expected_bytes:
		DirAccess.remove_absolute(temporary_path)
		return false

	if DirAccess.rename_absolute(temporary_path, path) != OK:
		DirAccess.remove_absolute(temporary_path)
		return false
	return true

func _segment_is_reusable(segment_path: String, manifest_path: String, expected: Dictionary) -> bool:
	if _path_has_symlink_component(segment_path) or _path_has_symlink_component(manifest_path):
		return false
	if not FileAccess.file_exists(segment_path) or not FileAccess.file_exists(manifest_path):
		return false
	var value: Variant = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	if typeof(value) != TYPE_DICTIONARY:
		return false
	var manifest: Dictionary = value
	var recorded_hash = String(manifest.get("sha256", ""))
	if recorded_hash.length() != 64 or not recorded_hash.is_valid_hex_number(false):
		return false
	if int(manifest.get("index", -1)) != int(expected.get("index", -2)):
		return false
	if int(manifest.get("start_frame", -1)) != int(expected.get("start_frame", -2)):
		return false
	if int(manifest.get("frame_count", -1)) != int(expected.get("frame_count", -2)):
		return false
	var actual_hash = _hash_file(segment_path)
	return actual_hash != "" and actual_hash == recorded_hash

func _resume_binding(
	project: Dictionary,
	audio_asset_id: String,
	actual_audio_hash: String,
	analysis: Dictionary,
	template: Dictionary,
	draft: bool,
	simulate_only: bool,
	fps: int,
	width: int,
	height: int,
	duration_frames: int,
	segments: Array
) -> String:
	var exporter_source_hash = _renderer_resource_hash("res://src/core/export_service.gd")
	var ffmpeg_adapter_source_hash = _renderer_resource_hash("res://src/adapters/ffmpeg_adapter.gd")
	var ffmpeg_build_hash = _ffmpeg_build_hash()
	var ffmpeg_version = ffmpeg.ffmpeg_version()
	var godot_version = _godot_version_string()
	if exporter_source_hash == "" or ffmpeg_adapter_source_hash == "" or ffmpeg_build_hash == "" or ffmpeg_version == "unknown" or godot_version == "":
		return ""
	var snapshot = {
		"schema_version": 2,
		"project": project,
		"audio_asset_id": audio_asset_id,
		"audio_sha256": actual_audio_hash,
		"analysis": analysis,
		"template": template,
		"draft": draft,
		"simulate_only": simulate_only,
		"fps": fps,
		"width": width,
		"height": height,
		"duration_frames": duration_frames,
		"segments": segments,
		"godot_version": godot_version,
		"ffmpeg_version": ffmpeg_version,
		"ffmpeg_build_sha256": ffmpeg_build_hash,
		"encoder": ffmpeg.preferred_h264_encoder(),
		"export_service_sha256": exporter_source_hash,
		"ffmpeg_adapter_sha256": ffmpeg_adapter_source_hash,
	}
	return _sha256_text(JSON.stringify(_canonicalize(snapshot)))

func _renderer_resource_hash(source_path: String) -> String:
	# Compiled Godot exports remap `.gd` resources to `.gdc` and omit source.
	# Follow that mapping when present so the resume binding fingerprints the
	# executable script bytes, not a stale source copy shipped alongside them.
	var remap_path = source_path + ".remap"
	if FileAccess.file_exists(remap_path):
		var remap := ConfigFile.new()
		if remap.load(remap_path) != OK:
			return ""
		var runtime_path = String(remap.get_value("remap", "path", ""))
		if runtime_path != "":
			if not runtime_path.begins_with("res://"):
				return ""
			var runtime_hash = _hash_file(runtime_path)
			return "compiled:" + runtime_hash if runtime_hash != "" else ""
		return ""

	var source_hash = _hash_file(source_path)
	if source_hash != "":
		return "source:" + source_hash
	return ""

func _canonicalize(value: Variant) -> Variant:
	if typeof(value) == TYPE_DICTIONARY:
		var result = {}
		var keys: Array = value.keys()
		keys.sort()
		for key in keys:
			result[key] = _canonicalize(value[key])
		return result
	if typeof(value) == TYPE_ARRAY:
		var result: Array = []
		for item in value:
			result.append(_canonicalize(item))
		return result
	return value

func _ffmpeg_build_hash() -> String:
	var output: Array = []
	var code = OS.execute(ffmpeg.ffmpeg_bin, PackedStringArray(["-version"]), output, true)
	if code != 0 or output.is_empty():
		return ""
	return _sha256_text("\n".join(output))

func _is_safe_job_id(value: String) -> bool:
	return _matches_id(value, "job_")

func _is_safe_export_id(value: String) -> bool:
	return _matches_id(value, "export_")

func _matches_id(value: String, prefix: String) -> bool:
	if not value.begins_with(prefix):
		return false
	var suffix = value.substr(prefix.length())
	if suffix.length() != 16:
		return false
	for char in suffix:
		if not ((char >= "a" and char <= "f") or (char >= "0" and char <= "9")):
			return false
	return true

func _path_has_symlink_component(path: String) -> bool:
	var current = path.simplify_path()
	while current != "" and current != ".":
		var output: Array = []
		var code = OS.execute("/usr/bin/test", PackedStringArray(["-L", current]), output, true)
		if code == 0:
			return true
		var parent = current.get_base_dir()
		if parent == current or parent == "":
			break
		current = parent
	return false

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
