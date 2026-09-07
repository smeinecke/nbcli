"""Default views for models of NetBox plugins."""

from nbcli.views.tools import BaseView


class PluginsNetboxDnsNameserversView(BaseView):
    """Default view for netbox_dns nameservers."""

    def table_view(self):
        """Define columns for nameservers."""
        self.add_col("Name Server", self.get_attr("name"))
        self.add_col("Description", self.get_attr("description"))


class PluginsNetboxDnsViewsView(BaseView):
    """Default view for netbox_dns views."""

    def table_view(self):
        """Define columns for views."""
        self.add_col("View", self.get_attr("name"))
        self.add_col("Description", self.get_attr("description"))


class PluginsNetboxDnsZonesView(BaseView):
    """Default view for netbox_dns zones."""

    def table_view(self):
        """Define columns for zones."""
        self.add_col("Zone", self.get_attr("name"))
        self.add_col("View", self.get_attr("view"))
        self.add_col("Status", self.get_attr("status"))
        self.add_col("Active", self.get_attr("active"))
        self.add_col("Description", self.get_attr("description"))


class PluginsNetboxDnsRecordsView(BaseView):
    """Default view for netbox_dns records."""

    def table_view(self):
        """Define columns for records."""
        self.add_col("Name", self.get_attr("fqdn") or self.get_attr("name"))
        self.add_col("Zone", self.get_attr("zone"))
        self.add_col("Type", self.get_attr("type"))
        self.add_col("Value", self.get_attr("value"))
        self.add_col("TTL", self.get_attr("ttl"))
        self.add_col("Status", self.get_attr("status"))


class PluginsNetboxDnsRegistrarsView(BaseView):
    """Default view for netbox_dns registrars."""

    def table_view(self):
        """Define columns for registrars."""
        self.add_col("Registrar", self.get_attr("name"))
        self.add_col("IANA ID", self.get_attr("iana_id"))
        self.add_col("Description", self.get_attr("description"))


class PluginsNetboxDnsContactsView(BaseView):
    """Default view for netbox_dns registration contacts."""

    def table_view(self):
        """Define columns for registration contacts."""
        self.add_col("Contact", self.get_attr("name"))
        self.add_col("Contact ID", self.get_attr("contact_id"))
        self.add_col("Organization", self.get_attr("organization"))
        self.add_col("Email", self.get_attr("email"))


class PluginsNetboxDnsZonetemplatesView(BaseView):
    """Default view for netbox_dns zone templates."""

    def table_view(self):
        """Define columns for zone templates."""
        self.add_col("Zone Template", self.get_attr("name"))
        self.add_col("Description", self.get_attr("description"))


class PluginsNetboxDnsRecordtemplatesView(BaseView):
    """Default view for netbox_dns record templates."""

    def table_view(self):
        """Define columns for record templates."""
        self.add_col("Record Template", self.get_attr("name"))
        self.add_col("Type", self.get_attr("type"))
        self.add_col("Value", self.get_attr("value"))
        self.add_col("TTL", self.get_attr("ttl"))


class PluginsNetboxDnsDnsseckeytemplatesView(BaseView):
    """Default view for netbox_dns DNSSEC key templates."""

    def table_view(self):
        """Define columns for DNSSEC key templates."""
        self.add_col("Key Template", self.get_attr("name"))
        self.add_col("Type", self.get_attr("type"))
        self.add_col("Algorithm", self.get_attr("algorithm"))
        self.add_col("Lifetime", self.get_attr("lifetime"))


class PluginsNetboxDnsDnssecpoliciesView(BaseView):
    """Default view for netbox_dns DNSSEC policies."""

    def table_view(self):
        """Define columns for DNSSEC policies."""
        self.add_col("Policy", self.get_attr("name"))
        self.add_col("Status", self.get_attr("status"))
        self.add_col("Description", self.get_attr("description"))
