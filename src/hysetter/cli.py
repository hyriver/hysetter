"""Command-line interface for hysetter."""

from __future__ import annotations

import importlib.metadata
import shutil
import sys
from pathlib import Path

import rich_click as click
from rich import box
from rich.console import Console
from rich.table import Table

from . import hysetter as hs

console = Console()
CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def get_versions() -> dict[str, str]:
    """Get the versions of the dependencies."""

    def _get_version(module: str) -> str:
        """Get the version of the module."""
        try:
            return importlib.metadata.version(module)
        except importlib.metadata.PackageNotFoundError:
            return "not installed"

    hs_ver = _get_version("hysetter")
    if "dev" in hs_ver:
        hs_ver = ".".join(hs_ver.split(".")[:3]) + "-dev"
    return {
        "HySetter": hs_ver,
        "HyRiver Stack": ".".join(_get_version("pygeohydro").split(".")[:2]),
        "Python": ".".join(map(str, sys.version_info[:3])),
    }


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("config_yml", type=click.Path(exists=True))
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite the existing data, defaults to ``False``.",
)
@click.version_option(importlib.metadata.version("hysetter"), prog_name="HySetter")
def cli(config_yml: str, overwrite: bool = False) -> None:
    r"""Get hydroclimate data for areas of interest.

    \b
    CONFIG_YML: Path to the configuration file in YAML format.

    \b
    $ hysetter config.yml --overwrite
    """
    table = Table(box=box.ROUNDED)
    table.add_column("Package", style="bold")
    table.add_column("Version", style="magenta", justify="center")
    for p, v in get_versions().items():
        table.add_row(p, v)
    console.print(table)

    console.print(f"Reading configuration file: [bold green]{Path(config_yml).resolve()}")
    cfg = hs.read_config(config_yml)

    if overwrite:
        console.print("Removing existing data")
        shutil.rmtree(cfg.project.data_dir, ignore_errors=True)
    try:
        cfg.get_data()
    except Exception:
        console.print_exception(extra_lines=3, show_locals=True)
        sys.exit(1)
