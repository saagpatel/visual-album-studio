extends SceneTree

const ExportService = preload("res://src/core/export_service.gd")
const PROCESS_EXITED := 0
const PROCESS_MATCHED := 1
const PROCESS_UNKNOWN := 2
const PROCESS_ZOMBIE := 3

class FixtureDb extends RefCounted:
	var audio_sha256 := "fixture-audio-sha256"
	var exports_written: Array[String] = []
	var exports: Dictionary = {}
	var fail_next_insert := false

	func quote(value: String) -> String:
		return "'%s'" % value.replace("'", "''")

	func query(sql: String) -> Array:
		if sql.contains("FROM assets"):
			return [{"library_relpath": "library/audio.wav", "sha256": audio_sha256}]
		if sql.contains("FROM exports"):
			var parts := sql.split("'")
			if parts.size() >= 2 and exports.has(parts[1]):
				return [exports[parts[1]].duplicate()]
		return []

	func exec(sql: String) -> Dictionary:
		exports_written.append(sql)
		if fail_next_insert:
			fail_next_insert = false
			return {"ok": false}
		var pattern := RegEx.new()
		pattern.compile("VALUES \\(\\s*'([^']+)',\\s*'([^']+)',\\s*'([^']+)',\\s*[0-9]+,\\s*'([^']+)',\\s*'([^']+)',\\s*'([^']+)',\\s*'([^']+)',\\s*'([^']+)',\\s*'([^']+)'")
		var found := pattern.search(sql)
		if found == null:
			return {"ok": false}
		var row := {
			"id": found.get_string(1),
			"job_id": found.get_string(2),
			"project_id": found.get_string(3),
			"bundle_relpath": found.get_string(4),
			"video_relpath": found.get_string(5),
			"thumbnail_relpath": found.get_string(6),
			"metadata_relpath": found.get_string(7),
			"provenance_relpath": found.get_string(8),
			"build_manifest_relpath": found.get_string(9),
		}
		exports[row["id"]] = row
		return {"ok": true}

class FixtureAssets extends RefCounted:
	func validate_production_allowed(_audio_asset_id: String) -> Dictionary:
		return {"allowed": true}

	func provenance_json(_audio_asset_id: String, _template_id: String, _preset_id: String, _mapping_id: String, _seed: int) -> Dictionary:
		return {"attribution_block": "synthetic fixture"}

class FixtureFfmpeg extends RefCounted:
	var ffmpeg_bin := "ffmpeg"
	var fail_second_segment_once := true
	var fail_concat_once := false
	var fail_thumbnail_once := false
	var segment_encodes: Dictionary = {}
	var calls: Array[String] = []
	var use_real_media := false
	var on_segment_encode: Callable
	var pause_on_second_segment := false
	var concurrent_result: Dictionary = {}

	func preferred_h264_encoder() -> String:
		return "libx264" if use_real_media else "fixture-h264"

	func ffmpeg_version() -> String:
		return "fixture-ffmpeg-1"

	func run(args: PackedStringArray) -> Dictionary:
		var target := String(args[args.size() - 1])
		calls.append(target)
		if args.has("-framerate"):
			var segment_index := "000" if target.contains("/000/") else "001"
			segment_encodes[segment_index] = int(segment_encodes.get(segment_index, 0)) + 1
			if on_segment_encode.is_valid():
				on_segment_encode.call(target)
				on_segment_encode = Callable()
			if segment_index == "001" and pause_on_second_segment:
				var fixture_root := OS.get_environment("VAS_RESUME_FIXTURE_ROOT")
				var parts := target.split("/")
				var jobs_index := parts.find("jobs")
				if use_real_media:
					# Throttle frames by presentation time so a real FFmpeg child remains
					# active through the separate contender check and immediate pre-kill assertion.
					var active_args := args.duplicate()
					var filter_index := active_args.find("-pix_fmt")
					if filter_index < 0:
						return {"ok": false, "code": 2, "output": "could not locate FFmpeg output options for realtime filter"}
					# The crash-only encoder flushes low-latency packets so the fixture can
					# prove real media bytes and FFmpeg progress before holding the PID.
					active_args.insert(filter_index, "1")
					active_args.insert(filter_index, "-flush_packets")
					active_args.insert(filter_index, "zerolatency")
					active_args.insert(filter_index, "-tune")
					active_args.insert(filter_index, "realtime")
					active_args.insert(filter_index, "-vf")
					active_args.insert(0, fixture_root.path_join("child-ffmpeg-progress.txt"))
					active_args.insert(0, "-progress")
					var ffmpeg_pid := OS.create_process("ffmpeg", active_args, false)
					if ffmpeg_pid <= 0:
						return {"ok": false, "code": 2, "output": "could not launch owned FFmpeg child"}
					var ffmpeg_pid_file := FileAccess.open(fixture_root.path_join("child-ffmpeg-pid.txt"), FileAccess.WRITE)
					ffmpeg_pid_file.store_string(str(ffmpeg_pid))
					ffmpeg_pid_file.close()
					var marker := fixture_root.path_join("child-paused-job.json")
					var marker_file := FileAccess.open(marker, FileAccess.WRITE)
					marker_file.store_string(JSON.stringify({"job_id": String(parts[jobs_index + 1]), "godot_pid": OS.get_process_id(), "ffmpeg_pid": ffmpeg_pid, "progress_path": fixture_root.path_join("child-ffmpeg-progress.txt"), "segment_path": target}))
					marker_file.close()
					while OS.is_process_running(ffmpeg_pid):
						OS.delay_msec(10)
					return {"ok": true, "code": 0, "output": "owned FFmpeg child completed"}
				var marker := fixture_root.path_join("child-paused-job.json")
				var marker_file := FileAccess.open(marker, FileAccess.WRITE)
				marker_file.store_string(JSON.stringify({"job_id": String(parts[jobs_index + 1]), "godot_pid": OS.get_process_id(), "ffmpeg_pid": 0}))
				marker_file.close()
				OS.delay_msec(30000)
			if segment_index == "001" and fail_second_segment_once:
				fail_second_segment_once = false
				return {"ok": false, "code": 1, "output": "synthetic interruption"}
		if fail_concat_once and args.has("-f") and args.has("concat"):
			fail_concat_once = false
			return {"ok": false, "code": 1, "output": "synthetic concat failure"}
		if fail_thumbnail_once and args.has("-vframes"):
			fail_thumbnail_once = false
			return {"ok": false, "code": 1, "output": "synthetic thumbnail failure"}
		if use_real_media:
			var output: Array = []
			var code := OS.execute("ffmpeg", args, output, true)
			return {"ok": code == 0, "code": code, "output": "\n".join(output)}
		var file := FileAccess.open(target, FileAccess.WRITE)
		if file == null:
			return {"ok": false, "code": 2, "output": "fixture could not write output"}
		file.store_buffer(("fixture-output:%s" % target).to_utf8_buffer())
		file.close()
		return {"ok": true, "code": 0, "output": ""}

func _init() -> void:
	if OS.get_environment("VAS_RESUME_CHILD_MODE") == "1":
		quit(_run_crash_child())
	elif OS.get_environment("VAS_RESUME_CONTENDER_MODE") == "1":
		quit(_run_lock_contender())
	else:
		quit(_run())

func _run() -> int:
	var fixture_root := OS.get_environment("VAS_RESUME_FIXTURE_ROOT")
	var allowed_fixture_root := fixture_root.begins_with("/private/tmp/vas-resume-fixture-") or fixture_root.begins_with("/tmp/vas-resume-fixture-")
	if not allowed_fixture_root:
		return _fail("VAS_RESUME_FIXTURE_ROOT must name a unique fixture directory under /private/tmp or /tmp")
	if FileAccess.file_exists(fixture_root):
		return _fail("VAS_RESUME_FIXTURE_ROOT must be a directory")
	if DirAccess.dir_exists_absolute(fixture_root):
		var root_dir := DirAccess.open(fixture_root)
		if root_dir == null:
			return _fail("could not inspect the supplied fixture directory")

		root_dir.list_dir_begin()
		var first_entry := root_dir.get_next()
		var empty := first_entry == ""
		root_dir.list_dir_end()
		if not empty:
			return _fail("VAS_RESUME_FIXTURE_ROOT must be empty; refusing to clear existing data")
	else:
		DirAccess.make_dir_recursive_absolute(fixture_root)
	for child in ["tmp/jobs", "exports", "out/library"]:
		DirAccess.make_dir_recursive_absolute(fixture_root.path_join(child))
	var use_real_media := OS.get_environment("VAS_RESUME_USE_REAL_FFMPEG") == "1"
	if use_real_media:
		var audio_path := fixture_root.path_join("out/library/audio.wav")
		var audio_output: Array = []
		var audio_code := OS.execute("ffmpeg", PackedStringArray([
			"-y", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=65",
			"-ac", "2", audio_path,
		]), audio_output, true)
		if audio_code != 0:
			print("\n".join(audio_output))
			return _fail("could not create isolated 61-second synthetic audio input")
	else:
		var fixture_audio := FileAccess.open(fixture_root.path_join("out/library/audio.wav"), FileAccess.WRITE)
		if fixture_audio == null:
			return _fail("could not write synthetic audio hash input")
		fixture_audio.store_string("synthetic audio input for orchestration coverage")
		fixture_audio.close()

	var project := _project()
	var analysis := {"tempo_bpm": 120.0, "analysis_version": "fixture-analysis-1"}
	var template := {"schema_version": 1, "metadata": {"title": "fixture", "description": "fixture", "tags": []}}
	var db := FixtureDb.new()
	var assets := FixtureAssets.new()
	var ffmpeg := FixtureFfmpeg.new()
	ffmpeg.use_real_media = use_real_media
	var paths := {
		"root": fixture_root,
		"out_dir": fixture_root.path_join("out"),
		"tmp_dir": fixture_root.path_join("tmp"),
		"exports_dir": fixture_root.path_join("exports"),
	}
	var exporter := ExportService.new(db, paths, ffmpeg, assets)
	var atomic_destination := fixture_root.path_join("tmp/atomic_replace.json")
	var old_manifest := FileAccess.open(atomic_destination, FileAccess.WRITE)
	old_manifest.store_string("{\"value\":\"old\"}")
	old_manifest.close()
	if not _assert(exporter._write_json_atomic(atomic_destination, {"value": "new"}), "atomic manifest replacement must succeed"):
		return 1
	if not _assert(JSON.parse_string(FileAccess.get_file_as_string(atomic_destination)).get("value", "") == "new", "atomic replacement must publish the new manifest"):
		return 1
	var failed_write_destination := fixture_root.path_join("tmp/failed_atomic_write.json")
	var prior_manifest_bytes := "{\"job_id\":\"fixture-prior\",\"resume_binding\":\"prior-binding\"}\n"
	var prior_manifest := FileAccess.open(failed_write_destination, FileAccess.WRITE)
	if not _assert(prior_manifest != null, "failed-write fixture must create its prior manifest"):
		return 1
	prior_manifest.store_string(prior_manifest_bytes)
	prior_manifest.close()
	var truncated_temp_path := ""
	var truncation_fault := {"opened": false}
	exporter._atomic_write_after_stage = func(temp_path: String) -> void:
		truncated_temp_path = temp_path
		var truncated_temp := FileAccess.open(temp_path, FileAccess.WRITE)
		if truncated_temp == null:
			return
		truncation_fault["opened"] = true
		truncated_temp.store_string("{")
		truncated_temp.flush()
		truncated_temp.close()
	var failed_manifest_write := exporter._write_json_atomic(failed_write_destination, {"job_id": "fixture-replacement"})
	exporter._atomic_write_after_stage = Callable()
	if not _assert(bool(truncation_fault["opened"]), "failed-write fixture must truncate only the staged temporary manifest"):
		return 1
	if not _assert(not failed_manifest_write, "atomic manifest write must reject a truncated staged temporary file"):
		return 1
	if not _assert(FileAccess.get_file_as_string(failed_write_destination).to_utf8_buffer() == prior_manifest_bytes.to_utf8_buffer(), "failed atomic write must preserve the prior manifest byte-for-byte"):
		return 1
	if not _assert(not FileAccess.file_exists(truncated_temp_path), "failed atomic write must remove the rejected temporary file"):
		return 1
	var simulated := exporter.export_project(project, "fixture-audio", analysis, template, false, true)
	if not _assert(not simulated.has("error"), "simulated export must finalize in its synthetic fixture"):
		print(simulated)
		return 1
	var simulated_job_id := String(simulated.get("job_id", ""))
	var calls_before_simulated_mode_mismatch := ffmpeg.calls.size()
	var simulated_as_real := exporter.resume_export(simulated_job_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(String(simulated_as_real.get("error", "")) == "E_RESUME_INPUT_MISMATCH", "a finalized simulated job must reject resume in real mode"):
		print(simulated_as_real)
		return 1
	if not _assert(ffmpeg.calls.size() == calls_before_simulated_mode_mismatch, "simulated-to-real mismatch must be rejected before invoking FFmpeg"):
		return 1
	ffmpeg.on_segment_encode = func(target_path: String) -> void:
		var pieces := target_path.split("/")
		var jobs_index := pieces.find("jobs")
		var active_job_id := String(pieces[jobs_index + 1])
		ffmpeg.concurrent_result = exporter.resume_export(active_job_id, project, "fixture-audio", analysis, template, false, false)

	var interrupted := exporter.export_project(project, "fixture-audio", analysis, template, false, false)
	if not _assert(String(interrupted.get("error", "")) == "E_FFMPEG_FAILED", "first run must stop at injected second-segment failure"):
		print(interrupted)
		return 1
	var job_id := String(interrupted.get("job_id", ""))
	if not _assert(job_id != "", "interrupted result must identify its resumable job"):
		return 1
	var workspace := fixture_root.path_join("tmp/jobs").path_join(job_id)
	var segment_zero := workspace.path_join("segments/000/segment.mp4")
	if not _assert(FileAccess.file_exists(segment_zero), "first completed segment must survive interruption"):
		return 1
	var first_segment_calls := int(ffmpeg.segment_encodes.get("000", 0))
	if not _assert(first_segment_calls == 1, "first segment encoded once before interruption"):
		return 1
	if not _assert(String(ffmpeg.concurrent_result.get("error", "")) == "E_RESUME_LOCKED", "a concurrent resume must be blocked while a new export owns its lock"):
		print(ffmpeg.concurrent_result)
		return 1
	var calls_before_real_mode_mismatch := ffmpeg.calls.size()
	var interrupted_real_as_simulated := exporter.resume_export(job_id, project, "fixture-audio", analysis, template, false, true)
	if not _assert(String(interrupted_real_as_simulated.get("error", "")) == "E_RESUME_INPUT_MISMATCH", "an interrupted real job must reject resume in simulated mode"):
		print(interrupted_real_as_simulated)
		return 1
	if not _assert(ffmpeg.calls.size() == calls_before_real_mode_mismatch, "real-to-simulated mismatch must be rejected before invoking FFmpeg"):
		return 1

	var changed_project := project.duplicate(true)
	changed_project["seed"] = int(changed_project["seed"]) + 1
	var calls_before_mismatch := ffmpeg.calls.size()
	var mismatch := exporter.resume_export(job_id, changed_project, "fixture-audio", analysis, template, false, false)
	if not _assert(String(mismatch.get("error", "")) == "E_RESUME_INPUT_MISMATCH", "changed render input must fail closed"):
		print(mismatch)
		return 1
	if not _assert(ffmpeg.calls.size() == calls_before_mismatch, "mismatch must be rejected before rendering"):
		return 1

	var resumed := exporter.resume_export(job_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(not resumed.has("error"), "same-input resume must finish"):
		print(resumed)
		return 1
	if not _assert(resumed.get("job_id", "") == job_id, "resume must preserve the job ID"):
		return 1
	if not _assert(resumed.get("export_id", "") == interrupted.get("export_id", ""), "resume must preserve the export ID"):
		return 1
	if not _assert(int(ffmpeg.segment_encodes.get("000", 0)) == first_segment_calls, "valid first segment must be reused"):
		return 1
	if not _assert(int(ffmpeg.segment_encodes.get("001", 0)) == 2, "failed segment must be retried once"):
		return 1
	if not _assert(FileAccess.file_exists(String(resumed.get("bundle_dir", "")).path_join("build_manifest.json")), "completed resume must publish a bundle manifest"):
		return 1
	var repaired_export_id := String(resumed.get("export_id", ""))
	var repaired_bundle_dir := String(resumed.get("bundle_dir", ""))
	if not _assert(db.exports.has(repaired_export_id), "successful export must register its database row"):
		return 1
	var durable_manifest_path := repaired_bundle_dir.path_join("build_manifest.json")
	var durable_manifest_contents := FileAccess.get_file_as_string(durable_manifest_path)
	db.exports.erase(repaired_export_id)
	db.fail_next_insert = true
	var failed_repair := exporter.resume_export(job_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(String(failed_repair.get("error", "")) == "E_EXPORT_REGISTRATION_FAILED", "database repair failure must remain visible"):
		print(failed_repair)
		return 1
	if not _assert(not db.exports.has(repaired_export_id), "failed registration must not fabricate a database row"):
		return 1
	var corrupt_manifest := FileAccess.open(durable_manifest_path, FileAccess.WRITE)
	corrupt_manifest.store_string("{}")
	corrupt_manifest.close()
	var invalid_bundle := exporter.resume_export(job_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(String(invalid_bundle.get("error", "")) == "E_RESUME_BUNDLE_INCOMPLETE", "an invalid finalized bundle must not be registered"):
		print(invalid_bundle)
		return 1
	if not _assert(not db.exports.has(repaired_export_id), "invalid bundle must leave database repair pending"):
		return 1
	var restored_manifest := FileAccess.open(durable_manifest_path, FileAccess.WRITE)
	restored_manifest.store_string(durable_manifest_contents)
	restored_manifest.close()
	var repaired_bundle := exporter.resume_export(job_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(not repaired_bundle.has("error") and db.exports.has(repaired_export_id), "valid finalized bundle must repair a missing database row on retry"):
		print(repaired_bundle)
		return 1

	# A second interrupted job proves that the on-disk segment hash is checked,
	# rather than trusting a matching job manifest after its media bytes change.
	ffmpeg.fail_second_segment_once = true
	var tamper_job := exporter.export_project(project, "fixture-audio", analysis, template, false, false)
	if not _assert(tamper_job.has("error"), "tamper control setup must interrupt on segment two"):
		return 1
	var tamper_id := String(tamper_job.get("job_id", ""))
	var tamper_path := fixture_root.path_join("tmp/jobs").path_join(tamper_id).path_join("segments/000/segment.mp4")
	var tampered := FileAccess.open(tamper_path, FileAccess.WRITE)
	if tampered == null:
		return _fail("could not alter owned synthetic segment fixture")
	tampered.store_string("tampered media bytes")
	tampered.close()
	var zero_calls_before := int(ffmpeg.segment_encodes.get("000", 0))
	var tamper_resume := exporter.resume_export(tamper_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(not tamper_resume.has("error"), "resume after segment corruption must recover"):
		print(tamper_resume)
		return 1
	if not _assert(int(ffmpeg.segment_encodes.get("000", 0)) == zero_calls_before + 1, "corrupted segment must be re-encoded"):
		return 1

	if not _run_abrupt_stop_control(fixture_root, project, analysis, template, db):
		return 1
	if not _run_post_render_failure_controls(fixture_root, project, analysis, template):
		return 1

	print("Phase 1 resume integration passed: interruption, same-job recovery, input mismatch, post-render failures, and segment tampering")
	return 0

func _run_post_render_failure_controls(fixture_root: String, project: Dictionary, analysis: Dictionary, template: Dictionary) -> bool:
	var paths := {
		"root": fixture_root,
		"out_dir": fixture_root.path_join("out"),
		"tmp_dir": fixture_root.path_join("tmp"),
		"exports_dir": fixture_root.path_join("exports"),
	}
	var concat_db := FixtureDb.new()
	var concat_ffmpeg := FixtureFfmpeg.new()
	concat_ffmpeg.fail_second_segment_once = false
	concat_ffmpeg.fail_concat_once = true
	var concat_exporter := ExportService.new(concat_db, paths, concat_ffmpeg, FixtureAssets.new())
	var concat_failure := concat_exporter.export_project(project, "fixture-audio", analysis, template, false, false)
	if not _assert(String(concat_failure.get("error", "")) == "E_FFMPEG_FAILED", "post-render concat failure must retain its error classification"):
		print(concat_failure)
		return false
	var concat_details: Variant = concat_failure.get("details", {})
	if not _assert(typeof(concat_details) == TYPE_DICTIONARY and int(concat_details.get("code", -1)) == 1 and String(concat_details.get("output", "")) == "synthetic concat failure", "concat failure must preserve nested FFmpeg details"):
		print(concat_failure)
		return false
	var concat_job_id := String(concat_failure.get("job_id", ""))
	var concat_export_id := String(concat_failure.get("export_id", ""))
	if not _assert(concat_job_id != "" and concat_export_id != "", "concat failure must return both resumable job and export IDs"):
		print(concat_failure)
		return false
	var concat_segment_calls := concat_ffmpeg.segment_encodes.duplicate(true)
	var concat_resume := concat_exporter.resume_export(concat_job_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(not concat_resume.has("error") and concat_resume.get("job_id", "") == concat_job_id and concat_resume.get("export_id", "") == concat_export_id, "concat failure must resume by returned job ID and preserve the export ID"):
		print(concat_resume)
		return false
	if not _assert(concat_ffmpeg.segment_encodes == concat_segment_calls, "resume after concat failure must reuse every completed segment"):
		return false
	var thumbnail_db := FixtureDb.new()
	var thumbnail_ffmpeg := FixtureFfmpeg.new()
	thumbnail_ffmpeg.fail_second_segment_once = false
	thumbnail_ffmpeg.fail_thumbnail_once = true
	var thumbnail_exporter := ExportService.new(thumbnail_db, paths, thumbnail_ffmpeg, FixtureAssets.new())
	var thumbnail_failure := thumbnail_exporter.export_project(project, "fixture-audio", analysis, template, false, false)
	if not _assert(String(thumbnail_failure.get("error", "")) == "E_FFMPEG_FAILED", "post-render thumbnail failure must retain its error classification"):
		print(thumbnail_failure)
		return false
	var thumbnail_details: Variant = thumbnail_failure.get("details", {})
	if not _assert(typeof(thumbnail_details) == TYPE_DICTIONARY and int(thumbnail_details.get("code", -1)) == 1 and String(thumbnail_details.get("output", "")) == "synthetic thumbnail failure", "thumbnail failure must preserve nested FFmpeg details"):
		print(thumbnail_failure)
		return false
	var thumbnail_job_id := String(thumbnail_failure.get("job_id", ""))
	var thumbnail_export_id := String(thumbnail_failure.get("export_id", ""))
	if not _assert(thumbnail_job_id != "" and thumbnail_export_id != "", "thumbnail failure must return both resumable job and export IDs"):
		print(thumbnail_failure)
		return false
	var thumbnail_segment_calls := thumbnail_ffmpeg.segment_encodes.duplicate(true)
	var thumbnail_resume := thumbnail_exporter.resume_export(thumbnail_job_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(not thumbnail_resume.has("error") and thumbnail_resume.get("job_id", "") == thumbnail_job_id and thumbnail_resume.get("export_id", "") == thumbnail_export_id, "thumbnail failure must resume by returned job ID and preserve the export ID"):
		print(thumbnail_resume)
		return false
	if not _assert(thumbnail_ffmpeg.segment_encodes == thumbnail_segment_calls, "resume after thumbnail failure must reuse every completed segment"):
		return false

	var bundle_db := FixtureDb.new()
	var bundle_ffmpeg := FixtureFfmpeg.new()
	bundle_ffmpeg.fail_second_segment_once = false
	var bundle_exporter := ExportService.new(bundle_db, paths, bundle_ffmpeg, FixtureAssets.new())
	var bundle_fault := {"triggered": false}
	bundle_exporter._atomic_write_after_stage = func(temp_path: String) -> void:
		if bundle_fault["triggered"] or not temp_path.get_file().begins_with("metadata.json."):
			return
		var staged_metadata := FileAccess.open(temp_path, FileAccess.WRITE)
		if staged_metadata == null:
			return
		bundle_fault["triggered"] = true
		staged_metadata.store_string("{")
		staged_metadata.flush()
		staged_metadata.close()
	var bundle_failure := bundle_exporter.export_project(project, "fixture-audio", analysis, template, false, false)
	bundle_exporter._atomic_write_after_stage = Callable()
	if not _assert(bool(bundle_fault["triggered"]), "bundle staging control must truncate its owned staged metadata file"):
		return false
	if not _assert(String(bundle_failure.get("error", "")) == "E_BUNDLE_WRITE_FAILED", "bundle staging failure must retain its error classification"):
		print(bundle_failure)
		return false
	var bundle_job_id := String(bundle_failure.get("job_id", ""))
	var bundle_export_id := String(bundle_failure.get("export_id", ""))
	if not _assert(bundle_job_id != "" and bundle_export_id != "", "bundle staging failure must return both resumable job and export IDs"):
		print(bundle_failure)
		return false
	var bundle_segment_calls := bundle_ffmpeg.segment_encodes.duplicate(true)
	var bundle_resume := bundle_exporter.resume_export(bundle_job_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(not bundle_resume.has("error") and bundle_resume.get("job_id", "") == bundle_job_id and bundle_resume.get("export_id", "") == bundle_export_id, "bundle staging failure must resume by returned job ID and preserve the export ID"):
		print(bundle_resume)
		return false
	if not _assert(bundle_ffmpeg.segment_encodes == bundle_segment_calls, "resume after bundle staging failure must reuse every completed segment"):
		return false
	return true

func _run_abrupt_stop_control(fixture_root: String, project: Dictionary, analysis: Dictionary, template: Dictionary, db: FixtureDb) -> bool:
	var use_real_media := OS.get_environment("VAS_RESUME_USE_REAL_FFMPEG") == "1"
	for marker_name in ["child-paused-job.json", "child-ffmpeg-pid.txt", "contender-result.json"]:
		var marker_path := fixture_root.path_join(marker_name)
		if FileAccess.file_exists(marker_path):
			DirAccess.remove_absolute(marker_path)
	var executable := OS.get_executable_path()
	var app_path := ProjectSettings.globalize_path("res://").trim_suffix("/")
	# `env` must exec Godot after applying the two child-only variables.
	var child_args := PackedStringArray([
		"VAS_RESUME_CHILD_MODE=1",
		"VAS_RESUME_FIXTURE_ROOT=" + fixture_root,
		executable,
		"--headless",
		"--path",
		app_path,
		"--script",
		"res://tests/phase1_resume_test.gd",
	])
	var child_pid := OS.create_process("/usr/bin/env", child_args, false)
	if child_pid <= 0:
		push_error("[FAIL] could not launch the isolated child Godot process")
		return false
	var marker := fixture_root.path_join("child-paused-job.json")
	var ffmpeg_pid := 0
	var deadline := Time.get_ticks_msec() + 20000
	while not FileAccess.file_exists(marker) and Time.get_ticks_msec() < deadline and _godot_process_state(child_pid) != PROCESS_EXITED:
		OS.delay_msec(50)
	if not FileAccess.file_exists(marker):
		var ffmpeg_pid_path := fixture_root.path_join("child-ffmpeg-pid.txt")
		if FileAccess.file_exists(ffmpeg_pid_path):
			ffmpeg_pid = int(FileAccess.get_file_as_string(ffmpeg_pid_path).strip_edges())
		_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
		push_error("[FAIL] child did not reach its synthetic second-segment pause")
		return false
	var child_info_value: Variant = JSON.parse_string(FileAccess.get_file_as_string(marker))
	if typeof(child_info_value) != TYPE_DICTIONARY:
		var ffmpeg_pid_path := fixture_root.path_join("child-ffmpeg-pid.txt")
		if FileAccess.file_exists(ffmpeg_pid_path):
			ffmpeg_pid = int(FileAccess.get_file_as_string(ffmpeg_pid_path).strip_edges())
		_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
		return _assert(false, "child marker must contain owned process identities")
	var child_info: Dictionary = child_info_value
	var job_id := String(child_info.get("job_id", ""))
	ffmpeg_pid = int(child_info.get("ffmpeg_pid", 0))
	if not _assert(int(child_info.get("godot_pid", -1)) == child_pid, "child marker must identify the owned Godot process"):
		_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
		return false
	var job_root := fixture_root.path_join("tmp/jobs")
	var lock_path := job_root.path_join(job_id + ".lock")
	var owner_path := lock_path.path_join("owner.json")
	if not _assert(FileAccess.file_exists(owner_path), "child export must own a durable lock while paused"):
		_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
		return false
	var owner: Variant = JSON.parse_string(FileAccess.get_file_as_string(owner_path))
	if not _assert(typeof(owner) == TYPE_DICTIONARY and int(owner.get("pid", -1)) == child_pid, "lock owner must identify the child process"):
		_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
		return false
	var segment_zero := job_root.path_join(job_id).path_join("segments/000/segment.mp4")
	var segment_zero_manifest := job_root.path_join(job_id).path_join("segments/000/segment.manifest.json")
	if not _assert(FileAccess.file_exists(segment_zero) and FileAccess.file_exists(segment_zero_manifest), "first segment must be durably encoded before the second FFmpeg process starts"):
		_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
		return false
	if use_real_media and not _assert(ffmpeg_pid > 0 and _ffmpeg_process_state(ffmpeg_pid, fixture_root) == PROCESS_MATCHED, "real crash control must observe the owned FFmpeg child actively encoding segment two"):
		_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
		return false
	if use_real_media:
		var progress_path := String(child_info.get("progress_path", ""))
		var segment_path := String(child_info.get("segment_path", ""))
		var progress_deadline := Time.get_ticks_msec() + 10000
		var saw_media_progress := false
		while not saw_media_progress and Time.get_ticks_msec() < progress_deadline and _ffmpeg_process_state(ffmpeg_pid, fixture_root) == PROCESS_MATCHED:
			var output_time_us := 0
			if FileAccess.file_exists(progress_path):
				for line in FileAccess.get_file_as_string(progress_path).split("\n"):
					if String(line).begins_with("out_time_us="):
						output_time_us = int(String(line).trim_prefix("out_time_us="))
			var partial_file := FileAccess.open(segment_path, FileAccess.READ)
			saw_media_progress = output_time_us > 0 and partial_file != null and partial_file.get_length() > 0
			if partial_file != null:
				partial_file.close()
			if not saw_media_progress:
				OS.delay_msec(25)
		if not _assert(saw_media_progress, "real FFmpeg must report nonzero output-time progress and write partial segment bytes before the crash window is held"):
			_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
			return false
		var stop_output: Array = []
		var stop_code := OS.execute("/bin/kill", PackedStringArray(["-STOP", str(ffmpeg_pid)]), stop_output, true)
		if not _assert(stop_code == 0 and _ffmpeg_process_state(ffmpeg_pid, fixture_root) == PROCESS_MATCHED, "test must pause the exact progress-confirmed FFmpeg PID while preserving its live file handle"):
			_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
			return false
	var contender_pid := _launch_lock_contender(fixture_root)
	if not _assert(contender_pid > 0, "separate contender process must launch while the exporter lock is held"):
		_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
		return false
	var contender_deadline := Time.get_ticks_msec() + 5000
	while OS.is_process_running(contender_pid) and Time.get_ticks_msec() < contender_deadline:
		OS.delay_msec(25)
	var contender_result_path := fixture_root.path_join("contender-result.json")
	if not _assert(not OS.is_process_running(contender_pid) and FileAccess.file_exists(contender_result_path), "separate contender must finish while the owner is paused"):
		_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
		if OS.is_process_running(contender_pid):
			_stop_owned_processes(contender_pid, 0, fixture_root)
		return false
	var contender_result: Variant = JSON.parse_string(FileAccess.get_file_as_string(contender_result_path))
	if not _assert(typeof(contender_result) == TYPE_DICTIONARY and String(contender_result.get("error", "")) == "E_RESUME_LOCKED", "a separate OS process must be denied concurrent resume"):
		_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
		return false
	if use_real_media and not _assert(_ffmpeg_process_state(ffmpeg_pid, fixture_root) == PROCESS_MATCHED, "real FFmpeg must remain active after the contender check immediately before the abrupt kill"):
		_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
		return false
	_stop_owned_processes(child_pid, ffmpeg_pid, fixture_root)
	var stopped_deadline := Time.get_ticks_msec() + 5000
	while not _process_is_stopped(_godot_process_state(child_pid)) and Time.get_ticks_msec() < stopped_deadline:
		OS.delay_msec(50)
	while ffmpeg_pid > 0 and not _process_is_stopped(_ffmpeg_process_state(ffmpeg_pid, fixture_root)) and Time.get_ticks_msec() < stopped_deadline:
		OS.delay_msec(50)
	if not _assert(_process_is_stopped(_godot_process_state(child_pid)), "the owned child Godot process must be reaped or confirmed zombie"):
		return false
	if not _assert(ffmpeg_pid == 0 or _process_is_stopped(_ffmpeg_process_state(ffmpeg_pid, fixture_root)), "the owned FFmpeg descendant must be reaped or confirmed zombie"):
		return false
	if not _assert(DirAccess.dir_exists_absolute(lock_path), "ordinary process stop must leave its lock for supervised reconciliation"):
		return false
	var ffmpeg := FixtureFfmpeg.new()
	ffmpeg.fail_second_segment_once = false
	ffmpeg.use_real_media = use_real_media
	var paths := {
		"root": fixture_root,
		"out_dir": fixture_root.path_join("out"),
		"tmp_dir": fixture_root.path_join("tmp"),
		"exports_dir": fixture_root.path_join("exports"),
	}
	var assets := FixtureAssets.new()
	var exporter := ExportService.new(db, paths, ffmpeg, assets)
	var blocked := exporter.resume_export(job_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(String(blocked.get("error", "")) == "E_RESUME_LOCKED", "a retained crash lock must fail closed"):
		print(blocked)
		return false
	var owner_pid := int(owner.get("pid", -1))
	if not _assert(owner_pid == child_pid and _process_is_stopped(_godot_process_state(owner_pid)), "manual recovery must confirm the recorded owner is reaped or zombie"):
		return false
	if not _assert(FileAccess.file_exists(job_root.path_join(job_id).path_join("job_manifest.json")), "manual recovery must retain the interrupted job manifest"):
		return false
	if not _assert(FileAccess.file_exists(job_root.path_join(job_id).path_join("segments/000/segment.manifest.json")), "manual recovery must retain the first segment evidence"):
		return false
	if not _assert(DirAccess.remove_absolute(owner_path) == OK and DirAccess.remove_absolute(lock_path) == OK, "test performs exact supervised lock reconciliation in its disposable fixture"):
		return false
	var recovered := exporter.resume_export(job_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(not recovered.has("error"), "supervised reconciliation must permit a safe resume"):
		print(recovered)
		return false
	return true

func _run_crash_child() -> int:
	var fixture_root := OS.get_environment("VAS_RESUME_FIXTURE_ROOT")
	var ffmpeg := FixtureFfmpeg.new()
	ffmpeg.use_real_media = OS.get_environment("VAS_RESUME_USE_REAL_FFMPEG") == "1"
	ffmpeg.fail_second_segment_once = false
	ffmpeg.pause_on_second_segment = true
	var paths := {
		"root": fixture_root,
		"out_dir": fixture_root.path_join("out"),
		"tmp_dir": fixture_root.path_join("tmp"),
		"exports_dir": fixture_root.path_join("exports"),
	}
	var exporter := ExportService.new(FixtureDb.new(), paths, ffmpeg, FixtureAssets.new())
	var result := exporter.export_project(_project(), "fixture-audio", {"tempo_bpm": 120.0, "analysis_version": "fixture-analysis-1"}, {"schema_version": 1, "metadata": {"title": "fixture", "description": "fixture", "tags": []}}, false, false)
	print("Unexpected child export return before parent stop: ", result)
	return 2

func _launch_lock_contender(fixture_root: String) -> int:
	var executable := OS.get_executable_path()
	var app_path := ProjectSettings.globalize_path("res://").trim_suffix("/")
	var contender_args := PackedStringArray([
		"VAS_RESUME_CONTENDER_MODE=1",
		"VAS_RESUME_FIXTURE_ROOT=" + fixture_root,
		"VAS_RESUME_USE_REAL_FFMPEG=" + OS.get_environment("VAS_RESUME_USE_REAL_FFMPEG"),
		executable,
		"--headless",
		"--path",
		app_path,
		"--script",
		"res://tests/phase1_resume_test.gd",
	])
	return OS.create_process("/usr/bin/env", contender_args, false)

func _run_lock_contender() -> int:
	var fixture_root := OS.get_environment("VAS_RESUME_FIXTURE_ROOT")
	var marker := fixture_root.path_join("child-paused-job.json")
	var child_info: Variant = JSON.parse_string(FileAccess.get_file_as_string(marker))
	if typeof(child_info) != TYPE_DICTIONARY:
		return 2
	var ffmpeg := FixtureFfmpeg.new()
	ffmpeg.use_real_media = OS.get_environment("VAS_RESUME_USE_REAL_FFMPEG") == "1"
	var paths := {
		"root": fixture_root,
		"out_dir": fixture_root.path_join("out"),
		"tmp_dir": fixture_root.path_join("tmp"),
		"exports_dir": fixture_root.path_join("exports"),
	}
	var exporter := ExportService.new(FixtureDb.new(), paths, ffmpeg, FixtureAssets.new())
	var result := exporter.resume_export(String(child_info.get("job_id", "")), _project(), "fixture-audio", {"tempo_bpm": 120.0, "analysis_version": "fixture-analysis-1"}, {"schema_version": 1, "metadata": {"title": "fixture", "description": "fixture", "tags": []}}, false, false)
	var result_file := FileAccess.open(fixture_root.path_join("contender-result.json"), FileAccess.WRITE)
	if result_file == null:
		return 3
	result_file.store_string(JSON.stringify(result))
	result_file.close()
	return 0 if String(result.get("error", "")) == "E_RESUME_LOCKED" else 1

func _stop_owned_processes(godot_pid: int, ffmpeg_pid: int, fixture_root: String) -> bool:
	# These PIDs come only from the uniquely owned fixture child and its marker.
	if _godot_process_state(godot_pid) == PROCESS_MATCHED:
		OS.execute("/bin/kill", PackedStringArray(["-KILL", str(godot_pid)]), [], true)
	if _ffmpeg_process_state(ffmpeg_pid, fixture_root) == PROCESS_MATCHED:
		OS.execute("/bin/kill", PackedStringArray(["-KILL", str(ffmpeg_pid)]), [], true)
	var deadline := Time.get_ticks_msec() + 5000
	while (not _process_is_stopped(_godot_process_state(godot_pid)) or not _process_is_stopped(_ffmpeg_process_state(ffmpeg_pid, fixture_root))) and Time.get_ticks_msec() < deadline:
		OS.delay_msec(50)
	var godot_state := _godot_process_state(godot_pid)
	var ffmpeg_state := _ffmpeg_process_state(ffmpeg_pid, fixture_root)
	var stopped := _process_is_stopped(godot_state) and _process_is_stopped(ffmpeg_state)
	if not stopped:
		var unsafe_marker := FileAccess.open(fixture_root.path_join("PRESERVE_FIXTURE_CHILD_RUNNING"), FileAccess.WRITE)
		if unsafe_marker != null:
			unsafe_marker.store_string("owned process state is unconfirmed godot=%d ffmpeg=%d; preserve this fixture" % [godot_state, ffmpeg_state])
			unsafe_marker.close()
		push_error("Owned child process did not stop; preserve fixture root: " + fixture_root)
	return stopped

func _ffmpeg_process_state(pid: int, fixture_root: String) -> int:
	return _observe_process_state(pid, "ffmpeg", fixture_root)

func _godot_process_state(pid: int) -> int:
	return _observe_process_state(pid, OS.get_executable_path(), "--script res://tests/phase1_resume_test.gd")

func _observe_process_state(pid: int, expected_command: String, expected_context: String) -> int:
	if pid <= 0:
		return PROCESS_EXITED
	var output: Array = []
	var code := OS.execute("/bin/ps", PackedStringArray(["-p", str(pid), "-o", "stat=,command="]), output, true)
	if code == 0 and not output.is_empty():
		var command := "\n".join(output).strip_edges()
		var separator := command.find(" ")
		if separator > 0 and command.substr(0, separator).contains("Z"):
			return PROCESS_ZOMBIE
		command = command.substr(separator + 1).strip_edges() if separator >= 0 else command
		if command.contains(expected_command) and command.contains(expected_context):
			return PROCESS_MATCHED
		return PROCESS_UNKNOWN
	# `ps` can fail for reasons other than ESRCH; require kill -0's explicit
	# no-such-process response before treating an empty result as proof of exit.
	var probe_output: Array = []
	var probe_code := OS.execute("/bin/kill", PackedStringArray(["-0", str(pid)]), probe_output, true)
	if probe_code == 0:
		return PROCESS_UNKNOWN
	if "No such process" in "\n".join(probe_output):
		return PROCESS_EXITED
	return PROCESS_UNKNOWN

func _process_is_stopped(state: int) -> bool:
	return state == PROCESS_EXITED or state == PROCESS_ZOMBIE

func _project() -> Dictionary:
	var real_media := OS.get_environment("VAS_RESUME_USE_REAL_FFMPEG") == "1"
	return {
		"id": "fixture-project",
		"name": "Resume Fixture",
		"fps": 1,
		"width": 8,
		"height": 8,
		"duration_frames": 65 if real_media else 61,
		"seed": 17,
		"visual_mode": "motion_poster",
		"preset_id": "fixture-preset",
		"mapping_id": "fixture-mapping",
		"template_id": "fixture-template",
	}

func _assert(condition: bool, message: String) -> bool:
	if not condition:
		push_error("[FAIL] " + message)
		return false
	print("[PASS] " + message)
	return true

func _fail(message: String) -> int:
	push_error("[FAIL] " + message)
	return 1
