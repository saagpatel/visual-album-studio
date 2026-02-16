extends RefCounted
class_name DiagnosticsPanel

var productization_service

func _init(p_productization_service = null) -> void:
	productization_service = p_productization_service

func export_support_bundle(scope: Dictionary) -> Dictionary:
	if productization_service == null:
		return {
			"ok": false,
			"error": "service_missing",
		}
	return productization_service.export_diagnostics(scope)

func build_support_report(context: Dictionary) -> Dictionary:
	if productization_service == null:
		return {
			"id": "",
			"severity": "error",
			"summary": "productization service missing",
			"details": context,
		}
	return productization_service.generate_support_report(context)
