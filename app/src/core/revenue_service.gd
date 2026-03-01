extends RefCounted
class_name RevenueService

const VasIds = preload("res://src/shared/ids.gd")
const AnalyticsService = preload("res://src/core/analytics_service.gd")

var db

func _init(p_db = null) -> void:
	db = p_db

func import_revenue_csv(channel_row_id: String, csv_path: String) -> int:
	var analytics = AnalyticsService.new(db)
	return analytics.import_reporting_csv(channel_row_id, csv_path, "revenue")

func list_revenue_rows(channel_row_id: String) -> Array:
	return db.query(
		"""
		SELECT id, channel_row_id, date_ymd, currency, amount_micros, source, created_at
		FROM revenue_records
		WHERE channel_row_id = %s
		ORDER BY date_ymd ASC, id ASC;
		""" % db.quote(channel_row_id)
	)

func delete_revenue_row(row_id: String) -> bool:
	var result = db.exec("DELETE FROM revenue_records WHERE id = %s;" % db.quote(row_id))
	return bool(result.get("ok", false))

func upsert_manual_revenue_row(channel_row_id: String, date_ymd: String, currency: String, amount_micros: int) -> String:
	var row_id = "rev_manual_%s_%s" % [channel_row_id, date_ymd]
	var now = int(Time.get_unix_time_from_system())
	db.exec(
		"""
		INSERT OR REPLACE INTO revenue_records(id, channel_row_id, date_ymd, currency, amount_micros, source, created_at)
		VALUES (%s, %s, %s, %s, %d, 'manual_import', %d);
		""" % [db.quote(row_id), db.quote(channel_row_id), db.quote(date_ymd), db.quote(currency), amount_micros, now]
	)
	return row_id
