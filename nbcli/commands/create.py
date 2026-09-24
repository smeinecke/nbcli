"""Sub command to create and/or update objects as defined in YAML file."""

import yaml
from nbcli.core.utils import app_model_by_loc
from nbcli.commands.base import BaseSubCommand
from nbcli.commands.tools import NbArgs


class Upsert:
    """Create and/or Update objects defined in dict."""

    def __init__(self, netbox, logger, model, data, res=None, parent=None):
        """Initialize Upsert object."""
        assert (parent is None) or isinstance(parent, Upsert)

        if isinstance(data, list):
            for d in data:
                Upsert(netbox, logger, model, d, res=res, parent=parent)
            return

        self.netbox = netbox
        self.logger = logger
        self.model = model
        self.data = data
        self.parent = parent

        self.res = res or netbox.nbcli.rm.get(self.model.split(":")[0])
        self.ep = app_model_by_loc(self.netbox, self.res.model)
        self.args = None
        self.obj = None
        self.children = list()  # list of tuples (model, data, res)

        assert self.res

        self.obj = None

        self.proc_model()

        self.action()

        self.proc_children()

    def _add_parent_arg(self):
        """If self has a parent object, make sure to apply the correct resolve model."""
        if self.parent:
            # Match the child entry by alias first, then by model. Matching by
            # model alone is ambiguous when a parent defines several children
            # of the same model (e.g. interface_a/interface_b on a cable).
            res = (
                self.parent.res.get(self.res.alias)
                or self.parent.res.get(self.res.model)
                or self.parent.res
            )
            self.args.apply_res([self.parent.obj], res)

    def proc_model(self):
        """Process model string (key), and resolve if needed."""
        # A trailing '^' on the model key excludes the parent object's reply
        # args from the lookup (existence check) filter; they are still applied
        # to the create/update data. Only needed when the parent's reply fields
        # are not valid filter parameters on the child's endpoint and no
        # relation-specific child entry exists in resolve_reference.yml.
        scope_by_parent = True
        if self.model.endswith("^"):
            scope_by_parent = False
            self.model = self.model[:-1]

        if ":" in self.model:
            self.args = NbArgs(self.netbox)
            alias, kws = self.model.split(":", 1)
            if scope_by_parent:
                self._add_parent_arg()

            # Pass the lookup value verbatim. Running it through NbArgs.proc()
            # would mangle values containing ':' or '=' (e.g. IPv6 addresses).
            lookup_kwargs = dict(self.args.kwargs)
            lookup_kwargs[self.res.lookup] = kws
            nba, self.obj = self.args.resolve(alias, kwargs=lookup_kwargs, res=self.res)
            if self.obj:
                assert len(self.obj) == 1, (
                    f"'{self.model}' matched {len(self.obj)} objects - refine the lookup value"
                )
                self.obj = self.obj[0]
                self.args = NbArgs(self.netbox, action="patch")
                if not scope_by_parent:
                    self._add_parent_arg()
            else:
                self.obj = None
                self.args = NbArgs(self.netbox, action="post")
                if self.res.lookup in nba.kwargs:
                    lookup_value = nba.kwargs[self.res.lookup]
                    if isinstance(lookup_value, list):
                        lookup_value = lookup_value[-1]
                    self.args.update(self.res.lookup, lookup_value)
        else:
            self.args = NbArgs(self.netbox, action="post")

        self._add_parent_arg()

    def action(self):
        """Perform the create or update action for defined object."""
        for key, value in self.data.items():
            self.proc_data_items(key, value)

        if self.obj:
            self.logger.info("Updating %s with data: %s", str(self.obj), str(self.args.kwargs))
            self.obj.update(self.args.kwargs)
        else:
            self.logger.info("Creating %s with data: %s", self.res.alias, str(self.args.kwargs))
            self.obj = self.ep.create(**self.args.kwargs)

    def proc_data_items(self, key, value, create=False):
        """Process individual key, value pair to determine what to do with it."""
        rstr = key.split(":")[0]
        res = self.res.get(rstr) or self.netbox.nbcli.rm.get(rstr)

        if res:
            if (":" in key) and (value is None):
                self.children.append((key, {}, res))
            elif isinstance(value, (dict, list)):
                self.children.append((key, value, res))
            elif value is None or rstr in (self.res.alias, self.res.model, self.res.lookup):
                # The key names this object's own model (e.g. 'address' on
                # ipam.ip_addresses) - the value is data, not a reference.
                # An explicit null is also literal data (clears the field on
                # update).
                self.args.update(key, value)
            else:
                _, result = self.args.resolve(key, value, res=res)
                if not result:
                    self.logger.warning("Could not resolve '%s: %s'", key, value)
        else:
            self.args.update(key, value)

    def proc_children(self):
        """Run Upsert on any child objects found."""
        for child in self.children:
            model, data, res = child

            Upsert(self.netbox, self.logger, model, data, res=res, parent=self)


class CreateSubCommand(BaseSubCommand):
    """Create and/or Update objects defined in YAML file."""

    name = "create"
    parser_kwargs = dict(help="Create/Update objects with YAML file.")
    default_loglevel = 20

    def setup(self):
        """Add file argument to create subcommand."""
        self.parser.add_argument("file", type=str, help="YAML file.")

    def run(self):
        """Run command.

        See documentation and reference examples.
        https://nbcli.codeberg.page/latest/commands/create/
        https://nbcli.codeberg.page/latest/reference/create-examples/

        Usage Examples:

        - Create/Update objects defined in YAML file
          $ nbcli create file.yml
        """
        with open(self.args.file) as fh:
            self.logger.debug("Reading yaml file")
            data_stream = yaml.safe_load_all(fh.read())

        for data in data_stream:
            if not data:
                # empty document (e.g. a trailing '---' in the file)
                continue
            if not isinstance(data, dict):
                self.logger.error("Skipping non-mapping YAML document: %s", data)
                continue
            self.logger.debug(data)
            for key, value in data.items():
                assert self.netbox.nbcli.rm.get(key.split(":")[0])
                Upsert(self.netbox, self.logger, key, value, parent=None)
