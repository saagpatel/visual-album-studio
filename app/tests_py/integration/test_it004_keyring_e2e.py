import os
import re
import subprocess
import uuid

def test_it004_keyring_roundtrip(repo_root):
    bin_path = repo_root / "native/vas_keyring/target/debug/vas_keyring"
    service = "vas-test"
    account = os.environ.get("VAS_TEST_ACCOUNT", "")
    if account and not re.fullmatch(r"vas-gate-\d{8}-[0-9a-f]{12}", account):
        raise ValueError("VAS_TEST_ACCOUNT must use vas-gate-YYYYMMDD-<12 lowercase hex>")
    if not account:
        account = f"acct-{uuid.uuid4().hex[:8]}"
    secret = "test-secret"

    set_proc = subprocess.run(
        [str(bin_path), "set", service, account, "--from-stdin"],
        capture_output=True,
        text=True,
        input=secret,
        check=False,
    )
    if set_proc.returncode != 0:
        import pytest

        pytest.skip("Keyring set unavailable on this host")

    try:
        get_proc = subprocess.run([str(bin_path), "get", service, account], capture_output=True, text=True, check=False)
        assert get_proc.returncode == 0
        assert get_proc.stdout.strip() == secret
    finally:
        del_proc = subprocess.run([str(bin_path), "delete", service, account], capture_output=True, text=True, check=False)
        assert del_proc.returncode == 0


def test_it004_keyring_rejects_insecure_cli_secret(repo_root):
    bin_path = repo_root / "native/vas_keyring/target/debug/vas_keyring"
    service = "vas-test"
    account = f"acct-{uuid.uuid4().hex[:8]}"
    secret = "test-secret"
    env = dict(os.environ)
    env.pop("VAS_ALLOW_INSECURE_KEYRING_ARG", None)

    set_proc = subprocess.run(
        [str(bin_path), "set", service, account, secret],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert set_proc.returncode != 0
    assert "insecure_cli_secret_disallowed" in set_proc.stderr
