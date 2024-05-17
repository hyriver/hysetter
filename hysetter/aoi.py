"""Main functions of hysetter."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import cast

import geopandas as gpd
import pandas as pd
from pynhd import WaterData

from .hysetter import Config

__all__ = ["get_aoi"]

def _get_hucs(huc_ids: list[str]) -> gpd.GeoDataFrame:
    """Get HUCs."""
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
    wd = WaterData("nhdflowline_network")
    for i, geom in enumerate(gdf.geometry):
        try:
            flw = wd.bygeom(geom, gdf.crs)
        except Exception:
            warnings.warn(f"Failed to get flowlines for AOI {i}.", UserWarning, stacklevel=2)
            continue
        flw.to_parquet(Path(flowlines_dir, f"aoi_geom_{i}.parquet"))


def get_aoi(config: Config) -> None:
    """Get the area of interest.

    Parameters
    ----------
    config : Config
        A Config object.
    """
    aoi = config.aoi
    gdf = None
    if aoi.huc_ids:
        gdf = _get_hucs(aoi.huc_ids)
    elif aoi.nhdv2_ids:
        gdf = WaterData("catchmentsp").byid("featureid", aoi.nhdv2_ids)
    elif aoi.gagesii_basins:
        gdf = WaterData("gagesii_basins").byid("gage_id", aoi.gagesii_basins)
    elif aoi.geometry_file:
        gdf = _read_geometry_file(aoi.geometry_file)
    if gdf is None:
        raise ValueError("Area of interest not found.")
    gdf.to_parquet(config.file_paths.aoi_parquet)
    if aoi.nhdv2_flowlines:
        _get_flowlines(gdf, config.file_paths.flowlines_dir)