"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from hysetter.hysetter import NID, Config

__all__ = ["get_nid"]


def get_nid(nid_cfg: NID, model_config: Config) -> None:
    """Get NID data for the area of interest.

    Parameters
    ----------
    cfg_nid : NID
        A NID object.
    nid_dir : Path
        Path to the directory where the NID data will be saved.
    aoi_parquet : Path
        The path to the AOI parquet file.
    """
    from pygeohydro import NID

    console = Console(force_jupyter=False)
    nid_paths = model_config.file_paths.nid
    nid_paths.mkdir()
    gdf = gpd.read_parquet(model_config.file_paths.aoi_parquet)
    if not nid_cfg.within_aoi:
        return

    nid = None
    for i, geom in track(
        enumerate(gdf.geometry),
        description="Getting dams from NID",
        total=len(gdf),
        console=console,
    ):
        if nid is None:
            nid = NID()
            nid.stage_nid_inventory(Path(nid_paths.parent, "full_nid_inventory.parquet"))
        nid_paths[i] = f"nid_geom_{i}.parquet"
        if nid_paths[i].exists():
            continue
        try:
            nid.get_bygeom(geom, gdf.crs).to_parquet(nid_paths[i])  # pyright: ignore[reportArgumentType]
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get NID data for AOI index {i}")
            continue
