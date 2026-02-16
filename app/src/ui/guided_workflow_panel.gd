extends RefCounted
class_name GuidedWorkflowPanel

var ux_service

func _init(p_ux_service = null) -> void:
	ux_service = p_ux_service

func evaluate(state: Dictionary) -> Dictionary:
	if ux_service == null:
		return {
			"next_step": "import_assets",
			"can_queue_export": false,
			"is_complete": false,
		}
	return ux_service.guided_workflow_status(state)
