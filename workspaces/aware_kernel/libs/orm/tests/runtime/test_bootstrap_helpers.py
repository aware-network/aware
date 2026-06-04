from __future__ import annotations

from pathlib import Path

import pytest

from aware_orm.runtime.bundle_runtime_install import (
    DEFAULT_MANIFEST_PATH,
    ENVIRONMENT_MANIFEST_ENV,
    resolve_environment_manifest_path,
)
from aware_orm._support import find_aware_root


def test_resolve_environment_manifest_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENVIRONMENT_MANIFEST_ENV, raising=False)
    path = resolve_environment_manifest_path()
    assert path.is_absolute()
    assert path == find_aware_root() / DEFAULT_MANIFEST_PATH


def test_resolve_environment_manifest_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENVIRONMENT_MANIFEST_ENV, "relative/path/environment.manifest.json")
    path = resolve_environment_manifest_path()
    assert path == find_aware_root() / Path("relative/path/environment.manifest.json")

    monkeypatch.setenv(ENVIRONMENT_MANIFEST_ENV, str(Path("/tmp") / "manifest.json"))
    path = resolve_environment_manifest_path()
    assert path == Path("/tmp/manifest.json")
