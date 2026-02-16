extends RefCounted
class_name VasIds

static func new_id(prefix: String) -> String:
	return "%s_%s" % [prefix, str(Time.get_unix_time_from_system())]
