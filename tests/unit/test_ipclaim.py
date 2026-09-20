"""Unit tests for the ipclaim and ipblocks subcommands."""

import argparse
import ipaddress
import logging
from unittest.mock import MagicMock

from nbcli.commands.ipblocks import IpBlocksSubCommand
from nbcli.commands.ipclaim import IpClaimSubCommand


def _command(cls, argv):
    """Build a subcommand with parsed args, a mock netbox session and a logger."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    command = cls(subparsers)
    command.args = parser.parse_args([cls.name.lower()] + argv)
    command.netbox = MagicMock()
    command.logger = logging.getLogger("nbcli.test")
    return command


def test_ipblocks_has_pick_option():
    """The ipblocks parser should accept --pick."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    command = IpBlocksSubCommand(subparsers)
    option_strings = [
        option for action in command.parser._actions for option in action.option_strings
    ]
    assert "--pick" in option_strings
    assert "--ongoing" in option_strings


def test_ipblocks_pick_output(capsys):
    """--pick prints the first COUNT free IPs from one contiguous block."""
    command = _command(IpBlocksSubCommand, ["192.168.1.0/29", "--pick", "2"])
    command.netbox.ipam.prefixes.filter.return_value = [MagicMock(id=1)]
    used = MagicMock()
    used.address = "192.168.1.1/29"
    command.netbox.ipam.ip_addresses.filter.return_value = iter([used])

    command.run()

    out = capsys.readouterr().out
    assert out == "192.168.1.2\n192.168.1.3\n"


def test_ipclaim_parser_options():
    """The ipclaim parser should accept the documented options."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    command = IpClaimSubCommand(subparsers)
    option_strings = [
        option for action in command.parser._actions for option in action.option_strings
    ]
    for option in ("--address", "--description", "--status", "--json"):
        assert option in option_strings


def test_ipclaim_creates_first_free(capsys):
    """ipclaim without --address creates the first free host address."""
    command = _command(
        IpClaimSubCommand,
        ["192.168.1.0/24", "host1.example.com", "--description", "test host"],
    )
    command.netbox.ipam.prefixes.filter.return_value = [MagicMock(id=1)]
    used = MagicMock()
    used.address = "192.168.1.1/24"
    command.netbox.ipam.ip_addresses.filter.side_effect = [[], iter([used])]
    result = MagicMock()
    result.id = 42
    result.address = "192.168.1.2/24"
    command.netbox.ipam.ip_addresses.create.return_value = result
    command.netbox.plugins.netbox_dns.records.filter.return_value = iter([MagicMock()])

    command.run()

    command.netbox.ipam.ip_addresses.create.assert_called_once_with(
        address="192.168.1.2/24",
        dns_name="host1.example.com",
        status="active",
        description="test host",
    )
    assert "192.168.1.2/24" in capsys.readouterr().out


def test_ipclaim_specific_address():
    """--address claims the given IP with the prefix's mask."""
    command = _command(
        IpClaimSubCommand, ["192.168.1.0/24", "host2.example.com", "--address", "192.168.1.10"]
    )
    command.netbox.ipam.prefixes.filter.return_value = [MagicMock(id=1)]
    command.netbox.ipam.ip_addresses.filter.side_effect = [[], iter([])]
    result = MagicMock()
    result.address = "192.168.1.10/24"
    command.netbox.ipam.ip_addresses.create.return_value = result
    command.netbox.plugins.netbox_dns.records.filter.return_value = iter([MagicMock()])

    command.run()

    command.netbox.ipam.ip_addresses.create.assert_called_once_with(
        address="192.168.1.10/24",
        dns_name="host2.example.com",
        status="active",
        description="",
    )


def test_ipclaim_rejects_used_address(caplog):
    """--address fails when the IP is already in use."""
    command = _command(
        IpClaimSubCommand, ["192.168.1.0/24", "host3.example.com", "--address", "192.168.1.5"]
    )
    command.netbox.ipam.prefixes.filter.return_value = [MagicMock(id=1)]
    used = MagicMock()
    used.address = "192.168.1.5/24"
    command.netbox.ipam.ip_addresses.filter.side_effect = [[], iter([used])]

    with caplog.at_level(logging.CRITICAL, logger="nbcli.test"):
        command.run()

    command.netbox.ipam.ip_addresses.create.assert_not_called()
    assert "already in use" in caplog.text


def test_ipclaim_rejects_address_outside_prefix(caplog):
    """--address fails when the IP is not in the prefix."""
    command = _command(
        IpClaimSubCommand, ["192.168.1.0/24", "host4.example.com", "--address", "10.0.0.5"]
    )
    command.netbox.ipam.prefixes.filter.return_value = [MagicMock(id=1)]
    command.netbox.ipam.ip_addresses.filter.side_effect = [[], iter([])]

    with caplog.at_level(logging.CRITICAL, logger="nbcli.test"):
        command.run()

    command.netbox.ipam.ip_addresses.create.assert_not_called()
    assert "not in prefix" in caplog.text


def test_ipclaim_rejects_claimed_fqdn(caplog):
    """ipclaim fails when the FQDN is already claimed."""
    command = _command(IpClaimSubCommand, ["192.168.1.0/24", "host5.example.com"])
    command.netbox.ipam.prefixes.filter.return_value = [MagicMock(id=1)]
    existing = MagicMock()
    existing.address = "192.168.1.9/24"
    command.netbox.ipam.ip_addresses.filter.return_value = iter([existing])

    with caplog.at_level(logging.CRITICAL, logger="nbcli.test"):
        command.run()

    command.netbox.ipam.ip_addresses.create.assert_not_called()
    assert "already claimed" in caplog.text


def test_ipclaim_network_addresses_not_usable(caplog):
    """--address rejects network and broadcast addresses."""
    for addr in ("192.168.1.0", "192.168.1.255"):
        command = _command(
            IpClaimSubCommand, ["192.168.1.0/24", "host6.example.com", "--address", addr]
        )
        command.netbox.ipam.prefixes.filter.return_value = [MagicMock(id=1)]
        command.netbox.ipam.ip_addresses.filter.side_effect = [[], iter([])]

        with caplog.at_level(logging.CRITICAL, logger="nbcli.test"):
            command.run()

        command.netbox.ipam.ip_addresses.create.assert_not_called()
    assert "not a usable host" in caplog.text
