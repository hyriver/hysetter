"""Main functions of hysetter."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import cast

import geopandas as gpd
import pandas as pd
import pydaymet as daymet

from .hysetter import Config

__all__ = ["get_forcing"]


def get_forcing(config: Config) -> None:
    """Get forcing for the area of interest.

    Parameters
    ----------
    config : Config
        A Config object.
    """
    if config.forcing is None:
        return

    if config.forcing.source == "daymet":
        gdf = gpd.read_parquet(config.file_paths.aoi_parquet)
        for i, geom in enumerate(gdf.geometry):
            try:
                clm = daymet.get_bygeom(geom, (config.forcing.start_date, config.forcing.end_date), gdf.crs, config.forcing.variables)
                clm.to_netcdf(Path(config.file_paths.forcing_dir, f"forcing_{i}.nc"))
            except Exception:
                warnings.warn(f"Failed to get forcing for AOI index {i}.", UserWarning, stacklevel=2)
                continue