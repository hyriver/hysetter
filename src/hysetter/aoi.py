"""Main functions of hysetter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

import geopandas as gpd
import pandas as pd
from rich.console import Console
from rich.progress import track

if TYPE_CHECKING:
    from .hysetter import AOI

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


def _get_flowlines(
    gdf: gpd.GeoDataFrame,
    flowlines_dir: Path,
    sc_attrs: list[str] | None,
    nldi_attrs: list[str] | None,
) -> None:
    """Get flowlines."""
    from pynhd import NLDI, WaterData, streamcat

    console = Console()
    wd = WaterData("nhdflowline_network")

    if sc_attrs or nldi_attrs:
        description = "Getting flowlines and their attributes"
    else:
        description = "Getting flowlines from WaterData"

    nldi = NLDI() if nldi_attrs else None
    for i, geom in track(
        enumerate(gdf.geometry),
        description=description,
        total=len(gdf),
    ):
        fpath = Path(flowlines_dir, f"aoi_geom_{i}.parquet")
        if not fpath.exists():
            try:
                wd.bygeom(geom, gdf.crs).to_parquet(fpath)
            except Exception:
                console.print_exception(show_locals=True, max_frames=4)
                console.print(f"Failed to get flowlines for AOI {i}.")

        comids = gpd.read_parquet(fpath).comid.tolist()
        fpath = Path(flowlines_dir, f"streamcat_geom_{i}.parquet")
        if sc_attrs and not fpath.exists():
            try:
                streamcat(sc_attrs, "catchment", comids).to_parquet(fpath)
            except Exception:
                console.print_exception(show_locals=True, max_frames=4)
                console.print(f"Failed to get StreamCat for AOI {i}.")

        fpath = Path(flowlines_dir, f"nldi_geom_{i}.parquet")
        if nldi_attrs and nldi and not fpath.exists():
            try:
                nldi.getcharacteristic_byid(
                    comids, "local", "comid", nldi_attrs, values_only=True
                ).to_parquet(fpath)
            except Exception:
                console.print_exception(show_locals=True, max_frames=4)
                console.print(f"Failed to get NLDI attrs for AOI {i}.")


def get_aoi(cfg_aoi: AOI, flw_dir: Path, aoi_parquet: Path) -> None:
    """Get the area of interest.

    Parameters
    ----------
    cfg_aoi : AOI
        An AOI object.
    flw_dir : pathlib.Path
        Path to the directory where the flowlines will be saved.
    aoi_parquet : pathlib.Path
        The path to the AOI parquet file.
    """
    from pynhd import WaterData

    console = Console()

    if aoi_parquet.exists():
        console.print(f"Reading AOI from [bold green]{aoi_parquet.resolve()}")
        gdf = gpd.read_parquet(aoi_parquet)
    else:
        if cfg_aoi.huc_ids:
            console.print("Getting AOI: HUCs from WaterData.")
            gdf = _get_hucs(cfg_aoi.huc_ids)
        elif cfg_aoi.nhdv2_ids:
            console.print("Getting AOI: NHDPlusV2 catchments from WaterData.")
            gdf = WaterData("catchmentsp").byid("featureid", cfg_aoi.nhdv2_ids)
        elif cfg_aoi.gagesii_basins:
            console.print("Getting AOI: GAGES-II basins from WaterData.")
            gdf = WaterData("gagesii_basins").byid("gage_id", cfg_aoi.gagesii_basins)
        elif cfg_aoi.geometry_file:
            console.print(f"Getting AOI: From {cfg_aoi.geometry_file}")
            gdf = _read_geometry_file(cfg_aoi.geometry_file)
        else:
            raise ValueError(
                "Only one of `huc_ids`, `nhdv2_ids`, `gagesii_basins`, or `geometry_file` must be provided."
            )
        gdf.to_parquet(aoi_parquet)

    if cfg_aoi.nhdv2_flowlines or cfg_aoi.streamcat_attrs or cfg_aoi.nldi_attrs:
        flw_dir.mkdir(exist_ok=True, parents=True)
        _get_flowlines(gdf, flw_dir, cfg_aoi.streamcat_attrs, cfg_aoi.nldi_attrs)
