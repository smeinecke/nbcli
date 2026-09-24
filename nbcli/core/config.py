"""Objects related to loading nbcli configuration."""

import os
from importlib.resources import files
import pynetbox
import requests
import urllib3
import yaml
from nbcli import logger, __version__
from nbcli.core.utils import ResMgr, auto_cast, get_nbcli_dir


class Config:
    """nbcli config Namespace."""

    def __init__(self, init=False):
        """Create Config object.

        Args:
            init (bool): Seting True will create a new configuration file.
        """
        uf = type("tree", (), {})()

        uf.dir = get_nbcli_dir()
        uf.user_config = uf.dir.joinpath("user_config.yml")
        uf.extdir = uf.dir.joinpath("user_extensions")
        uf.user_commands = uf.extdir.joinpath("user_commands.py")
        uf.user_views = uf.extdir.joinpath("user_views.py")

        self.user_files = uf

        if init:
            self._init()
            return

        self._load()

    def _init(self):
        """Create a new empty config file."""
        # Create user directory tree
        dirlist = [self.user_files.dir, self.user_files.extdir]
        for udir in dirlist:
            if udir.exists() and not udir.is_dir():
                logger.critical("%s exists, but is not a directory", str(udir.absolute()))
                raise FileExistsError(str(udir.absolute()))
            else:
                udir.mkdir(parents=True, exist_ok=True)

        # Create user files
        filelist = [
            self.user_files.user_config,
            self.user_files.user_commands,
            self.user_files.user_views,
        ]
        for ufile in filelist:
            if ufile.exists():
                logger.info("%s already exists. Skipping.", str(ufile))
            else:
                ufile.touch()
                default = ufile.name + ".default"
                logger.debug(default)
                with open(str(ufile), "w") as fh:
                    fh.write((files("nbcli.user_defaults") / default).read_text())

        print("Edit pynetbox 'url' and 'token' entries in user_config.yml:")
        print("\t{}".format(str(self.user_files.user_config.absolute())))

    def _load(self):
        """Set attributes from config file or os environment variables."""
        conffile = self.user_files.user_config
        try:
            with open(str(conffile)) as fh:
                user_config = yaml.safe_load(fh) or {}
        except Exception as e:
            logger.critical("Error loading user_config!")
            logger.critical("Run: 'nbcli init' to create a user_config file")
            raise e

        if not isinstance(user_config, dict):
            raise ValueError(
                f"user_config must be a YAML mapping, got {type(user_config).__name__}"
            )

        for key, value in user_config.items():
            if isinstance(value, (dict, type(None))):
                setattr(self, key, value or {})

        # get envars - NBCLI_<SECTION>_<ATTR> overrides or creates sections
        for envkey in os.environ:
            if not envkey.startswith("NBCLI_"):
                continue
            section, _, attr = envkey[6:].partition("_")
            if not section or not attr:
                continue
            target = getattr(self, section.lower(), None)
            if not isinstance(target, dict):
                target = {}
                setattr(self, section.lower(), target)
            target[attr.lower()] = auto_cast(os.environ[envkey])


def get_session(init=False):
    """Create and return pynetbox api object."""
    conf = Config(init=init)
    delattr(conf, "user_files")

    if init:
        return

    url = getattr(conf, "pynetbox", {}).get("url")
    if not url:
        raise ValueError("No 'url' set in the 'pynetbox' section of user_config.yml")
    del conf.pynetbox["url"]

    nb = pynetbox.api(url, **conf.pynetbox)
    del conf.pynetbox

    if hasattr(conf, "requests"):
        reqconf = getattr(conf, "requests")
        session = requests.Session()
        for key, value in reqconf.items():
            setattr(session, key, value)

        nb.http_session = session
        del conf.requests

    if nb.http_session.verify is False:
        urllib3.disable_warnings()

    nb.http_session.headers["User-Agent"] = f"nbcli/{__version__}"

    nb.nbcli = type("nbcli", (), {})()

    resstr = (files("nbcli.core") / "resolve_reference.yml").read_text()
    resdict = yaml.safe_load(resstr)

    # 'nbcli' section is optional in user_config.yml - normalize it so
    # callers can rely on conf.nbcli being a dict
    nbcli_conf = getattr(conf, "nbcli", None)
    conf.nbcli = nbcli_conf if isinstance(nbcli_conf, dict) else {}

    # load resolve definitions for enabled NetBox plugins
    plugins = conf.nbcli.get("plugins") or []
    if isinstance(plugins, str):
        plugins = [plugins]

    for plugin in plugins:
        try:
            plugstr = (files("nbcli.core") / "resolve_reference_{}.yml".format(plugin)).read_text()
        except FileNotFoundError:
            logger.warning("No resolve definitions found for plugin '%s'", plugin)
            continue
        resdict.update(yaml.safe_load(plugstr) or {})

    nb.nbcli.rm = ResMgr(**resdict)

    nb.nbcli.logger = logger
    nb.nbcli.conf = conf

    return nb
