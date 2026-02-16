import subprocess
import uuid

def test_it004_keyring_roundtrip(repo_root):
    bin_path = repo_root / "native/vas_keyring/target/debug/vas_keyring"
    service = "vas-test"
    account = f"acct-{uuid.uuid4().hex[:8]}"
    secret = "test-secret"

    set_proc = subprocess.run([str(bin_path), "set", service, account, secret], capture_output=True, text=True, check=False)
    if set_proc.returncode != 0:
        import pytest

        pytest.skip(f"Keyring set unavailable on this host: {set_proc.stderr.strip()}")

    get_proc = subprocess.run([str(bin_path), "get", service, account], capture_output=True, text=True, check=False)
    assert get_proc.returncode == 0
    assert get_proc.stdout.strip() == secret

    del_proc = subprocess.run([str(bin_path), "delete", service, account], capture_output=True, text=True, check=False)
    assert del_proc.returncode == 0
