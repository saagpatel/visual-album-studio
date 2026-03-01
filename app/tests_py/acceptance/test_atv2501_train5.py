import json
from pathlib import Path


def test_atv2501_train5_closeout_artifacts_and_gate_contracts_present(repo_root):
    required_tests = [
        "app/tests_py/acceptance/test_atv2101_train1.py",
        "app/tests_py/acceptance/test_atv2201_train2.py",
        "app/tests_py/acceptance/test_atv2301_train3.py",
        "app/tests_py/acceptance/test_atv2401_train4.py",
        "app/tests_py/acceptance/test_atv2501_train5.py",
        "app/tests_py/integration/test_itv2_510_accessibility_gates.py",
        "app/tests_py/integration/test_itv2_511_provenance_closeout_bundle.py",
    ]
    required_docs = [
        "docs/33-v2-closeout-report.md",
        "docs/34-post-v2-backlog.md",
        "docs/26-v2-test-verification.md",
        "docs/29-v2-train-execution-board.md",
    ]

    for rel in required_tests + required_docs:
        assert (repo_root / rel).exists(), f"missing required closeout artifact: {rel}"

    waivers = json.loads((repo_root / "docs/security-waivers.json").read_text(encoding="utf-8"))
    assert isinstance(waivers.get("waivers", []), list)
    assert len(waivers.get("waivers", [])) == 0

    closeout = (repo_root / "docs/33-v2-closeout-report.md").read_text(encoding="utf-8")
    assert "## Evidence index" in closeout
    assert "## Final signoff statement" in closeout

    backlog = (repo_root / "docs/34-post-v2-backlog.md").read_text(encoding="utf-8")
    assert "## Rendering and ML enhancements" in backlog
    assert "## Collaboration and cloud features" in backlog

    # Train 5 acceptance is a closeout-contract gate: required files and waiver posture.
    assert Path(repo_root).exists()
