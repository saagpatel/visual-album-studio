extends RefCounted
class_name PythonWorkerAdapter

var worker_cmd: PackedStringArray = PackedStringArray(["python3", "-m", "vas_audio_worker.cli"])

func _init(p_worker_cmd: PackedStringArray = PackedStringArray(["python3", "-m", "vas_audio_worker.cli"])) -> void:
	worker_cmd = p_worker_cmd

func analyze_audio(audio_path: String, temp_dir: String) -> Dictionary:
	DirAccess.make_dir_recursive_absolute(temp_dir)
	var req_path = temp_dir.path_join("worker_req_%s.jsonl" % str(Time.get_ticks_usec()))
	var req = FileAccess.open(req_path, FileAccess.WRITE)
	if req == null:
		return {"ok": false, "error": "E_WORKER_IO", "message": "Failed to create worker request file"}
	req.store_line(JSON.stringify({"audio_path": audio_path}))
	req.close()

	var repo_root = ProjectSettings.globalize_path("res://..")
	var worker_pythonpath = repo_root.path_join("worker")
	var cmd = "cat %s | env PYTHONPATH=%s %s" % [
		_shell_escape(req_path),
		_shell_escape(worker_pythonpath),
		_shell_join(worker_cmd),
	]

	var out: Array = []
	var code = OS.execute("sh", PackedStringArray(["-lc", cmd]), out, true)
	DirAccess.remove_absolute(req_path)

	if code != 0:
		return {
			"ok": false,
			"error": "E_WORKER_UNAVAILABLE",
			"message": "Python worker command failed",
			"details": "\n".join(out),
		}

	for raw in out:
		var line = String(raw).strip_edges()
		if line == "":
			continue
		var parsed: Variant = JSON.parse_string(line)
		if typeof(parsed) == TYPE_DICTIONARY:
			var data: Dictionary = parsed
			data["ok"] = true
			return data

	return {"ok": false, "error": "E_WORKER_INVALID_OUTPUT", "message": "Worker did not return JSON"}

func _shell_join(parts: PackedStringArray) -> String:
	var escaped: Array[String] = []
	for part in parts:
		escaped.append(_shell_escape(part))
	return " ".join(escaped)

func _shell_escape(value: String) -> String:
	return "'" + value.replace("'", "'\"'\"'") + "'"
