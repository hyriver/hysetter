"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

import geopandas as gpd
import pandas as pd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from .hysetter import Config

__all__ = ["get_aoi"]


def _get_hucs(huc_ids: list[str]) -> gpd.GeoDataFrame:
    """Get HUCs."""
    from pynhd import WaterData

    huc_df = pd.Series(huc_ids).astype(str)
    if not huc_df.str.len().isin([2, 4, 6, 8, 10, 12]).all():
        raise ValueError("HUC IDs must be strings and have even lengths between 2 and 12.")
    huc_dict = huc_df.groupby(huc_df.str.len()).apply(list).to_dict()
    aoi_list = []
    for lvl, ids in huc_dict.items():
        wd = WaterData(f"wbd{str(lvl).zfill(2)}")  # pyright: ignore[reportArgumentType]
        aoi_list.append(wd.byid(f"huc{lvl}", ids))
    return gpd.GeoDataFrame(pd.concat(aoi_list, ignore_index=True))


def _read_geometry_file(geometry_file: str) -> gpd.GeoDataFrame:
    """Read geometry file."""
    file_ext = Path(geometry_file).suffix
    if file_ext == ".parquet":
        gdf = pd.read_parquet(geometry_file)
    elif file_ext == ".feather":
        gdf = pd.read_feather(geometry_file)
    else:
        gdf = gpd.read_file(geometry_file, engine="pyogrio")
    if not gdf.geom_type.isin(["Polygon", "MultiPolygon"]).all():
        raise ValueError("Geometry file must contain polygons or multipolygons.")
    gdf = gdf.reset_index(drop=True)
    gdf = cast("gpd.GeoDataFrame", gdf)
    return gdf


def _get_flowlines(gdf: gpd.GeoDataFrame, flowlines_dir: Path) -> None:
    """Get flowlines."""
    from pynhd import WaterData

    console = Console()
    wd = WaterData("nhdflowline_network")
    for i, geom in track(
        enumerate(gdf.geometry),
        description="Getting NHDPlusV2 flowlines from WaterData",
        total=len(gdf),
    ):
        fpath = Path(flowlines_dir, f"aoi_geom_{i}.parquet")
        if fpath.exists():
            continue
        try:
            flw = wd.bygeom(geom, gdf.crs)
        except Exception:
            console.print_exception(show_locals=True, max_frames=4)
            console.print(f"Failed to get flowlines for AOI {i}.")
            continue
        flw.to_parquet(fpath)


def get_aoi(config: Config) -> None:
    """Get the area of interest.

    Parameters
    ----------
    config : Config
        A Config object.
    """
    from pynhd import WaterData

    console = Console()
    aoi = config.aoi

    config.file_paths.project_dir.mkdir(exist_ok=True, parents=True)
    if config.file_paths.aoi_parquet.exists():
        console.print(f"Reading AOI from [bold green]{config.file_paths.aoi_parquet.resolve()}")
        gdf = gpd.read_parquet(config.file_paths.aoi_parquet)
    else:
        if aoi.huc_ids:
            console.print("Getting AOI: HUCs from WaterData.")
            gdf = _get_hucs(aoi.huc_ids)
        elif aoi.nhdv2_ids:
            console.print("Getting AOI: NHDPlusV2 catchments from WaterData.")
            gdf = WaterData("catchmentsp").byid("featureid", aoi.nhdv2_ids)
        elif aoi.gagesii_basins:
            console.print("Getting AOI: GAGES-II basins from WaterData.")
            gdf = WaterData("gagesii_basins").byid("gage_id", aoi.gagesii_basins)
        elif aoi.geometry_file:
            console.print(f"Getting AOI: From {aoi.geometry_file}")
            gdf = _read_geometry_file(aoi.geometry_file)
        else:
            raise ValueError(
                "Only one of `huc_ids`, `nhdv2_ids`, `gagesii_basins`, or `geometry_file` must be provided."
            )
        gdf.to_parquet(config.file_paths.aoi_parquet)
    if aoi.nhdv2_flowlines:
        config.file_paths.flowlines_dir.mkdir(exist_ok=True, parents=True)
        _get_flowlines(gdf, config.file_paths.flowlines_dir)
