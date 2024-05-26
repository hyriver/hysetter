from __future__ import annotations

import io

import pytest
from click.testing import CliRunner

import hysetter as hs
from hysetter.cli import cli


@pytest.fixture()
def runner():
    """Return a CliRunner."""
    return CliRunner()


def test_config(runner: CliRunner) -> None:
    ret = runner.invoke(cli, ["config_demo.yml"])
    assert ret.exit_code == 0
    ret = runner.invoke(cli, ["config_demo.yml", "--overwrite"])
    assert ret.exit_code == 0


def test_show_versions() -> None:
    f = io.StringIO()
    hs.show_versions(file=f)
    assert "SYS INFO" in f.getvalue()
