extends SceneTree

const SQLiteAdapter = preload("res://src/adapters/sqlite_adapter.gd")
const FfmpegAdapter = preload("res://src/adapters/ffmpeg_adapter.gd")
const PythonWorkerAdapter = preload("res://src/adapters/python_worker_adapter.gd")
const AssetService = preload("res://src/core/asset_service.gd")
const AnalysisService = preload("res://src/core/analysis_service.gd")
const ExportService = preload("res://src/core/export_service.gd")
const VasIds = preload("res://src/shared/ids.gd")

var DEFAULT_MAPPING_DSL = """
mp.motion.float_amp = clamp(20 + sin(time_sec) * 5, 0, 80)
mp.beat.pulse_amount = clamp(0.4 + beat_phase * 0.3, 0, 1)
""".strip_edges()

const DEFAULT_TEMPLATE = {
	"schema_version": 1,
	"name": "Default Template",
	"metadata": {
		"title": "{project.title} — Visual Album",
		"description": "Track: {project.title}\\nBPM: {audio.bpm}\\n\\n{provenance.attribution_block}",
		"tags": ["visual album", "{project.genre}"],
		"categoryId": "10",
		"privacyStatus": "private",
		"publishAt": null,
		"chapters": [],
		"playlistIds": [],
	},
	"visual_defaults": {
		"mode_id": "motion_poster",
		"preset_id": "mp_preset_01",
		"seed_strategy": "project_seed",
	},
}

func _init() -> void:
	randomize()
	var code = _run_acceptance()
	quit(code)

func _run_acceptance() -> int:
	var repo_root = OS.get_environment("VAS_REPO_ROOT")
	if repo_root == "":
		repo_root = ProjectSettings.globalize_path("res://" ).get_base_dir()
	var out_root = repo_root.path_join("out/product_phase1")
	_safe_remove_tree(out_root)
	DirAccess.make_dir_recursive_absolute(out_root)
	DirAccess.make_dir_recursive_absolute(out_root.path_join("tmp"))
	DirAccess.make_dir_recursive_absolute(out_root.path_join("exports"))
	DirAccess.make_dir_recursive_absolute(out_root.path_join("cache"))
	DirAccess.make_dir_recursive_absolute(out_root.path_join("library"))

	var db = SQLiteAdapter.new(out_root.path_join("vas.db"))
	var schema_version = db.apply_migrations(repo_root.path_join("migrations"), 1)
	if not _assert_true(schema_version >= 1, "migrations applied"):
		return 1

	_seed_defaults(db)

	var ffmpeg = FfmpegAdapter.new("ffmpeg")
	var worker = PythonWorkerAdapter.new(PackedStringArray(["python3", "-m", "vas_audio_worker.cli"]))
	var assets = AssetService.new(db, ffmpeg, out_root.path_join("library"), out_root)
	var analysis = AnalysisService.new(db, worker, out_root)
	var exporter = ExportService.new(
		db,
		{
			"root": repo_root,
			"out_dir": out_root,
			"tmp_dir": out_root.path_join("tmp"),
			"exports_dir": out_root.path_join("exports"),
		},
		ffmpeg,
		assets
	)

	var src_audio = out_root.path_join("fixtures/tone.wav")
	DirAccess.make_dir_recursive_absolute(src_audio.get_base_dir())
	var synth = ffmpeg.run(PackedStringArray([
		"-y",
		"-f", "lavfi",
		"-i", "sine=frequency=440:sample_rate=48000:duration=10",
		"-ac", "2",
		src_audio,
	]))
	if not _assert_true(synth["ok"], "tone generation succeeded"):
		return 1

	var audio_asset_id = assets.import_asset(src_audio)
	if not _assert_true(audio_asset_id != "", "audio import"):
		return 1

	assets.set_license(audio_asset_id, "original", "Owned", "", "", "", "")
	if not _assert_true(assets.verify_integrity(audio_asset_id), "asset integrity"):
		return 1

	var analysis_id = analysis.request_analysis(audio_asset_id, "analysis_default", "phase1-v1")
	if not _assert_true(analysis_id != "", "analysis cached"):
		return 1
	var analysis_row = analysis.get_analysis(audio_asset_id, "phase1-v1")
	if not _assert_true(not analysis_row.is_empty(), "analysis row readback"):
		return 1

	var project_10s = _create_project(db, "AT001-10s", 10)
	var result_10s = exporter.export_project(
		db.query("SELECT * FROM projects WHERE id = %s LIMIT 1;" % db.quote(project_10s))[0],
		audio_asset_id,
		{"tempo_bpm": float(analysis_row.get("tempo_bpm", 120.0)), "analysis_version": String(analysis_row.get("analysis_version", "phase1-v1"))},
		DEFAULT_TEMPLATE,
		false,
		false
	)
	if not _assert_true(not result_10s.has("error"), "10s export"):
		print(result_10s)
		return 1
	if not _assert_bundle_complete(String(result_10s.get("bundle_dir", ""))):
		return 1

	var project_10m = _create_project(db, "AT001-10m", 600)
	var result_10m = exporter.export_project(
		db.query("SELECT * FROM projects WHERE id = %s LIMIT 1;" % db.quote(project_10m))[0],
		audio_asset_id,
		{"tempo_bpm": float(analysis_row.get("tempo_bpm", 120.0)), "analysis_version": String(analysis_row.get("analysis_version", "phase1-v1"))},
		DEFAULT_TEMPLATE,
		false,
		true
	)
	if not _assert_true(not result_10m.has("error"), "10m simulated export"):
		return 1
	if not _assert_true(Array(result_10m.get("segments", [])).size() >= 10, "10m segment plan"):
		return 1

	var project_2h = _create_project(db, "AT001-2h", 7200)
	var result_2h = exporter.export_project(
		db.query("SELECT * FROM projects WHERE id = %s LIMIT 1;" % db.quote(project_2h))[0],
		audio_asset_id,
		{"tempo_bpm": float(analysis_row.get("tempo_bpm", 120.0)), "analysis_version": String(analysis_row.get("analysis_version", "phase1-v1"))},
		DEFAULT_TEMPLATE,
		false,
		true
	)
	if not _assert_true(not result_2h.has("error"), "2h simulated export"):
		return 1
	if not _assert_true(Array(result_2h.get("segments", [])).size() >= 100, "2h segment plan"):
		return 1

	var result_10s_b = exporter.export_project(
		db.query("SELECT * FROM projects WHERE id = %s LIMIT 1;" % db.quote(project_10s))[0],
		audio_asset_id,
		{"tempo_bpm": float(analysis_row.get("tempo_bpm", 120.0)), "analysis_version": String(analysis_row.get("analysis_version", "phase1-v1"))},
		DEFAULT_TEMPLATE,
		false,
		false
	)
	if not _assert_true(not result_10s_b.has("error"), "10s deterministic rerun export"):
		return 1

	var manifest_a = _read_json(String(result_10s.get("bundle_dir", "")).path_join("build_manifest.json"))
	var manifest_b = _read_json(String(result_10s_b.get("bundle_dir", "")).path_join("build_manifest.json"))
	if not _assert_true(
		manifest_a.get("snapshot", {}).get("checkpoints", {}) == manifest_b.get("snapshot", {}).get("checkpoints", {}),
		"checkpoint determinism"
	):
		return 1

	print("AT-001 product-path acceptance passed")
	return 0

func _seed_defaults(db: SQLiteAdapter) -> void:
	var now = int(Time.get_unix_time_from_system())
	db.exec("INSERT OR IGNORE INTO analysis_profiles(id, name, sample_rate_hz, hop_length, algorithm_json, created_at) VALUES ('analysis_default', 'Default', 48000, 512, '{\"algorithm\":\"baseline\"}', %d);" % now)
	db.exec("INSERT OR IGNORE INTO mapping_schemas(version, name, created_at) VALUES (1, 'v1', %d);" % now)
	db.exec("INSERT OR IGNORE INTO preset_schemas(version, name, created_at) VALUES (1, 'v1', %d);" % now)
	db.exec("INSERT OR IGNORE INTO template_schemas(version, name, created_at) VALUES (1, 'v1', %d);" % now)

	db.exec("""
		INSERT OR IGNORE INTO mappings(id, name, schema_version, dsl_text, compiled_json, created_at, updated_at)
		VALUES ('mapping_motion_poster_default', 'Motion Poster Default', 1, %s, '{"compiled":true}', %d, %d);
	""" % [db.quote(DEFAULT_MAPPING_DSL), now, now])

	db.exec("""
		INSERT OR IGNORE INTO presets(id, mode_id, name, schema_version, mapping_id, seed, overrides_json, created_at, updated_at)
		VALUES ('mp_preset_01', 'motion_poster', 'Noir Pulse', 1, 'mapping_motion_poster_default', 101, '{}', %d, %d);
	""" % [now, now])

	db.exec("""
		INSERT OR IGNORE INTO templates(id, name, schema_version, template_json, created_at, updated_at)
		VALUES ('template_default', 'Default Template', 1, %s, %d, %d);
	""" % [db.quote(JSON.stringify(DEFAULT_TEMPLATE)), now, now])

func _create_project(db: SQLiteAdapter, name: String, duration_sec: int, fps: int = 30, width: int = 1920, height: int = 1080) -> String:
	var project_id = VasIds.new_id("project")
	var now = int(Time.get_unix_time_from_system())
	var slug = name.to_lower().replace(" ", "-") + "-" + str(Time.get_ticks_msec())
	db.exec("""
		INSERT INTO projects(
			id, name, slug, created_at, updated_at, visual_mode, preset_id, mapping_id,
			template_id, seed, fps, width, height, duration_frames, settings_json
		) VALUES (
			%s, %s, %s, %d, %d, 'motion_poster', 'mp_preset_01', 'mapping_motion_poster_default',
			'template_default', 101, %d, %d, %d, %d, '{}'
		);
	""" % [
		db.quote(project_id),
		db.quote(name),
		db.quote(slug),
		now,
		now,
		fps,
		width,
		height,
		duration_sec * fps,
	])
	return project_id

func _assert_bundle_complete(bundle_dir: String) -> bool:
	if not _assert_true(DirAccess.dir_exists_absolute(bundle_dir), "bundle dir exists: %s" % bundle_dir):
		return false
	for filename in ["video.mp4", "thumbnail.png", "metadata.json", "provenance.json", "build_manifest.json"]:
		if not _assert_true(FileAccess.file_exists(bundle_dir.path_join(filename)), "bundle contains %s" % filename):
			return false
	return true

func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY:
		return {}
	return parsed

func _assert_true(condition: bool, label: String) -> bool:
	if condition:
		print("[PASS] %s" % label)
		return true
	printerr("[FAIL] %s" % label)
	return false

func _safe_remove_tree(path: String) -> void:
	if path.strip_edges() == "" or path == "/":
		return
	OS.execute("rm", PackedStringArray(["-rf", path]), [], true)
