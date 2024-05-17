"""Command-line interface for hysetter."""

from __future__ import annotations

import importlib.metadata
import sys
from pathlib import Path

import rich_click as click
from rich import box
from rich.console import Console
from rich.table import Table

from . import aoi, forcing
from . import hysetter as hs

console = Console()
CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def get_versions() -> dict[str, str]:
    """Get the versions of the dependencies."""

    def _get_version(module: str) -> str:
        try:
            return importlib.metadata.version(module)
        except importlib.metadata.PackageNotFoundError:
            return "not installed"

    return {
        "HySetter": _get_version("hysetter"),
        "HyRiver Stack": ".".join(_get_version("pygeohydro").split(".")[:2]),
        "Python": ".".join(map(str, sys.version_info[:3])),
    }


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("config", type=click.Path(exists=True))
@click.version_option(importlib.metadata.version("hysetter"), prog_name="HySetter")
def cli(config: str) -> None:
    """Get the requested data for the area of interest."""
    table = Table(box=box.ROUNDED)
    table.add_column("Package", style="bold")
    table.add_column("Version", style="magenta", justify="center")
    for p, v in get_versions().items():
        table.add_row(p, v)
    console.print(table)

    console.print(f"Reading configuration file: [bold green]{Path(config).resolve()}")
    cfg = hs.read_config(config)

    try:
        console.print("Getting AOI geometries.")
        aoi.get_aoi(cfg)
        console.print("Getting forcing data.")
        forcing.get_forcing(cfg)
    except Exception:
        console.print_exception(extra_lines=8, show_locals=True)
        sys.exit(1)
