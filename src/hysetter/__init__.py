"""Top-level package for hysetter."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .aoi import get_aoi
from .forcing import get_forcing
from .hysetter import Config, read_config, write_config
from .nid import get_nid
from .nlcd import get_nlcd
from .nwis import get_streamflow
from .print_versions import show_versions
from .soil import get_soil
from .topo import get_topo

try:
    __version__ = version("hysetter")
except PackageNotFoundError:
    __version__ = "999"

__all__ = [
    "Config",
    "read_config",
    "write_config",
    "show_versions",
    "get_aoi",
    "get_forcing",
    "get_topo",
    "get_soil",
    "get_nlcd",
    "get_nid",
    "get_streamflow",
    "__version__",
]
