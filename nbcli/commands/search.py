"""Search sub command to emulate Netbox main search bar."""

import json
from concurrent.futures import ThreadPoolExecutor

from nbcli.commands.base import BaseSubCommand
from nbcli.core.utils import app_model_by_loc, rs_limit
from nbcli.views.tools import nbprint
from pynetbox.core.query import RequestError
from pynetbox.core.response import Record

# Plugin model aliases considered safe to search by default with an arbitrary
# string. Some plugin filtersets 500 when q= is passed to non-string or
# non-existent fields (e.g. registrar iana_id, zone_template registry_domain_id).
SAFE_PLUGIN_SEARCH_ALIASES = {
    "plugins.netbox_dns": ["nameserver", "view", "zone", "record", "contact"],
}


class SearchSubCommand(BaseSubCommand):
    """Search Netbox objects with the given searchterm.

    The List of search objects can be modified in:
    $CONF_DIR/user_config.yml
    """

    name = "search"
    parser_kwargs = dict(help="Search Netbox Objects")

    def setup(self):
        """Add parser arguments to search sub command."""
        self.parser.add_argument("obj_type", type=str, nargs="?", help="Object type to search")

        self.parser.add_argument("searchterm", help="Search term")

        self.parser.add_argument(
            "--json", action="store_true", help="Display results as json string."
        )

        self.parser.add_argument(
            "--limit",
            type=int,
            metavar="LIMIT",
            help="Limit number of results per object type (overrides 'nbcli.filter_limit').",
        )

    def run(self):
        """Run a search of Netbox objects and show a table or json view of results.

        Usage Examples:

        - Search all object types for 'server1':
          $ nbcli search server1

        - Search the interface object type for 'eth 1':
          $ nbcli search interface 'eth 1'

        - Search for 'server1' and return json for agent consumption:
          $ nbcli search server1 --json

        - Search only devices for 'server1' and return json:
          $ nbcli search device server1 --json

        - Search all object types for 'server1' and return up to 5 results per type:
          $ nbcli search server1 --limit 5
        """
        if hasattr(self.netbox.nbcli.conf, "nbcli") and (
            "search_objects" in self.netbox.nbcli.conf.nbcli.keys()
        ):
            self.search_objects = self.netbox.nbcli.conf.nbcli["search_objects"]
        else:
            self.search_objects = [
                "provider",
                "circuit",
                "site",
                "rack",
                "location",
                "device_type",
                "device",
                "virtual_chassis",
                "cable",
                "power_feed",
                "vrf",
                "aggregate",
                "prefix",
                "address",
                "vlan",
                "tenant",
                "cluster",
                "virtual_machine",
            ]

        # append safe models from NetBox plugins enabled via 'nbcli.plugins' config
        self.search_objects = list(self.search_objects)
        for res in self.netbox.nbcli.rm:
            if res.model.startswith("plugins."):
                plugin = ".".join(res.model.split(".")[:2])
                if res.alias in SAFE_PLUGIN_SEARCH_ALIASES.get(plugin, []) and (
                    res.alias not in self.search_objects
                ):
                    self.search_objects.append(res.alias)

        self.nbprint = nbprint

        self.search_limit = self.args.limit
        if self.search_limit is None:
            self.search_limit = self.netbox.nbcli.conf.nbcli.get("filter_limit", 15)
        self.search_limit = int(self.search_limit)

        if self.args.obj_type:
            modellist = [self.args.obj_type]
        else:
            modellist = self.search_objects

        self.result_count = 0
        self.results = list()

        max_workers = self.netbox.nbcli.conf.nbcli.get("max_workers", 4)

        if self.netbox.threading:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                self.results = list(executor.map(self.search_model, modellist))
        else:
            for obj_type in modellist:
                self.results.append(self.search_model(obj_type))

        self.results = [r for r in self.results if r["records"]]

        if self.args.json:
            print(self.json_output())
            return

        if self.result_count == 0:
            self.logger.warning("No results found")
        else:
            print("")
            for result in self.results:
                print(f"{result['result_str']}\n")

    def search_model(self, obj_type):
        """Search for given model for search term."""
        result_data = {"obj_type": obj_type, "records": list(), "result_str": ""}

        try:
            model = app_model_by_loc(self.netbox, obj_type)
            if self.search_limit <= 0:
                result = list(model.filter(self.args.searchterm))
            else:
                result = rs_limit(model.filter(self.args.searchterm), self.search_limit)
            full_count = model.count(self.args.searchterm)
            if len(result) > 0:
                self.result_count += 1
                records = list(result)
                result_data["records"] = records
                result_data["result_str"] += f"{obj_type.title()}\n{'=' * len(obj_type)}\n"
                result_data["result_str"] += self.nbprint(records, string=True)
                if len(records) < full_count:
                    result_data["result_str"] += (
                        f"\n*** See all {full_count} results: "
                        f"'$nbcli filter {obj_type} {self.args.searchterm} --dl' ***"
                    )

        except AssertionError as err:
            self.logger.warning('No API endpoint found for "%s".', obj_type)
            self.logger.warning(err)
        except RequestError as err:
            if err.req.status_code == 404:
                self.logger.warning('No API endpoint found for "%s".', obj_type)
            else:
                self.logger.warning('Error searching "%s": %s', obj_type, err)

        return result_data

    def json_output(self):
        """Build a json string from all search results."""

        def build(data):
            if isinstance(data, Record):
                data = dict(data)
            elif isinstance(data, list):
                data = [build(d) for d in data]
            return data

        all_records = list()
        for result in self.results:
            for record in result["records"]:
                record_data = build(record)
                record_data["_nbcli_type"] = result["obj_type"]
                all_records.append(record_data)

        return json.dumps(all_records)
