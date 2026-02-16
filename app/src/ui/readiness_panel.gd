extends RefCounted
class_name ReadinessPanel

var ux_service

func _init(p_ux_service = null) -> void:
	ux_service = p_ux_service

func run_checks(output_dir: String) -> Dictionary:
	if ux_service == null:
		return {
			"ok": false,
			"issues": ["ux_service_missing"],
			"checks": {},
		}
	return ux_service.readiness_report(output_dir)
