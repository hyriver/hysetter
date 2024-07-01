"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from .hysetter import Forcing

__all__ = ["get_forcing"]


def get_forcing(cfg_forcing: Forcing, forcing_dir: Path, aoi_parquet: Path) -> None:
    """Get forcing for the area of interest.

    Parameters
    ----------
    cfg_forcing : Forcing
        A Forcing object.
    forcing_dir : Path
        Path to the directory where the forcing data will be saved.
    aoi_parquet : Path
        The path to the AOI parquet file.
    """
    console = Console()
    if cfg_forcing.source == "daymet":
        import pydaymet as daymet

        get_clm = daymet.get_bygeom
    elif cfg_forcing.source == "gridmet":
        import pygridmet as gridmet

        get_clm = gridmet.get_bygeom
    elif cfg_forcing.source == "nldas2":
        import pynldas2 as nldas2

        get_clm = nldas2.get_bygeom
    else:
        raise ValueError("Unknown forcing source.")

    gdf = gpd.read_parquet(aoi_parquet)
    forcing_dir.mkdir(exist_ok=True, parents=True)
    forcing_name = {
        "daymet": "Daymet",
        "gridmet": "GridMet",
        "nldas2": "NLDAS2",
    }[cfg_forcing.source]
    for i, geom in track(
        enumerate(gdf.geometry), description=f"Getting forcing from {forcing_name}", total=len(gdf)
    ):
        fpath = Path(forcing_dir, f"{cfg_forcing.source}_geom_{i}.nc")
        if fpath.exists():
            continue
        try:
            clm = get_clm(
                geom,
                (cfg_forcing.start_date, cfg_forcing.end_date),  # pyright: ignore[reportArgumentType]
                gdf.crs,
                cfg_forcing.variables,  # pyright: ignore[reportArgumentType]
            )
            clm.to_netcdf(Path(forcing_dir, f"{cfg_forcing.source}_geom_{i}.nc"))
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get forcing for AOI index {i}.")
            continue
