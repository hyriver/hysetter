"""Main functions of hysetter."""

from __future__ import annotations

import functools
import shutil
from dataclasses import dataclass
from datetime import datetime  # noqa: TC003
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Literal, overload

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_core import core_schema
from typing_extensions import Self, SupportsIndex

from hysetter.aoi import get_aoi
from hysetter.forcing import get_forcing
from hysetter.nid import get_nid
from hysetter.nlcd import get_nlcd
from hysetter.nwis import get_streamflow
from hysetter.rasters import get_rasters
from hysetter.soil import get_soil
from hysetter.topo import get_topo

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pydantic_core.core_schema import ValidationInfo
    from yaml.nodes import Node

__all__ = [
    "Config",
    "read_config",
    "write_config",
]

yaml_load = functools.partial(yaml.load, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
SafeDumper = getattr(yaml, "CSafeDumper", yaml.SafeDumper)


class _PathDumper(SafeDumper):  # pyright: ignore[reportGeneralTypeIssues,reportUntypedBaseClass]
    """A dumper that can represent pathlib.Path objects as strings."""

    def represent_data(self, data: Any) -> Node:
        """Represent Path objects as strings."""
        if isinstance(data, Path):
            return self.represent_scalar("tag:yaml.org,2002:str", str(data))
        return super().represent_data(data)


def _yaml_dump(o: Any, **kwargs: Any) -> str:
    """Dump YAML.

    Notes
    -----
    When python/mypy#1484 is solved, this can be ``functools.partial``
    """
    return yaml.dump(
        o,
        Dumper=_PathDumper,
        stream=None,
        default_flow_style=False,
        indent=2,
        sort_keys=False,
        **kwargs,
    )


class Project(BaseModel):
    """Project information.

    Attributes
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

    Attributes
    ----------
    huc_ids : list, optional
        List of HUC IDs, by default ``None``. The IDs must be strings and HUC
        level will be determined by the length of the string (even numbers
        between 2 and 12).
    nhdv2_ids : list, optional
        List of NHD Feature IDs, by default ``None``. The IDs must be integers
        and are assumed to be NHDPlus V2 catchment IDs.
    gagesii_basins : list, optional
        List of GAGES-II basin IDs, by default ``None``. The IDs must be strings.
    mainstem_main : int, optional
        NHDPlus V2 mainstem ID to get only its main upstream flowlines,
        by default ``None``. The ID must be an integer.
    mainstem_tributaries : bool, optional
        NHDPus V2 mainstem ID to get all its upstream tributaries, by default ``None``.
        The ID must be an integer.
    geometry_file : str, optional
        Path to a geometry file, by default ``None``. Supported file extensions are
        ``.feather``, ``.parquet``, and any format supported by
        ``geopandas.read_file`` (e.g., ``.shp``, ``.geojson``, and ``.gpkg``).
    nhdv2_flowlines : bool, optional
        Whether to retrieve the NHDPlus V2 flowlines within the AOI, by default False.
    streamcat_attrs : list, optional
        StreamCat attributes to retrieve, by default ``None``. This will
        set the ``nhdv2_flowlines`` to True. Use ``pynhd.StreamCat().metrics_df``
        to get a dataframe of all available attributes with their descriptions.
    nldi_attrs : list, optional
        List of slelect attributes to retrieve, by default ``None``.
        Use ``pynhd.nhdplus_attrs_s3()`` to get a dataframe of all available
        attributes with their descriptions.
    """

    huc_ids: list[str] | None = None
    nhdv2_ids: list[int] | None = None
    gagesii_basins: list[str] | None = None
    mainstem_main: int | None = None
    mainstem_tributaries: int | None = None
    geometry_file: str | None = None
    nhdv2_flowlines: bool = False
    streamcat_attrs: list[str] | None = None
    nldi_attrs: list[str] | None = None

    @model_validator(mode="after")
    def _check_exclusive_options(self) -> Self:
        """Check if only one of the options is provided."""
        provided_options = [
            option
            for option in (
                self.huc_ids,
                self.nhdv2_ids,
                self.gagesii_basins,
                self.mainstem_main,
                self.geometry_file,
            )
            if option
        ]
        if len(provided_options) != 1:
            options = (
                "`huc_ids`",
                "`nhdv2_ids`",
                "`gagesii_basins`",
                "`mainstem_main`",
                "`geometry_file`",
            )
            op_list = ", ".join(options[:-1]) + f", or {options[-1]}"
            raise ValueError(f"Only one of {op_list} must be provided.")
        return self


class Forcing(BaseModel):
    """Forcing data.

    Attributes
    ----------
    source : str
        Source of the forcing data. Supported sources are "daymet", "gridmet", and "nldas2".
    start_date : datetime
        Start date of the forcing data.
    end_date : datetime
        End date of the forcing data.
    variables : list, optional
        List of variables to retrieve, by default ``None``. If not provided, all available
        variables will be retrieved.
    crop : bool, optional
        Whether to crop the data to the geometry of the AOI, by default True.
        If False, the data will be saved for the bounding box of the AOI.
    geometry_buffer : int, optional
        Buffer distance in meters to add to the geometry of the AOI before requesting
        the data, by default 0. This is useful for cases where additional post-processing
        is needed that are sensitive to the edges of the data.
    """

    source: Literal["daymet", "gridmet", "nldas2"]
    start_date: datetime
    end_date: datetime
    variables: list[str] | None = None
    crop: bool = True
    geometry_buffer: Annotated[float, Field(strict=True, ge=0)] = 0


class Topo(BaseModel):
    """Topographic data.

    Attributes
    ----------
    resolution_m : int
        Resolution of the data in meters.
    derived_variables : list, optional
        List of derived variables to calculate, by default ``None``. Supported derived
        variables are "slope", "aspect", and "curvature".
    crop : bool, optional
        Whether to crop the data to the geometry of the AOI, by default True.
        If False, the data will be saved for the bounding box of the AOI.
    geometry_buffer : int, optional
        Buffer distance in meters to add to the geometry of the AOI before requesting
        the data, by default 0. This is useful for cases where additional post-processing
        is needed that are sensitive to the edges of the data.
    """

    resolution_m: int
    derived_variables: list[Literal["slope", "aspect", "curvature"]] | None = None
    crop: bool = True
    geometry_buffer: Annotated[float, Field(strict=True, ge=0)] = 0


class RemoteRasters(BaseModel):
    """Remote raster data configuration.

    Attributes
    ----------
    crop : bool, optional
        Whether to crop the data to the geometry of the AOI, by default True.
    geometry_buffer : float, optional
        Buffer distance in meters to add to the AOI geometry before requesting data.

    Notes
    -----
    Additional fields are treated as raster names (URLs). Raster names are sanitized:
        - Lowercased
        - Stripped of whitespace
        - Spaces replaced with underscores
    """

    crop: bool = True
    geometry_buffer: Annotated[float, Field(strict=True, ge=0)] = 0
    model_config = ConfigDict(extra="allow", from_attributes=True)

    @field_validator("*", mode="before")
    @classmethod
    def sanitize_keys(cls, v: Any, info: ValidationInfo) -> Any:
        """Sanitize raster names (keys) and validate URL strings."""
        if info.field_name not in ("crop", "geometry_buffer"):
            if not isinstance(v, str):
                raise ValueError(f"URL must be a string, got {type(v)}")
            return v.strip()
        return v

    @property
    def rasters(self) -> dict[str, str]:
        """Return a dictionary of raster names and URLs."""
        return {k: v for k, v in self.model_dump().items() if k not in ("crop", "geometry_buffer")}


class Soil(BaseModel):
    """Soil data.

    Attributes
    ----------
    source : str
        Source of the soil data. Supported sources are``soilgrids``, ``gnatsgo``,
        and ``polaris``.
    variables : list
        List of variables to retrieve. Each source has its own set of variables.
    crop : bool, optional
        Whether to crop the data to the geometry of the AOI, by default True.
        If False, the data will be saved for the bounding box of the AOI.
    geometry_buffer : int, optional
        Buffer distance in meters to add to the geometry of the AOI before requesting
        the data, by default 0. This is useful for cases where additional post-processing
        is needed that are sensitive to the edges of the data.
    """

    source: Literal["soilgrids", "gnatsgo", "polaris"]
    variables: list[str]
    crop: bool = True
    geometry_buffer: Annotated[float, Field(strict=True, ge=0)] = 0


class NLCD(BaseModel):
    """National Land Cover Database (NLCD) data.

    Attributes
    ----------
    cover : list, optional
        List of years for land cover data, by default ``None``., which defaults to
        the most recent data. Available years are 2021, 2019, 2016, 2013, 2011,
        2008, 2006, 2004, and 2001.
    impervious : list, optional
        List of years for impervious data, by default ``None``., which defaults to
        the most recent data. Available years are 2021, 2019, 2016, 2013, 2011,
        2008, 2006, 2004, and 2001.
    canopy : list, optional
        List of years for canopy data, by default ``None``., which defaults to
        the most recent data. Available years are between 2011 and 2022.
    descriptor : list, optional
        List of years for descriptor data, by default ``None``., which defaults to
        the most recent data. Available years are 2021, 2019, 2016, 2013, 2011,
        2008, 2006, 2004, and 2001.
    crop : bool, optional
        Whether to crop the data to the geometry of the AOI, by default True.
        If False, the data will be saved for the bounding box of the AOI.
    geometry_buffer : int, optional
        Buffer distance in meters to add to the geometry of the AOI before requesting
        the data, by default 0. This is useful for cases where additional post-processing
        is needed that are sensitive to the edges of the data.
    """

    cover: list[int] | None = None
    impervious: list[int] | None = None
    canopy: list[int] | None = None
    descriptor: list[int] | None = None
    crop: bool = True
    geometry_buffer: Annotated[float, Field(strict=True, ge=0)] = 0


class NID(BaseModel):
    """National Inventory of Dams (NID) data.

    Attributes
    ----------
    within_aoi : bool
        Whether to retrieve the NID data within the AOI.
    """

    within_aoi: bool


class Streamflow(BaseModel):
    """Streamflow data from NWIS.

    Attributes
    ----------
    start_date : datetime
        Start date of the streamflow data.
    end_date : datetime
        End date of the streamflow data.
    frequency : str
        Frequency of the streamflow data. Supported frequencies are
        "daily" and "instantaneous".
    within_aoi : bool, optional
        Whether to retrieve the streamflow data for USGS stations that
        are within the AOI, by default True.
    use_col : str, optional
        Instead of getting data for all stations within the AOI, get data
        for a column in the AOI dataframe that contains the USGS station
        IDs, by default None.
    """

    start_date: datetime
    end_date: datetime
    frequency: Literal["daily", "instantaneous"]
    within_aoi: bool = True
    use_col: str | None = None

    @model_validator(mode="after")
    def _check_exclusive_options(self) -> Self:
        """Check if the frequency is either 'daily' or 'instantaneous'."""
        if self.frequency not in ("daily", "instantaneous"):
            raise ValueError("Frequency must be either 'daily' or 'instantaneous'.")
        if self.use_col:
            self.within_aoi = False
        return self


class FileList(list[Path]):
    """A list of files in a directory, ensuring all elements are Path objects within the directory."""

    def __init__(self, parent: str | Path) -> None:
        """
        Initialize the FileList object.

        Parameters
        ----------
        parent : str | Path
            The root directory containing the files.
        """
        self.parent = Path(parent).resolve()
        super().__init__()

    def append(self, file: str | Path) -> None:
        """Append a file as a Path relative to the parent directory."""
        super().append(self.parent / file)

    def extend(self, files: Iterable[str | Path]) -> None:
        """Extend the list with multiple files as Paths relative to the parent directory."""
        super().extend(self.parent / f for f in files)

    def mkdir(self, exist_ok: bool = True, parents: bool = True) -> None:
        """Create the parent directory if it does not exist."""
        self.parent.mkdir(exist_ok=exist_ok, parents=parents)

    def rm_tree(self) -> None:
        """Remove the directory and all its contents."""
        if self.parent.exists():
            shutil.rmtree(self.parent)

    def __get_pydantic_core_schema__(self, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        """Define Pydantic schema for serialization and validation."""
        return core_schema.no_info_plain_validator_function(FileList._validate)

    @classmethod
    def _validate(cls, value: Any) -> FileList:
        """Validate the value as a FileList object."""
        if isinstance(value, FileList):
            return value
        elif isinstance(value, list):
            return cls(Path.cwd())
        raise TypeError(f"Cannot validate {value} as FileList")

    @overload
    def __getitem__(self, key: SupportsIndex, /) -> Path: ...

    @overload
    def __getitem__(self, key: slice, /) -> FileList: ...

    def __getitem__(self, key: SupportsIndex | slice, /) -> Path | FileList:
        """Retrieve an item or a slice."""
        if isinstance(key, slice):
            return FileList(self.parent, super().__getitem__(key))  # pyright: ignore[reportCallIssue]
        return super().__getitem__(key)

    @overload
    def __setitem__(self, key: SupportsIndex, value: str | Path, /) -> None: ...

    @overload
    def __setitem__(self, key: slice, value: Iterable[str | Path], /) -> None: ...

    def __setitem__(
        self, key: SupportsIndex | slice, value: str | Path | Iterable[str | Path], /
    ) -> None:
        """Allow assignment by index, expanding the list if necessary."""
        if isinstance(key, slice):
            super().__setitem__(key, [self.parent / f for f in value])  # pyright: ignore[reportGeneralTypeIssues]
        elif isinstance(key, int):
            if key >= len(self):
                self.extend([""] * (key - len(self) + 1))  # Expand the list
            super().__setitem__(key, self.parent / value)  # pyright: ignore[reportOperatorIssue]
        else:
            raise TypeError("Index must be an integer or a slice.")

    def __repr__(self) -> str:
        """Return a string representation of the FileList object."""
        files = "\n".join(str(f) for f in self)
        return f"FileList({self.parent}, {len(self)} files):\n{files}"


@dataclass
class FilePaths:
    """File paths to store the data.

    Attributes
    ----------
    project : pathlib.Path
        Path to the project directory.
    aoi_parquet : Path
        Path to the AOI data in Parquet format.
    flowlines : FileList
        List of NHDPlus V2 flowlines.
    streamcat_attrs : FileList
        List of StreamCat attributes.
    nldi_attrs : FileList
        List of NLDI attributes.
    forcing : FileList
        List of forcing data files.
    topo : FileList
        List of topographic data files.
    soil : FileList
        List of soil data files.
    nlcd : FileList
        List of NLCD data files.
    nid : FileList
        List of NID data files.
    streamflow : FileList
        List of streamflow data files.
    remote_rasters : dict
        Dictionary of remote raster data files, where keys are raster names and values are FileList objects
        containing the file paths.
    """

    project: Path
    aoi_parquet: Path
    flowlines: FileList
    streamcat_attrs: FileList
    nldi_attrs: FileList
    forcing: FileList
    topo: FileList
    soil: FileList
    nlcd: FileList
    nid: FileList
    streamflow: FileList
    remote_rasters: dict[str, FileList]

    def rm_tree(self) -> None:
        """Remove the directory and all its contents."""
        shutil.rmtree(self.project)


class Config(BaseModel):
    """Configuration for HySetter.

    Notes
    -----
    Only ``project`` and ``aoi`` are required. The rest are optional.

    Attributes
    ----------
    project : Project
        Project information.
    aoi : AOI
        Area of interest.
    forcing : Forcing, optional
        Forcing data, by default ``None``.
    topo : Topo, optional
        Topographic data, by default ``None``.
    soil : Soil, optional
        Soil data, by default ``None``.
    nlcd : NLCD, optional
        National Land Cover Database (NLCD) data, by default ``None``.
    nid : NID, optional
        National Inventory of Dams (NID) data, by default ``None``.
    streamflow : Streamflow, optional
        Streamflow data from NWIS, by default ``None``.
    remote_rasters : RemoteRasters, optional
        Remote raster data, by default ``None``.
    overwrite : bool, optional
        Whether to overwrite existing data, by default ``False``.
    """

    project: Project
    aoi: AOI
    forcing: Forcing | None = None
    topo: Topo | None = None
    soil: Soil | None = None
    nlcd: NLCD | None = None
    nid: NID | None = None
    streamflow: Streamflow | None = None
    remote_rasters: RemoteRasters | None = None
    overwrite: bool = False
    file_paths: FilePaths = Field(default=None, init=False)  # pyright: ignore[reportAssignmentType]

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        project_dir = Path(self.project.data_dir, self.project.name.replace(" ", "_"))
        project_dir.mkdir(exist_ok=True, parents=True)
        raster_names = list(self.remote_rasters.rasters) if self.remote_rasters else ["rasters"]
        self.file_paths = FilePaths(
            project=project_dir,
            aoi_parquet=Path(project_dir, "aoi.parquet"),
            flowlines=FileList(Path(project_dir, "nhdv2_flowlines")),
            streamcat_attrs=FileList(Path(project_dir, "streamcat_attrs")),
            nldi_attrs=FileList(Path(project_dir, "nldi_attrs")),
            forcing=FileList(Path(project_dir, "forcing")),
            topo=FileList(Path(project_dir, "topo")),
            soil=FileList(Path(project_dir, "soil")),
            nlcd=FileList(Path(project_dir, "nlcd")),
            nid=FileList(Path(project_dir, "nid")),
            streamflow=FileList(Path(project_dir, "streamflow")),
            remote_rasters={n: FileList(Path(project_dir, n)) for n in raster_names},
        )
        if self.overwrite:
            self.file_paths.rm_tree()

    def get_data(self) -> None:
        """Iterate over non-None attributes."""
        get_aoi(self.aoi, self)
        if self.forcing:
            get_forcing(self.forcing, self)
        if self.topo:
            get_topo(self.topo, self)
        if self.soil:
            get_soil(self.soil, self)
        if self.nlcd:
            get_nlcd(self.nlcd, self)
        if self.nid:
            get_nid(self.nid, self)
        if self.streamflow:
            get_streamflow(self.streamflow, self)
        if self.remote_rasters:
            get_rasters(self.remote_rasters, self)


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
    Path(file_path).write_text(_yaml_dump(config.model_dump()))
