"""Unit tests for the create (Upsert) subcommand."""

import logging
from importlib.resources import files
from unittest.mock import MagicMock, call

import yaml

from nbcli.commands.create import Upsert
from nbcli.core.utils import ResMgr

_RESDICT = yaml.safe_load((files("nbcli.core") / "resolve_reference.yml").read_text())
_LOGGER = logging.getLogger("nbcli.test")


def _netbox():
    """Mock pynetbox API object with a real ResMgr built from resolve_reference.yml."""
    nb = MagicMock(name="netbox")
    nb.nbcli.rm = ResMgr(**_RESDICT)
    nb.nbcli.logger = _LOGGER
    return nb


def _upsert(nb, data):
    for key, value in data.items():
        Upsert(nb, _LOGGER, key, value, parent=None)
    return nb


def _prefix_obj(prefix):
    obj = MagicMock(name="prefix")
    obj.prefix = prefix
    return obj


def test_own_lookup_field_is_literal_data():
    """'address' on an ip_address object is data, not a reference lookup."""
    nb = _netbox()
    ep = nb.ipam.ip_addresses

    _upsert(nb, {"address": [{"address": "10.0.0.1/24", "dns_name": "a.example.com"}]})

    ep.filter.assert_not_called()
    ep.create.assert_called_once_with(address="10.0.0.1/24", dns_name="a.example.com")


def test_own_lookup_field_is_literal_data_prefix():
    """'prefix' on a prefix object is data, not a reference lookup."""
    nb = _netbox()
    ep = nb.ipam.prefixes

    _upsert(nb, {"prefix": [{"prefix": "10.0.0.0/24", "status": "active"}]})

    ep.filter.assert_not_called()
    ep.create.assert_called_once_with(prefix="10.0.0.0/24", status="active")


def test_reference_field_still_resolves():
    """'site' on a device resolves to the existing site's id."""
    nb = _netbox()
    site = MagicMock(name="site")
    site.id = 7
    nb.dcim.sites.filter.return_value = [site]

    _upsert(nb, {"device": [{"name": "web-1", "site": "DC 1"}]})

    nb.dcim.sites.filter.assert_called_once_with(name="DC 1")
    nb.dcim.devices.create.assert_called_once_with(name="web-1", site=7)


def test_self_model_reference_alias_still_resolves():
    """'parent' on a region resolves via the nested self-reference."""
    nb = _netbox()
    parent = MagicMock(name="region")
    parent.id = 3
    nb.dcim.regions.filter.return_value = [parent]

    _upsert(nb, {"region": [{"name": "NY", "slug": "ny", "parent": "USA"}]})

    nb.dcim.regions.filter.assert_called_once_with(name="USA")
    nb.dcim.regions.create.assert_called_once_with(name="NY", slug="ny", parent=3)


def test_unresolvable_reference_warns(caplog):
    """A failed reference resolution warns instead of silently dropping the field."""
    nb = _netbox()
    nb.dcim.sites.filter.return_value = []

    with caplog.at_level(logging.WARNING, logger="nbcli.test"):
        _upsert(nb, {"device": [{"name": "web-1", "site": "Nowhere"}]})

    assert "Could not resolve" in caplog.text
    nb.dcim.devices.create.assert_called_once_with(name="web-1")


def test_upsert_form_patches_existing():
    """'model:lookup' updates the existing object."""
    nb = _netbox()
    ep = nb.ipam.ip_addresses
    obj = MagicMock(name="address")
    ep.filter.return_value = [obj]

    _upsert(nb, {"address:10.0.0.1/24": {"dns_name": "new.example.com"}})

    ep.filter.assert_called_once_with(address="10.0.0.1/24")
    ep.create.assert_not_called()
    obj.update.assert_called_once_with({"dns_name": "new.example.com"})


def test_upsert_form_creates_missing():
    """'model:lookup' creates the object with the lookup value when missing."""
    nb = _netbox()
    ep = nb.ipam.ip_addresses
    ep.filter.return_value = []

    _upsert(nb, {"address:10.0.0.2/24": {"dns_name": "b.example.com"}})

    ep.create.assert_called_once_with(address="10.0.0.2/24", dns_name="b.example.com")


def test_upsert_form_ipv6_lookup_value():
    """IPv6 addresses survive the 'model:lookup' split."""
    nb = _netbox()
    ep = nb.ipam.ip_addresses
    ep.filter.return_value = []

    _upsert(nb, {"address:2001:db8::1/64": {"status": "active"}})

    ep.filter.assert_called_once_with(address="2001:db8::1/64")
    ep.create.assert_called_once_with(address="2001:db8::1/64", status="active")


def test_nested_address_under_prefix_scopes_lookup_by_parent():
    """Existence check uses the 'parent' filter, not the invalid 'prefix' field."""
    nb = _netbox()
    nb.ipam.prefixes.filter.return_value = [_prefix_obj("10.0.9.0/24")]
    nb.ipam.ip_addresses.filter.return_value = []

    _upsert(
        nb,
        {"prefix:10.0.9.0/24": {"status": "active", "address:10.0.9.1/24": {"dns_name": "x"}}},
    )

    nb.ipam.ip_addresses.filter.assert_called_once_with(parent="10.0.9.0/24", address="10.0.9.1/24")
    nb.ipam.ip_addresses.create.assert_called_once_with(address="10.0.9.1/24", dns_name="x")


def test_nested_address_list_under_prefix():
    """List-form children under a prefix get literal 'address' fields."""
    nb = _netbox()
    nb.ipam.prefixes.filter.return_value = [_prefix_obj("10.0.9.0/24")]
    nb.ipam.ip_addresses.filter.return_value = []

    _upsert(
        nb,
        {
            "prefix:10.0.9.0/24": {
                "address": [
                    {"address": "10.0.9.5/24", "dns_name": "n1"},
                    {"address": "10.0.9.6/24"},
                ]
            }
        },
    )

    nb.ipam.ip_addresses.filter.assert_not_called()
    nb.ipam.ip_addresses.create.assert_has_calls(
        [call(address="10.0.9.5/24", dns_name="n1"), call(address="10.0.9.6/24")]
    )


def test_caret_still_skips_parent_scoping():
    """The 'model:lookup^' escape hatch keeps parent args out of the lookup filter."""
    nb = _netbox()
    nb.ipam.prefixes.filter.return_value = [_prefix_obj("10.0.9.0/24")]
    nb.ipam.ip_addresses.filter.return_value = []

    _upsert(nb, {"prefix:10.0.9.0/24": {"address:10.0.9.2/24^": {}}})

    nb.ipam.ip_addresses.filter.assert_called_once_with(address="10.0.9.2/24")
    nb.ipam.ip_addresses.create.assert_called_once_with(address="10.0.9.2/24")
