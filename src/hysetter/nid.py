"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from .hysetter import NID

__all__ = ["get_nid"]


def get_nid(cfg_nid: NID, nid_dir: Path, aoi_parquet: Path) -> None:
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

    console = Console()
    gdf = gpd.read_parquet(aoi_parquet)
    nid_dir.mkdir(exist_ok=True, parents=True)
    nid = NID()
    nid.stage_nid_inventory(Path(nid_dir, "full_nid_inventory.parquet"))
    if not cfg_nid.within_aoi:
        return

    for i, geom in track(
        enumerate(gdf.geometry), description="Getting dams from NID", total=len(gdf)
    ):
        fpath = Path(nid_dir, f"nid_geom_{i}.parquet")
        if fpath.exists():
            continue
        try:
            nid.get_bygeom(geom, gdf.crs).to_parquet(fpath)
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get NID data for AOI index {i}")
            continue
