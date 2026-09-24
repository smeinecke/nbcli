"""Sub command to export NetBox objects as create-compatible YAML."""

import sys
import yaml
from nbcli.commands.base import BaseSubCommand
from nbcli.commands.filter import Filter
from nbcli.core.utils import is_list_of_records

# Read-only fields rendered by the API that cannot be written back.
SKIP_FIELDS = frozenset(
    [
        "id",
        "url",
        "display",
        "display_url",
        "display_name",
        "created",
        "last_updated",
        "config_context",
        "children",
        "_depth",
    ]
)

# Lookup fields tried, in order, for related objects that cannot be mapped
# to a resolve-reference entry.
LOOKUP_GUESSES = ("name", "model", "prefix", "address", "slug", "display")


class Exporter:
    """Serialize objects to the YAML structure understood by 'nbcli create'."""

    def __init__(self, netbox, model, logger, upsert=False, include_empty=False):
        """Initialize Exporter object."""
        self.netbox = netbox
        self.logger = logger
        self.upsert = upsert
        self.include_empty = include_empty
        self.res = netbox.nbcli.rm.get(model)
        self.alias = self.res.alias if self.res else model.split(".")[-1]

    def _res_for_key(self, key):
        """Return Resolve entry for a field name, like Upsert.proc_data_items does."""
        res = self.res.get(key) if self.res else None
        return res or self.netbox.nbcli.rm.get(key)

    def _res_for_url(self, url):
        """Derive a Resolve entry from a nested object's API url."""
        if not isinstance(url, str):
            return None
        parts = url.replace(self.netbox.base_url, "").strip("/").split("/")
        end = 3 if parts[0] == "plugins" else 2
        return self.netbox.nbcli.rm.get(".".join(parts[:end]).replace("-", "_"))

    def _value(self, key, value):
        """Convert a single API field value to its create-compatible form."""
        if isinstance(value, list):
            return [self._value(key, item) for item in value]

        if not isinstance(value, dict):
            return value

        if set(value) == {"value", "label"}:
            # choice field - the 'value' is what the API accepts on write
            return value["value"]

        if "url" not in value:
            # plain data mapping (custom_fields, local_context_data, ...)
            return {k: self._value(k, v) for k, v in value.items()}

        # related object - emit the value create would resolve it by
        res = self._res_for_key(key) or self._res_for_url(value.get("url"))
        if res and value.get(res.lookup) is not None:
            return value[res.lookup]

        for guess in LOOKUP_GUESSES:
            if value.get(guess) is not None:
                return value[guess]
        return value.get("id")

    def serialize_obj(self, obj):
        """Return a create-compatible field mapping for a single object."""
        drop = self.res.lookup if self.upsert and self.res else None
        data = dict()
        for key, value in dict(obj).items():
            if key in SKIP_FIELDS or key.endswith("_count") or key == drop:
                continue
            value = self._value(key, value)
            if not self.include_empty and value in (None, "", [], {}):
                continue
            data[key] = value
        return data

    def build(self, result):
        """Return the YAML document structure for a list of objects."""
        if self.upsert and self.res:
            data = dict()
            for obj in result:
                lookup = self._value(self.res.lookup, dict(obj).get(self.res.lookup))
                key = "{}:{}".format(self.alias, lookup)
                if key in data:
                    self.logger.warning("Duplicate lookup value in '%s'", key)
                data[key] = self.serialize_obj(obj)
            return data

        if self.upsert:
            self.logger.warning(
                "Ignoring --upsert: no resolve reference entry for '%s'", self.alias
            )

        return {self.alias: [self.serialize_obj(obj) for obj in result]}


class ExportSubCommand(BaseSubCommand):
    """Export NetBox objects as YAML for use with 'nbcli create'."""

    name = "export"
    parser_kwargs = dict(help="Export NetBox objects to YAML.")

    def setup(self):
        """Add argparse arguments to export subcommand."""
        self.parser.add_argument("model", help="NetBox model.")

        self.parser.add_argument("args", nargs="*", help="Argument(s) to filter results.")

        self.parser.add_argument(
            "-f",
            "--file",
            type=str,
            help="Write YAML to file instead of stdout.",
        )

        self.parser.add_argument(
            "--upsert",
            action="store_true",
            help="Export as 'model:lookup' mapping so re-import updates existing objects.",
        )

        self.parser.add_argument(
            "-e",
            "--include-empty",
            action="store_true",
            help="Include fields with empty/null values.",
        )

    def run(self):
        """Run command.

        Export matching objects as YAML in the format 'nbcli create' reads.
        Always exports all matching objects - 'filter_limit' is not applied.

        Usage Examples:

        - Export all sites to a YAML file:
          $ nbcli export site -f sites.yml

        - Export IP addresses matching a filter to stdout:
          $ nbcli export address parent=10.0.0.0/24

        - Export devices as an upsert document (re-import updates in place):
          $ nbcli export device --upsert
        """
        nbfilter = Filter(
            self.netbox,
            self.args.model,
            self.logger,
            args=self.args.args or [],
            dl=True,
        )

        if not is_list_of_records(nbfilter.result):
            self.logger.warning("No results found")
            return

        exporter = Exporter(
            self.netbox,
            self.args.model,
            self.logger,
            upsert=self.args.upsert,
            include_empty=self.args.include_empty,
        )
        data = exporter.build(nbfilter.result)

        text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        if self.args.file:
            with open(self.args.file, "w") as fh:
                fh.write(text)
            self.logger.info(
                "Wrote %s %s object(s) to %s",
                len(nbfilter.result),
                exporter.alias,
                self.args.file,
            )
        else:
            sys.stdout.write(text)
