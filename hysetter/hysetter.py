"""Main functions of hysetter."""

from __future__ import annotations

import functools
from dataclasses import dataclass
from datetime import datetime  # noqa: TCH003
from pathlib import Path
from typing import Any

import rich.repr
import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing_extensions import Self

__all__ = ["read_config", "write_config"]

yaml_load = functools.partial(yaml.load, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
Dumper = getattr(yaml, "CSafeDumper", yaml.SafeDumper)


def yaml_dump(o: Any, **kwargs: Any) -> str:
    """Dump YAML.

    Notes
    -----
    When python/mypy#1484 is solved, this can be `functools.partial`
    """
    return yaml.dump(
        o,
        Dumper=Dumper,
        stream=None,
        default_flow_style=False,
        indent=2,
        sort_keys=False,
        **kwargs,
    )


class Project(BaseModel):
    name: str
    data_dir: str


@rich.repr.auto
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
    """

    huc_ids: list[str] | None = None
    nhdv2_ids: list[int] | None = None
    gagesii_basins: list[str] | None = None
    geometry_file: str | None = None
    nhdv2_flowlines: bool = False

    @model_validator(mode="after")
    def check_exclusive_options(self) -> Self:
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


@rich.repr.auto
class Forcing(BaseModel):
    source: str
    start_date: datetime
    end_date: datetime
    variables: list[str]


@rich.repr.auto
class Topo(BaseModel):
    resolution_m: int
    derived_variables: list[str]


@rich.repr.auto
class GNATSGO(BaseModel):
    variables: list[str]


@rich.repr.auto
class NLCD(BaseModel):
    variables: list[str] | None = None
    years: list[int] | None = None


@rich.repr.auto
class NID(BaseModel):
    federal_ids: list[str] | None = None
    within_aoi: bool = False

    @model_validator(mode="after")
    def check_exclusive_options(self) -> Self:
        if self.federal_ids is None and not self.within_aoi:
            raise ValueError("One of `federal_ids` or `within_aoi` must be provided.")
        return self


@rich.repr.auto
class Streamflow(BaseModel):
    gage_ids: list[str]
    start_date: datetime
    end_date: datetime
    frequency: str


@dataclass
class FilePaths:
    project_dir: Path
    aoi_parquet: Path
    flowlines_dir: Path
    forcing_dir: Path


@rich.repr.auto
class Config(BaseModel):
    project: Project
    aoi: AOI
    forcing: Forcing | None = None
    topo: Topo | None = None
    gnatsgo: GNATSGO | None = None
    nlcd: NLCD | None = None
    nid: NID | None = None
    streamflow: Streamflow | None = None
    file_paths: FilePaths = Field(default=None, init=False)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        project_dir = Path(self.project.data_dir, self.project.name.replace(" ", "_"))
        self.file_paths = FilePaths(
            project_dir=project_dir,
            aoi_parquet=Path(project_dir, "aoi.parquet"),
            flowlines_dir=Path(project_dir, "nhdv2_flowlines"),
            forcing_dir=Path(project_dir, "forcing"),
        )
        self.file_paths.flowlines_dir.mkdir(exist_ok=True, parents=True)
        self.file_paths.forcing_dir.mkdir(exist_ok=True, parents=True)


def read_config(file_path: str | Path) -> Config:
    """Read a configuration file and return a Config object.

    Parameters
    ----------
    file_path : str or Path
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
    file_path : str or Path
        Path to the configuration file.
    """
    Path(file_path).write_text(yaml_dump(config.model_dump()))
