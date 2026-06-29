from __future__ import annotations

from pathlib import Path

import pytest

from aware_orm.runtime.bundle_runtime_install import (
    install_default_environment_bundle,
    install_environment_bundle,
    resolve_environment_manifest_path,
)
from aware_orm.runtime.errors import BundleInstallError


@pytest.mark.parametrize(
    "call",
    (
        lambda tmp_path: resolve_environment_manifest_path(),
        lambda tmp_path: resolve_environment_manifest_path(
            tmp_path / "environment.manifest.json"
        ),
        lambda tmp_path: install_environment_bundle(
            manifest_path=tmp_path / "environment.manifest.json"
        ),
        lambda tmp_path: install_default_environment_bundle(),
    ),
)
def test_environment_bundle_install_helpers_are_retired(tmp_path: Path, call) -> None:
    with pytest.raises(
        BundleInstallError, match="Environment bundle installation is retired"
    ):
        call(tmp_path)


def test_environment_bundle_installer_does_not_import_structure() -> None:
    source_path = (
        Path(__file__).parents[2]
        / "aware_orm"
        / "runtime"
        / "bundle_runtime_install.py"
    )

    assert "aware_structure" not in source_path.read_text(encoding="utf-8")
