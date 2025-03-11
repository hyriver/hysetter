"""Main functions of hysetter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from hysetter.hysetter import RemoteRaster, Config

__all__ = ["get_rasters"]


def get_rasters(data_cfg: RemoteRaster, model_cfg: Config) -> None:
    """Get NLCD data for the area of interest."""
    import rioxarray as rxr
    from shapely import box

    console = Console(force_jupyter=False)
    gdf = gpd.read_parquet(model_cfg.file_paths.aoi_parquet)
    raster_paths = model_cfg.file_paths.nlcd
    raster_paths.mkdir()
    if not data_cfg.crop:
        gdf["geometry"] = box(*gdf.geometry.bounds.to_numpy().T)
    if data_cfg.geometry_buffer > 0:
        gdf = gdf.to_crs(5070).buffer(data_cfg.geometry_buffer)
    for name, url in data_cfg.rasters.items():
        for i, geom in track(
            enumerate(gdf.geometry),
            description="Getting raster data",
            total=len(gdf),
            console=console,
        ):
            raster_paths[i] = f"{name}_geom_{i}.tif"
            if raster_paths[i].exists():
                continue
            try:
                rxr.open_rasterio(url).squeeze(drop=True).rio.clip_box(
                    *geom.bounds, crs=gdf.crs, auto_expand=True
                ).rio.clip(
                    [geom], crs=gdf.crs, all_touched=True
                ).rio.to_raster(raster_paths[i])
            except Exception:
                console.print_exception(show_locals=True, max_frames=4)
                console.print(f"Failed to get raster data from {url} for AOI index {i}")
                continue
