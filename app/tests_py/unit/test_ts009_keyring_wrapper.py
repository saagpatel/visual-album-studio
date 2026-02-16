import subprocess


def test_ts009_keyring_wrapper_cli_exists(repo_root):
    bin_path = repo_root / "native/vas_keyring/target/debug/vas_keyring"
    proc = subprocess.run([str(bin_path)], capture_output=True, text=True, check=False)
    assert proc.returncode != 0
