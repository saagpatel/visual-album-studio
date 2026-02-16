extends RefCounted
class_name VasError

var code: String
var message: String
var details: Dictionary
var recoverable: bool
var hint: String

func _init(p_code: String = "E_UNKNOWN", p_message: String = "", p_details: Dictionary = {}, p_recoverable: bool = false, p_hint: String = "") -> void:
	code = p_code
	message = p_message
	details = p_details
	recoverable = p_recoverable
	hint = p_hint
