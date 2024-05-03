"""Command-line interface for hysetter."""

from __future__ import annotations

import click

import hysetter.hysetter as hs

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command()
@click.argument("config", type=click.Path(exists=True))
def cli(config: str) -> None:
    """Read a configuration file and print its contents.

    Parameters
    ----------
    config : str
        Path to the configuration file.
    """
    cfg = hs.read_config(config)

    if cfg.forcing:
        pass

    if cfg.topo:
        pass
