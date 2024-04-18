"""Command-line interface for hysetter."""

from __future__ import annotations

import click

import hysetter.hysetter as hs
CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}

@click.command()
@click.argument('config', type=click.Path(exists=True))
def cli(config: str)-> None:
    """Read a configuration file and print its contents.
    
    Parameters
    ----------
    config : str
        Path to the configuration file.
    """
    cfg = hs.read_config(config)

    print("Project:")
    print(f"  Name: {cfg.project.name}")
    print(f"  Data Directory: {cfg.project.data_dir}")

    print("AOI:")
    print(f"  HUC IDs: {cfg.aoi.huc_ids}")
    print(f"  NHD Feature IDs: {cfg.aoi.nhd_featureids}")
    print(f"  Geometry File: {cfg.aoi.geometry_file}")
    print(f"  Drainage Network: {cfg.aoi.drainage_network}")

    if cfg.forcing:
        print("Forcing:")
        print(f"  Source: {cfg.forcing.source}")
        print(f"  Start Date: {cfg.forcing.start_date}")
        print(f"  End Date: {cfg.forcing.end_date}")
        print(f"  Resolution (km): {cfg.forcing.resolution_km}")
        print(f"  Variables: {cfg.forcing.variables}")

    if cfg.topo:
        print("Topo:")
        print(f"  Resolution (m): {cfg.topo.resolution_m}")
        print(f"  Derived Variables: {cfg.topo.derived_variables}")

