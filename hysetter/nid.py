"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from .hysetter import Config

__all__ = ["get_nlcd"]


def get_nlcd(config: Config) -> None:
    """Get NID data for the area of interest.

    Parameters
    ----------
    config : Config
        A Config object.
    """
    from pygeohydro import NID

    console = Console()
    if config.nlcd is None:
        return

    gdf = gpd.read_parquet(config.file_paths.aoi_parquet)
    config.file_paths.nid_dir.mkdir(exist_ok=True, parents=True)
    nid = NID()
    nid.stage_nid_inventory(Path(config.file_paths.project_dir, "full_nid_inventory.feather"))

    for i, geom in track(
        enumerate(gdf.geometry), description="Getting NID from MRLC", total=len(gdf)
    ):
        fpath = Path(config.file_paths.nid_dir, f"nid_geom_{i}.parquet")
        if fpath.exists():
            continue
        try:
            nid.get_bygeom(geom, gdf.crs).to_parquet(fpath)
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get NID data for AOI index {i}")
            continue
