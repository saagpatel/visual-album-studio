extends SceneTree

const SQLiteAdapter = preload("res://src/adapters/sqlite_adapter.gd")
const AnalyticsService = preload("res://src/core/analytics_service.gd")
const NicheService = preload("res://src/core/niche_service.gd")
const RevenueService = preload("res://src/core/revenue_service.gd")

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

	var incremental = analytics.run_incremental_sync("ch6", "2026-01-01", "2026-02-01", [
		{"date_ymd": "2026-01-01", "metrics": {"views": 1}},
		{"date_ymd": "2026-01-15", "metrics": {"views": 2}},
	])
	if not _assert_true(String(incremental.get("status", "")) == "succeeded", "incremental sync succeeded"):
		return 1
	if not _assert_true(incremental.has("ingest_run_id"), "incremental ingest run id present"):
		return 1

	var csv_path = out_root.path_join("report.csv")
	var csv_file = FileAccess.open(csv_path, FileAccess.WRITE)
	csv_file.store_string("date,currency,amount\n2026-01-01,USD,1.23\n")
	csv_file.close()
	var revenue = RevenueService.new(db)
	var imported = revenue.import_revenue_csv("ch6", csv_path)
	if not _assert_true(imported == 1, "revenue csv import"):
		return 1
	var upserted_row_id = revenue.upsert_manual_revenue_row("ch6", "2026-01-03", "USD", 2_500_000)
	if not _assert_true(upserted_row_id.begins_with("rev_manual_"), "manual revenue upsert id"):
		return 1
	var rows = revenue.list_revenue_rows("ch6")
	if not _assert_true(rows.size() >= 2, "revenue rows listed"):
		return 1

	var niche = NicheService.new(db)
	var keyword_id = niche.add_keyword("ambient study music")
	var note_id = niche.add_note(keyword_id, "offline note")
	if not _assert_true(keyword_id.begins_with("kw_"), "keyword id"):
		return 1
	if not _assert_true(note_id.begins_with("note_"), "note id"):
		return 1
	if not _assert_true(niche.list_keywords().size() >= 1, "keywords list available"):
		return 1
	if not _assert_true(niche.list_notes(keyword_id).size() >= 1, "notes list available"):
		return 1
	var lookup = niche.run_optional_lookup(["ambient", "study"], 500, 0)
	if not _assert_true(bool(lookup.get("ok", false)), "optional lookup succeeds within budget"):
		return 1

	var dashboard = analytics.get_dashboard_snapshot("ch6", "2026-01-01", "2026-02-01")
	if not _assert_true(dashboard.has("last_synced_at"), "dashboard last_synced_at present"):
		return 1
	var snapshot_rows = db.query("SELECT COUNT(*) AS c FROM analytics_snapshots WHERE channel_row_id = 'ch6';")
	var count = int(snapshot_rows[0].get("c", 0)) if not snapshot_rows.is_empty() else 0
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
