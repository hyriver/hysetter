"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from xarray import DataArray

    from .hysetter import Topo

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


def get_topo(cfg_topo: Topo, topo_dir: Path, aoi_parquet: Path) -> None:
    """Get topo data for the area of interest.

    Parameters
    ----------
    cfg_topo : Topo
        A Topo object.
    topo_dir : Path
        Path to the directory where the topo data will be saved.
    aoi_parquet : Path
        The path to the AOI parquet file.
    """
    import xarray as xr
    from py3dep import get_dem

    console = Console()

    topo_functions = {"slope": _slope, "aspect": _aspect, "curvature": _curvature}

    gdf = gpd.read_parquet(aoi_parquet)
    topo_dir.mkdir(exist_ok=True, parents=True)
    for i, geom in track(
        enumerate(gdf.geometry), description="Getting DEM from 3DEP", total=len(gdf)
    ):
        fpath = Path(topo_dir, f"topo_geom_{i}.nc")
        if fpath.exists():
            continue
        try:
            topo = get_dem(geom, cfg_topo.resolution_m, gdf.crs).rio.reproject(5070)
            topo = topo.where(topo.notnull(), drop=True).rio.write_transform()
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get topo data for AOI index {i}")
            continue
        if cfg_topo.derived_variables:
            topo.attrs["res"] = topo.rio.resolution()
            topo_list = [
                topo_functions[var](topo)
                for var in cfg_topo.derived_variables
                if var in topo_functions
            ]
            topo = xr.merge([topo, *topo_list])
        topo.to_netcdf(fpath)
