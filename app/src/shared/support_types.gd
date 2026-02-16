extends RefCounted
class_name SupportTypes

class DiagnosticsBundleInfo:
	extends RefCounted
	var id: String = ""
	var output_path: String = ""
	var redaction_summary: Dictionary = {}
	var created_at: int = 0

	func _init(
		p_id: String = "",
		p_output_path: String = "",
		p_redaction_summary: Dictionary = {},
		p_created_at: int = 0
	) -> void:
		id = p_id
		output_path = p_output_path
		redaction_summary = p_redaction_summary.duplicate(true)
		created_at = p_created_at

	func to_dict() -> Dictionary:
		return {
			"id": id,
			"output_path": output_path,
			"redaction_summary": redaction_summary.duplicate(true),
			"created_at": created_at,
		}


class PackageManifest:
	extends RefCounted
	var profile_id: String = ""
	var manifest_path: String = ""
	var content_sha256: String = ""
	var created_at: int = 0

	func _init(
		p_profile_id: String = "",
		p_manifest_path: String = "",
		p_content_sha256: String = "",
		p_created_at: int = 0
	) -> void:
		profile_id = p_profile_id
		manifest_path = p_manifest_path
		content_sha256 = p_content_sha256
		created_at = p_created_at

	func to_dict() -> Dictionary:
		return {
			"profile_id": profile_id,
			"manifest_path": manifest_path,
			"content_sha256": content_sha256,
			"created_at": created_at,
		}


class SupportReport:
	extends RefCounted
	var id: String = ""
	var severity: String = "info"
	var summary: String = ""
	var details: Dictionary = {}

	func _init(
		p_id: String = "",
		p_severity: String = "info",
		p_summary: String = "",
		p_details: Dictionary = {}
	) -> void:
		id = p_id
		severity = p_severity
		summary = p_summary
		details = p_details.duplicate(true)

	func to_dict() -> Dictionary:
		return {
			"id": id,
			"severity": severity,
			"summary": summary,
			"details": details.duplicate(true),
		}
