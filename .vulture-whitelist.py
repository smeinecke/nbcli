"""Vulture whitelist for nbcli dynamic attributes and entry points."""

from nbcli.commands.create import CreateSubCommand
from nbcli.commands.filter import FilterSubCommand
from nbcli.commands.info import InfoSubCommand
from nbcli.commands.init import InitSubCommand
from nbcli.commands.search import SearchSubCommand
from nbcli.commands.shell import ShellSubCommand
from nbcli.core.utils import getter
from nbcli.views.circuits import (
    CircuitsCircuitTypesView,
    CircuitsCircuitsView,
    CircuitsProvidersView,
)
from nbcli.views.dcim import (
    DcimDeviceTypesView,
    DcimDevicesView,
    DcimInterfacesView,
    DcimLocationsView,
    DcimRUsView,
    DcimRacksView,
    DcimSitesView,
)
from nbcli.views.extras import ExtrasConfigContextsView, ExtrasObjectChangesView
from nbcli.views.ipam import (
    IpamAggregatesView,
    IpamIpAddressesView,
    IpamPrefixesView,
    IpamVlansView,
)
from nbcli.views.tenancy import TenancyTenantGroupsView, TenancyTenantsView

_ = (
    CreateSubCommand,
    FilterSubCommand,
    InfoSubCommand,
    InitSubCommand,
    SearchSubCommand,
    ShellSubCommand,
    getter,
    CircuitsCircuitTypesView,
    CircuitsCircuitsView,
    CircuitsProvidersView,
    DcimDeviceTypesView,
    DcimDevicesView,
    DcimInterfacesView,
    DcimLocationsView,
    DcimRUsView,
    DcimRacksView,
    DcimSitesView,
    ExtrasConfigContextsView,
    ExtrasObjectChangesView,
    IpamAggregatesView,
    IpamIpAddressesView,
    IpamPrefixesView,
    IpamVlansView,
    TenancyTenantGroupsView,
    TenancyTenantsView,
)


