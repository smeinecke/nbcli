"""Sub command to find unused and ongoing IP blocks in a subnet."""

import ipaddress
import json

from pynetbox.core.query import RequestError
from nbcli.commands.base import BaseSubCommand
from nbcli.core.ipam import find_free_blocks, resolve_prefix, used_address_ints
from nbcli.core.utils import rend_table


class IpBlocksSubCommand(BaseSubCommand):
    """Find unused or ongoing IP blocks within a NetBox prefix.

    Query a subnet/prefix for available (unused) IP space and report
    contiguous blocks. Use --ongoing to find blocks with at least a given
    number of consecutive available IPs.
    """

    name = "ipblocks"
    parser_kwargs = dict(help="Find unused or ongoing IP blocks in a subnet.")

    def setup(self):
        """Add parser arguments for ipblocks subcommand."""
        self.parser.add_argument("prefix", help="Subnet/prefix to search (e.g. 192.168.1.0/24)")

        self.parser.add_argument(
            "--ongoing",
            type=int,
            metavar="COUNT",
            help="Search for blocks with at least COUNT consecutive available IPs.",
        )

        self.parser.add_argument(
            "--pick",
            type=int,
            metavar="COUNT",
            help="Print COUNT free IPs from the first block with enough space.",
        )

        self.parser.add_argument(
            "--json", action="store_true", help="Display results as json string."
        )

        self.parser.add_argument(
            "--limit",
            type=int,
            default=10000,
            metavar="LIMIT",
            help="Maximum number of addresses to evaluate (default: 10000).",
        )

    def run(self):
        """Find unused or ongoing IP blocks in a subnet.

        Usage Examples:

        - List all unused (available) IP blocks in a prefix:
          $ nbcli ipblocks 192.168.1.0/24

        - Find blocks with at least 10 consecutive available IPs:
          $ nbcli ipblocks 192.168.1.0/24 --ongoing 10

        - Print the next 2 free IPs (from one contiguous block):
          $ nbcli ipblocks 192.168.1.0/24 --pick 2

        - Return results as json:
          $ nbcli ipblocks 192.168.1.0/24 --json
        """
        try:
            network = ipaddress.ip_network(self.args.prefix, strict=False)
        except ValueError as exc:
            self.logger.critical("Invalid prefix: %s", exc)
            return

        if network.num_addresses > self.args.limit:
            self.logger.critical(
                "Prefix %s contains %s addresses, exceeds --limit %s",
                network,
                network.num_addresses,
                self.args.limit,
            )
            return

        try:
            nb_prefix = resolve_prefix(self.netbox, network)
        except RequestError as exc:
            self.logger.critical("Error querying NetBox for prefix %s: %s", network, exc)
            return

        if nb_prefix is None:
            self.logger.warning("Prefix %s not found in NetBox", network)
            return

        self.logger.info("Found prefix %s (%s)", nb_prefix, nb_prefix.id)

        try:
            used = used_address_ints(self.netbox, network)
        except RequestError as exc:
            self.logger.critical("Error querying addresses in %s: %s", network, exc)
            return

        hosts = list(network.hosts())
        if not hosts:
            self.logger.warning("No usable hosts in %s", network)
            return

        blocks = find_free_blocks(hosts, used)

        min_count = self.args.ongoing
        if min_count:
            blocks = [b for b in blocks if b["size"] >= min_count]

        if self.args.pick:
            self._print_pick(blocks)
            return

        if not blocks:
            self.logger.warning(
                "No %s blocks found in %s",
                "ongoing" if min_count else "unused",
                network,
            )
            return

        if self.args.json:
            print(json.dumps(blocks))
        else:
            self._print_table(blocks)

    def _print_pick(self, blocks):
        """Print the first COUNT free IPs taken from one contiguous block."""
        count = self.args.pick
        picked = []
        for block in blocks:
            if block["size"] >= count:
                start = ipaddress.ip_address(block["start"])
                picked = [str(start + i) for i in range(count)]
                break

        if not picked:
            self.logger.warning("No block with %s consecutive free IPs found", count)
            return

        if self.args.json:
            print(json.dumps(picked))
        else:
            print("\n".join(picked))

    def _print_table(self, blocks):
        """Print blocks as a formatted table."""
        table = [["Start", "End", "Size"]]
        table.extend([[b["start"], b["end"], str(b["size"])] for b in blocks])
        print(rend_table(table))
