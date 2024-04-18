"""Top-level package for hysetter."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from hysetter.hysetter import read_config
from hysetter.print_versions import show_versions

try:
    __version__ = version("hysetter")
except PackageNotFoundError:
    __version__ = "999"

__all__ = ["read_config", "show_versions", "__version__"]
