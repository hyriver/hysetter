"""Main functions of hysetter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from hysetter.hysetter import NLCD, Config

__all__ = ["get_nlcd"]


def get_nlcd(data_cfg: NLCD, model_cfg: Config) -> None:
    """Get NLCD data for the area of interest."""
    from pygeohydro import nlcd_bygeom
    from shapely import box

    console = Console(force_jupyter=False)
    gdf = gpd.read_parquet(model_cfg.file_paths.aoi_parquet)
    nlcd_paths = model_cfg.file_paths.nlcd
    nlcd_paths.mkdir()
    years = {
        "cover": data_cfg.cover,
        "impervious": data_cfg.impervious,
        "canopy": data_cfg.canopy,
        "descriptor": data_cfg.descriptor,
    }
    years = {k: v for k, v in years.items() if v is not None}
    join_style = "round"
    if not data_cfg.crop:
        gdf["geometry"] = box(*gdf.geometry.bounds.to_numpy().T)
        join_style = "mitre"
    if data_cfg.geometry_buffer > 0:
        gdf = gdf.to_crs(5070).buffer(data_cfg.geometry_buffer, join_style=join_style)
    if not years:
        years = None
    for i, geom in track(
        enumerate(gdf.geometry),
        description="Getting NLCD from MRLC",
        total=len(gdf),
        console=console,
    ):
        nlcd_paths[i] = f"nlcd_geom_{i}.nc"
        if nlcd_paths[i].exists():
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
        nlcd[0].to_netcdf(nlcd_paths[i])
