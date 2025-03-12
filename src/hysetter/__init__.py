"""Top-level package for hysetter."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from hysetter import exceptions
from hysetter.aoi import get_aoi
from hysetter.forcing import get_forcing
from hysetter.hysetter import Config, read_config, write_config
from hysetter.nid import get_nid
from hysetter.nlcd import get_nlcd
from hysetter.nwis import get_streamflow
from hysetter.print_versions import show_versions
from hysetter.soil import get_soil
from hysetter.topo import get_topo

try:
    __version__ = version("hysetter")
except PackageNotFoundError:
    __version__ = "999"

__all__ = [
    "Config",
    "__version__",
    "exceptions",
    "get_aoi",
    "get_forcing",
    "get_nid",
    "get_nlcd",
    "get_soil",
    "get_streamflow",
    "get_topo",
    "read_config",
    "show_versions",
    "write_config",
]
