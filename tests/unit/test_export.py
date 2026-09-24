"""Unit tests for the export subcommand."""

import logging
from importlib.resources import files
from unittest.mock import MagicMock, patch

import yaml

from nbcli.commands.export import Exporter
from nbcli.core.utils import ResMgr

_RESDICT = yaml.safe_load((files("nbcli.core") / "resolve_reference.yml").read_text())
_LOGGER = logging.getLogger("nbcli.test")

_BASE = "http://netbox/api"


def _netbox():
    """Mock pynetbox API object with a real ResMgr built from resolve_reference.yml."""
    nb = MagicMock(name="netbox")
    nb.nbcli.rm = ResMgr(**_RESDICT)
    nb.nbcli.logger = _LOGGER
    nb.base_url = _BASE
    return nb


def _exporter(model="site", **kwargs):
    return Exporter(_netbox(), model, _LOGGER, **kwargs)


def _site(**extra):
    obj = {
        "id": 5,
        "url": f"{_BASE}/dcim/sites/5/",
        "display": "DC 1",
        "display_url": "http://netbox/dcim/sites/5/",
        "name": "DC 1",
        "slug": "dc-1",
        "status": {"value": "active", "label": "Active"},
        "region": {"id": 1, "url": f"{_BASE}/dcim/regions/1/", "name": "USA"},
        "tenant": None,
        "facility": "",
        "description": "",
        "tags": [],
        "custom_fields": {},
        "created": "2026-01-01T00:00:00Z",
        "last_updated": "2026-01-02T00:00:00Z",
        "circuit_count": 0,
        "device_count": 3,
        "_depth": 0,
    }
    obj.update(extra)
    return obj


def test_readonly_fields_are_dropped():
    data = _exporter().build([_site()])["site"][0]
    for key in (
        "id",
        "url",
        "display",
        "display_url",
        "created",
        "last_updated",
        "device_count",
        "circuit_count",
        "_depth",
    ):
        assert key not in data
    assert data["name"] == "DC 1"


def test_empty_fields_are_dropped():
    data = _exporter().build([_site()])["site"][0]
    for key in ("tenant", "facility", "description", "tags", "custom_fields"):
        assert key not in data


def test_include_empty_keeps_fields():
    data = _exporter(include_empty=True).build([_site()])["site"][0]
    for key in ("tenant", "facility", "description", "tags", "custom_fields"):
        assert key in data
    assert data["tenant"] is None
    assert data["tags"] == []


def test_false_and_zero_are_kept():
    data = _exporter().build([_site(is_pool=False, u_height=0)])["site"][0]
    assert data["is_pool"] is False
    assert data["u_height"] == 0


def test_choice_field_uses_value():
    data = _exporter().build([_site()])["site"][0]
    assert data["status"] == "active"


def test_related_object_uses_lookup_value():
    data = _exporter().build([_site()])["site"][0]
    assert data["region"] == "USA"


def test_model_child_res_takes_precedence():
    """'role' on a device resolves via the nested dcim.device_roles entry."""
    dev = {
        "name": "web-1",
        "role": {"id": 9, "url": f"{_BASE}/dcim/device-roles/9/", "name": "server"},
    }
    data = _exporter("device").build([dev])["device"][0]
    assert data["role"] == "server"


def test_own_lookup_field_is_literal():
    addr = {"address": "10.0.0.1/24", "vrf": None}
    data = _exporter("address").build([addr])["address"][0]
    assert data["address"] == "10.0.0.1/24"


def test_url_derived_res_for_unresolvable_key():
    """'tags' has no resolve entry - the object type is derived from its url."""
    site = _site(tags=[{"id": 1, "url": f"{_BASE}/extras/tags/1/", "name": "cmk"}])
    data = _exporter().build([site])["site"][0]
    assert data["tags"] == ["cmk"]


def test_nonstandard_lookup_field():
    """device_type resolves via its 'model' lookup, not 'name'."""
    dev = {
        "name": "web-1",
        "device_type": {
            "id": 2,
            "url": f"{_BASE}/dcim/device-types/2/",
            "model": "A-2U-C",
            "display": "ACME A-2U-C",
        },
    }
    data = _exporter("device").build([dev])["device"][0]
    assert data["device_type"] == "A-2U-C"


def test_unknown_related_object_falls_back_to_display():
    site = _site(group={"id": 1, "url": f"{_BASE}/dcim/site-groups/1/", "name": "Grp"})
    # dcim.site_groups has no resolve entry - url-derived res also fails
    data = _exporter().build([site])["site"][0]
    assert data["group"] == "Grp"


def test_plain_data_dicts_pass_through():
    site = _site(custom_fields={"env": "prod", "n": 3}, local_context_data={"a": 1})
    data = _exporter().build([site])["site"][0]
    assert data["custom_fields"] == {"env": "prod", "n": 3}
    assert data["local_context_data"] == {"a": 1}


def test_scalar_lists_pass_through():
    site = _site(asns=[65001, 65002])
    data = _exporter().build([site])["site"][0]
    assert data["asns"] == [65001, 65002]


def test_build_list_form():
    data = _exporter().build([_site(), _site(name="DC 2", slug="dc-2")])
    assert list(data) == ["site"]
    assert [o["name"] for o in data["site"]] == ["DC 1", "DC 2"]


def test_build_upsert_form():
    data = _exporter(upsert=True).build([_site()])
    assert list(data) == ["site:DC 1"]
    # lookup field is encoded in the key, not repeated in the data
    assert "name" not in data["site:DC 1"]
    assert data["site:DC 1"]["slug"] == "dc-1"


def test_build_upsert_ipv6_lookup():
    addr = {"address": "2001:db8::1/64", "status": {"value": "active", "label": "Active"}}
    data = _exporter("address", upsert=True).build([addr])
    assert list(data) == ["address:2001:db8::1/64"]
    assert "address" not in data["address:2001:db8::1/64"]


def test_build_upsert_duplicate_warns(caplog):
    with caplog.at_level(logging.WARNING, logger="nbcli.test"):
        data = _exporter(upsert=True).build([_site(), _site()])
    assert "Duplicate lookup value" in caplog.text
    assert len(data) == 1


def test_build_upsert_unknown_model_falls_back(caplog):
    nb = _netbox()
    exporter = Exporter(nb, "ipam.asns", _LOGGER, upsert=True)
    with caplog.at_level(logging.WARNING, logger="nbcli.test"):
        data = exporter.build([{"asn": 65001}])
    assert "Ignoring --upsert" in caplog.text
    assert list(data) == ["asns"]


def test_unknown_model_alias_fallback():
    data = _exporter("ipam.asns").build([{"asn": 65001, "rir": None}])
    assert data == {"asns": [{"asn": 65001}]}


def test_output_is_valid_create_yaml():
    data = _exporter().build(
        [_site(tags=[{"id": 1, "url": f"{_BASE}/extras/tags/1/", "name": "t"}])]
    )
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    assert yaml.safe_load(text) == data


def test_run_writes_file(tmp_path):
    import argparse

    from nbcli.commands.export import ExportSubCommand

    nb = _netbox()
    out = tmp_path / "out.yml"

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cmd = ExportSubCommand(subparsers)
    cmd.netbox = nb
    cmd.logger = _LOGGER
    cmd.args = parser.parse_args(["export", "site", "-f", str(out)])

    fake_filter = MagicMock()
    fake_filter.result = [_site()]
    with (
        patch("nbcli.commands.export.Filter", return_value=fake_filter),
        patch("nbcli.commands.export.is_list_of_records", return_value=True),
    ):
        cmd.run()

    assert yaml.safe_load(out.read_text()) == {"site": [_exporter().serialize_obj(_site())]}


def test_run_no_results_warns(caplog):
    import argparse

    from nbcli.commands.export import ExportSubCommand

    nb = _netbox()
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cmd = ExportSubCommand(subparsers)
    cmd.netbox = nb
    cmd.logger = _LOGGER
    cmd.args = parser.parse_args(["export", "site"])

    fake_filter = MagicMock()
    fake_filter.result = []
    with patch("nbcli.commands.export.Filter", return_value=fake_filter):
        with caplog.at_level(logging.WARNING, logger="nbcli.test"):
            cmd.run()

    assert "No results found" in caplog.text
