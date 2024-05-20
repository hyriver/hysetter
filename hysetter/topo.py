"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from xarray import DataArray

    from .hysetter import Config

__all__ = ["get_topo"]


def _slope(dem: DataArray) -> DataArray:
    """Calculate slope in degrees."""
    from xrspatial import slope

    return slope(dem)


def _aspect(dem: DataArray) -> DataArray:
    """Calculate aspect in degrees.

    It is measured clockwise in degrees with 0 (due north), and 360 (again due north).
    """
    from xrspatial import aspect

    return aspect(dem)


def _curvature(dem: DataArray) -> DataArray:
    """Calculate curvature.

    A positive curvature indicates the surface is upwardly convex.
    A negative value indicates it is upwardly concave. A value of 0 indicates a flat surface.
    """
    from xrspatial import curvature

    return curvature(dem)


def get_topo(config: Config) -> None:
    """Get topo data for the area of interest.

    Parameters
    ----------
    config : Config
        A Config object.
    """
    import xarray as xr
    from py3dep import get_dem

    console = Console()
    if config.topo is None:
        return
    topo_functions = {"slope": _slope, "aspect": _aspect, "curvature": _curvature}

    gdf = gpd.read_parquet(config.file_paths.aoi_parquet)
    config.file_paths.topo_dir.mkdir(exist_ok=True, parents=True)
    for i, geom in track(
        enumerate(gdf.geometry), description="Getting DEM from 3DEP", total=len(gdf)
    ):
        fpath = Path(config.file_paths.topo_dir, f"topo_geom_{i}.nc")
        if fpath.exists():
            continue
        try:
            topo = get_dem(geom, config.topo.resolution_m, gdf.crs)
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get topo data for AOI index {i}")
            continue
        if config.topo.derived_variables:
            topo_list = [
                topo_functions[var](topo)
                for var in config.topo.derived_variables
                if var in topo_functions
            ]
            topo = xr.merge([topo, *topo_list])
        topo.to_netcdf(fpath)
