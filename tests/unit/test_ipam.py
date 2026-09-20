"""Unit tests for nbcli.core.ipam helpers."""

import ipaddress

from nbcli.core.ipam import find_free_blocks, free_hosts, make_block


def test_find_free_blocks_all_free():
    """A fully unused network returns one block spanning all hosts."""
    network = ipaddress.ip_network("192.168.1.0/29")
    blocks = find_free_blocks(list(network.hosts()), set())
    assert blocks == [{"start": "192.168.1.1", "end": "192.168.1.6", "size": 6}]


def test_find_free_blocks_splits_on_used():
    """Used addresses split the free space into separate blocks."""
    network = ipaddress.ip_network("192.168.1.0/29")
    used = {int(ipaddress.ip_address("192.168.1.3"))}
    blocks = find_free_blocks(list(network.hosts()), used)
    assert blocks == [
        {"start": "192.168.1.1", "end": "192.168.1.2", "size": 2},
        {"start": "192.168.1.4", "end": "192.168.1.6", "size": 3},
    ]


def test_find_free_blocks_none_free():
    """A fully used network returns no blocks."""
    network = ipaddress.ip_network("192.168.1.0/30")
    used = {int(h) for h in network.hosts()}
    assert find_free_blocks(list(network.hosts()), used) == []


def test_free_hosts_skips_used():
    """free_hosts yields only unused addresses."""
    network = ipaddress.ip_network("192.168.1.0/30")
    used = {int(ipaddress.ip_address("192.168.1.1"))}
    assert [str(h) for h in free_hosts(network, used)] == ["192.168.1.2"]


def test_make_block_size():
    """make_block reports start, end and inclusive size."""
    start = ipaddress.ip_address("192.168.1.10")
    end = ipaddress.ip_address("192.168.1.12")
    assert make_block(start, end) == {
        "start": "192.168.1.10",
        "end": "192.168.1.12",
        "size": 3,
    }
