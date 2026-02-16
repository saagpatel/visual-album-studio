extends RefCounted
class_name RevenueService

var db

func _init(p_db = null) -> void:
	db = p_db

func import_revenue_csv(channel_row_id: String, csv_path: String) -> int:
	var analytics = AnalyticsService.new(db)
	return analytics.import_reporting_csv(channel_row_id, csv_path, "revenue")
