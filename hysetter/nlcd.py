"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from .hysetter import NLCD

__all__ = ["get_nlcd"]


def get_nlcd(cfg_nlcd: NLCD, nlcd_dir: Path, aoi_parquet: Path) -> None:
    """Get NLCD data for the area of interest.

    Parameters
    ----------
    cfg_nlcd : NLCD
        A NLCD object.
    nlcd_dir : Path
        Path to the directory where the NLCD data will be saved.
    aoi_parquet : Path
        The path to the AOI parquet file.
    """
    from pygeohydro import nlcd_bygeom

    console = Console()
    gdf = gpd.read_parquet(aoi_parquet)
    nlcd_dir.mkdir(exist_ok=True, parents=True)
    years = {
        "cover": cfg_nlcd.cover,
        "impervious": cfg_nlcd.impervious,
        "canopy": cfg_nlcd.canopy,
        "descriptor": cfg_nlcd.descriptor,
    }
    years = {k: v for k, v in years.items() if v is not None}
    if not years:
        years = None
    for i, geom in track(
        enumerate(gdf.geometry), description="Getting NLCD from MRLC", total=len(gdf)
    ):
        fpath = Path(nlcd_dir, f"nlcd_geom_{i}.nc")
        if fpath.exists():
            continue
        try:
            nlcd = nlcd_bygeom(
                gpd.GeoSeries(geom, crs=gdf.crs),  # pyright: ignore[reportCallIssue]
                30,
                years=years,
            )
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get NLCD data for AOI index {i}")
            continue
        nlcd[0].to_netcdf(fpath)
