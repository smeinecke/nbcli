"""Define function for loading user extensions and plugins."""

import importlib
import pkgutil
import sys
from nbcli import logger
from nbcli.core.utils import get_nbcli_dir


def load_extensions():
    """Load user extensions and plugins."""
    extdir = get_nbcli_dir().joinpath("user_extensions")
    sys.path.append(str(extdir))

    extensions = list()

    for _, name, _ in pkgutil.iter_modules():
        if name.startswith("nbcli_"):
            extensions.append(name)

    # only try to import user files when they actually exist - avoids
    # ModuleNotFoundError noise on every command before 'nbcli init'
    for name in ("user_views", "user_commands"):
        if extdir.joinpath(name + ".py").exists():
            extensions.append(name)

    prev_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True

    for ext in extensions:
        try:
            importlib.import_module(ext)
            logger.info("%s loaded.", ext)
        except Exception as e:
            logger.error("Error loading %s!", ext)
            logger.error("%s: %s", type(e).__name__, str(e))
            if 0 < logger.level <= 10:
                raise e

    sys.dont_write_bytecode = prev_dont_write_bytecode
