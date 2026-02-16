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
