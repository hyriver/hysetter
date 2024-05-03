"""Main functions of hysetter."""

from __future__ import annotations

import functools
from datetime import datetime  # noqa: TCH003
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

__all__ = ["read_config"]

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


class AOI(BaseModel):
    huc_ids: list[str]
    nhd_featureids: list[int]
    geometry_file: str
    drainage_network: bool


class Forcing(BaseModel):
    source: str
    start_date: datetime
    end_date: datetime
    resolution_km: int
    variables: list[str]


class Topo(BaseModel):
    resolution_m: int
    derived_variables: list[str]


class GNATSGO(BaseModel):
    variables: list[str]


class NLCD(BaseModel):
    variables: list[str]
    years: list[int]


class NID(BaseModel):
    federal_ids: list[str]
    within_aio: bool


class RemoteDatasets(BaseModel):
    service_names: list[str]
    service_types: list[str]
    urls: list[str]


class Streamflow(BaseModel):
    gage_ids: list[str]
    start_date: datetime
    end_date: datetime
    frequency: str


class Config(BaseModel):
    project: Project
    aoi: AOI
    forcing: Forcing | None = None
    topo: Topo | None = None
    gnatsgo: GNATSGO | None = None
    nlcd: NLCD | None = None
    nid: NID | None = None
    remote_datasets: RemoteDatasets | None = None
    streamflow: Streamflow | None = None


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
    return Config(**config_data)
