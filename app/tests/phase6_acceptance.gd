extends SceneTree

const SQLiteAdapter = preload("res://src/adapters/sqlite_adapter.gd")
const AnalyticsService = preload("res://src/core/analytics_service.gd")
const NicheService = preload("res://src/core/niche_service.gd")

func _init() -> void:
	randomize()
	quit(_run())

func _run() -> int:
	var repo_root = OS.get_environment("VAS_REPO_ROOT")
	if repo_root == "":
		repo_root = ProjectSettings.globalize_path("res://").get_base_dir()
	var out_root = repo_root.path_join("out/product_phase6")
	DirAccess.make_dir_recursive_absolute(out_root)

	var db = SQLiteAdapter.new(out_root.path_join("vas.db"))
	var schema = db.apply_migrations(repo_root.path_join("migrations"), 6)
	if not _assert_true(schema >= 6, "migrations through phase 6"):
		return 1

	db.exec("INSERT INTO oauth_profiles(id, provider, display_name, keyring_account, created_at, updated_at) VALUES ('op6', 'youtube', 'p', 'acc6', 0, 0);")
	db.exec("INSERT INTO channels(id, oauth_profile_id, channel_id, channel_title, created_at, updated_at) VALUES ('ch6', 'op6', 'cid6', 'title6', 0, 0);")

	var analytics = AnalyticsService.new(db)
	for day in range(1, 91):
		var date_ymd = "2026-01-%02d" % mini(day, 31)
		analytics.store_snapshot("ch6", date_ymd, "2026-02-01", {"views": day})

	var csv_path = out_root.path_join("report.csv")
	var csv_file = FileAccess.open(csv_path, FileAccess.WRITE)
	csv_file.store_string("date,currency,amount\n2026-01-01,USD,1.23\n")
	csv_file.close()
	var imported = analytics.import_reporting_csv("ch6", csv_path, "revenue")
	if not _assert_true(imported == 1, "revenue csv import"):
		return 1

	var niche = NicheService.new(db)
	var keyword_id = niche.add_keyword("ambient study music")
	var note_id = niche.add_note(keyword_id, "offline note")
	if not _assert_true(keyword_id.begins_with("kw_"), "keyword id"):
		return 1
	if not _assert_true(note_id.begins_with("note_"), "note id"):
		return 1

	var rows = db.query("SELECT COUNT(*) AS c FROM analytics_snapshots WHERE channel_row_id = 'ch6';")
	var count = int(rows[0].get("c", 0)) if not rows.is_empty() else 0
	if not _assert_true(count >= 90, "analytics snapshot count >= 90"):
		return 1

	print("AT-006 product-path acceptance passed")
	return 0

func _assert_true(condition: bool, label: String) -> bool:
	if condition:
		print("[PASS] %s" % label)
		return true
	printerr("[FAIL] %s" % label)
	return false
