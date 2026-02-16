extends RefCounted
class_name KeyringAdapter

var helper_path: String = "native/vas_keyring/target/debug/vas_keyring"

func _init(p_helper_path: String = "native/vas_keyring/target/debug/vas_keyring") -> void:
	helper_path = p_helper_path

func set_secret(service: String, account: String, secret: String) -> Dictionary:
	return _run(PackedStringArray(["set", service, account, secret]))

func get_secret(service: String, account: String) -> Dictionary:
	return _run(PackedStringArray(["get", service, account]))

func delete_secret(service: String, account: String) -> Dictionary:
	return _run(PackedStringArray(["delete", service, account]))

func _run(args: PackedStringArray) -> Dictionary:
	var out: Array = []
	var code = OS.execute(helper_path, args, out, true)
	return {
		"ok": code == 0,
		"code": code,
		"output": "\n".join(out).strip_edges(),
	}
