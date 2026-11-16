extends SceneTree

const ExportService = preload("res://src/core/export_service.gd")

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
				var marker := OS.get_environment("VAS_RESUME_FIXTURE_ROOT").path_join("child-paused-job-id.txt")
				var parts := target.split("/")
				var jobs_index := parts.find("jobs")
				var marker_file := FileAccess.open(marker, FileAccess.WRITE)
				marker_file.store_string(String(parts[jobs_index + 1]))
				marker_file.close()
				OS.delay_msec(30000)
			if segment_index == "001" and fail_second_segment_once:
				fail_second_segment_once = false
				return {"ok": false, "code": 1, "output": "synthetic interruption"}
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
			"-y", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=61",
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

	print("Phase 1 resume integration passed: interruption, same-job recovery, input mismatch, and segment tampering")
	return 0

func _run_abrupt_stop_control(fixture_root: String, project: Dictionary, analysis: Dictionary, template: Dictionary, db: FixtureDb) -> bool:
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
	var marker := fixture_root.path_join("child-paused-job-id.txt")
	var deadline := Time.get_ticks_msec() + 20000
	while not FileAccess.file_exists(marker) and Time.get_ticks_msec() < deadline and OS.is_process_running(child_pid):
		OS.delay_msec(50)
	if not FileAccess.file_exists(marker):
		if OS.is_process_running(child_pid):
			OS.kill(child_pid)
		push_error("[FAIL] child did not reach its synthetic second-segment pause")
		return false
	var job_id := FileAccess.get_file_as_string(marker).strip_edges()
	var job_root := fixture_root.path_join("tmp/jobs")
	var lock_path := job_root.path_join(job_id + ".lock")
	var owner_path := lock_path.path_join("owner.json")
	if not _assert(FileAccess.file_exists(owner_path), "child export must own a durable lock while paused"):
		OS.kill(child_pid)
		return false
	var owner: Variant = JSON.parse_string(FileAccess.get_file_as_string(owner_path))
	if not _assert(typeof(owner) == TYPE_DICTIONARY and int(owner.get("pid", -1)) == child_pid, "lock owner must identify the child process"):
		OS.kill(child_pid)
		return false
	OS.kill(child_pid)
	var stopped_deadline := Time.get_ticks_msec() + 5000
	while OS.is_process_running(child_pid) and Time.get_ticks_msec() < stopped_deadline:
		OS.delay_msec(50)
	if not _assert(not OS.is_process_running(child_pid), "the owned child Godot process must stop"):
		return false
	if not _assert(DirAccess.dir_exists_absolute(lock_path), "ordinary process stop must leave its lock for supervised reconciliation"):
		return false
	var ffmpeg := FixtureFfmpeg.new()
	ffmpeg.fail_second_segment_once = false
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
	if not _assert(owner_pid == child_pid and not OS.is_process_running(owner_pid), "manual recovery must prove the recorded owner is gone"):
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

func _project() -> Dictionary:
	return {
		"id": "fixture-project",
		"name": "Resume Fixture",
		"fps": 1,
		"width": 8,
		"height": 8,
		"duration_frames": 61,
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

