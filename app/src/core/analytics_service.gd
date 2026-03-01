extends RefCounted
class_name AnalyticsService

const VasIds = preload("res://src/shared/ids.gd")

var db

func _init(p_db = null) -> void:
	db = p_db

func store_snapshot(channel_row_id: String, start_ymd: String, end_ymd: String, metrics: Dictionary) -> String:
	var snapshot_id = VasIds.new_id("snapshot")
	var row_created_at = int(Time.get_unix_time_from_system())
	var sql = """
		INSERT INTO analytics_snapshots(
			id, channel_row_id, range_start_ymd, range_end_ymd,
			metrics_json, dimensions_json, data_json, created_at
		) VALUES (
			%s, %s, %s, %s, %s, %s, %s, %d
		);
	""" % [
		db.quote(snapshot_id),
		db.quote(channel_row_id),
		db.quote(start_ymd),
		db.quote(end_ymd),
		db.quote(JSON.stringify(metrics)),
		db.quote(JSON.stringify({})),
		db.quote(JSON.stringify(metrics)),
		row_created_at,
	]
	db.exec(sql)
	return snapshot_id

func get_dashboard_snapshot(channel_row_id: String, range_start_ymd: String = "", range_end_ymd: String = "") -> Dictionary:
	var where_parts: Array = ["channel_row_id = %s" % db.quote(channel_row_id)]
	if range_start_ymd != "":
		where_parts.append("range_start_ymd >= %s" % db.quote(range_start_ymd))
	if range_end_ymd != "":
		where_parts.append("range_end_ymd <= %s" % db.quote(range_end_ymd))
	var where_sql = " WHERE %s" % " AND ".join(where_parts)

	var count_rows = db.query("SELECT COUNT(*) AS c FROM analytics_snapshots%s;" % where_sql)
	var snapshot_count = int(count_rows[0].get("c", 0)) if not count_rows.is_empty() else 0
	var latest_rows = db.query("SELECT COALESCE(MAX(created_at), 0) AS ts FROM analytics_snapshots%s;" % where_sql)
	var latest_snapshot_at = int(latest_rows[0].get("ts", 0)) if not latest_rows.is_empty() else 0
	var synced_rows = db.query(
		"SELECT COALESCE(MAX(updated_at), 0) AS ts FROM analytics_ingest_runs WHERE channel_row_id = %s AND status = 'succeeded';"
		% db.quote(channel_row_id)
	)
	var last_synced_at = int(synced_rows[0].get("ts", 0)) if not synced_rows.is_empty() else 0
	return {
		"channel_row_id": channel_row_id,
		"range_start_ymd": range_start_ymd,
		"range_end_ymd": range_end_ymd,
		"snapshot_count": snapshot_count,
		"latest_snapshot_at": latest_snapshot_at,
		"last_synced_at": last_synced_at,
		"availability": _availability(snapshot_count > 0, "" if snapshot_count > 0 else "E_ANALYTICS_EMPTY"),
	}

func run_incremental_sync(
	channel_row_id: String,
	range_start_ymd: String,
	range_end_ymd: String,
	rows: Array = []
) -> Dictionary:
	var run_id = VasIds.new_id("ingest")
	var started_at = int(Time.get_unix_time_from_system())
	db.exec(
		"""
		INSERT INTO analytics_ingest_runs(id, channel_row_id, source, range_start_ymd, range_end_ymd, rows_ingested, status, details_json, created_at, updated_at)
		VALUES (%s, %s, 'analytics_api', %s, %s, 0, 'started', '{}', %d, %d);
		"""
		% [db.quote(run_id), db.quote(channel_row_id), db.quote(range_start_ymd), db.quote(range_end_ymd), started_at, started_at]
	)

	var ingested = 0
	for row in rows:
		var start_ymd = String(row.get("date_ymd", range_start_ymd))
		var end_ymd = String(row.get("date_ymd", range_end_ymd))
		var existing = db.query(
			"SELECT COUNT(*) AS c FROM analytics_snapshots WHERE channel_row_id = %s AND range_start_ymd = %s AND range_end_ymd = %s;"
			% [db.quote(channel_row_id), db.quote(start_ymd), db.quote(end_ymd)]
		)
		var existing_count = int(existing[0].get("c", 0)) if not existing.is_empty() else 0
		if existing_count > 0:
			continue
		var metrics = row.get("metrics", {})
		if typeof(metrics) != TYPE_DICTIONARY:
			metrics = {"value": row}
		store_snapshot(channel_row_id, start_ymd, end_ymd, metrics)
		ingested += 1

	var complete_at = int(Time.get_unix_time_from_system())
	db.exec(
		"""
		UPDATE analytics_ingest_runs
		SET rows_ingested = %d, status = 'succeeded', updated_at = %d
		WHERE id = %s;
		""" % [ingested, complete_at, db.quote(run_id)]
	)
	return {
		"ingest_run_id": run_id,
		"rows_ingested": ingested,
		"status": "succeeded",
		"last_synced_at": complete_at,
	}

func import_reporting_csv(channel_row_id: String, csv_path: String, _report_type: String) -> int:
	if not FileAccess.file_exists(csv_path):
		return 0
	var run_id = VasIds.new_id("ingest")
	var now = int(Time.get_unix_time_from_system())
	db.exec(
		"""
		INSERT INTO analytics_ingest_runs(id, channel_row_id, source, range_start_ymd, range_end_ymd, rows_ingested, status, details_json, created_at, updated_at)
		VALUES (%s, %s, 'manual_import', '', '', 0, 'started', '{}', %d, %d);
		""" % [db.quote(run_id), db.quote(channel_row_id), now, now]
	)

	var text = FileAccess.get_file_as_string(csv_path)
	var lines = text.split("\n", false)
	if lines.size() <= 1:
		return 0

	var headers = lines[0].split(",")
	var date_idx = headers.find("date")
	var currency_idx = headers.find("currency")
	var amount_idx = headers.find("amount")
	if date_idx == -1:
		return 0

	var count = 0
	for i in range(1, lines.size()):
		var line = lines[i].strip_edges()
		if line == "":
			continue
		var cols = line.split(",")
		if cols.size() <= date_idx:
			continue
		var date_ymd = cols[date_idx]
		var currency = cols[currency_idx] if currency_idx >= 0 and cols.size() > currency_idx else "USD"
		var amount_val = 0.0
		if amount_idx >= 0 and cols.size() > amount_idx:
			amount_val = float(cols[amount_idx])
		var micros = int(round(amount_val * 1_000_000.0))
		var row_id = "rev_%s_%s" % [channel_row_id, date_ymd]
		var row_created_at = int(Time.get_unix_time_from_system())
		var sql = """
			INSERT OR REPLACE INTO revenue_records(id, channel_row_id, date_ymd, currency, amount_micros, source, created_at)
			VALUES (%s, %s, %s, %s, %d, 'manual_import', %d);
		""" % [
			db.quote(row_id),
			db.quote(channel_row_id),
			db.quote(date_ymd),
			db.quote(currency),
			micros,
			row_created_at,
		]
		db.exec(sql)
		count += 1

	var done_at = int(Time.get_unix_time_from_system())
	db.exec(
		"""
		UPDATE analytics_ingest_runs
		SET rows_ingested = %d, status = 'succeeded', updated_at = %d, details_json = %s
		WHERE id = %s;
		""" % [count, done_at, db.quote(JSON.stringify({"csv_path": csv_path})), db.quote(run_id)]
	)
	return count

func _availability(available: bool, reason_code: String) -> Dictionary:
	return {
		"available": available,
		"reason_code": reason_code,
		"manual_fallback_available": not available,
	}
