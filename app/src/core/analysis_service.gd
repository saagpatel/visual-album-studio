extends RefCounted
class_name AnalysisService

var db
var worker
var out_root: String

func _init(p_db = null, p_worker = null, p_out_root: String = "") -> void:
	db = p_db
	worker = p_worker
	out_root = p_out_root

func request_analysis(audio_asset_id: String, analysis_profile_id: String, analysis_version: String) -> String:
	var asset_rows = db.query("SELECT sha256, library_relpath FROM assets WHERE id = %s LIMIT 1;" % db.quote(audio_asset_id))
	if asset_rows.is_empty():
		push_error("E_ASSET_NOT_FOUND: %s" % audio_asset_id)
		return ""
	var asset: Dictionary = asset_rows[0]

	var existing = db.query(
		"SELECT id FROM analysis_cache WHERE audio_sha256 = %s AND analysis_profile_id = %s AND analysis_version = %s LIMIT 1;"
		% [db.quote(String(asset.get("sha256", ""))), db.quote(analysis_profile_id), db.quote(analysis_version)]
	)
	if not existing.is_empty():
		return String(existing[0].get("id", ""))

	var audio_path = out_root.path_join(String(asset.get("library_relpath", "")))
	var worker_result = worker.analyze_audio(audio_path, out_root.path_join("tmp"))
	if not bool(worker_result.get("ok", false)):
		push_error("E_WORKER_UNAVAILABLE: %s" % worker_result)
		return ""

	var cache_id = "%s_%s" % [audio_asset_id, analysis_version]
	var now = int(Time.get_unix_time_from_system())
	var insert = """
		INSERT INTO analysis_cache(
			id, audio_asset_id, audio_sha256, analysis_profile_id, analysis_version,
			tempo_bpm, beat_times_json, summary_json, created_at, computed_at
		) VALUES (
			%s, %s, %s, %s, %s,
			%f, %s, %s, %d, %d
		);
	""" % [
		db.quote(cache_id),
		db.quote(audio_asset_id),
		db.quote(String(asset.get("sha256", ""))),
		db.quote(analysis_profile_id),
		db.quote(analysis_version),
		float(worker_result.get("tempo_bpm", 0.0)),
		db.quote(JSON.stringify(worker_result.get("beat_times_sec", []))),
		db.quote(JSON.stringify({"duration_sec": worker_result.get("duration_sec", 0.0)})),
		now,
		now,
	]
	db.exec(insert)
	return cache_id

func get_analysis(audio_asset_id: String, analysis_version: String) -> Dictionary:
	var rows = db.query(
		"SELECT * FROM analysis_cache WHERE audio_asset_id = %s AND analysis_version = %s LIMIT 1;"
		% [db.quote(audio_asset_id), db.quote(analysis_version)]
	)
	if rows.is_empty():
		return {}
	return rows[0]
