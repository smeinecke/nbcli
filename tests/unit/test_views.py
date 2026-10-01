"""Unit tests for Formatter output options in views/tools.py."""

import json

from pynetbox.core.response import Record

from nbcli.core.utils import smart_key, sort_records
from nbcli.views.tools import Formatter


def _rec(values):
    return Record(values, None, None)


def _addr(last_octet, dns_name=""):
    return _rec(
        {
            "id": last_octet,
            "address": f"10.30.80.{last_octet}/24",
            "dns_name": dns_name,
        }
    )


def test_smart_key_orders_ips_numerically():
    """IP strings must order by value, not lexically ('.9' < '.10')."""
    keys = [smart_key(f"10.30.80.{o}/24") for o in (9, 10, 100)]
    assert keys[0] < keys[1] < keys[2]


def test_smart_key_groups_ips_numbers_strings_empty():
    """Sort order: IPs < numbers < strings < empty/missing."""
    assert smart_key("10.0.0.1") < smart_key("::1")
    assert smart_key("::1") < smart_key("5")
    assert smart_key("5") < smart_key("abc")
    assert smart_key("abc") < smart_key("")
    assert smart_key("") == smart_key(None)


def test_smart_key_uses_choice_label():
    """Dicts/records with a 'label' key sort by that label."""
    assert smart_key({"value": "b", "label": "a"}) < smart_key({"value": "a", "label": "b"})


def test_sort_records_by_ip_and_desc():
    """sort_records applies field specs; '-' prefix reverses that key."""
    records = [_addr(100), _addr(9), _addr(10)]

    sort_records(records, ["address"])
    assert [r.address for r in records] == [
        "10.30.80.9/24",
        "10.30.80.10/24",
        "10.30.80.100/24",
    ]

    sort_records(records, ["-address"])
    assert records[0].address == "10.30.80.100/24"


def test_sort_records_missing_values_last():
    """Records missing the sort field sort after all valued records."""
    records = [_addr(10), _rec({"id": 99, "dns_name": "no-addr"})]
    sort_records(records, ["address"])
    assert records[-1].dns_name == "no-addr"


def test_formatter_json_cols_limits_fields():
    """--json --cols emits only the requested attribute paths."""
    out = Formatter(
        [_addr(15, "db.example.com")],
        json_view=True,
        cols=["address", "dns_name", "missing"],
    ).string
    data = json.loads(out)

    assert data == [{"address": "10.30.80.15/24", "dns_name": "db.example.com", "missing": None}]


def test_formatter_json_cols_sorts_ips():
    """--json --cols --sort produces IP-ordered trimmed objects."""
    out = Formatter(
        [_addr(100), _addr(9)],
        json_view=True,
        cols=["address"],
        sort=["address"],
    ).string

    assert [d["address"] for d in json.loads(out)] == [
        "10.30.80.9/24",
        "10.30.80.100/24",
    ]


def test_formatter_delim_joins_view_cells():
    """--delim renders sep-joined rows with empty cells for missing values."""
    records = [_addr(15, "db.example.com")]
    out = Formatter(
        records,
        sep="|",
        cols=["address", "dns_name", "description"],
    ).string

    assert out == "address|dns_name|description\n10.30.80.15/24|db.example.com|"


def test_formatter_delim_no_header():
    """--nh drops the header row in delimited output."""
    records = [_addr(15)]
    out = Formatter(
        records,
        sep="|",
        cols=["address", "dns_name"],
        disable_header=True,
    ).string

    assert out == "10.30.80.15/24|"
