"""Main functions of hysetter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from hysetter.hysetter import Config, Soil

__all__ = ["get_soil"]


def get_soil(data_cfg: Soil, model_cfg: Config) -> None:
    """Get soil data for the area of interest."""
    import pygeohydro as gh
    from shapely import box

    console = Console(force_jupyter=False)

    if data_cfg.source == "gnatsgo":
        soil_func = gh.soil_gnatsgo
    elif data_cfg.source == "soilgrids":
        soil_func = gh.soil_soilgrids
    elif data_cfg.source == "polaris":
        soil_func = gh.soil_polaris
    else:
        raise ValueError("Unknown forcing source.")

    gdf = gpd.read_parquet(model_cfg.file_paths.aoi_parquet)
    source_name = {
        "gnatsgo": "gNATSGO",
        "soilgrids": "SoilGrids",
        "polaris": "POLARIS",
    }[data_cfg.source]
    soil_paths = model_cfg.file_paths.soil
    soil_paths.mkdir()
    join_style = "round"
    if not data_cfg.crop:
        gdf["geometry"] = box(*gdf.geometry.bounds.to_numpy().T)
        join_style = "mitre"
    if data_cfg.geometry_buffer > 0:
        gdf = gdf.to_crs(5070).buffer(data_cfg.geometry_buffer, join_style=join_style)
    for i, geom in track(
        enumerate(gdf.geometry),
        description=f"Getting soil from {source_name}",
        total=len(gdf),
        console=console,
    ):
        soil_paths[i] = f"{data_cfg.source}_geom_{i}.nc"
        if soil_paths[i].exists():
            continue
        try:
            soil = soil_func(data_cfg.variables, geom, gdf.crs)  # pyright: ignore[reportArgumentType]
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get soil for AOI index {i}")
            continue
        soil.to_netcdf(soil_paths[i])
