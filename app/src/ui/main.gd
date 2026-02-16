extends Control

const SQLiteAdapter = preload("res://src/adapters/sqlite_adapter.gd")
const DiagnosticsAdapter = preload("res://src/adapters/diagnostics_adapter.gd")
const PackagingAdapter = preload("res://src/adapters/packaging_adapter.gd")
const UxPlatformService = preload("res://src/core/ux_platform_service.gd")
const ProductizationService = preload("res://src/core/productization_service.gd")
const GuidedWorkflowPanel = preload("res://src/ui/guided_workflow_panel.gd")
const ReadinessPanel = preload("res://src/ui/readiness_panel.gd")
const CommandPaletteShell = preload("res://src/ui/command_palette_shell.gd")
const ExportCommandCenterShell = preload("res://src/ui/export_command_center_shell.gd")
const DiagnosticsPanel = preload("res://src/ui/diagnostics_panel.gd")

const COLOR_BG := Color("161a22")
const COLOR_BG_MID := Color("1f2431")
const COLOR_BG_END := Color("262b39")
const COLOR_SURFACE := Color("2a3040")
const COLOR_SURFACE_SOFT := Color("252b39")
const COLOR_BORDER := Color("4b5469")
const COLOR_TEXT := Color("f4f6fb")
const COLOR_MUTED := Color("bac3d8")
const COLOR_ACCENT := Color("58a7ff")
const COLOR_SUCCESS := Color("52d28a")
const COLOR_WARNING := Color("f2b75c")
const COLOR_DANGER := Color("ff7676")

const TWO_COLUMN_WIDTH := 1050
const CARD_MIN_WIDTH := 420

var repo_root: String = ""
var out_root: String = ""

var db
var ux_service
var productization_service

var guided_panel
var readiness_panel
var command_palette
var command_center_shell
var diagnostics_panel

var cards_grid: GridContainer
var last_updated_label: Label
var data_path_label: Label
var release_channel_selector: OptionButton
var release_channel_note: Label

var readiness_summary_label: Label
var readiness_checks_label: Label
var workflow_summary_label: Label
var workflow_details_label: Label
var command_summary_label: Label
var command_result_label: Label
var queue_summary_label: Label
var queue_recovery_label: Label
var diagnostics_summary_label: Label
var diagnostics_details_label: Label
var packaging_summary_label: Label

var chip_readiness: Dictionary = {}
var chip_workflow: Dictionary = {}
var chip_queue: Dictionary = {}
var chip_diagnostics: Dictionary = {}

var _release_channel_ids: Array = []
var _last_command_result: Dictionary = {}
var _last_diagnostics_result: Dictionary = {}
var _last_packaging_result: Dictionary = {}

func _ready() -> void:
	_resolve_paths()
	_initialize_services()
	_build_ui()
	_refresh_all()

func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		_update_responsive_layout()

func _resolve_paths() -> void:
	var app_root = ProjectSettings.globalize_path("res://").trim_suffix("/")
	repo_root = app_root.get_base_dir()
	out_root = repo_root.path_join("out/runtime_ui")
	DirAccess.make_dir_recursive_absolute(out_root)

func _initialize_services() -> void:
	db = SQLiteAdapter.new(out_root.path_join("vas.db"))
	db.apply_migrations(repo_root.path_join("migrations"), 7)

	ux_service = UxPlatformService.new(db)
	productization_service = ProductizationService.new(
		db,
		DiagnosticsAdapter.new(),
		PackagingAdapter.new(),
		{
			"root": repo_root,
			"out_dir": out_root,
		}
	)

	guided_panel = GuidedWorkflowPanel.new(ux_service)
	readiness_panel = ReadinessPanel.new(ux_service)
	command_palette = CommandPaletteShell.new(ux_service)
	command_center_shell = ExportCommandCenterShell.new(ux_service)
	diagnostics_panel = DiagnosticsPanel.new(productization_service)

	command_palette.register_commands([
		{
			"id": "export.retry_last",
			"label": "Retry Last Export",
			"description": "Retry the latest failed export job",
			"idempotent": true,
		},
		{
			"id": "diagnostics.export",
			"label": "Export Diagnostics",
			"description": "Create a support diagnostics bundle",
			"idempotent": true,
		},
		{
			"id": "packaging.dry_run",
			"label": "Packaging Dry Run",
			"description": "Generate deterministic release manifest preview",
			"idempotent": true,
		},
	])

func _build_ui() -> void:
	for child in get_children():
		child.queue_free()

	var gradient_backdrop = TextureRect.new()
	gradient_backdrop.anchor_right = 1.0
	gradient_backdrop.anchor_bottom = 1.0
	gradient_backdrop.grow_horizontal = Control.GROW_DIRECTION_BOTH
	gradient_backdrop.grow_vertical = Control.GROW_DIRECTION_BOTH
	gradient_backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	gradient_backdrop.texture = _build_gradient_texture()
	gradient_backdrop.stretch_mode = TextureRect.STRETCH_SCALE
	add_child(gradient_backdrop)

	var root_margin = MarginContainer.new()
	root_margin.anchor_right = 1.0
	root_margin.anchor_bottom = 1.0
	root_margin.add_theme_constant_override("margin_left", 24)
	root_margin.add_theme_constant_override("margin_top", 20)
	root_margin.add_theme_constant_override("margin_right", 24)
	root_margin.add_theme_constant_override("margin_bottom", 20)
	add_child(root_margin)

	var page = VBoxContainer.new()
	page.add_theme_constant_override("separation", 14)
	root_margin.add_child(page)

	var hero = _new_card_panel(true)
	page.add_child(hero)
	var hero_margin = _new_inner_margin(hero, 20)
	var hero_content = VBoxContainer.new()
	hero_content.add_theme_constant_override("separation", 10)
	hero_margin.add_child(hero_content)

	var hero_top = HBoxContainer.new()
	hero_top.add_theme_constant_override("separation", 10)
	hero_content.add_child(hero_top)

	var title = Label.new()
	title.text = "Visual Album Studio"
	title.add_theme_font_size_override("font_size", 34)
	title.add_theme_color_override("font_color", COLOR_TEXT)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hero_top.add_child(title)

	var phase_badge = _new_badge("Phase 7")
	hero_top.add_child(phase_badge)

	last_updated_label = Label.new()
	last_updated_label.text = "Updated --"
	last_updated_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	last_updated_label.add_theme_color_override("font_color", COLOR_MUTED)
	hero_top.add_child(last_updated_label)

	var subtitle = Label.new()
	subtitle.text = "Workspace dashboard for readiness, guided flow, command recovery, and diagnostics export."
	subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	subtitle.add_theme_font_size_override("font_size", 16)
	subtitle.add_theme_color_override("font_color", COLOR_MUTED)
	hero_content.add_child(subtitle)

	var action_row = HFlowContainer.new()
	action_row.add_theme_constant_override("h_separation", 10)
	action_row.add_theme_constant_override("v_separation", 10)
	hero_content.add_child(action_row)

	action_row.add_child(_new_action_button("Refresh Dashboard", Callable(self, "_on_refresh_pressed"), "primary"))
	action_row.add_child(_new_action_button("Run Demo Command", Callable(self, "_on_demo_command_pressed"), "neutral"))
	action_row.add_child(_new_action_button("Export Diagnostics", Callable(self, "_on_export_diagnostics_pressed"), "accent"))
	action_row.add_child(_new_action_button("Packaging Dry Run", Callable(self, "_on_packaging_dry_run_pressed"), "neutral"))

	var chip_row = HFlowContainer.new()
	chip_row.add_theme_constant_override("h_separation", 10)
	chip_row.add_theme_constant_override("v_separation", 10)
	hero_content.add_child(chip_row)

	chip_readiness = _new_chip("Readiness: --", "neutral")
	chip_workflow = _new_chip("Workflow: --", "neutral")
	chip_queue = _new_chip("Queue: --", "neutral")
	chip_diagnostics = _new_chip("Diagnostics: --", "neutral")

	chip_row.add_child(chip_readiness.get("panel"))
	chip_row.add_child(chip_workflow.get("panel"))
	chip_row.add_child(chip_queue.get("panel"))
	chip_row.add_child(chip_diagnostics.get("panel"))

	cards_grid = GridContainer.new()
	cards_grid.columns = 2
	cards_grid.size_flags_vertical = Control.SIZE_EXPAND_FILL
	cards_grid.add_theme_constant_override("h_separation", 14)
	cards_grid.add_theme_constant_override("v_separation", 14)
	page.add_child(cards_grid)

	var readiness_card = _new_dashboard_card(
		"Readiness Checks",
		"System validation for FFmpeg, output path, and disk probe availability."
	)
	cards_grid.add_child(readiness_card.get("panel"))
	var readiness_body: VBoxContainer = readiness_card.get("body")
	readiness_summary_label = _new_body_label(16, COLOR_TEXT)
	readiness_checks_label = _new_body_label(14, COLOR_MUTED)
	readiness_body.add_child(readiness_summary_label)
	readiness_body.add_child(readiness_checks_label)

	var workflow_card = _new_dashboard_card(
		"Guided Workflow",
		"State machine checkpoint from import through provenance and queue readiness."
	)
	cards_grid.add_child(workflow_card.get("panel"))
	var workflow_body: VBoxContainer = workflow_card.get("body")
	workflow_summary_label = _new_body_label(16, COLOR_TEXT)
	workflow_details_label = _new_body_label(14, COLOR_MUTED)
	workflow_body.add_child(workflow_summary_label)
	workflow_body.add_child(workflow_details_label)

	var command_card = _new_dashboard_card(
		"Command Center",
		"Command palette coverage and recovery actions for failed export jobs."
	)
	cards_grid.add_child(command_card.get("panel"))
	var command_body: VBoxContainer = command_card.get("body")
	command_summary_label = _new_body_label(16, COLOR_TEXT)
	command_result_label = _new_body_label(14, COLOR_MUTED)
	queue_summary_label = _new_body_label(14, COLOR_TEXT)
	queue_recovery_label = _new_body_label(14, COLOR_MUTED)
	command_body.add_child(command_summary_label)
	command_body.add_child(command_result_label)
	command_body.add_child(queue_summary_label)
	command_body.add_child(queue_recovery_label)

	var diagnostics_card = _new_dashboard_card(
		"Diagnostics + Productization",
		"Support bundle status, release channel selection, and deterministic packaging manifest."
	)
	cards_grid.add_child(diagnostics_card.get("panel"))
	var diagnostics_body: VBoxContainer = diagnostics_card.get("body")

	var channel_row = HBoxContainer.new()
	channel_row.add_theme_constant_override("separation", 8)
	diagnostics_body.add_child(channel_row)

	var channel_label = Label.new()
	channel_label.text = "Release channel"
	channel_label.add_theme_color_override("font_color", COLOR_MUTED)
	channel_row.add_child(channel_label)

	release_channel_selector = OptionButton.new()
	release_channel_selector.item_selected.connect(_on_release_channel_selected)
	channel_row.add_child(release_channel_selector)

	release_channel_note = _new_body_label(13, COLOR_MUTED)
	release_channel_note.text = ""
	diagnostics_body.add_child(release_channel_note)

	diagnostics_summary_label = _new_body_label(16, COLOR_TEXT)
	diagnostics_details_label = _new_body_label(14, COLOR_MUTED)
	packaging_summary_label = _new_body_label(14, COLOR_TEXT)
	diagnostics_body.add_child(diagnostics_summary_label)
	diagnostics_body.add_child(diagnostics_details_label)
	diagnostics_body.add_child(packaging_summary_label)

	data_path_label = _new_body_label(13, COLOR_MUTED)
	data_path_label.text = "Data path: %s" % out_root
	page.add_child(data_path_label)

	_populate_release_channels()
	_update_responsive_layout()

func _new_dashboard_card(title_text: String, subtitle_text: String) -> Dictionary:
	var panel = _new_card_panel(false)
	panel.custom_minimum_size = Vector2(CARD_MIN_WIDTH, 180)
	var margin = _new_inner_margin(panel, 18)

	var layout = VBoxContainer.new()
	layout.add_theme_constant_override("separation", 8)
	margin.add_child(layout)

	var title = Label.new()
	title.text = title_text
	title.add_theme_font_size_override("font_size", 21)
	title.add_theme_color_override("font_color", COLOR_TEXT)
	layout.add_child(title)

	var subtitle = Label.new()
	subtitle.text = subtitle_text
	subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	subtitle.add_theme_font_size_override("font_size", 13)
	subtitle.add_theme_color_override("font_color", COLOR_MUTED)
	layout.add_child(subtitle)

	layout.add_child(HSeparator.new())

	var body = VBoxContainer.new()
	body.add_theme_constant_override("separation", 7)
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_child(body)

	return {
		"panel": panel,
		"body": body,
	}

func _new_card_panel(is_hero: bool) -> PanelContainer:
	var panel = PanelContainer.new()
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.add_theme_stylebox_override(
		"panel",
		_panel_style(
			COLOR_SURFACE if is_hero else COLOR_SURFACE_SOFT,
			COLOR_ACCENT if is_hero else COLOR_BORDER,
			16 if is_hero else 14,
			2 if is_hero else 1
		)
	)
	return panel

func _new_inner_margin(parent: Control, margin_px: int) -> MarginContainer:
	var margin = MarginContainer.new()
	margin.add_theme_constant_override("margin_left", margin_px)
	margin.add_theme_constant_override("margin_top", margin_px)
	margin.add_theme_constant_override("margin_right", margin_px)
	margin.add_theme_constant_override("margin_bottom", margin_px)
	parent.add_child(margin)
	return margin

func _new_action_button(text: String, callback: Callable, tone: String) -> Button:
	var button = Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(170, 38)
	button.add_theme_stylebox_override("normal", _button_style(tone, "normal"))
	button.add_theme_stylebox_override("hover", _button_style(tone, "hover"))
	button.add_theme_stylebox_override("pressed", _button_style(tone, "pressed"))
	button.add_theme_stylebox_override("focus", _button_style(tone, "hover"))
	button.add_theme_color_override("font_color", COLOR_TEXT)
	button.add_theme_color_override("font_hover_color", COLOR_TEXT)
	button.add_theme_color_override("font_pressed_color", COLOR_TEXT)
	button.pressed.connect(callback)
	return button

func _new_badge(text: String) -> PanelContainer:
	var panel = PanelContainer.new()
	panel.add_theme_stylebox_override("panel", _chip_style("accent"))
	var margin = _new_inner_margin(panel, 8)
	var label = Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 13)
	label.add_theme_color_override("font_color", COLOR_TEXT)
	margin.add_child(label)
	return panel

func _new_chip(text: String, tone: String) -> Dictionary:
	var panel = PanelContainer.new()
	panel.add_theme_stylebox_override("panel", _chip_style(tone))
	var margin = _new_inner_margin(panel, 8)
	var label = Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 13)
	label.add_theme_color_override("font_color", COLOR_TEXT)
	margin.add_child(label)
	return {
		"panel": panel,
		"label": label,
	}

func _new_body_label(size_px: int, color: Color) -> Label:
	var label = Label.new()
	label.add_theme_font_size_override("font_size", size_px)
	label.add_theme_color_override("font_color", color)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return label

func _panel_style(bg: Color, border: Color, radius: int, border_width: int) -> StyleBoxFlat:
	var style = StyleBoxFlat.new()
	style.bg_color = bg
	style.border_color = border
	style.border_width_left = border_width
	style.border_width_top = border_width
	style.border_width_right = border_width
	style.border_width_bottom = border_width
	style.corner_radius_top_left = radius
	style.corner_radius_top_right = radius
	style.corner_radius_bottom_right = radius
	style.corner_radius_bottom_left = radius
	return style

func _chip_style(tone: String) -> StyleBoxFlat:
	var palette = _tone_palette(tone)
	var bg: Color = palette.get("bg", Color("2d3344"))
	var border: Color = palette.get("border", Color("596178"))
	return _panel_style(bg, border, 999, 1)

func _button_style(tone: String, state: String) -> StyleBoxFlat:
	var palette = _tone_palette(tone)
	var normal_bg: Color = palette.get("bg", Color("2d3344"))
	var border: Color = palette.get("border", Color("596178"))
	var bg = normal_bg
	if state == "hover":
		bg = normal_bg.lightened(0.08)
	elif state == "pressed":
		bg = normal_bg.darkened(0.1)
	return _panel_style(bg, border, 10, 1)

func _tone_palette(tone: String) -> Dictionary:
	match tone:
		"success":
			return {
				"bg": Color("1f3a2d"),
				"border": COLOR_SUCCESS,
			}
		"warning":
			return {
				"bg": Color("413421"),
				"border": COLOR_WARNING,
			}
		"danger":
			return {
				"bg": Color("432830"),
				"border": COLOR_DANGER,
			}
		"accent":
			return {
				"bg": Color("233a57"),
				"border": COLOR_ACCENT,
			}
		"primary":
			return {
				"bg": Color("2f5f99"),
				"border": Color("7bc2ff"),
			}
		_:
			return {
				"bg": Color("323a4d"),
				"border": Color("646f89"),
			}

func _build_gradient_texture() -> GradientTexture2D:
	var gradient = Gradient.new()
	gradient.colors = PackedColorArray([COLOR_BG, COLOR_BG_MID, COLOR_BG_END])
	gradient.offsets = PackedFloat32Array([0.0, 0.55, 1.0])
	var texture = GradientTexture2D.new()
	texture.gradient = gradient
	texture.width = 2
	texture.height = 1024
	texture.fill = GradientTexture2D.FILL_LINEAR
	texture.fill_from = Vector2(0.0, 0.0)
	texture.fill_to = Vector2(1.0, 1.0)
	return texture

func _populate_release_channels() -> void:
	release_channel_selector.clear()
	_release_channel_ids.clear()
	var channels = productization_service.get_release_channels()
	var selected_index = 0
	for index in range(channels.size()):
		var entry: Dictionary = channels[index]
		var id = String(entry.get("id", "stable"))
		release_channel_selector.add_item(id.capitalize())
		_release_channel_ids.append(id)
		if bool(entry.get("selected", false)):
			selected_index = index
	release_channel_selector.select(selected_index)

func _set_chip(chip: Dictionary, text: String, tone: String) -> void:
	var panel = chip.get("panel")
	var label = chip.get("label")
	if panel is PanelContainer:
		panel.add_theme_stylebox_override("panel", _chip_style(tone))
	if label is Label:
		label.text = text
	_pulse(chip.get("panel"))

func _update_responsive_layout() -> void:
	if cards_grid == null:
		return
	cards_grid.columns = 2 if size.x >= TWO_COLUMN_WIDTH else 1

func _refresh_all() -> void:
	var readiness = readiness_panel.run_checks(out_root.path_join("exports"))
	var readiness_ok = bool(readiness.get("ok", false))
	var readiness_issues: Array = readiness.get("issues", [])
	var readiness_checks: Dictionary = readiness.get("checks", {})

	_set_chip(chip_readiness, "Readiness: %s" % ("OK" if readiness_ok else "Review"), "success" if readiness_ok else "warning")
	readiness_summary_label.text = "System is ready for export queueing." if readiness_ok else "Readiness requires attention before export."
	readiness_checks_label.text = "ffmpeg=%s  |  output_writable=%s  |  disk_probe=%s" % [
		_bool_label(bool(readiness_checks.get("ffmpeg_available", false))),
		_bool_label(bool(readiness_checks.get("output_writable", false))),
		_bool_label(bool(readiness_checks.get("disk_check_available", false))),
	]
	if not readiness_issues.is_empty():
		readiness_checks_label.text += "\nIssues: %s" % ", ".join(readiness_issues)

	var workflow = guided_panel.evaluate({
		"assets_imported": true,
		"preset_selected": true,
		"provenance_complete": true,
		"export_queued": false,
	})
	var next_step = String(workflow.get("next_step", "import_assets"))
	var can_queue = bool(workflow.get("can_queue_export", false))
	var workflow_tone = "success" if can_queue else "warning"
	_set_chip(chip_workflow, "Workflow: %s" % _humanize_step(next_step), workflow_tone)
	workflow_summary_label.text = "Next step: %s" % _humanize_step(next_step)
	workflow_details_label.text = "can_queue_export=%s | complete=%s" % [
		_bool_label(can_queue),
		_bool_label(bool(workflow.get("is_complete", false))),
	]

	var command_hits = command_palette.search("export")
	command_summary_label.text = "%d command(s) match query 'export'." % command_hits.size()
	if _last_command_result.is_empty():
		command_result_label.text = "No command run yet in this session."
	else:
		command_result_label.text = "Last command: ok=%s message=%s" % [
			_bool_label(bool(_last_command_result.get("ok", false))),
			str(_last_command_result.get("message", "")),
		]

	var queue_state = command_center_shell.render_state([
		{"id": "job_queued", "status": "queued"},
		{"id": "job_running", "status": "running"},
		{"id": "job_failed", "status": "failed"},
	])
	var failed_count = Array(queue_state.get("buckets", {}).get("failed", [])).size()
	var recovery_actions = Array(queue_state.get("recovery_actions", []))
	queue_summary_label.text = "Queue status: failed=%d running=%d queued=%d" % [
		failed_count,
		Array(queue_state.get("buckets", {}).get("running", [])).size(),
		Array(queue_state.get("buckets", {}).get("queued", [])).size(),
	]
	queue_recovery_label.text = "Recovery actions available: %d" % recovery_actions.size()
	_set_chip(chip_queue, "Queue: %d failed" % failed_count, "warning" if failed_count > 0 else "success")

	if _last_diagnostics_result.is_empty():
		diagnostics_summary_label.text = "Diagnostics bundle has not been exported in this session."
		diagnostics_details_label.text = "Use Export Diagnostics to generate a redacted support bundle."
		_set_chip(chip_diagnostics, "Diagnostics: Ready", "neutral")
	elif bool(_last_diagnostics_result.get("ok", false)):
		var diag_path = str(_last_diagnostics_result.get("diagnostics", {}).get("output_path", ""))
		diagnostics_summary_label.text = "Diagnostics export completed successfully."
		diagnostics_details_label.text = "Latest bundle: %s" % diag_path
		_set_chip(chip_diagnostics, "Diagnostics: Exported", "success")
	else:
		diagnostics_summary_label.text = "Diagnostics export failed."
		diagnostics_details_label.text = "Review logs and retry export."
		_set_chip(chip_diagnostics, "Diagnostics: Failed", "danger")

	if _last_packaging_result.is_empty():
		packaging_summary_label.text = "Packaging dry run has not been executed yet."
	elif bool(_last_packaging_result.get("ok", false)):
		var pkg = _last_packaging_result.get("package", {})
		packaging_summary_label.text = "Packaging manifest ready: %s" % str(pkg.get("content_sha256", ""))
	else:
		packaging_summary_label.text = "Packaging dry run failed."

	last_updated_label.text = "Updated %s" % _timestamp_now()

func _on_refresh_pressed() -> void:
	_refresh_all()

func _on_demo_command_pressed() -> void:
	_last_command_result = command_palette.execute("export.retry_last", {"job_id": "job_failed"})
	_refresh_all()

func _on_export_diagnostics_pressed() -> void:
	var log_path = out_root.path_join("logs").path_join("ui_runtime.log")
	DirAccess.make_dir_recursive_absolute(log_path.get_base_dir())
	var f = FileAccess.open(log_path, FileAccess.WRITE)
	if f != null:
		f.store_string("ui started\nAuthorization: Bearer demo-token\n")
		f.close()
	_last_diagnostics_result = diagnostics_panel.export_support_bundle({
		"log_paths": [log_path],
		"scope_id": "ui_runtime",
	})
	_refresh_all()

func _on_packaging_dry_run_pressed() -> void:
	_last_packaging_result = productization_service.run_packaging_dry_run("ui_local_profile")
	_refresh_all()

func _on_release_channel_selected(index: int) -> void:
	if index < 0 or index >= _release_channel_ids.size():
		return
	var channel_id = String(_release_channel_ids[index])
	var result = productization_service.set_release_channel(channel_id)
	if bool(result.get("ok", false)):
		release_channel_note.text = "Release channel saved as %s." % channel_id
		release_channel_note.add_theme_color_override("font_color", COLOR_MUTED)
	else:
		release_channel_note.text = "Failed to set channel: %s" % str(result.get("error", "unknown"))
		release_channel_note.add_theme_color_override("font_color", COLOR_DANGER)
	_refresh_all()

func _bool_label(value: bool) -> String:
	return "yes" if value else "no"

func _humanize_step(step_id: String) -> String:
	match step_id:
		"import_assets":
			return "Import Assets"
		"select_preset":
			return "Select Preset"
		"fix_provenance":
			return "Resolve Provenance"
		"queue_export":
			return "Queue Export"
		"complete":
			return "Complete"
		_:
			return step_id

func _timestamp_now() -> String:
	var dt = Time.get_datetime_dict_from_system()
	return "%04d-%02d-%02d %02d:%02d:%02d" % [
		int(dt.get("year", 0)),
		int(dt.get("month", 0)),
		int(dt.get("day", 0)),
		int(dt.get("hour", 0)),
		int(dt.get("minute", 0)),
		int(dt.get("second", 0)),
	]

func _pulse(target: Variant) -> void:
	if not (target is Control):
		return
	var node: Control = target
	node.modulate = Color(1.1, 1.1, 1.1, 1.0)
	var tween = create_tween()
	tween.set_trans(Tween.TRANS_SINE)
	tween.set_ease(Tween.EASE_OUT)
	tween.tween_property(node, "modulate", Color(1.0, 1.0, 1.0, 1.0), 0.18)
