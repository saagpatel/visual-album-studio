extends RefCounted
class_name SQLiteAdapter

var db_path: String
var sqlite_bin: String = "sqlite3"

func _init(p_db_path: String = "", p_sqlite_bin: String = "sqlite3") -> void:
	db_path = p_db_path
	sqlite_bin = p_sqlite_bin
	if db_path != "":
		var parent = db_path.get_base_dir()
		if parent != "":
			DirAccess.make_dir_recursive_absolute(parent)

func quote(value: Variant) -> String:
	match typeof(value):
		TYPE_NIL:
			return "NULL"
		TYPE_BOOL:
			return "1" if value else "0"
		TYPE_INT, TYPE_FLOAT:
			return str(value)
		TYPE_STRING:
			return "'%s'" % String(value).replace("'", "''")
		_:
			return "'%s'" % JSON.stringify(value).replace("'", "''")

func exec(sql: String) -> Dictionary:
	var out: Array = []
	var code = OS.execute(sqlite_bin, PackedStringArray([db_path, sql]), out, true)
	return {
		"ok": code == 0,
		"code": code,
		"output": "\n".join(out),
	}

func query(sql: String) -> Array:
	var out: Array = []
	var code = OS.execute(sqlite_bin, PackedStringArray(["-json", db_path, sql]), out, true)
	if code != 0:
		push_error("SQLite query failed (%d): %s\n%s" % [code, sql, "\n".join(out)])
		return []
	var raw = "\n".join(out).strip_edges()
	if raw == "":
		return []
	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_ARRAY:
		push_error("SQLite returned non-array JSON: %s" % raw)
		return []
	return parsed

func scalar(sql: String, fallback: Variant = null) -> Variant:
	var rows = query(sql)
	if rows.is_empty():
		return fallback
	var row: Dictionary = rows[0]
	if row.is_empty():
		return fallback
	var key: String = row.keys()[0]
	return row.get(key, fallback)

func ensure_wal() -> void:
	exec("PRAGMA journal_mode=WAL;")

func current_schema_version() -> int:
	_ensure_migrations_table()
	var v = scalar("SELECT COALESCE(MAX(version), 0) AS v FROM schema_migrations;", 0)
	return int(v)

func apply_migrations(migrations_dir: String, max_version: int = -1) -> int:
	_ensure_migrations_table()
	ensure_wal()

	var dir = DirAccess.open(migrations_dir)
	if dir == null:
		push_error("Missing migrations dir: %s" % migrations_dir)
		return current_schema_version()

	var files = dir.get_files()
	files.sort()

	var current = current_schema_version()
	for file_name in files:
		if not file_name.ends_with(".sql"):
			continue
		var prefix = file_name.split("_", false, 1)[0]
		if not prefix.is_valid_int():
			continue
		var version = int(prefix)
		if version <= current:
			continue
		if max_version >= 0 and version > max_version:
			continue

		var sql_path = migrations_dir.path_join(file_name)
		var sql_text = FileAccess.get_file_as_string(sql_path)
		if sql_text == "":
			push_error("Empty migration: %s" % sql_path)
			return current

		var checksum = _sha256_text(sql_text)
		var wrapped = "BEGIN;\n%s\nINSERT INTO schema_migrations(version, name, checksum, applied_at) VALUES (%d, %s, %s, %d);\nCOMMIT;" % [
			sql_text,
			version,
			quote(file_name),
			quote(checksum),
			int(Time.get_unix_time_from_system()),
		]
		var result = exec(wrapped)
		if not result["ok"]:
			exec("ROLLBACK;")
			push_error("Failed migration %s: %s" % [file_name, result["output"]])
			return current
		current = version

	return current

func _ensure_migrations_table() -> void:
	exec("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, checksum TEXT NOT NULL, applied_at INTEGER NOT NULL);")

func _sha256_text(text: String) -> String:
	var hash = HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(text.to_utf8_buffer())
	return hash.finish().hex_encode()
