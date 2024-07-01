"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from .hysetter import Soil

__all__ = ["get_soil"]


def get_soil(cfg_soil: Soil, soil_dir: Path, aoi_parquet: Path) -> None:
    """Get soil data for the area of interest.

    Parameters
    ----------
    config : Config
        A Config object.
    soil_dir : Path
        Path to the directory where the soil data will be saved.
    aoi_parquet : Path
        The path to the AOI parquet file.
    """
    import pygeohydro as gh

    console = Console()

    if cfg_soil.source == "gnatsgo":
        soil_func = gh.soil_gnatsgo
    elif cfg_soil.source == "soilgrids":
        soil_func = gh.soil_soilgrids
    else:
        raise ValueError("Unknown forcing source.")

    gdf = gpd.read_parquet(aoi_parquet)
    source_name = {
        "gnatsgo": "gNATSGO",
        "soilgrids": "SoilGrids",
    }[cfg_soil.source]
    soil_dir.mkdir(exist_ok=True, parents=True)
    for i, geom in track(
        enumerate(gdf.geometry), description=f"Getting soil from {source_name}", total=len(gdf)
    ):
        fpath = Path(soil_dir, f"{cfg_soil.source}_geom_{i}.nc")
        if fpath.exists():
            continue
        try:
            soil = soil_func(cfg_soil.variables, geom, gdf.crs)
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get soil for AOI index {i}")
            continue
        soil.to_netcdf(fpath)
