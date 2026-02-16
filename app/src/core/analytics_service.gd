extends RefCounted
class_name AnalyticsService

const VasIds = preload("res://src/shared/ids.gd")

var db

func _init(p_db = null) -> void:
	db = p_db

func store_snapshot(channel_row_id: String, start_ymd: String, end_ymd: String, metrics: Dictionary) -> String:
	var snapshot_id = VasIds.new_id("snapshot")
	var now = int(Time.get_unix_time_from_system())
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
		now,
	]
	db.exec(sql)
	return snapshot_id

func import_reporting_csv(channel_row_id: String, csv_path: String, _report_type: String) -> int:
	if not FileAccess.file_exists(csv_path):
		return 0
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
		var now = int(Time.get_unix_time_from_system())
		var sql = """
			INSERT OR REPLACE INTO revenue_records(id, channel_row_id, date_ymd, currency, amount_micros, source, created_at)
			VALUES (%s, %s, %s, %s, %d, 'manual_import', %d);
		""" % [
			db.quote(row_id),
			db.quote(channel_row_id),
			db.quote(date_ymd),
			db.quote(currency),
			micros,
			now,
		]
		db.exec(sql)
		count += 1
	return count
