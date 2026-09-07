"""Tests for NetBox plugin support (e.g. netbox_dns)."""

import argparse
import logging
import os

from nbcli.commands.search import SearchSubCommand
from nbcli.core.config import get_session
from nbcli.core.utils import app_model_by_loc
from nbcli.views.tools import view_name

CONFIG = """pynetbox:
  url: http://localhost:8080
  token: testtoken
"""

CONFIG_DNS = CONFIG + """nbcli:
  plugins:
    - netbox_dns
"""


def _session(tmp_path, monkeypatch, config):
    """Write user_config.yml to tmp dir and return a pynetbox session."""
    (tmp_path / "user_config.yml").write_text(config)
    for key in list(os.environ.keys()):
        if key.startswith("NBCLI_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("NBCLI_DIR", str(tmp_path))
    return get_session()


def test_plugin_models_not_loaded_by_default(tmp_path, monkeypatch):
    """Plugin models should not resolve without 'nbcli.plugins' config."""
    nb = _session(tmp_path, monkeypatch, CONFIG)
    assert nb.nbcli.rm.get("record") is None
    assert nb.nbcli.rm.get("zone") is None
    assert nb.nbcli.rm.get("nameserver") is None


def test_plugin_models_loaded_when_enabled(tmp_path, monkeypatch):
    """Plugin models should resolve when the plugin is enabled in config."""
    nb = _session(tmp_path, monkeypatch, CONFIG_DNS)
    assert nb.nbcli.rm.get("record") is not None
    assert nb.nbcli.rm.get("zone") is not None
    assert nb.nbcli.rm.get("nameserver") is not None
    assert nb.nbcli.rm.get("view") is not None


def test_plugin_endpoint_resolution(tmp_path, monkeypatch):
    """Plugin models should resolve to their plugin api endpoint."""
    nb = _session(tmp_path, monkeypatch, CONFIG_DNS)
    ep = app_model_by_loc(nb, "record")
    assert ep.url == "http://localhost:8080/api/plugins/netbox-dns/records"
    ep = app_model_by_loc(nb, "zone")
    assert ep.url == "http://localhost:8080/api/plugins/netbox-dns/zones"


def test_core_endpoint_resolution_unchanged(tmp_path, monkeypatch):
    """Core models should still resolve to their api endpoints."""
    nb = _session(tmp_path, monkeypatch, CONFIG)
    ep = app_model_by_loc(nb, "device")
    assert ep.url == "http://localhost:8080/api/dcim/devices"
    ep = app_model_by_loc(nb, "dcim.devices")
    assert ep.url == "http://localhost:8080/api/dcim/devices"


def test_plugin_view_name(tmp_path, monkeypatch):
    """Plugin models should get a view name derived from their location."""
    nb = _session(tmp_path, monkeypatch, CONFIG_DNS)
    ep = app_model_by_loc(nb, "record")
    assert view_name(ep) == "PluginsNetboxDnsRecordsView"


def test_unknown_plugin_warns_and_continues(tmp_path, monkeypatch, caplog):
    """Unknown plugins in config should warn, not break the session."""
    config = CONFIG + """nbcli:
  plugins:
    - no_such_plugin
"""
    nb = _session(tmp_path, monkeypatch, config)
    assert nb.nbcli.rm.get("record") is None
    assert "no_such_plugin" in caplog.text


def test_search_only_uses_safe_plugin_models(tmp_path, monkeypatch):
    """Default search should only include plugin aliases with safe q= filters."""
    nb = _session(tmp_path, monkeypatch, CONFIG_DNS)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    command = SearchSubCommand(subparsers)
    command.args = command.parser.parse_args(["pg-dev.k8s.ane.energy"])
    command.netbox = nb
    command.logger = logging.getLogger("test")
    searched = []

    def fake_search_model(obj_type):
        searched.append(obj_type)
        return {"obj_type": obj_type, "records": [], "result_str": ""}

    command.search_model = fake_search_model
    command.run()

    assert "record" in searched
    assert "zone" in searched
    assert "nameserver" in searched
    assert "view" in searched
    assert "contact" in searched
    assert "registrar" not in searched
    assert "zone_template" not in searched
    assert "record_template" not in searched
    assert "dnssec_policy" not in searched
    assert "dnssec_key_template" not in searched
