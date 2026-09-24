"""Unit tests for the filter subcommand."""

import logging
import types
from importlib.resources import files
from unittest.mock import MagicMock

import yaml
from pynetbox.core.query import Request
from pynetbox.core.response import RecordSet

from nbcli.commands.filter import Filter
from nbcli.core.utils import ResMgr

_RESDICT = yaml.safe_load((files("nbcli.core") / "resolve_reference.yml").read_text())


def _netbox():
    nb = MagicMock(name="netbox")
    nb.nbcli.conf = types.SimpleNamespace(nbcli={})
    nb.nbcli.logger = logging.getLogger("nbcli.test")
    nb.nbcli.rm = ResMgr(**_RESDICT)
    return nb


def _record_set(endpoint, filters=None):
    """Build a real RecordSet whose request has the given filters dict."""
    req = Request(
        filters=filters,
        base="http://netbox.example/api/dcim/devices/",
        token="t",
        http_session=MagicMock(),
    )
    req.get = MagicMock(return_value=iter([]))
    return RecordSet(endpoint, req)


def test_filter_bare_model_no_args():
    """'nbcli filter <model>' with no args must not crash on request.filters=None."""
    nb = _netbox()
    ep = nb.dcim.devices
    ep.count.return_value = 0
    ep.filter.return_value = _record_set(ep)

    f = Filter(nb, "device", logging.getLogger("nbcli.test"), args=[])

    assert f.result == []


def test_filter_all_no_args():
    """'nbcli filter <model> --all' hits the same request.filters=None path."""
    nb = _netbox()
    ep = nb.dcim.devices
    ep.count.return_value = 0
    ep.all.return_value = _record_set(ep)

    f = Filter(nb, "device", logging.getLogger("nbcli.test"), list_all=True)

    ep.all.assert_called_once_with()
    assert f.result == []
