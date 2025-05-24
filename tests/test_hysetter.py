from __future__ import annotations

import io

import pytest
from click.testing import CliRunner, Result

import hysetter as hs
from hysetter.cli import cli


@pytest.fixture
def runner():
    """Return a CliRunner."""
    return CliRunner()


@pytest.fixture
def run_config_once(runner: CliRunner) -> Result:
    ret = runner.invoke(cli, ["config_demo.yml"])
    return ret


def test_config(run_config_once: Result) -> None:
    assert run_config_once.exit_code == 0


def test_config_overwrite(runner: CliRunner, run_config_once: Result) -> None:
    ret = runner.invoke(cli, ["config_demo.yml", "--overwrite"])
    assert ret.exit_code == 0


def test_show_versions() -> None:
    f = io.StringIO()
    hs.show_versions(file=f)
    assert "SYS INFO" in f.getvalue()
