extends RefCounted
class_name CommandPaletteShell

var ux_service

func _init(p_ux_service = null) -> void:
	ux_service = p_ux_service

func register_commands(commands: Array) -> void:
	if ux_service == null:
		return
	for command in commands:
		if typeof(command) != TYPE_DICTIONARY:
			continue
		ux_service.register_command(command)

func search(query: String) -> Array:
	if ux_service == null:
		return []
	return ux_service.search_commands(query)

func execute(command_id: String, args: Dictionary = {}) -> Dictionary:
	if ux_service == null:
		return {"ok": false, "message": "ux_service_missing"}
	return ux_service.run_command(command_id, args)
