"""Shared test fixtures.

Redirects the SQLite DATA_DIR to a per-session tmp dir so live API tests
don't pollute the working directory or leak state between runs.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest

from app.core.config import get_settings
from app.services import reference_store as rs_module


@pytest.fixture(autouse=True, scope="session")
def _isolated_data_dir() -> Iterator[None]:
    tmp = tempfile.mkdtemp(prefix="corpusai-test-")
    os.environ["DATA_DIR"] = tmp
    get_settings.cache_clear()
    rs_module._store = None
    yield
    rs_module._store = None
