"""Main functions of hysetter."""

from __future__ import annotations

import functools
from dataclasses import dataclass
from datetime import datetime  # noqa: TCH003
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing_extensions import Self

from . import aoi, forcing, nid, nlcd, nwis, soil, topo

if TYPE_CHECKING:
    from yaml.nodes import Node

__all__ = [
    "read_config",
    "write_config",
    "AOI",
    "Config",
    "Project",
    "Forcing",
    "Topo",
    "Soil",
    "NLCD",
    "NID",
    "Streamflow",
    "FilePaths",
]

yaml_load = functools.partial(yaml.load, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
SafeDumper = getattr(yaml, "CSafeDumper", yaml.SafeDumper)


class PathDumper(SafeDumper):  # pyright: ignore[reportGeneralTypeIssues,reportUntypedBaseClass]
    """A dumper that can represent pathlib.Path objects as strings."""

    def represent_data(self, data: Any) -> Node:
        """Represent Path objects as strings."""
        if isinstance(data, Path):
            return self.represent_scalar("tag:yaml.org,2002:str", str(data))
        return super().represent_data(data)


def yaml_dump(o: Any, **kwargs: Any) -> str:
    """Dump YAML.

    Notes
    -----
    When python/mypy#1484 is solved, this can be ``functools.partial``
    """
    return yaml.dump(
        o,
        Dumper=PathDumper,
        stream=None,
        default_flow_style=False,
        indent=2,
        sort_keys=False,
        **kwargs,
    )


class Project(BaseModel):
    """Project information.

    Parameters
    ----------
    name : str
        Name of the project.
    data_dir : str
        Path to the directory where the data will be stored.
    """

    name: str
    data_dir: str


class AOI(BaseModel):
    """Area of interest.

    Notes
    -----
    Only one of ``huc_ids``, ``nhdv2_ids``, ``gagesii_basins``, or
    ``geometry_file`` must be provided.

    Parameters
    ----------
    huc_ids : list of str, optional
        List of HUC IDs, by default None. The IDs must be strings and HUC
        level will be determined by the length of the string (even numbers
        between 2 and 12).
    nhdv2_ids : list of int, optional
        List of NHD Feature IDs, by default None. The IDs must be integers
        and are assumed to be NHDPlus V2 catchment IDs.
    gagesii_basins : list of str, optional
        List of GAGES-II basin IDs, by default None. The IDs must be strings.
    geometry_file : str, optional
        Path to a geometry file, by default None. Supported file extensions are
        ``.feather``, ``.parquet``, and any format supported by
        ``geopandas.read_file`` (e.g., ``.shp``, ``.geojson``, and ``.gpkg``).
    nhdv2_flowlines : bool, optional
        Whether to retrieve the NHDPlus V2 flowlines within the AOI, by default False.
    streamcat_attrs : list of str, optional
        List of StreamCat attributes to retrieve, by default None. This will
        set the ``nhdv2_flowlines`` to True. Use ``pynhd.StreamCat().metrics_df``
        to get a dataframe of all available attributes with their descriptions.
    nldi_attrs : list of str, optional
        List of slelect attributes to retrieve, by default None.
        Use ``pynhd.nhdplus_attrs_s3()`` to get a dataframe of all available
        attributes with their descriptions.
    """

    huc_ids: list[str] | None = None
    nhdv2_ids: list[int] | None = None
    gagesii_basins: list[str] | None = None
    geometry_file: str | None = None
    nhdv2_flowlines: bool = False
    streamcat_attrs: list[str] | None = None
    nldi_attrs: list[str] | None = None

    @model_validator(mode="after")
    def check_exclusive_options(self) -> Self:
        """Check if only one of the options is provided."""
        provided_options = [
            option
            for option in (self.huc_ids, self.nhdv2_ids, self.gagesii_basins, self.geometry_file)
            if option
        ]
        if len(provided_options) != 1:
            raise ValueError(
                "Only one of `huc_ids`, `nhdv2_ids`, `gagesii_basins`, or `geometry_file` must be provided."
            )
        return self


class Forcing(BaseModel):
    """Forcing data.

    Parameters
    ----------
    source : str
        Source of the forcing data. Supported sources are "daymet", "gridmet", and "nldas2".
    start_date : datetime
        Start date of the forcing data.
    end_date : datetime
        End date of the forcing data.
    variables : list of str, optional
        List of variables to retrieve, by default None. If not provided, all available
        variables will be retrieved.
    """

    source: Literal["daymet", "gridmet", "nldas2"]
    start_date: datetime
    end_date: datetime
    variables: list[str] | None = None


class Topo(BaseModel):
    """Topographic data.

    Parameters
    ----------
    resolution_m : int
        Resolution of the data in meters.
    derived_variables : list of str, optional
        List of derived variables to calculate, by default None. Supported derived
        variables are "slope", "aspect", and "curvature".
    """

    resolution_m: int
    derived_variables: list[Literal["slope", "aspect", "curvature"]] | None = None


class Soil(BaseModel):
    """Soil data.

    Parameters
    ----------
    source : str
        Source of the soil data. Supported sources are "soilgrids" and "gnatsgo".
    variables : list of str
        List of variables to retrieve. Each source has its own set of variables.
    """

    source: Literal["soilgrids", "gnatsgo"]
    variables: list[str]


class NLCD(BaseModel):
    """National Land Cover Database (NLCD) data.

    Parameters
    ----------
    cover : list of int, optional
        List of years for land cover data, by default None, which defaults to
        the most recent data. Available years are 2021, 2019, 2016, 2013, 2011,
        2008, 2006, 2004, and 2001.
    impervious : list of int, optional
        List of years for impervious data, by default None, which defaults to
        the most recent data. Available years are 2021, 2019, 2016, 2013, 2011,
        2008, 2006, 2004, and 2001.
    canopy : list of int, optional
        List of years for canopy data, by default None, which defaults to
        the most recent data. Available years are between 2011 and 2022.
    descriptor : list of int, optional
        List of years for descriptor data, by default None, which defaults to
        the most recent data. Available years are 2021, 2019, 2016, 2013, 2011,
        2008, 2006, 2004, and 2001.
    """

    cover: list[int] | None = None
    impervious: list[int] | None = None
    canopy: list[int] | None = None
    descriptor: list[int] | None = None


class NID(BaseModel):
    """National Inventory of Dams (NID) data.

    Parameters
    ----------
    within_aoi : bool
        Whether to retrieve the NID data within the AOI.
    """

    within_aoi: bool


class Streamflow(BaseModel):
    """Streamflow data from NWIS.

    Parameters
    ----------
    start_date : datetime
        Start date of the streamflow data.
    end_date : datetime
        End date of the streamflow data.
    frequency : str
        Frequency of the streamflow data. Supported frequencies are
        "daily" and "instantaneous".
    """

    start_date: datetime
    end_date: datetime
    frequency: Literal["daily", "instantaneous"]

    @model_validator(mode="after")
    def check_exclusive_options(self) -> Self:
        """Check if the frequency is either 'daily' or 'instantaneous'."""
        if self.frequency not in ("daily", "instantaneous"):
            raise ValueError("Frequency must be either 'daily' or 'instantaneous'.")
        return self


@dataclass
class FilePaths:
    """File paths to store the data."""

    project: Path
    aoi_parquet: Path
    flowlines: Path
    forcing: Path
    topo: Path
    soil: Path
    nlcd: Path
    nid: Path
    streamflow: Path


class Config(BaseModel):
    """Configuration for HySetter.

    Notes
    -----
    Only ``project`` and ``aoi`` are required. The rest are optional.

    Parameters
    ----------
    project : Project
        Project information.
    aoi : AOI
        Area of interest.
    forcing : Forcing, optional
        Forcing data, by default None.
    topo : Topo, optional
        Topographic data, by default None.
    soil : Soil, optional
        Soil data, by default None.
    nlcd : NLCD, optional
        National Land Cover Database (NLCD) data, by default None.
    nid : NID, optional
        National Inventory of Dams (NID) data, by default None.
    streamflow : Streamflow, optional
        Streamflow data from NWIS, by default None.
    """

    project: Project
    aoi: AOI
    forcing: Forcing | None = None
    topo: Topo | None = None
    soil: Soil | None = None
    nlcd: NLCD | None = None
    nid: NID | None = None
    streamflow: Streamflow | None = None
    file_paths: FilePaths = Field(default=None, init=False)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        project_dir = Path(self.project.data_dir, self.project.name.replace(" ", "_"))
        self.file_paths = FilePaths(
            project=project_dir,
            aoi_parquet=Path(project_dir, "aoi.parquet"),
            flowlines=Path(project_dir, "nhdv2_flowlines"),
            forcing=Path(project_dir, "forcing"),
            topo=Path(project_dir, "topo"),
            soil=Path(project_dir, "soil"),
            nlcd=Path(project_dir, "nlcd"),
            nid=Path(project_dir, "nid"),
            streamflow=Path(project_dir, "streamflow"),
        )

    def get_data(self) -> None:
        """Iterate over non-None attributes."""
        get_func = {
            "aoi": aoi.get_aoi,
            "forcing": forcing.get_forcing,
            "topo": topo.get_topo,
            "soil": soil.get_soil,
            "nlcd": nlcd.get_nlcd,
            "nid": nid.get_nid,
            "streamflow": nwis.get_streamflow,
        }
        self.file_paths.project.mkdir(exist_ok=True, parents=True)
        for name, func in get_func.items():
            cfg = getattr(self, name)
            if cfg is not None:
                fdir = (
                    self.file_paths.flowlines if name == "aoi" else getattr(self.file_paths, name)
                )
                func(cfg, fdir, self.file_paths.aoi_parquet)


def read_config(file_path: str | Path) -> Config:
    """Read a configuration file and return a Config object.

    Parameters
    ----------
    file_path : str or pathlib.Path
        Path to the configuration file.

    Returns
    -------
    Config
        A Config object.
    """
    config_data = yaml_load(Path(file_path).read_text())
    try:
        return Config(**config_data)
    except ValidationError as e:
        raise ValueError(e) from e


def write_config(config: Config, file_path: str | Path) -> None:
    """Write a Config object to a file.

    Parameters
    ----------
    config : Config
        A Config object.
    file_path : str or pathlib.Path
        Path to the configuration file.
    """
    Path(file_path).write_text(yaml_dump(config.model_dump()))
