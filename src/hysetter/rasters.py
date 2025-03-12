"""Main functions of hysetter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from hysetter.hysetter import Config, RemoteRasters

__all__ = ["get_rasters"]


def get_rasters(data_cfg: RemoteRasters, model_cfg: Config) -> None:
    """Get raster data for the area of interest."""
    import rioxarray as rxr
    from shapely import box

    console = Console(force_jupyter=False)
    gdf = gpd.read_parquet(model_cfg.file_paths.aoi_parquet)
    raster_paths = model_cfg.file_paths.remote_rasters
    join_style = "round"
    if not data_cfg.crop:
        gdf["geometry"] = box(*gdf.geometry.bounds.to_numpy().T)
        join_style = "mitre"
    if data_cfg.geometry_buffer > 0:
        gdf = gdf.to_crs(5070).buffer(data_cfg.geometry_buffer, join_style=join_style)
    for name, url in data_cfg.rasters.items():
        raster_paths[name].mkdir()
        for i, geom in track(
            enumerate(gdf.geometry),
            description=f"Getting raster data for {name}",
            total=len(gdf),
            console=console,
        ):
            raster_paths[name][i] = f"{name}_geom_{i}.tif"
            if raster_paths[name][i].exists():
                continue
            try:
                rxr.open_rasterio(url).squeeze(drop=True).rio.clip_box(
                    *geom.bounds, crs=gdf.crs, auto_expand=True
                ).rio.clip([geom], crs=gdf.crs, all_touched=True).rio.to_raster(
                    raster_paths[name][i]
                )
            except Exception:
                console.print_exception(show_locals=True, max_frames=4)
                console.print(f"Failed to get raster data from {url} for AOI index {i}")
                continue
