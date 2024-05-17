"""Main functions of hysetter."""

from __future__ import annotations

import itertools
import functools
from pathlib import Path
from typing import TYPE_CHECKING, cast

import geopandas as gpd
from rich.progress import track

from .utils import get_logger

if TYPE_CHECKING:
    from .hysetter import Config
    from shapely import Polygon, MultiPolygon
    from pyproj import CRS
    from xarray import DataArray

__all__ = ["get_soil"]


SG_ATTRS = {
    "bdod": {
        "description": "Bulk density of the fine earth fraction",
        "long_name": "Bulk Density",
        "mapped_units": "cg/cm³",
        "conversion_factor": 100,
        "conventional_units": "kg/dm³"
    },
    "cec": {
        "description": "Cation Exchange Capacity of the soil",
        "long_name": "Cation Exchange Capacity",
        "mapped_units": "mmol(c)/kg",
        "conversion_factor": 10,
        "conventional_units": "cmol(c)/kg"
    },
    "cfvo": {
        "description": "Volumetric fraction of coarse fragments (> 2 mm)",
        "long_name": "Coarse Fragments Vol",
        "mapped_units": "cm3/dm3 (vol‰)",
        "conversion_factor": 10,
        "conventional_units": "cm3/100cm3 (vol%)"
    },
    "clay": {
        "description": "Proportion of clay particles (< 0.002 mm) in the fine earth fraction",
        "long_name": "Clay Content",
        "mapped_units": "g/kg",
        "conversion_factor": 10,
        "conventional_units": "g/100g (%)"
    },
    "nitrogen": {
        "description": "Total nitrogen (N)",
        "long_name": "Nitrogen Content",
        "mapped_units": "cg/kg",
        "conversion_factor": 100,
        "conventional_units": "g/kg"
    },
    "phh2o": {
        "description": "Soil pH",
        "long_name": "Ph In H2O",
        "mapped_units": "pHx10",
        "conversion_factor": 10,
        "conventional_units": "pH"
    },
    "sand": {
        "description": "Proportion of sand particles (> 0.05 mm) in the fine earth fraction",
        "long_name": "Sand Content",
        "mapped_units": "g/kg",
        "conversion_factor": 10,
        "conventional_units": "g/100g (%)"
    },
    "silt": {
        "description": "Proportion of silt particles (≥ 0.002 mm and ≤ 0.05 mm) in the fine earth fraction",
        "long_name": "Silt Content",
        "mapped_units": "g/kg",
        "conversion_factor": 10,
        "conventional_units": "g/100g (%)"
    },
    "soc": {
        "description": "Soil organic carbon content in the fine earth fraction",
        "long_name": "Soil Organic Carbon",
        "mapped_units": "dg/kg",
        "conversion_factor": 10,
        "conventional_units": "g/kg"
    },
    "ocd": {
        "description": "Organic carbon density",
        "long_name": "Organic Carbon Density",
        "mapped_units": "hg/m³",
        "conversion_factor": 10,
        "conventional_units": "kg/m³"
    },
    "ocs": {
        "description": "Organic carbon stocks",
        "long_name": "Organic Carbon Stock",
        "mapped_units": "t/ha",
        "conversion_factor": 10,
        "conventional_units": "kg/m²"
    }
}

def soilgrids(
    layers: list[str],
    geometry: Polygon | MultiPolygon,
    geo_crs: CRS,
) -> DataArray:
    """Get soil data from SoilGrids for the area of interest.

    Parameters
    ----------
    layers : list of str
        SoilGrids layers to get. Available options are:
        ``bdod_*``, ``cec_*``, ``cfvo_*``, ``clay_*``, ``nitrogen_*``, ``ocd_*``,
        ``ocs_*``, ``phh2o_*``, ``sand_*``, ``silt_*``, and ``soc_*``. Where ``*`` is
        the depth in cm and can be one of ``5``, ``15``, ``30``, ``60``, ``100``, or ``200``.
        The values are mean values over the depth range.
    geometry : Polygon, MultiPolygon, or tuple of length 4
        Geometry to get DEM within. It can be a polygon or a boundong box
        of form (xmin, ymin, xmax, ymax).
    geo_crs : int, str, of pyproj.CRS
        CRS of the input geometry.
    resolution : int, optional
        Target DEM source resolution in meters, defaults to 10 m which is the highest
        resolution available over the US. Available options are 10, 30, and 60.

    Returns
    -------
    xarray.DataArray
        The request DEM at the specified resolution.
    """
    import numpy as np
    import rioxarray as rxr
    import xarray as xr

    valid_depths = {'5': "0-5cm", '15': "5-15cm", '30': "15-30cm", '60': "30-60cm", '100': "60-100cm", '200': "100-200cm"}
    valid_layers = [f"{layer}_{depth}" for layer, depth in itertools.product(SG_ATTRS.keys(), valid_depths.keys())]
    invalid_layers = [layer for layer in layers if layer not in valid_layers]
    if invalid_layers:
        raise ValueError(f"Invalid layers: {invalid_layers}")
    lyr_names, lyr_depths = zip(*[layer.split("_") for layer in layers])
    
    def _read_layer(lyr: str, depth: str) -> DataArray:
        base_url = "https://files.isric.org/soilgrids/latest/data"
        ds = rxr.open_rasterio(f"{base_url}/{lyr}/{lyr}_{depth}_mean.vrt")
        ds = cast("DataArray", ds)
        ds = ds.squeeze(drop=True)
        ds = ds.rio.clip_box(*geometry.bounds, crs=geo_crs)
        ds = ds.rio.clip([geometry], crs=geo_crs)
        ds = ds.where(ds != ds.rio.nodata)
        ds = ds.rio.write_nodata(np.nan)
        
        # Convert mapped units to conventional units
        attributes = SG_ATTRS[lyr]
        ds = ds / attributes["conversion_factor"]
        
        ds.name = f"Mean {lyr}_{depth.replace('-', '_')}_mean"
        ds.attrs["long_name"] = f"{attributes['long_name']} ({depth})"
        ds.attrs["description"] = attributes["description"]
        ds.attrs["units"] = attributes["conventional_units"]
        
        return ds

    return xr.merge([_read_layer(lyr, valid_depths[d]) for lyr, d in zip(lyr_names, lyr_depths)])


def get_soil(config: Config) -> None:
    """Get soil data for the area of interest.

    Parameters
    ----------
    config : Config
        A Config object.
    """
    import pygeohydro as gh

    logger = get_logger()
    if config.gnatsgo is None:
        return

    gdf = gpd.read_parquet(config.file_paths.aoi_parquet)
    for i, geom in track(
        enumerate(gdf.geometry), description="Getting soil data from gNATSGO", total=len(gdf)
    ):
        try:
            soil = gh.soil_gnatsgo(config.gnatsgo.variables, geom, gdf.crs)
        except Exception as e:
            logger.warning(
                f"Failed to get soil for AOI index {i}:\n{e!s}",
                UserWarning,
                stacklevel=2,
            )
            continue
        soil.to_netcdf(Path(config.file_paths.soil_dir, f"soil_geom_{i}.nc"))
