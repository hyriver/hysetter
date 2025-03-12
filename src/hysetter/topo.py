"""Main functions of hysetter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from pathlib import Path

    from pyproj import CRS
    from shapely import Polygon
    from xarray import DataArray

    from hysetter.hysetter import Config, Topo

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


def _read_tiffs(tiff_files: list[Path], poly: Polygon, crs: CRS) -> DataArray:
    """Convert a list of tiff files to a vrt file and return a xarray.DataArray."""
    from seamless_3dep import tiffs_to_da

    topo = tiffs_to_da(tiff_files, poly, crs)
    topo.name = "elevation"
    return topo


def get_topo(data_cfg: Topo, model_cfg: Config) -> None:
    """Get topo data for the area of interest."""
    import xarray as xr
    from seamless_3dep import get_map
    from shapely import box

    console = Console(force_jupyter=False)

    topo_functions = {"slope": _slope, "aspect": _aspect, "curvature": _curvature}

    gdf = gpd.read_parquet(model_cfg.file_paths.aoi_parquet)
    topo_paths = model_cfg.file_paths.topo
    topo_paths.mkdir()
    if data_cfg.geometry_buffer > 0:
        buffer = data_cfg.geometry_buffer
    else:
        buffer = 10 * data_cfg.resolution_m
    join_style = "round"
    if not data_cfg.crop:
        gdf["geometry"] = box(*gdf.geometry.bounds.to_numpy().T)
        join_style = "mitre"
    gdf = gdf.to_crs(5070).buffer(buffer, join_style=join_style).to_crs(4326)
    for i, geom in track(
        enumerate(gdf.geometry),
        description="Getting DEM from 3DEP",
        total=len(gdf),
        console=console,
    ):
        topo_paths[i] = f"topo_geom_{i}.nc"
        if topo_paths[i].exists():
            continue
        try:
            tiff_files = get_map("DEM", geom.bounds, topo_paths.parent, data_cfg.resolution_m)
            topo = _read_tiffs(tiff_files, geom, gdf.crs)  # pyright: ignore[reportArgumentType]
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get topo data for AOI index {i}")
            continue
        if data_cfg.derived_variables:
            topo.attrs["res"] = topo.rio.resolution()
            topo_list = [
                topo_functions[var](topo)
                for var in data_cfg.derived_variables
                if var in topo_functions
            ]
            topo = xr.merge([topo, *topo_list])
        topo.to_netcdf(topo_paths[i])
