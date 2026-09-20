"""Helpers for working with NetBox IPAM prefixes and addresses."""

import ipaddress


def resolve_prefix(netbox, network):
    """Return the NetBox prefix object matching network, or None."""
    prefixes = list(netbox.ipam.prefixes.filter(prefix=str(network)))
    return prefixes[0] if prefixes else None


def used_address_ints(netbox, network):
    """Return the set of used addresses (as ints) within an ip_network."""
    used = set()
    for addr in netbox.ipam.ip_addresses.filter(parent=str(network)):
        try:
            used.add(int(ipaddress.ip_address(str(addr.address).split("/")[0])))
        except (ValueError, AttributeError):
            continue
    return used


def free_hosts(network, used):
    """Yield usable host addresses in network not present in the used set."""
    for host in network.hosts():
        if int(host) not in used:
            yield host


def make_block(start, end):
    """Build a dict describing a contiguous block."""
    return {
        "start": str(start),
        "end": str(end),
        "size": int(end) - int(start) + 1,
    }


def find_free_blocks(hosts, used):
    """Return contiguous unused blocks from a host list as list of dicts."""
    blocks = []
    current_start = None
    current_end = None

    for host in hosts:
        if int(host) in used:
            if current_start is not None:
                blocks.append(make_block(current_start, current_end))
                current_start = None
                current_end = None
        else:
            if current_start is None:
                current_start = host
            current_end = host

    if current_start is not None:
        blocks.append(make_block(current_start, current_end))

    return blocks
