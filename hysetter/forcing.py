"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
import pydaymet as daymet

from .utils import get_logger

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
    logger = get_logger()
    if config.forcing is None:
        return

    if config.forcing.source == "daymet":
        gdf = gpd.read_parquet(config.file_paths.aoi_parquet)
        for i, geom in enumerate(gdf.geometry):
            try:
                logger.info(f"forcing for AOI index {i}.")
                clm = daymet.get_bygeom(
                    geom,
                    (config.forcing.start_date, config.forcing.end_date),  # pyright: ignore[reportArgumentType]
                    gdf.crs,
                    config.forcing.variables,  # pyright: ignore[reportArgumentType]
                )
                clm.to_netcdf(Path(config.file_paths.forcing_dir, f"daymet_geom_{i}.nc"))
            except Exception as e:
                logger.warning(
                    f"Failed to get forcing for AOI index {i}:\n{e!s}", UserWarning, stacklevel=2
                )
                continue
