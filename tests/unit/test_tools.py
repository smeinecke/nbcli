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
