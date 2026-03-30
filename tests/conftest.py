import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _configure_headless_matplotlib(tmp_path_factory: pytest.TempPathFactory) -> None:
    """Ensure matplotlib/fontconfig cache paths are writable in CI/sandbox."""
    cache_dir = Path(tmp_path_factory.mktemp("mpl_cache"))
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache_dir))

