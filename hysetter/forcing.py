"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from .hysetter import Config

__all__ = ["get_forcing"]


def get_forcing(config: Config) -> None:
    """Get forcing for the area of interest.

    Parameters
    ----------
    config : Config
        A Config object.
    """
    console = Console()
    if config.forcing is None:
        return

    if config.forcing.source == "daymet":
        import pydaymet as daymet

        get_clm = daymet.get_bygeom
    elif config.forcing.source == "gridmet":
        import pygridmet as gridmet

        get_clm = gridmet.get_bygeom
    elif config.forcing.source == "nldas2":
        import pynldas2 as nldas2

        get_clm = nldas2.get_bygeom
    else:
        raise ValueError("Unknown forcing source.")

    gdf = gpd.read_parquet(config.file_paths.aoi_parquet)
    config.file_paths.forcing_dir.mkdir(exist_ok=True, parents=True)
    forcing_name = {
        "daymet": "Daymet",
        "gridmet": "GridMet",
        "nldas2": "NLDAS2",
    }[config.forcing.source]
    for i, geom in track(
        enumerate(gdf.geometry), description=f"Getting forcing from {forcing_name}", total=len(gdf)
    ):
        fpath = Path(config.file_paths.forcing_dir, f"{config.forcing.source}_geom_{i}.nc")
        if fpath.exists():
            continue
        try:
            clm = get_clm(
                geom,
                (config.forcing.start_date, config.forcing.end_date),  # pyright: ignore[reportArgumentType]
                gdf.crs,
                config.forcing.variables,  # pyright: ignore[reportArgumentType]
            )
            clm.to_netcdf(
                Path(config.file_paths.forcing_dir, f"{config.forcing.source}_geom_{i}.nc")
            )
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get forcing for AOI index {i}.")
            continue
