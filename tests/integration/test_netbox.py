"""Integration tests that run against a live NetBox Docker instance."""

import os
import subprocess
import sys
import time
import urllib.request

import pytest

NETBOX_URL = "http://localhost:8080"
NETBOX_TOKEN = "nbt_test.0123456789abcdef0123456789abcdef01234567"


def _netbox_ready(timeout: float = 5.0):
    """Return True if NetBox API is up and the token works."""
    try:
        req = urllib.request.Request(
            f"{NETBOX_URL}/api/",
            headers={"Authorization": f"Bearer {NETBOX_TOKEN}"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


@pytest.fixture(scope="module", autouse=True)
def netbox_service():
    """Wait for NetBox to be ready; skip tests if it is not."""
    # Wait longer in CI where the workflow starts the NetBox container.
    ci = os.environ.get("CI")
    max_attempts = 100 if ci else 1
    timeout = 5.0 if ci else 1.0
    for _ in range(max_attempts):
        if _netbox_ready(timeout):
            break
        time.sleep(5)
    else:
        pytest.skip("NetBox is not reachable at localhost:8080")


@pytest.fixture
def nbcli_env(tmp_path_factory):
    """Provide an isolated nbcli directory for the test run."""
    nbcli_dir = tmp_path_factory.mktemp("nbcli")
    env = os.environ.copy()
    env["NBCLI_DIR"] = str(nbcli_dir)
    env["NBCLI_PYNETBOX_TOKEN"] = NETBOX_TOKEN
    # Initialize a default user_config so subsequent commands work.
    subprocess.run([sys.executable, "-m", "nbcli", "init"], env=env, check=True, capture_output=True, text=True)
    return env


def _run_nbcli(env, *args, check=True):
    """Run nbcli via the same interpreter used by pytest."""
    cmd = [sys.executable, "-m", "nbcli", *args]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if check:
        assert result.returncode == 0, (
            f"nbcli {' '.join(args)} failed:\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
    return result


def test_init(nbcli_env):
    _run_nbcli(nbcli_env, "init")


def test_info(nbcli_env):
    _run_nbcli(nbcli_env, "info")


def test_create_region_and_site(nbcli_env):
    """Create test region and site, tolerating re-runs against the same NetBox instance."""
    for data_file in ("tests/integration/region.yml", "tests/integration/site.yml"):
        result = _run_nbcli(nbcli_env, "create", data_file, check=False)
        assert result.returncode == 0 or "already exists" in result.stderr, result.stderr


def test_search_and_filter(nbcli_env):
    result = _run_nbcli(nbcli_env, "search", "IntegrationSite", "--json")
    assert "IntegrationSite" in result.stdout or "integration-site" in result.stdout.lower()

    result = _run_nbcli(nbcli_env, "filter", "site", "IntegrationSite", "--json")
    assert "IntegrationSite" in result.stdout or "integration-site" in result.stdout.lower()
