"""Unit tests for NbArgs resolution in commands/tools.py."""

import logging
from importlib.resources import files
from unittest.mock import MagicMock

import yaml

from nbcli.commands.tools import NbArgs
from nbcli.core.utils import ResMgr

_RESDICT = yaml.safe_load((files("nbcli.core") / "resolve_reference.yml").read_text())


def _netbox():
    nb = MagicMock(name="netbox")
    nb.nbcli.rm = ResMgr(**_RESDICT)
    nb.nbcli.logger = logging.getLogger("nbcli.test")
    return nb


def test_resolve_with_no_args_returns_empty():
    """An empty resolve must not fall through to an unrestricted filter()."""
    nb = _netbox()
    nb_args = NbArgs(nb)

    nba, result = nb_args.resolve("site")

    assert result == []
    assert nb_args.failed
    nb.dcim.sites.filter.assert_not_called()


def test_ipv6_literal_is_plain_arg():
    """An IPv6 address looks like 'model:value' - it must stay a plain arg."""
    nb = _netbox()
    nb_args = NbArgs(nb)

    nb_args.proc("2001:db8::1/64")

    assert nb_args.args == ["2001:db8::1/64"]
    assert not nb_args.failed


def test_mac_literal_is_plain_arg():
    """MAC addresses contain ':' too - keep them literal."""
    nb = _netbox()
    nb_args = NbArgs(nb)

    nb_args.proc("aa:bb:cc:dd:ee:ff")

    assert nb_args.args == ["aa:bb:cc:dd:ee:ff"]
    assert not nb_args.failed


def test_kwarg_value_may_contain_equals():
    """'k=a=b' should keep the full value instead of dropping the arg."""
    nb = _netbox()
    nb_args = NbArgs(nb)

    nb_args.proc("description=foo=bar")

    assert nb_args.kwargs == {"description": "foo=bar"}
    assert not nb_args.failed


def test_res_arg_value_may_contain_colons():
    """'site:a:b' should filter name='a:b', not split the value."""
    nb = _netbox()
    nb.dcim.sites.filter.return_value = iter([MagicMock(id=5)])
    nb_args = NbArgs(nb)

    nb_args.proc("site:a:b")

    nb.dcim.sites.filter.assert_called_once_with(name="a:b")
    assert nb_args.kwargs == {"site_id": 5}
    assert not nb_args.failed


def test_res_arg_still_resolves():
    """'site:DC1' resolves to the site id as before."""
    nb = _netbox()
    nb.dcim.sites.filter.return_value = iter([MagicMock(id=7)])
    nb_args = NbArgs(nb)

    nb_args.proc("site:DC1")

    nb.dcim.sites.filter.assert_called_once_with(name="DC1")
    assert nb_args.kwargs == {"site_id": 7}
    assert not nb_args.failed
