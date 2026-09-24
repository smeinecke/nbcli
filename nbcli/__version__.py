"""Declare version number for nbcli."""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("nbcli")
except importlib.metadata.PackageNotFoundError:
    # running from a source checkout without an installed distribution
    __version__ = "0.0.0+unknown"
