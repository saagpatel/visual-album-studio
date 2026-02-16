extends RefCounted
class_name SQLiteAdapter

var db_path: String

func _init(p_db_path: String = "") -> void:
	db_path = p_db_path
