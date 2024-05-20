"""Configuration for pytest."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture(autouse=True)
def _add_standard_imports(doctest_namespace: dict[str, Any]):
    """Add hysetter namespace for doctest."""
    import hysetter as hs

    doctest_namespace["hs"] = hs
