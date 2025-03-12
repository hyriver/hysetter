"""Main functions of hysetter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from hysetter.hysetter import Config, Streamflow

__all__ = ["get_streamflow"]


def get_streamflow(streamflow_cfg: Streamflow, model_config: Config) -> None:
    """Get streamflow data for the area of interest."""
    from pygeohydro import NWIS

    console = Console(force_jupyter=False)
    gdf = gpd.read_parquet(model_config.file_paths.aoi_parquet)
    sf_paths = model_config.file_paths.streamflow
    sf_paths.mkdir()

    start = streamflow_cfg.start_date.strftime("%Y-%m-%d")
    end = streamflow_cfg.end_date.strftime("%Y-%m-%d")
    freq = "dv" if streamflow_cfg.frequency == "daily" else "iv"
    nwis = NWIS()
    if streamflow_cfg.use_col:
        if streamflow_cfg.use_col not in gdf.columns:
            console.print("Failed to get streamflow data.")
            console.print(f"Column {streamflow_cfg.use_col} not found in the AOI file")
            return
        sf_paths[0] = "streamflow.nc"
        console.print(f"Getting streamflow from NWIS for {len(gdf)} stations")
        if not sf_paths[0].exists():
            try:
                sids = gdf[streamflow_cfg.use_col].unique().tolist()  # pyright: ignore[reportCallIssue]
                qobs = nwis.get_streamflow(sids, (start, end), freq=freq, to_xarray=True)
                if len(qobs) == 0:
                    console.print(
                        f"Failed to get streamflow data for AOI for {streamflow_cfg.use_col} column"
                    )
                qobs.to_netcdf(sf_paths[0])
            except Exception:
                console.print_exception(show_locals=True, max_frames=4)
                console.print(
                    f"Failed to get streamflow data for AOI for {streamflow_cfg.use_col} column"
                )
    else:
        for i, geom in track(
            enumerate(gdf.geometry.to_crs(4326)),
            description="Getting streamflow from NWIS",
            total=len(gdf),
            console=console,
        ):
            sf_paths[i] = f"streamflow_geom_{i}.nc"
            if sf_paths[i].exists():
                continue
            try:
                query = {
                    "bBox": ",".join(f"{b:.06f}" for b in geom.bounds),
                    "outputDataTypeCd": freq,
                }
                siteinfo = nwis.get_info(query)
                sids = siteinfo.loc[siteinfo.within(geom), "site_no"].unique().tolist()
                qobs = nwis.get_streamflow(sids, (start, end), freq=freq, to_xarray=True)
                if len(qobs) == 0:
                    console.print(f"No streamflow data found for AOI index {i}")
                    continue
                qobs.to_netcdf(sf_paths[i])
            except Exception:
                console.print_exception(show_locals=True, max_frames=4)
                console.print(f"Failed to get streamflow data for AOI index {i}")
                continue
