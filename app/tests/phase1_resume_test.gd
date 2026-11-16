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
	elif OS.get_environment("VAS_RESUME_RELATIVE_PATH_CHILD_MODE") == "1":
		quit(_run_relative_path_child())
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
	var journal_fixture_dir := fixture_root.path_join("tmp/atomic_job_manifest")
	DirAccess.make_dir_recursive_absolute(journal_fixture_dir)
	var journal_manifest_path := journal_fixture_dir.path_join("job_manifest.json")
	var prior_job_manifest := {
		"schema_version": 2,
		"job_id": "job_0123456789abcdef",
		"export_id": "export_fedcba9876543210",
		"resume_binding": "fixture-prior-binding",
	}
	if not _assert(exporter._write_job_manifest_atomic(journal_manifest_path, prior_job_manifest, false), "initial job manifest write must create an absent owned destination"):
		return 1
	var prior_job_manifest_bytes := FileAccess.get_file_as_string(journal_manifest_path).to_utf8_buffer()
	var install_failure_state := {"called": false, "destination_absent": false, "previous_matches": false, "journal_exists": false, "temporary_exists": false}
	exporter._job_manifest_install_override = func(temporary_path: String, manifest_path: String) -> int:
		install_failure_state["called"] = manifest_path == journal_manifest_path
		install_failure_state["destination_absent"] = not FileAccess.file_exists(manifest_path)
		install_failure_state["previous_matches"] = FileAccess.get_file_as_string(manifest_path + ".previous").to_utf8_buffer() == prior_job_manifest_bytes
		install_failure_state["journal_exists"] = FileAccess.file_exists(manifest_path + ".replace-journal")
		install_failure_state["temporary_exists"] = FileAccess.file_exists(temporary_path)
		return ERR_CANT_CREATE
	var replacement_result := exporter._write_job_manifest_atomic(journal_manifest_path, {
		"schema_version": 2,
		"job_id": "job_0123456789abcdef",
		"export_id": "export_fedcba9876543210",
		"resume_binding": "fixture-replacement-binding",
	}, true)
	exporter._job_manifest_install_override = Callable()
	if not _assert(bool(install_failure_state["called"]) and bool(install_failure_state["destination_absent"]) and bool(install_failure_state["previous_matches"]) and bool(install_failure_state["journal_exists"]) and bool(install_failure_state["temporary_exists"]), "replacement fault must occur only after backup, journal, and verified stage exist and the old primary is removed"):
		return 1
	if not _assert(not replacement_result, "failed replacement install must report false"):
		return 1
	var restored_job_manifest_bytes := FileAccess.get_file_as_string(journal_manifest_path).to_utf8_buffer()
	if not _assert(restored_job_manifest_bytes == prior_job_manifest_bytes, "failed job manifest replacement must restore the exact prior bytes"):
		return 1
	var restored_job_manifest: Variant = JSON.parse_string(restored_job_manifest_bytes.get_string_from_utf8())
	if not _assert(typeof(restored_job_manifest) == TYPE_DICTIONARY and String(restored_job_manifest.get("resume_binding", "")) == "fixture-prior-binding", "failed replacement must leave the prior manifest valid"):
		return 1
	if not _assert(not FileAccess.file_exists(journal_manifest_path + ".previous") and not FileAccess.file_exists(journal_manifest_path + ".replace-journal"), "recovery must clean the previous manifest and replacement journal"):
		return 1
	var replacement_dir := DirAccess.open(journal_fixture_dir)
	if not _assert(replacement_dir != null, "replacement fixture directory must remain readable for cleanup verification"):
		return 1
	replacement_dir.list_dir_begin()
	var replacement_entry := replacement_dir.get_next()
	var leftover_replacement := false
	while replacement_entry != "":
		if replacement_entry.begins_with("job_manifest.json."):
			leftover_replacement = true
			replacement_entry = replacement_dir.get_next()
			continue
		replacement_entry = replacement_dir.get_next()
	replacement_dir.list_dir_end()
	if not _assert(not leftover_replacement, "recovery must remove staged replacement and journal temporary files"):
		return 1
	var interrupted_manifest_path := journal_fixture_dir.path_join("interrupted/job_manifest.json")
	var interrupted_state := _prepare_job_manifest_recovery_fixture(exporter, interrupted_manifest_path, "missing")
	if not _assert(bool(interrupted_state.get("ok", false)), "test must prepare an owned interrupted replacement with missing primary"):
		return 1
	if not _assert(exporter._recover_job_manifest(interrupted_manifest_path), "recovery must restore the prior job manifest after interruption with a missing primary"):
		return 1
	var interrupted_prior_bytes: PackedByteArray = interrupted_state.get("previous_bytes", PackedByteArray())
	if not _assert(FileAccess.get_file_as_string(interrupted_manifest_path).to_utf8_buffer() == interrupted_prior_bytes, "interrupted recovery must restore the exact prior manifest bytes"):
		return 1
	if not _assert(not FileAccess.file_exists(interrupted_manifest_path + ".previous") and not FileAccess.file_exists(interrupted_manifest_path + ".replace-journal") and not FileAccess.file_exists(String(interrupted_state.get("temporary_path", ""))), "interrupted recovery must clean its owned journal, previous, and replacement files"):
		return 1
	var malformed_manifest_path := journal_fixture_dir.path_join("malformed/job_manifest.json")
	var malformed_state := _prepare_job_manifest_recovery_fixture(exporter, malformed_manifest_path, "malformed")
	if not _assert(bool(malformed_state.get("ok", false)), "test must prepare an owned malformed-primary recovery state"):
		return 1
	var malformed_primary_before := FileAccess.get_file_as_string(malformed_manifest_path).to_utf8_buffer()
	var malformed_previous_before := FileAccess.get_file_as_string(malformed_manifest_path + ".previous").to_utf8_buffer()
	var malformed_journal_before := FileAccess.get_file_as_string(malformed_manifest_path + ".replace-journal").to_utf8_buffer()
	var malformed_temp_path := String(malformed_state.get("temporary_path", ""))
	var malformed_temporary_before := FileAccess.get_file_as_string(malformed_temp_path).to_utf8_buffer()
	if not _assert(not exporter._recover_job_manifest(malformed_manifest_path), "recovery must fail closed on an unknown malformed primary manifest"):
		return 1
	if not _assert(FileAccess.get_file_as_string(malformed_manifest_path).to_utf8_buffer() == malformed_primary_before and FileAccess.get_file_as_string(malformed_manifest_path + ".previous").to_utf8_buffer() == malformed_previous_before and FileAccess.get_file_as_string(malformed_manifest_path + ".replace-journal").to_utf8_buffer() == malformed_journal_before and FileAccess.get_file_as_string(malformed_temp_path).to_utf8_buffer() == malformed_temporary_before, "failed-closed recovery must preserve the malformed primary and every owned journal artifact byte-for-byte"):
		return 1
	for primary_state in ["previous", "replacement"]:
		var matching_primary_path := journal_fixture_dir.path_join(primary_state + "/job_manifest.json")
		var matching_state := _prepare_job_manifest_recovery_fixture(exporter, matching_primary_path, primary_state)
		if not _assert(bool(matching_state.get("ok", false)), "test must prepare an owned journal state with a recognized primary"):
			return 1
		var expected_primary_bytes: PackedByteArray = matching_state.get("primary_bytes", PackedByteArray())
		if not _assert(exporter._recover_job_manifest(matching_primary_path), "recovery must accept a primary matching the journal's " + primary_state + " hash"):
			return 1
		if not _assert(FileAccess.get_file_as_string(matching_primary_path).to_utf8_buffer() == expected_primary_bytes, "recovery must preserve the recognized " + primary_state + " primary byte-for-byte"):
			return 1
		if not _assert(not FileAccess.file_exists(matching_primary_path + ".previous") and not FileAccess.file_exists(matching_primary_path + ".replace-journal") and not FileAccess.file_exists(String(matching_state.get("temporary_path", ""))), "recognized-primary recovery must clean only its owned journal artifacts"):
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
	if not _run_symlink_guard_controls(fixture_root, project, analysis, template):
		return 1
	if not _run_relative_tmp_dir_controls(fixture_root, project, analysis, template):
		return 1

	print("Phase 1 resume integration passed: interruption, same-job recovery, input mismatch, post-render failures, symlink guards, and segment tampering")
	return 0

func _run_relative_tmp_dir_controls(fixture_root: String, project: Dictionary, analysis: Dictionary, template: Dictionary) -> bool:
	# A child process gives each relative-path case an isolated current directory
	# below the unique fixture root while the main fixture remains in the checkout.
	var default_root := fixture_root.path_join("relative-path-default")
	var relative_root := fixture_root.path_join("relative-path-explicit")
	for case_root in [default_root, relative_root]:
		if not _assert(not FileAccess.file_exists(case_root) and not DirAccess.dir_exists_absolute(case_root), "relative-path case root must be absent before fixture creation"):
			return false
	DirAccess.make_dir_recursive_absolute(default_root)
	DirAccess.make_dir_recursive_absolute(relative_root)
	if not _assert(DirAccess.dir_exists_absolute(default_root) and DirAccess.dir_exists_absolute(relative_root), "relative-path case roots must be created inside the owned fixture root"):
		return false
	var default_ok := _run_relative_tmp_dir_subprocess(default_root, "default")
	var relative_ok := _run_relative_tmp_dir_subprocess(relative_root, "relative")
	return default_ok and relative_ok

func _run_relative_tmp_dir_subprocess(case_root: String, case_kind: String) -> bool:
	var case_root_access := DirAccess.open(case_root)
	if not _assert(case_root_access != null, "relative-path case root must be readable before project setup"):
		return false
	case_root_access.list_dir_begin()
	var first_entry := case_root_access.get_next()
	case_root_access.list_dir_end()
	if not _assert(first_entry == "", "relative-path case root pre-inventory must be empty"):
		return false
	var source_root := ProjectSettings.globalize_path("res://").trim_suffix("/")
	for relative_path in ["project.godot", "tests/phase1_resume_test.gd", "src/core/export_service.gd", "src/shared/ids.gd", "src/adapters/ffmpeg_adapter.gd"]:
		var source_path := source_root.path_join(relative_path)
		var destination_path := case_root.path_join(relative_path)
		DirAccess.make_dir_recursive_absolute(destination_path.get_base_dir())
		var source_file := FileAccess.open(source_path, FileAccess.READ)
		if not _assert(source_file != null, "relative-path child must read only the required project fixture source"):
			return false
		var destination_file := FileAccess.open(destination_path, FileAccess.WRITE)
		if not _assert(destination_file != null, "relative-path child must copy required source into its task-owned project root"):
			return false
		destination_file.store_buffer(source_file.get_buffer(source_file.get_length()))
		destination_file.close()
		source_file.close()
	var executable := OS.get_executable_path()
	var output: Array = []
	var exit_code := OS.execute("/usr/bin/env", PackedStringArray([
		"VAS_RESUME_RELATIVE_PATH_CHILD_MODE=1",
		"VAS_RESUME_RELATIVE_PATH_KIND=" + case_kind,
		"VAS_RESUME_FIXTURE_ROOT=" + case_root,
		executable,
		"--headless",
		"--path",
		case_root,
		"--script",
		"res://tests/phase1_resume_test.gd",
	]), output, true)
	if exit_code != 0:
		print("Relative-path child output: ", "\n".join(output))
	return _assert(exit_code == 0, case_kind + " relative-path child must pass its task-owned export/resume fixture")

func _run_relative_path_child() -> int:
	var case_root := OS.get_environment("VAS_RESUME_FIXTURE_ROOT")
	var case_kind := OS.get_environment("VAS_RESUME_RELATIVE_PATH_KIND")
	var cwd_access := DirAccess.open(".")
	if cwd_access == null or cwd_access.get_current_dir().simplify_path() != case_root.simplify_path():
		return _fail("relative-path child working directory must exactly match its fresh task-owned case root")
	var case_paths: Dictionary
	var jobs_relative_path: String
	var case_label: String
	if case_kind == "default":
		case_paths = {"root": case_root}
		jobs_relative_path = "out/tmp/jobs"
		case_label = "default tmp_dir"
	elif case_kind == "relative":
		case_paths = {"root": case_root, "tmp_dir": "relative/tmp", "out_dir": "relative/out", "exports_dir": "relative/exports"}
		jobs_relative_path = "relative/tmp/jobs"
		case_label = "explicit relative tmp_dir"
	else:
		return _fail("relative-path child requires a recognized isolated case kind")
	var analysis := {"tempo_bpm": 120.0, "analysis_version": "fixture-analysis-1"}
	var template := {"schema_version": 1, "metadata": {"title": "fixture", "description": "fixture", "tags": []}}
	if not _run_relative_tmp_dir_case(case_root, case_paths, jobs_relative_path, _project(), analysis, template, case_label):
		return 1
	print("Relative tmp_dir export/resume passed: ", case_label)
	return 0

func _run_relative_tmp_dir_case(
	case_root: String,
	configured_paths: Dictionary,
	jobs_relative_path: String,
	project: Dictionary,
	analysis: Dictionary,
	template: Dictionary,
	case_label: String
) -> bool:
	var audio_dir := String(configured_paths.get("out_dir", "out")).path_join("library")
	DirAccess.make_dir_recursive_absolute(audio_dir)
	var audio_path := audio_dir.path_join("audio.wav")
	var audio_file := FileAccess.open(audio_path, FileAccess.WRITE)
	if not _assert(audio_file != null, case_label + " fixture must create synthetic audio inside its task-owned directory"):
		return false
	audio_file.store_string("synthetic audio for " + case_label)
	audio_file.close()
	var db := FixtureDb.new()
	var ffmpeg := FixtureFfmpeg.new()
	var exporter := ExportService.new(db, configured_paths, ffmpeg, FixtureAssets.new())
	var interrupted := exporter.export_project(project, "fixture-audio", analysis, template, false, false)
	if not _assert(String(interrupted.get("error", "")) == "E_FFMPEG_FAILED", case_label + " export must reach its synthetic second-segment interruption"):
		print(interrupted)
		return false
	var job_id := String(interrupted.get("job_id", ""))
	var export_id := String(interrupted.get("export_id", ""))
	if not _assert(job_id != "" and export_id != "", case_label + " interruption must return resumable job and export IDs"):
		return false
	var job_root := case_root.path_join(jobs_relative_path).path_join(job_id)
	var first_segment := job_root.path_join("segments/000/segment.mp4")
	if not _assert(FileAccess.file_exists(first_segment), case_label + " must retain its first completed segment under the task-owned root"):
		return false
	var first_segment_calls := int(ffmpeg.segment_encodes.get("000", 0))
	var resumed := exporter.resume_export(job_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(not resumed.has("error"), case_label + " resume must finish from the returned job ID"):
		print(resumed)
		return false
	if not _assert(String(resumed.get("job_id", "")) == job_id and String(resumed.get("export_id", "")) == export_id, case_label + " resume must preserve job and export IDs"):
		return false
	var expected_bundle_dir := String(configured_paths.get("exports_dir", "out/exports")).path_join(export_id)
	if not _assert(String(resumed.get("bundle_dir", "")) == expected_bundle_dir, case_label + " export result must preserve the configured relative bundle path"):
		print(resumed)
		return false
	var export_row: Dictionary = db.exports.get(export_id, {})
	if not _assert(String(export_row.get("bundle_relpath", "")) == expected_bundle_dir, case_label + " database bundle_relpath must preserve the same relative path"):
		print(export_row)
		return false
	if not _assert(int(ffmpeg.segment_encodes.get("000", 0)) == first_segment_calls, case_label + " resume must reuse the completed first segment"):
		return false
	var bundle_manifest := expected_bundle_dir.path_join("build_manifest.json")
	if not _assert(FileAccess.file_exists(bundle_manifest), case_label + " resume must publish its completed bundle inside the task-owned root"):
		return false
	return true

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

func _prepare_job_manifest_recovery_fixture(exporter: RefCounted, manifest_path: String, primary_state: String) -> Dictionary:
	DirAccess.make_dir_recursive_absolute(manifest_path.get_base_dir())
	var previous_payload := {
		"schema_version": 2,
		"job_id": "job_0123456789abcdef",
		"export_id": "export_fedcba9876543210",
		"resume_binding": "fixture-recovery-prior-binding",
	}
	var replacement_payload := {
		"schema_version": 2,
		"job_id": "job_0123456789abcdef",
		"export_id": "export_fedcba9876543210",
		"resume_binding": "fixture-recovery-next-binding",
	}
	if not exporter._write_job_manifest_atomic(manifest_path, previous_payload, false):
		return {"ok": false}
	var previous_bytes := FileAccess.get_file_as_string(manifest_path).to_utf8_buffer()
	var previous_path := manifest_path + ".previous"
	var journal_path := manifest_path + ".replace-journal"
	if _write_fixture_bytes(previous_path, previous_bytes) != OK:
		return {"ok": false}
	var temporary_path := manifest_path + ".replace_0123456789abcdef.replacement.partial"
	var replacement_bytes := JSON.stringify(replacement_payload, "\t").to_utf8_buffer()
	if _write_fixture_bytes(temporary_path, replacement_bytes) != OK:
		return {"ok": false}
	var journal := {
		"schema_version": 1,
		"destination": "job_manifest.json",
		"transaction_id": "replace_0123456789abcdef",
		"temporary": temporary_path.get_file(),
		"previous": previous_path.get_file(),
		"previous_sha256": exporter._sha256_bytes(previous_bytes),
		"replacement_sha256": exporter._sha256_bytes(replacement_bytes),
	}
	var journal_bytes := JSON.stringify(journal, "\t").to_utf8_buffer()
	if _write_fixture_bytes(journal_path, journal_bytes) != OK:
		return {"ok": false}
	var primary_bytes := PackedByteArray()
	if primary_state == "malformed":
		if _write_fixture_bytes(manifest_path, "{malformed primary".to_utf8_buffer()) != OK:
			return {"ok": false}
		primary_bytes = "{malformed primary".to_utf8_buffer()
	elif primary_state == "missing":
		if DirAccess.remove_absolute(manifest_path) != OK:
			return {"ok": false}
	elif primary_state == "previous":
		primary_bytes = previous_bytes
		if _write_fixture_bytes(manifest_path, primary_bytes) != OK:
			return {"ok": false}
	elif primary_state == "replacement":
		primary_bytes = replacement_bytes
		if _write_fixture_bytes(manifest_path, primary_bytes) != OK:
			return {"ok": false}
	else:
		return {"ok": false}
	return {"ok": true, "previous_bytes": previous_bytes, "primary_bytes": primary_bytes, "temporary_path": temporary_path}

func _write_fixture_bytes(path: String, bytes: PackedByteArray) -> int:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return ERR_CANT_CREATE
	file.store_buffer(bytes)
	file.flush()
	var result := file.get_error()
	file.close()
	return result

func _run_symlink_guard_controls(fixture_root: String, project: Dictionary, analysis: Dictionary, template: Dictionary) -> bool:
	var paths := {
		"root": fixture_root,
		"out_dir": fixture_root.path_join("out"),
		"tmp_dir": fixture_root.path_join("tmp"),
		"exports_dir": fixture_root.path_join("exports"),
	}
	var ffmpeg := FixtureFfmpeg.new()
	var exporter := ExportService.new(FixtureDb.new(), paths, ffmpeg, FixtureAssets.new())
	var interrupted := exporter.export_project(project, "fixture-audio", analysis, template, false, false)
	if not _assert(String(interrupted.get("error", "")) == "E_FFMPEG_FAILED", "symlink guard control must create an interrupted synthetic job"):
		print(interrupted)
		return false
	var job_id := String(interrupted.get("job_id", ""))
	var workspace := fixture_root.path_join("tmp/jobs").path_join(job_id)
	var canary_path := fixture_root.path_join("tmp/symlink_guard/owned-output.bin")
	DirAccess.make_dir_recursive_absolute(canary_path.get_base_dir())
	var canary := FileAccess.open(canary_path, FileAccess.WRITE)
	if not _assert(canary != null, "symlink guard fixture must create an in-root canary file"):
		return false
	var canary_bytes := "owned symlink target sentinel\n"
	canary.store_string(canary_bytes)
	canary.close()
	if not _assert(not exporter._path_has_symlink_component(canary_path), "guard must accept an ordinary in-root regular file on a supported inspector"):
		return false
	if not _assert(not exporter._path_has_symlink_component(fixture_root.path_join("tmp/symlink_guard/not-created/child")), "guard must allow a prospective missing child after successful parent inspection"):
		return false
	exporter._symlink_inspection_supported_override = false
	var unavailable_fails_closed := exporter._path_has_symlink_component(canary_path)
	exporter._symlink_inspection_supported_override = null
	if not _assert(unavailable_fails_closed, "guard must fail closed when symlink inspection is unavailable"):
		return false
	var final_video_link := workspace.path_join("final/video.mp4")
	var output_link_parent := DirAccess.open(final_video_link.get_base_dir())
	var link_code := FAILED
	if output_link_parent != null:
		link_code = output_link_parent.create_link(canary_path, final_video_link)
	if link_code != OK:
		if OS.get_name() == "Windows":
			print("[SKIP] symlink refusal cases unavailable without Windows Developer Mode or elevated privileges; error=%d" % link_code)
			return true
		push_error("[FAIL] could not create owned output symlink to in-root canary; error=%d" % link_code)
		return false
	print("[PASS] symlink guard fixture links an output file only to its in-root canary")
	var calls_before_output_link := ffmpeg.calls.size()
	var output_link_resume := exporter.resume_export(job_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(String(output_link_resume.get("error", "")) == "E_RESUME_UNSAFE_PATH", "resume must refuse a symlinked output file"):
		print(output_link_resume)
		return false
	if not _assert(ffmpeg.calls.size() == calls_before_output_link, "symlinked output file must be rejected before FFmpeg is called"):
		return false
	if not _assert(FileAccess.get_file_as_string(canary_path) == canary_bytes, "refusing a symlinked output must leave its in-root target unchanged"):
		return false
	if not _assert(DirAccess.remove_absolute(final_video_link) == OK, "test must remove its owned output symlink before the segment check"):
		return false

	var segment_dir := workspace.path_join("segments/001")
	var frames_dir := segment_dir.path_join("frames")
	var frame_path := frames_dir.path_join("frame_000000.png")
	if FileAccess.file_exists(frame_path) and not _assert(DirAccess.remove_absolute(frame_path) == OK, "test must remove only the failed segment's synthetic frame"):
		return false
	if DirAccess.dir_exists_absolute(frames_dir) and not _assert(DirAccess.remove_absolute(frames_dir) == OK, "test must remove the emptied failed segment frames directory"):
		return false
	if DirAccess.dir_exists_absolute(segment_dir) and not _assert(DirAccess.remove_absolute(segment_dir) == OK, "test must remove the emptied failed segment directory"):
		return false
	var segment_target := fixture_root.path_join("tmp/symlink_guard/owned-segment-directory")
	DirAccess.make_dir_recursive_absolute(segment_target)
	var segment_marker := FileAccess.open(segment_target.path_join("sentinel.txt"), FileAccess.WRITE)
	if not _assert(segment_marker != null, "symlink guard fixture must create an in-root segment target"):
		return false
	segment_marker.store_string("owned segment target sentinel\n")
	segment_marker.close()
	var segment_link_parent := DirAccess.open(segment_dir.get_base_dir())
	link_code = FAILED
	if segment_link_parent != null:
		link_code = segment_link_parent.create_link(segment_target, segment_dir)
	if link_code != OK:
		if OS.get_name() == "Windows":
			print("[SKIP] symlink refusal cases unavailable without Windows Developer Mode or elevated privileges; error=%d" % link_code)
			return true
		push_error("[FAIL] could not create owned segment symlink to in-root target; error=%d" % link_code)
		return false
	print("[PASS] symlink guard fixture links a segment directory only to its in-root target")
	var calls_before_segment_link := ffmpeg.calls.size()
	var segment_link_resume := exporter.resume_export(job_id, project, "fixture-audio", analysis, template, false, false)
	if not _assert(String(segment_link_resume.get("error", "")) == "E_RESUME_UNSAFE_PATH", "resume must refuse a symlinked segment directory"):
		print(segment_link_resume)
		return false
	if not _assert(ffmpeg.calls.size() == calls_before_segment_link, "symlinked segment directory must be rejected before FFmpeg is called"):
		return false
	if not _assert(FileAccess.get_file_as_string(segment_target.path_join("sentinel.txt")) == "owned segment target sentinel\n", "refusing a symlinked segment must leave its in-root target unchanged"):
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
