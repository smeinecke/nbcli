"""Tests for Config._load and get_session config handling."""

import os

import pytest

from nbcli.core.config import get_session

CONFIG = """pynetbox:
  url: http://localhost:8080
  token: testtoken
"""


def _prepare(tmp_path, monkeypatch, config):
    """Write user_config.yml to tmp dir and isolate NBCLI_* env vars."""
    (tmp_path / "user_config.yml").write_text(config)
    for key in list(os.environ.keys()):
        if key.startswith("NBCLI_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("NBCLI_DIR", str(tmp_path))


def _session(tmp_path, monkeypatch, config):
    """Write user_config.yml to tmp dir and return a pynetbox session."""
    _prepare(tmp_path, monkeypatch, config)
    return get_session()


def test_nbcli_section_defaults_to_empty_dict(tmp_path, monkeypatch):
    """A minimal config without an 'nbcli' section must not crash callers."""
    nb = _session(tmp_path, monkeypatch, CONFIG)
    assert nb.nbcli.conf.nbcli == {}
    assert nb.nbcli.conf.nbcli.get("filter_limit", 50) == 50


def test_env_var_overrides_existing_section(tmp_path, monkeypatch):
    """NBCLI_NBCLI_* env vars override values in the nbcli section."""
    _prepare(tmp_path, monkeypatch, CONFIG)
    monkeypatch.setenv("NBCLI_NBCLI_FILTER_LIMIT", "10")
    nb = get_session()
    # auto_cast leaves numeric strings as strings; use-sites int() them
    assert nb.nbcli.conf.nbcli["filter_limit"] == "10"


def test_env_var_creates_missing_section(tmp_path, monkeypatch):
    """NBCLI_<SECTION>_<ATTR> can create a section absent from the file."""
    _prepare(tmp_path, monkeypatch, CONFIG)
    monkeypatch.setenv("NBCLI_REQUESTS_VERIFY", "false")
    nb = get_session()
    assert nb.http_session.verify is False


def test_env_only_pynetbox_config(tmp_path, monkeypatch):
    """pynetbox url/token can come entirely from env vars."""
    _prepare(tmp_path, monkeypatch, "nbcli:\n  plugins: []\n")
    monkeypatch.setenv("NBCLI_PYNETBOX_URL", "http://localhost:8080")
    monkeypatch.setenv("NBCLI_PYNETBOX_TOKEN", "envtoken")
    nb = get_session()
    assert nb.base_url == "http://localhost:8080/api"


def test_empty_config_file_raises_clear_error(tmp_path, monkeypatch):
    """An empty user_config.yml gets a clear error, not an AttributeError."""
    with pytest.raises(ValueError, match="url"):
        _session(tmp_path, monkeypatch, "")


def test_non_mapping_config_raises_clear_error(tmp_path, monkeypatch):
    """A scalar/list user_config.yml gets a clear error, not an AttributeError."""
    with pytest.raises(ValueError, match="mapping"):
        _session(tmp_path, monkeypatch, "just a string\n")
