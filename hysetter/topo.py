"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
from rich.progress import track
import xarray as xr

from .utils import get_logger

if TYPE_CHECKING:
    from .hysetter import Config

    from xarray import DataArray

__all__ = ["get_topo"]


def _slope(dem: DataArray)->DataArray:
    """Calculate slope in degrees."""
    from xrspatial import slope
    return slope(dem)

def _aspect(dem: DataArray)->DataArray:
    """Calculate aspect in degrees.
    
    It is measured clockwise in degrees with 0 (due north), and 360 (again due north).
    """
    from xrspatial import aspect
    return aspect(dem)

def _curvature(dem: DataArray)->DataArray:
    """Calculate curvature.
    
    A positive curvature indicates the surface is upwardly convex.
    A negative value indicates it is upwardly concave. A value of 0 indicates a flat surface.
    """
    from xrspatial import curvature
    return curvature(dem)

def get_topo(config: Config) -> None:
    """Get forcing for the area of interest.

    Parameters
    ----------
    config : Config
        A Config object.
    """
    import py3dep

    logger = get_logger()
    if config.topo is None:
        return
    topo_functions = {
        "slope": lambda dem: _slope(dem),
        "aspect": lambda dem: _aspect(dem),
        "curvature": lambda dem: _curvature(dem)
    }

    gdf = gpd.read_parquet(config.file_paths.aoi_parquet)
    for i, geom in track(
        enumerate(gdf.geometry), description=f"Getting DEM from 3DEP", total=len(gdf)
    ):
        try:
            topo = py3dep.get_dem(geom, config.topo.resolution_m, gdf.crs)
        except Exception as e:
            logger.warning(
                f"Failed to get forcing for AOI index {i}:\n{e!s}", UserWarning, stacklevel=2
            )
            continue
        if config.topo.derived_variables:
            topo_list = [topo_functions[var](topo) for var in config.topo.derived_variables if var in topo_functions]
            topo = xr.merge([topo, *topo_list])
        topo.to_netcdf(
            Path(config.file_paths.topo_dir, f"topo_geom_{i}.nc")
        )
