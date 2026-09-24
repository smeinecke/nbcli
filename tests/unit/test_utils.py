"""Unit tests for helpers in core/utils.py."""

from nbcli.core.utils import ResMgr, auto_cast, rend_table


def test_rend_table_coerces_cells_and_short_rows():
    """Non-string cells and ragged rows must not crash table rendering."""
    table = [["Name", "Size"], ["a"], ["longer", 5]]
    out = rend_table(table)
    lines = out.splitlines()
    assert lines[0].startswith("Name")
    assert lines[1].startswith("a")
    assert "5" in lines[2]


def test_default_alias_strips_one_plural_s():
    """The implicit alias removes a single trailing 's' from the endpoint."""
    rm = ResMgr(**{"dcim.devices": {"lookup": "name"}})
    assert rm.get("device") is not None
    assert rm.get("device").model == "dcim.devices"


def test_auto_cast_basics():
    """auto_cast converts true/false/none/json and leaves the rest alone."""
    assert auto_cast("true") is True
    assert auto_cast("False") is False
    assert auto_cast("none") is None
    assert auto_cast("[1, 2]") == [1, 2]
    assert auto_cast("10") == "10"
    assert auto_cast("dc1") == "dc1"
