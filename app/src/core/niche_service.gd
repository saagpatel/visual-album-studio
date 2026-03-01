extends RefCounted
class_name NicheService

const VasIds = preload("res://src/shared/ids.gd")

var db

func _init(p_db = null) -> void:
	db = p_db

func add_keyword(keyword: String) -> String:
	var keyword_id = VasIds.new_id("kw")
	var now = int(Time.get_unix_time_from_system())
	db.exec("INSERT INTO niche_keywords(id, channel_row_id, keyword, created_at) VALUES (%s, NULL, %s, %d);" % [db.quote(keyword_id), db.quote(keyword), now])
	return keyword_id

func add_note(keyword_id: String, text: String) -> String:
	var note_id = VasIds.new_id("note")
	var now = int(Time.get_unix_time_from_system())
	db.exec("INSERT INTO niche_notes(id, keyword_id, note_text, created_at, updated_at) VALUES (%s, %s, %s, %d, %d);" % [db.quote(note_id), db.quote(keyword_id), db.quote(text), now, now])
	return note_id

func list_keywords(limit: int = 200) -> Array:
	return db.query(
		"""
		SELECT id, keyword, created_at
		FROM niche_keywords
		ORDER BY created_at DESC
		LIMIT %d;
		""" % limit
	)

func list_notes(keyword_id: String, limit: int = 500) -> Array:
	return db.query(
		"""
		SELECT id, keyword_id, note_text, created_at, updated_at
		FROM niche_notes
		WHERE keyword_id = %s
		ORDER BY updated_at DESC
		LIMIT %d;
		""" % [db.quote(keyword_id), limit]
	)

func estimate_quota_for_lookup(terms: Array) -> Dictionary:
	var term_count = max(1, terms.size())
	var estimated_units = term_count * 100
	return {
		"estimated_units": estimated_units,
		"availability": _availability(true, ""),
	}

func run_optional_lookup(terms: Array, quota_budget: int = 10000, quota_used: int = 0) -> Dictionary:
	var estimate = estimate_quota_for_lookup(terms)
	var estimated_units = int(estimate.get("estimated_units", 0))
	var remaining = quota_budget - quota_used
	if estimated_units > remaining:
		return {
			"ok": false,
			"results": [],
			"availability": _availability(false, "E_QUOTA_BUDGET_EXCEEDED"),
			"estimated_units": estimated_units,
		}
	var results: Array = []
	for term in terms:
		results.append({
			"term": String(term),
			"score": 0.5,
			"source": "manual_notebook",
		})
	return {
		"ok": true,
		"results": results,
		"availability": _availability(true, ""),
		"estimated_units": estimated_units,
	}

func _availability(available: bool, reason_code: String) -> Dictionary:
	return {
		"available": available,
		"reason_code": reason_code,
		"manual_fallback_available": not available,
	}
