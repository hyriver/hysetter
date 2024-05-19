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
    """Get topo data for the area of interest.

    Parameters
    ----------
    config : Config
        A Config object.
    """
    from pygeohydro import nlcd_bygeom

    console = Console()
    if config.nlcd is None:
        return

    gdf = gpd.read_parquet(config.file_paths.aoi_parquet)
    config.file_paths.topo_dir.mkdir(exist_ok=True, parents=True)
    years = {"cover": config.nlcd.cover, "impervious": config.nlcd.impervious, "canopy": config.nlcd.canopy, "descriptor": config.nlcd.descriptor}
    years = {k: v for k, v in years.items() if v is not None}
    if not years:
        years = None
    for i, geom in track(
        enumerate(gdf.geometry), description="Getting NLCD from MRLC", total=len(gdf)
    ):
        fpath = Path(config.file_paths.topo_dir, f"nlcd_geom_{i}.nc")
        if fpath.exists():
            continue
        try:
            nlcd = nlcd_bygeom(geom, 30, years=years, crs=gdf.crs)
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get NLCD data for AOI index {i}")
            continue
        nlcd.to_netcdf(fpath)
