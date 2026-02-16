extends RefCounted
class_name UxTypes

class UxTokenSet:
	extends RefCounted
	var spacing_scale: Array = []
	var typography_scale: Dictionary = {}
	var color_roles: Dictionary = {}
	var state_roles: Dictionary = {}

	func _init(
		p_spacing_scale: Array = [],
		p_typography_scale: Dictionary = {},
		p_color_roles: Dictionary = {},
		p_state_roles: Dictionary = {}
	) -> void:
		spacing_scale = p_spacing_scale.duplicate()
		typography_scale = p_typography_scale.duplicate(true)
		color_roles = p_color_roles.duplicate(true)
		state_roles = p_state_roles.duplicate(true)

	func to_dict() -> Dictionary:
		return {
			"spacing_scale": spacing_scale.duplicate(),
			"typography_scale": typography_scale.duplicate(true),
			"color_roles": color_roles.duplicate(true),
			"state_roles": state_roles.duplicate(true),
		}


class AccessibilityReport:
	extends RefCounted
	var screen_id: String = ""
	var ok: bool = true
	var violations: Array = []
	var checks: Dictionary = {}

	func _init(
		p_screen_id: String = "",
		p_ok: bool = true,
		p_violations: Array = [],
		p_checks: Dictionary = {}
	) -> void:
		screen_id = p_screen_id
		ok = p_ok
		violations = p_violations.duplicate(true)
		checks = p_checks.duplicate(true)

	func to_dict() -> Dictionary:
		return {
			"screen_id": screen_id,
			"ok": ok,
			"violations": violations.duplicate(true),
			"checks": checks.duplicate(true),
		}


class CommandSpec:
	extends RefCounted
	var id: String = ""
	var label: String = ""
	var description: String = ""
	var tags: Array = []
	var idempotent: bool = true

	func _init(
		p_id: String = "",
		p_label: String = "",
		p_description: String = "",
		p_tags: Array = [],
		p_idempotent: bool = true
	) -> void:
		id = p_id
		label = p_label
		description = p_description
		tags = p_tags.duplicate()
		idempotent = p_idempotent

	func to_dict() -> Dictionary:
		return {
			"id": id,
			"label": label,
			"description": description,
			"tags": tags.duplicate(),
			"idempotent": idempotent,
		}


class CommandResult:
	extends RefCounted
	var command_id: String = ""
	var ok: bool = false
	var message: String = ""
	var data: Dictionary = {}

	func _init(p_command_id: String = "", p_ok: bool = false, p_message: String = "", p_data: Dictionary = {}) -> void:
		command_id = p_command_id
		ok = p_ok
		message = p_message
		data = p_data.duplicate(true)

	func to_dict() -> Dictionary:
		return {
			"command_id": command_id,
			"ok": ok,
			"message": message,
			"data": data.duplicate(true),
		}
