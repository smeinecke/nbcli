"""Sub command to claim an IP address in a NetBox prefix."""

import ipaddress
import json

from pynetbox.core.query import RequestError
from nbcli.commands.base import BaseSubCommand
from nbcli.core.ipam import free_hosts, resolve_prefix, used_address_ints


class IpClaimSubCommand(BaseSubCommand):
    """Claim the next free (or a given) IP address within a NetBox prefix.

    Creates an ipam.ip_addresses object carrying a dns_name; on NetBox
    installations with netbox-dns IPAM coupling enabled, managed A/PTR
    records are created automatically.
    """

    name = "ipclaim"
    parser_kwargs = dict(help="Claim an IP address in a prefix.")

    def setup(self):
        """Add parser arguments for ipclaim subcommand."""
        self.parser.add_argument("prefix", help="Prefix to claim the address in.")

        self.parser.add_argument("fqdn", help="DNS name (FQDN) for the address.")

        self.parser.add_argument(
            "--address",
            metavar="IP",
            help="Specific IP to claim (default: first free host in the prefix).",
        )

        self.parser.add_argument(
            "--description", default="", help="Description for the IP address."
        )

        self.parser.add_argument(
            "--status",
            default="active",
            metavar="STATUS",
            help="IP address status (default: active).",
        )

        self.parser.add_argument(
            "--json", action="store_true", help="Display result as json string."
        )

    def run(self):
        """Claim an IP address in a prefix.

        Usage Examples:

        - Claim the next free address in a prefix:
          $ nbcli ipclaim 192.168.1.0/24 host1.example.com

        - Claim a specific address:
          $ nbcli ipclaim 192.168.1.0/24 host2.example.com --address 192.168.1.10

        - Claim with a description:
          $ nbcli ipclaim 192.168.1.0/24 host3.example.com --description "web server"
        """
        try:
            network = ipaddress.ip_network(self.args.prefix, strict=False)
        except ValueError as exc:
            self.logger.critical("Invalid prefix: %s", exc)
            return

        try:
            nb_prefix = resolve_prefix(self.netbox, network)
        except RequestError as exc:
            self.logger.critical("Error querying NetBox for prefix %s: %s", network, exc)
            return

        if nb_prefix is None:
            self.logger.critical("Prefix %s not found in NetBox", network)
            return

        try:
            existing = list(
                self.netbox.ipam.ip_addresses.filter(parent=str(network), dns_name=self.args.fqdn)
            )
        except RequestError as exc:
            self.logger.critical("Error querying addresses in %s: %s", network, exc)
            return

        if existing:
            self.logger.critical(
                "FQDN %s already claimed by %s", self.args.fqdn, existing[0].address
            )
            return

        try:
            used = used_address_ints(self.netbox, network)
        except RequestError as exc:
            self.logger.critical("Error querying addresses in %s: %s", network, exc)
            return

        if self.args.address:
            try:
                pick = ipaddress.ip_interface(self.args.address).ip
            except ValueError as exc:
                self.logger.critical("Invalid address: %s", exc)
                return
            if pick not in network:
                self.logger.critical("Address %s not in prefix %s", pick, network)
                return
            if pick in (network.network_address, network.broadcast_address):
                self.logger.critical("Address %s is not a usable host in %s", pick, network)
                return
            if int(pick) in used:
                self.logger.critical("Address %s already in use", pick)
                return
        else:
            pick = next(free_hosts(network, used), None)
            if pick is None:
                self.logger.critical("No free addresses in %s", network)
                return

        cidr = "{}/{}".format(pick, network.prefixlen)
        data = {
            "address": cidr,
            "dns_name": self.args.fqdn,
            "status": self.args.status,
            "description": self.args.description,
        }

        try:
            result = self.netbox.ipam.ip_addresses.create(**data)
        except RequestError as exc:
            self.logger.critical("Error creating address %s: %s", cidr, exc)
            return

        self.logger.info("Claimed %s for %s", cidr, self.args.fqdn)
        self._check_dns_record()

        if self.args.json:
            print(
                json.dumps(
                    {
                        "id": result.id,
                        "address": str(result.address),
                        "dns_name": self.args.fqdn,
                    }
                )
            )
        else:
            print("{}  {}".format(result.address, self.args.fqdn))

    def _check_dns_record(self):
        """Warn if no netbox-dns record appeared for the claimed FQDN."""
        try:
            records = list(
                self.netbox.plugins.netbox_dns.records.filter(fqdn=self.args.fqdn.rstrip(".") + ".")
            )
        except (AttributeError, RequestError):
            self.logger.debug("netbox-dns plugin not available, skipping record check")
            return

        if not records:
            self.logger.warning(
                "No DNS record found for %s - "
                "check that netbox-dns IPAM coupling is enabled for the zone",
                self.args.fqdn,
            )
