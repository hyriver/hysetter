"""Main functions of hysetter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from hysetter.hysetter import Config, Forcing

__all__ = ["get_forcing"]


def get_forcing(data_cfg: Forcing, model_cfg: Config) -> None:
    """Get forcing for the area of interest."""
    from shapely import box

    console = Console(force_jupyter=False)
    if data_cfg.source == "daymet":
        import pydaymet as daymet

        get_clm = daymet.get_bygeom
    elif data_cfg.source == "gridmet":
        import pygridmet as gridmet

        get_clm = gridmet.get_bygeom
    elif data_cfg.source == "nldas2":
        import pynldas2 as nldas2

        get_clm = nldas2.get_bygeom
    else:
        raise ValueError("Unknown forcing source.")

    gdf = gpd.read_parquet(model_cfg.file_paths.aoi_parquet)
    forcing_dir = model_cfg.file_paths.forcing
    forcing_dir.mkdir()
    forcing_name = {
        "daymet": "Daymet",
        "gridmet": "GridMet",
        "nldas2": "NLDAS2",
    }[data_cfg.source]

    join_style = "round"
    if not data_cfg.crop:
        gdf["geometry"] = box(*gdf.geometry.bounds.to_numpy().T)
        join_style = "mitre"
    if data_cfg.geometry_buffer > 0:
        gdf = gdf.to_crs(5070).buffer(data_cfg.geometry_buffer, join_style=join_style)
    for i, geom in track(
        enumerate(gdf.geometry),
        description=f"Getting forcing from {forcing_name}",
        total=len(gdf),
        console=console,
    ):
        forcing_dir[i] = f"{data_cfg.source}_geom_{i}.nc"
        if forcing_dir[i].exists():
            continue
        try:
            clm = get_clm(
                geom,  # pyright: ignore[reportArgumentType]
                (data_cfg.start_date, data_cfg.end_date),  # pyright: ignore[reportArgumentType]
                gdf.crs,  # pyright: ignore[reportArgumentType]
                data_cfg.variables,  # pyright: ignore[reportArgumentType]
            )
            clm.to_netcdf(forcing_dir[i])
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get forcing for AOI index {i}.")
            continue
