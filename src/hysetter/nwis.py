"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from .hysetter import Streamflow

__all__ = ["get_streamflow"]


def get_streamflow(cfg_streamflow: Streamflow, streamflow_dir: Path, aoi_parquet: Path) -> None:
    """Get streamflow data for the area of interest.

    Parameters
    ----------
    cfg_streamflow : Streamflow
        A Streamflow object.
    streamflow_dir : Path
        Path to the directory where the streamflow data will be saved.
    aoi_parquet : Path
        The path to the AOI parquet file.
    """
    from pygeohydro import NWIS

    console = Console()
    gdf = gpd.read_parquet(aoi_parquet)
    streamflow_dir.mkdir(exist_ok=True, parents=True)

    start = cfg_streamflow.start_date.strftime("%Y-%m-%d")
    end = cfg_streamflow.end_date.strftime("%Y-%m-%d")
    freq = "dv" if cfg_streamflow.frequency == "daily" else "iv"
    nwis = NWIS()
    for i, geom in track(
        enumerate(gdf.geometry.to_crs(4326)),
        description="Getting streamflow from NWIS",
        total=len(gdf),
    ):
        fpath = Path(streamflow_dir, f"streamflow_geom_{i}.nc")
        if fpath.exists():
            continue
        try:
            query = {"bBox": ",".join(f"{b:.06f}" for b in geom.bounds), "outputDataTypeCd": freq}
            siteinfo = nwis.get_info(query)
            sids = siteinfo.loc[siteinfo.within(geom), "site_no"].unique().tolist()
            qobs = nwis.get_streamflow(sids, (start, end), freq=freq, to_xarray=True)
            if len(qobs) == 0:
                console.print(f"No streamflow data found for AOI index {i}")
                continue
            qobs.to_netcdf(fpath)
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get streamflow data for AOI index {i}")
            continue
