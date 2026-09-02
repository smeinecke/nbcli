"""Unit tests for nbcli."""

import argparse

import nbcli.cli
from nbcli.commands.search import SearchSubCommand


def test_package_import():
    """Smoke test that the package imports cleanly."""
    assert nbcli.cli.main is not None


def test_search_subcommand_has_json_flag():
    """The search subcommand parser should accept --json."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    command = SearchSubCommand(subparsers)
    option_strings = [
        option
        for action in command.parser._actions
        for option in action.option_strings
    ]
    assert "--json" in option_strings
