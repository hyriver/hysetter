"""Hooks for the documentation."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import TYPE_CHECKING

from mkdocs.structure.files import File, Files

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig

changelog = Path(__file__).parent.parent / "CHANGELOG.md"
contributing = Path(__file__).parent.parent / "CONTRIBUTING.md"
license = Path(__file__).parent / "LICENSE.md"


def on_files(files: Files, config: MkDocsConfig):
    """Copy the schema to the site."""
    files.append(
        File(
            path=changelog.name,
            src_dir=changelog.parent,
            dest_dir=str(config.site_dir),
            use_directory_urls=config.use_directory_urls,
        )
    )
    files.append(
        File(
            path=contributing.name,
            src_dir=contributing.parent,
            dest_dir=str(config.site_dir),
            use_directory_urls=config.use_directory_urls,
        )
    )
    license_org = Path(__file__).parent.parent / "LICENSE"
    if license_org.exists() and not license.exists():
        shutil.copy(license_org, license)
    else:
        if not license.exists():
            raise FileNotFoundError(f"License file {license} does not exist.")

    files.append(
        File(
            path=license.name,
            src_dir=license.parent,
            dest_dir=str(config.site_dir),
            use_directory_urls=config.use_directory_urls,
        )
    )
    return files
