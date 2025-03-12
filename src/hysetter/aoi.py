"""Main functions of hysetter."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

import geopandas as gpd
import pandas as pd
from rich.console import Console
from rich.progress import track

from hysetter.exceptions import InputTypeError

if TYPE_CHECKING:
    from hysetter.hysetter import AOI, Config, FileList

__all__ = ["get_aoi"]


def _get_hucs(huc_ids: list[str]) -> gpd.GeoDataFrame:
    """Get HUCs."""
    from pynhd import WaterData

    huc_df = pd.Series(huc_ids).astype(str)
    if not huc_df.str.len().isin([2, 4, 6, 8, 10, 12]).all():
        raise InputTypeError("huc_ids", "strings of lengths between 2 and 12.")
    huc_dict = huc_df.groupby(huc_df.str.len()).apply(list).to_dict()
    aoi_list = []
    for lvl, ids in huc_dict.items():
        wd = WaterData(f"wbd{str(lvl).zfill(2)}")  # pyright: ignore[reportArgumentType]
        aoi_list.append(wd.byid(f"huc{lvl}", ids))
    return gpd.GeoDataFrame(pd.concat(aoi_list, ignore_index=True))


def _get_mainstem(
    mainstem_id: int,
    navigation: Literal["upstreamMain", "upstreamTributaries"],
    get_flw: bool,
    flw_dir: FileList,
    sc_attrs: list[str] | None,
    sc_dir: FileList,
    nldi_attrs: list[str] | None,
    nldi_dir: FileList,
) -> gpd.GeoDataFrame:
    """Get NHDPlus V2 catchments for ComIDs of a mainstem."""
    import pygeoutils as pgu
    from pynhd import NLDI, GeoConnex, WaterData, streamcat

    outlet_id = (
        GeoConnex("mainstems")
        .byid("id", str(mainstem_id))
        .outlet_nhdpv2_comid.str.split("/")
        .str[-1]
        .iloc[0]
    )
    nldi = NLDI()
    comids = nldi.navigate_byid(
        "comid", outlet_id, navigation, source="flowlines", distance=9999
    ).nhdplus_comid.tolist()
    if get_flw:
        wd = WaterData("nhdflowline_network")
        flw_dir.mkdir()
        flw_dir[0] = "flowlines.parquet"
        if not flw_dir[0].exists():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                flw = wd.byid("comid", comids)
                flw.to_parquet(flw_dir[0])
    if sc_attrs:
        sc_dir.mkdir()
        sc_dir[0] = "streamcat_attrs.parquet"
        if not sc_dir[0].exists():
            streamcat(sc_attrs, "cat", comids).to_parquet(sc_dir[0])

    if nldi_attrs:
        nldi_dir.mkdir()
        nldi_dir[0] = "nldi_attrs.parquet"
        if not nldi_dir[0].exists():
            nldi.get_characteristics(nldi_attrs, comids).to_parquet(nldi_dir[0])

    wd = WaterData("catchmentsp")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        cat = wd.byid("featureid", comids)
        return pgu.multi2poly(cat)


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
    flw_dir: FileList,
    sc_attrs: list[str] | None,
    sc_dir: FileList,
    nldi_attrs: list[str] | None,
    nldi_dir: FileList,
) -> None:
    """Get flowlines."""
    from pynhd import NLDI, WaterData, streamcat

    console = Console(force_jupyter=False)
    # To avoid instantiating WaterData if data already exists
    # we set it to None here and instantiate it later
    # in the loop if needed
    wd = None

    if sc_attrs or nldi_attrs:
        description = "Getting flowlines and their attributes"
    else:
        description = "Getting flowlines from WaterData"

    for i, geom in track(
        enumerate(gdf.geometry),
        description=description,
        total=len(gdf),
        console=console,
    ):
        # Only instantiate WaterData if not already done
        if wd is None:
            wd = WaterData("nhdflowline_network")
        flw_dir[i] = f"aoi_geom_{i}.parquet"
        if not flw_dir[i].exists():
            flw_dir.mkdir()
            try:
                wd.bygeom(geom, gdf.crs).to_parquet(flw_dir[i])  # pyright: ignore[reportArgumentType]
            except Exception:
                console.print_exception(show_locals=True, max_frames=4)
                console.print(f"Failed to get flowlines for AOI {i}.")

        if sc_attrs:
            sc_dir[i] = f"streamcat_geom_{i}.parquet"
            if not sc_dir[i].exists():
                sc_dir.mkdir()
                comids = gpd.read_parquet(flw_dir[i]).comid.tolist()
                try:
                    streamcat(sc_attrs, "cat", comids).to_parquet(sc_dir[i])
                except Exception:
                    console.print_exception(show_locals=True, max_frames=4)
                    console.print(f"Failed to get StreamCat for AOI {i}.")

        if nldi_attrs:
            nldi_dir[i] = f"nldi_geom_{i}.parquet"
            if not nldi_dir[i].exists():
                nldi_dir.mkdir()
                try:
                    nldi = NLDI()
                    comids = gpd.read_parquet(flw_dir[i]).comid.tolist()
                    nldi.get_characteristics(nldi_attrs, comids).to_parquet(nldi_dir[i])
                except Exception:
                    console.print_exception(show_locals=True, max_frames=4)
                    console.print(f"Failed to get NLDI attrs for AOI {i}.")


def get_aoi(aoi_cfg: AOI, model_cfg: Config) -> None:
    """Get the area of interest."""
    import pygeoutils as geoutils
    from pynhd import WaterData

    console = Console(force_jupyter=False)

    files = model_cfg.file_paths
    if files.aoi_parquet.exists():
        console.print(f"Reading AOI from [bold green]{files.aoi_parquet.resolve()}")
        gdf = gpd.read_parquet(files.aoi_parquet)
    else:
        gdf = None
        if aoi_cfg.huc_ids:
            console.print("Getting AOI: HUCs from WaterData.")
            gdf = _get_hucs(aoi_cfg.huc_ids)
        elif aoi_cfg.nhdv2_ids:
            console.print("Getting AOI: NHDPlusV2 catchments from WaterData.")
            gdf = WaterData("catchmentsp").byid("featureid", aoi_cfg.nhdv2_ids)
            gdf = geoutils.multi2poly(gdf)
        elif aoi_cfg.gagesii_basins:
            console.print("Getting AOI: GAGES-II basins from WaterData.")
            gdf = WaterData("gagesii_basins").byid("gage_id", aoi_cfg.gagesii_basins)
            gdf = geoutils.multi2poly(gdf)
        elif aoi_cfg.mainstem_main:
            console.print("Getting AOI: Mainstem catchments (main only) from GeoConnex.")
            try:
                gdf = _get_mainstem(
                    aoi_cfg.mainstem_main,
                    "upstreamMain",
                    aoi_cfg.nhdv2_flowlines,
                    files.flowlines,
                    aoi_cfg.nldi_attrs,
                    files.nldi_attrs,
                    aoi_cfg.streamcat_attrs,
                    files.streamcat_attrs,
                )
            except Exception:
                console.print_exception(show_locals=True, max_frames=4)
                console.print(f"Failed to get data for {aoi_cfg.mainstem_main}.")
            return
        elif aoi_cfg.mainstem_tributaries:
            console.print("Getting AOI: Mainstem catchments (tributaries) from GeoConnex.")
            try:
                gdf = _get_mainstem(
                    aoi_cfg.mainstem_tributaries,
                    "upstreamTributaries",
                    aoi_cfg.nhdv2_flowlines,
                    files.flowlines,
                    aoi_cfg.nldi_attrs,
                    files.nldi_attrs,
                    aoi_cfg.streamcat_attrs,
                    files.streamcat_attrs,
                )
            except Exception:
                console.print_exception(show_locals=True, max_frames=4)
                console.print(f"Failed to get data for {aoi_cfg.mainstem_main}.")
            return
        elif aoi_cfg.geometry_file:
            console.print(f"Getting AOI: From {aoi_cfg.geometry_file}")
            gdf = _read_geometry_file(aoi_cfg.geometry_file)

        if gdf is None:
            raise ValueError
        gdf.to_parquet(files.aoi_parquet)

    if aoi_cfg.nhdv2_flowlines or aoi_cfg.streamcat_attrs or aoi_cfg.nldi_attrs:
        files.flowlines.mkdir(exist_ok=True, parents=True)
        _get_flowlines(
            gdf,
            files.flowlines,
            aoi_cfg.streamcat_attrs,
            files.streamcat_attrs,
            aoi_cfg.nldi_attrs,
            files.nldi_attrs,
        )
