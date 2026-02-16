extends RefCounted
class_name ExportCommandCenterShell

var ux_service

func _init(p_ux_service = null) -> void:
	ux_service = p_ux_service

func render_state(jobs: Array) -> Dictionary:
	if ux_service == null:
		return {
			"buckets": {},
			"recovery_actions": [],
		}
	return ux_service.build_export_command_center(jobs)
