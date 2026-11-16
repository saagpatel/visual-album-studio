extends SceneTree

const ExportService = preload("res://src/core/export_service.gd")
const SQLiteAdapter = preload("res://src/adapters/sqlite_adapter.gd")
const FfmpegAdapter = preload("res://src/adapters/ffmpeg_adapter.gd")

class PauseBeforeExportInsertDb extends "res://src/adapters/sqlite_adapter.gd":
	var fixture_root := ""
	var pause_enabled := true

	func exec(sql: String) -> Dictionary:
		if pause_enabled and sql.contains("INSERT OR IGNORE INTO exports"):
			pause_enabled = false
			var expression := RegEx.new()
			expression.compile("VALUES \\(\\s*'([^']+)',\\s*'([^']+)',\\s*'([^']+)'")
			var found := expression.search(sql)
			if found == null:
				return {"ok": false, "output": "could not parse export row"}
			var marker := {
				"export_id": found.get_string(1),
				"job_id": found.get_string(2),
				"project_id": found.get_string(3),
			}
			var file := FileAccess.open(fixture_root.path_join("before-export-insert.json"), FileAccess.WRITE)
			if file == null:
				return {"ok": false, "output": "could not write insertion marker"}
			file.store_string(JSON.stringify(marker))
			file.close()
			OS.delay_msec(30000)
		return super.exec(sql)

class FixtureAssets extends RefCounted:
	func validate_production_allowed(_audio_asset_id: String) -> Dictionary:
		return {"allowed": true}

	func provenance_json(_audio_asset_id: String, _template_id: String, _preset_id: String, _mapping_id: String, _seed: int) -> Dictionary:
		return {"attribution_block": "synthetic sqlite recovery fixture"}

func _init() -> void:
	if OS.get_environment("VAS_RESUME_SQLITE_CHILD_MODE") == "1":
		quit(_run_child())
	else:
		quit(_run())

func _run() -> int:
	var root := OS.get_environment("VAS_RESUME_SQLITE_FIXTURE_ROOT")
	if not (root.begins_with("/private/tmp/vas-resume-sqlite-") or root.begins_with("/tmp/vas-resume-sqlite-")):
		return _fail("fixture root must be under the dedicated temporary prefix")
	if FileAccess.file_exists(root):
		return _fail("fixture root must be a directory")
	if DirAccess.dir_exists_absolute(root):
		var existing_root := DirAccess.open(root)
		if existing_root == null:
			return _fail("could not inspect pre-created fixture directory")
		existing_root.list_dir_begin()
		var first_entry := existing_root.get_next()
		var empty := first_entry == ""
		existing_root.list_dir_end()
		if not empty:
			return _fail("pre-created fixture directory must be empty; refusing to clear existing data")
	else:
		if DirAccess.make_dir_recursive_absolute(root) != OK:
			return _fail("could not create fixture root")
	for child in ["db", "out", "out/library", "tmp", "exports"]:
		if DirAccess.make_dir_recursive_absolute(root.path_join(child)) != OK:
			return _fail("could not create owned fixture directory")

	var db_path := root.path_join("db/vas.db")
	var db := SQLiteAdapter.new(db_path)
	var schema_version := db.apply_migrations(ProjectSettings.globalize_path("res://../migrations"))
	if schema_version < 1:
		return _fail("repository schema migration failed")
	if not _seed_references(db):
		return _fail("could not seed repository foreign-key references")
	var audio_path := root.path_join("out/library/audio.wav")
	var audio_output: Array = []
	var audio_code := OS.execute("ffmpeg", PackedStringArray(["-y", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=61", "-ac", "2", audio_path]), audio_output, true)
	if audio_code != 0:
		return _fail("could not create 61-second synthetic SQLite fixture audio")
	var audio_hash := _hash_file(audio_path)
	var now := int(Time.get_unix_time_from_system())
	var asset_insert := db.exec("INSERT INTO assets(id,kind,sha256,size_bytes,library_relpath,created_at,imported_at) VALUES('asset_fixture','audio',%s,%d,'library/audio.wav',%d,%d);" % [db.quote(audio_hash), FileAccess.get_file_as_bytes(audio_path).size(), now, now])
	if not bool(asset_insert.get("ok", false)):
		return _fail("could not seed repository audio asset row")
	if not _assert(_run_insert_window_crash(root, db), "child termination after bundle publication recovers through real SQLite"):
		return 1

	var bundle := root.path_join("exports/export_fixture0000000001")
	DirAccess.make_dir_recursive_absolute(bundle)
	var content := {"video.mp4": "synthetic-video-bytes", "thumbnail.png": "synthetic-thumbnail-bytes", "metadata.json": "{}", "provenance.json": "{}"}
	for name in content:
		if not _write(bundle.path_join(name), content[name]):
			return _fail("could not create synthetic bundle file " + name)
	var hashes := {}
	for name in content:
		hashes[name] = _hash_file(bundle.path_join(name))
	var manifest := {"schema_version": 1, "snapshot": {"export_id": "export_fixture0000000001", "project_id": "project_fixture"}, "outputs": {"integrity": hashes}}
	if not _write(bundle.path_join("build_manifest.json"), JSON.stringify(manifest)):
		return _fail("could not write synthetic build manifest")
	hashes["build_manifest.json"] = _hash_file(bundle.path_join("build_manifest.json"))
	var job_manifest_path := root.path_join("tmp/jobs/job_fixture0000000001/job_manifest.json")
	DirAccess.make_dir_recursive_absolute(job_manifest_path.get_base_dir())
	var receipt := {"published_bundle": {"export_id": "export_fixture0000000001", "project_id": "project_fixture", "resume_binding": "fixture-binding", "files": hashes}}
	if not _write(job_manifest_path, JSON.stringify(receipt)):
		return _fail("could not write synthetic recovery receipt")

	var paths := {"root": root, "tmp_dir": root.path_join("tmp"), "exports_dir": root.path_join("exports")}
	var exporter := ExportService.new(db, paths, FfmpegAdapter.new("ffmpeg"), FixtureAssets.new())
	if not _assert(exporter._is_complete_bundle(bundle, "export_fixture0000000001", "project_fixture", job_manifest_path, "fixture-binding"), "hash-verified published bundle qualifies for registration repair"):
		return 1
	if not _assert(exporter._register_export("export_fixture0000000001", "job_fixture0000000001", "project_fixture", bundle), "missing SQLite export row is repaired"):
		return 1
	var rows := db.query("SELECT id, job_id, project_id, bundle_relpath, video_relpath, thumbnail_relpath, metadata_relpath, provenance_relpath, build_manifest_relpath FROM exports WHERE id = 'export_fixture0000000001';")
	if not _assert(rows.size() == 1, "repair creates exactly one real SQLite row"):
		return 1
	if not _assert(String(rows[0].get("bundle_relpath", "")) == "exports/export_fixture0000000001", "SQLite row stores canonical bundle path"):
		return 1

	var wrong_path_update := db.exec("UPDATE exports SET bundle_relpath = 'exports/other' WHERE id = 'export_fixture0000000001';")
	if not _assert(bool(wrong_path_update.get("ok", false)), "wrong-path negative-control setup succeeds"):
		return 1
	if not _assert(not exporter._register_export("export_fixture0000000001", "job_fixture0000000001", "project_fixture", bundle), "existing SQLite row with wrong paths is rejected"):
		return 1

	var corrupt := FileAccess.open(bundle.path_join("video.mp4"), FileAccess.WRITE)
	if corrupt == null:
		return _fail("could not corrupt owned fixture video")
	corrupt.store_string("corrupt")
	corrupt.close()
	if not _assert(not exporter._is_complete_bundle(bundle, "export_fixture0000000001", "project_fixture", job_manifest_path, "fixture-binding"), "corrupted published file is rejected before database repair"):
		return 1
	print("Real SQLite bundle-recovery controls passed")
	return 0

func _run_insert_window_crash(root: String, db: SQLiteAdapter) -> bool:
	var godot_bin := OS.get_environment("VAS_GODOT_BIN")
	if godot_bin == "":
		godot_bin = OS.get_executable_path()
	var app_path := ProjectSettings.globalize_path("res://").trim_suffix("/")
	var args := PackedStringArray([
		"VAS_RESUME_SQLITE_CHILD_MODE=1",
		"VAS_RESUME_SQLITE_FIXTURE_ROOT=" + root,
		godot_bin,
		"--headless",
		"--path",
		app_path,
		"--script",
		"res://tests/phase1_resume_sqlite_test.gd",
	])
	var child_pid := OS.create_process("/usr/bin/env", args, false)
	if child_pid <= 0:
		return false
	var marker_path := root.path_join("before-export-insert.json")
	var deadline := Time.get_ticks_msec() + 60000
	while not FileAccess.file_exists(marker_path) and Time.get_ticks_msec() < deadline and OS.is_process_running(child_pid):
		OS.delay_msec(100)
	if not FileAccess.file_exists(marker_path):
		if not _kill_and_wait_owned_child(child_pid, root):
			return false
		return false
	var marker: Variant = JSON.parse_string(FileAccess.get_file_as_string(marker_path))
	if typeof(marker) != TYPE_DICTIONARY:
		if not _kill_and_wait_owned_child(child_pid, root):
			return false
		return false
	var export_id := String(marker.get("export_id", ""))
	var job_id := String(marker.get("job_id", ""))
	var project_id := String(marker.get("project_id", ""))
	var bundle := root.path_join("exports").path_join(export_id)
	if not _assert(_complete_synthetic_bundle(bundle), "final bundle is published before the child reaches its export-row insert"):
		if not _kill_and_wait_owned_child(child_pid, root):
			return false
		return false
	if not _assert(db.query("SELECT id FROM exports WHERE id = %s;" % db.quote(export_id)).is_empty(), "real SQLite export row is absent at the crash point"):
		if not _kill_and_wait_owned_child(child_pid, root):
			return false
		return false
	var job_manifest_path := root.path_join("tmp/jobs").path_join(job_id).path_join("job_manifest.json")
	var lock_path := root.path_join("tmp/jobs").path_join(job_id + ".lock")
	var owner_path := lock_path.path_join("owner.json")
	if not FileAccess.file_exists(job_manifest_path) or not FileAccess.file_exists(owner_path):
		if not _kill_and_wait_owned_child(child_pid, root):
			return false
		return false
	if not _kill_and_wait_owned_child(child_pid, root):
		return false
	var owner: Variant = JSON.parse_string(FileAccess.get_file_as_string(owner_path))
	if typeof(owner) != TYPE_DICTIONARY or int(owner.get("pid", -1)) != child_pid:
		return false
	if DirAccess.remove_absolute(owner_path) != OK or DirAccess.remove_absolute(lock_path) != OK:
		return false
	var paths := {"root": root, "tmp_dir": root.path_join("tmp"), "exports_dir": root.path_join("exports"), "out_dir": root.path_join("out")}
	var exporter := ExportService.new(db, paths, FfmpegAdapter.new("ffmpeg"), FixtureAssets.new())
	var result := exporter.resume_export(job_id, _project(), "asset_fixture", _analysis(), _template(), true, false)
	if result.has("error"):
		print(result)
		return false
	var recovered_rows := db.query("SELECT id, job_id, project_id FROM exports WHERE id = %s;" % db.quote(export_id))
	return recovered_rows.size() == 1 and String(recovered_rows[0].get("job_id", "")) == job_id and String(recovered_rows[0].get("project_id", "")) == project_id

func _kill_and_wait_owned_child(child_pid: int, root: String) -> bool:
	if OS.is_process_running(child_pid):
		OS.kill(child_pid)
	var deadline := Time.get_ticks_msec() + 10000
	while OS.is_process_running(child_pid) and Time.get_ticks_msec() < deadline:
		OS.delay_msec(50)
	if OS.is_process_running(child_pid):
		var preserve := FileAccess.open(root.path_join("PRESERVE_FIXTURE_CHILD_RUNNING"), FileAccess.WRITE)
		if preserve != null:
			preserve.store_string("Owned child PID %d did not stop; preserve this fixture for safe investigation.\n" % child_pid)
			preserve.close()
		push_error("[FAIL] owned child did not stop; fixture must be preserved")
		return false
	return true

func _run_child() -> int:
	var root := OS.get_environment("VAS_RESUME_SQLITE_FIXTURE_ROOT")
	var db := PauseBeforeExportInsertDb.new(root.path_join("db/vas.db"))
	db.fixture_root = root
	var paths := {"root": root, "tmp_dir": root.path_join("tmp"), "exports_dir": root.path_join("exports"), "out_dir": root.path_join("out")}
	var exporter := ExportService.new(db, paths, FfmpegAdapter.new("ffmpeg"), FixtureAssets.new())
	var result := exporter.export_project(_project(), "asset_fixture", _analysis(), _template(), true, false)
	print("Child unexpectedly left insertion pause: ", result)
	return 2

func _project() -> Dictionary:
	return {"id": "project_fixture", "name": "Fixture", "fps": 1, "width": 8, "height": 8, "duration_frames": 61, "seed": 17, "visual_mode": "motion_poster", "preset_id": "fixture-preset", "mapping_id": "fixture-mapping", "template_id": "fixture-template"}

func _analysis() -> Dictionary:
	return {"tempo_bpm": 120.0, "analysis_version": "sqlite-fixture-analysis"}

func _template() -> Dictionary:
	return {"schema_version": 1, "metadata": {"title": "fixture", "description": "fixture", "tags": []}}

func _complete_synthetic_bundle(bundle: String) -> bool:
	for name in ["video.mp4", "thumbnail.png", "metadata.json", "provenance.json", "build_manifest.json"]:
		if not FileAccess.file_exists(bundle.path_join(name)) or FileAccess.get_file_as_bytes(bundle.path_join(name)).is_empty():
			return false
	return true

func _seed_references(db: SQLiteAdapter) -> bool:
	var now := int(Time.get_unix_time_from_system())
	var statements := [
		"INSERT INTO projects(id,name,slug,created_at,updated_at,visual_mode,seed,fps,width,height,duration_frames) VALUES('project_fixture','Fixture','fixture',%d,%d,'motion_poster',17,1,8,8,61);" % [now, now],
		"INSERT INTO jobs(id,type,status,payload_json,created_at,updated_at) VALUES('job_fixture0000000001','render','failed','{}',%d,%d);" % [now, now],
		"INSERT INTO render_jobs(job_id,project_id,export_preset_json,segment_frames,total_frames,checkpoint_frames_json,workspace_relpath,output_bundle_relpath) VALUES('job_fixture0000000001','project_fixture','{}',60,61,'[]','tmp/jobs/job_fixture0000000001','exports/export_fixture0000000001');",
	]
	for statement in statements:
		if not bool(db.exec(statement).get("ok", false)):
			return false
	return true

func _write(path: String, value: String) -> bool:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(value)
	file.close()
	return true

func _hash_file(path: String) -> String:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return ""
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	while not file.eof_reached():
		hash.update(file.get_buffer(65536))
	file.close()
	return hash.finish().hex_encode()

func _assert(condition: bool, message: String) -> bool:
	if not condition:
		push_error("[FAIL] " + message)
		return false
	print("[PASS] " + message)
	return true

func _fail(message: String) -> int:
	push_error("[FAIL] " + message)
	return 1
