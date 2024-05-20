"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from .hysetter import Config

__all__ = ["get_streamflow"]


def get_streamflow(config: Config) -> None:
    """Get streamflow data for the area of interest.

    Parameters
    ----------
    config : Config
        A Config object.
    """
    from pygeohydro import NWIS

    console = Console()
    if config.streamflow is None:
        return

    gdf = gpd.read_parquet(config.file_paths.aoi_parquet)
    config.file_paths.streamflow_dir.mkdir(exist_ok=True, parents=True)

    start = config.streamflow.start_date.strftime("%Y-%m-%d")
    end = config.streamflow.end_date.strftime("%Y-%m-%d")
    freq = "dv" if config.streamflow.frequency == "daily" else "iv"
    nwis = NWIS()
    for i, geom in track(
        enumerate(gdf.geometry.to_crs(4326)), description="Getting streamflow from NWIS", total=len(gdf)
    ):
        fpath = Path(config.file_paths.streamflow_dir, f"streamflow_geom_{i}.nc")
        if fpath.exists():
            continue
        try:
            query = {"bBox": ",".join(f"{b:.06f}" for b in geom.bounds), "outputDataTypeCd": freq}
            siteinfo = nwis.get_info(query)
            sids = siteinfo.loc[siteinfo.within(geom), "site_no"].unique().tolist()
            nwis.get_streamflow(sids, (start, end), freq=freq, to_xarray=True).to_netcdf(fpath)
            
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get streamflow data for AOI index {i}")
            continue
