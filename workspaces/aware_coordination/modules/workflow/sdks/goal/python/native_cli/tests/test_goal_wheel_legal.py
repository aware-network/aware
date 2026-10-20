"""Prove the four Goal-owned neutral wheels carry their own legal files."""

from __future__ import annotations

import hashlib
import subprocess
import tomllib
from email.parser import BytesParser
from pathlib import Path
from zipfile import ZipFile

import pytest


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return next(
        parent for parent in Path(__file__).resolve().parents
        if (parent / "aware.repo.toml").is_file()
    )


GOAL_WHEELS = (
    ("workspaces/aware_coordination/modules/workflow/libs/goal_operational_runtime", "aware_goal_operational_runtime"),
    ("workspaces/aware_coordination/modules/workflow/sdks/goal/python/public", "aware_goal_sdk"),
    ("workspaces/aware_coordination/modules/workflow/sdks/goal/python/native_fs_adapter", "aware_goal_native_fs_adapter"),
    ("workspaces/aware_coordination/modules/workflow/sdks/goal/python/native_cli", "aware_goal_native_cli"),
)


@pytest.mark.parametrize(("relative_root", "wheel_prefix"), GOAL_WHEELS)
def test_goal_wheel_has_exact_aware_license_and_scoped_notice(
    repo_root: Path, tmp_path: Path, relative_root: str, wheel_prefix: str
) -> None:
    source = repo_root / relative_root
    manifest = tomllib.loads((source / "pyproject.toml").read_text(encoding="utf-8"))
    assert manifest["project"]["license"] == "Apache-2.0"
    assert manifest["project"]["license-files"] == ["LICENSE", "NOTICE"]
    assert (source / "LICENSE").read_bytes() == (repo_root / "LICENSE").read_bytes()
    notice = (source / "NOTICE").read_bytes()
    assert b"Copyright 2025-2026 Luis Lechuga Ruiz" in notice
    assert b"Separately distributed dependencies retain their own licenses" in notice
    assert b"THIRD_PARTY_NOTICES.md" not in notice

    build = subprocess.run(
        ("uv", "build", "--wheel", "--offline", "--out-dir", str(tmp_path), str(source)),
        cwd=repo_root, text=True, capture_output=True, check=False,
    )
    assert build.returncode == 0, build.stderr
    wheels = tuple(tmp_path.glob("*.whl"))
    assert len(wheels) == 1
    with ZipFile(wheels[0]) as wheel:
        members = wheel.namelist()
        metadata_path, = (name for name in members if name.endswith(".dist-info/METADATA"))
        distribution_info = metadata_path.removesuffix("METADATA")
        metadata = BytesParser().parsebytes(wheel.read(metadata_path))
        assert metadata["License-Expression"] == "Apache-2.0"
        assert set(metadata.get_all("License-File", [])) == {"LICENSE", "NOTICE"}
        assert wheel.read(distribution_info + "licenses/LICENSE") == (repo_root / "LICENSE").read_bytes()
        assert wheel.read(distribution_info + "licenses/NOTICE") == notice
        assert all(
            member.startswith((wheel_prefix + "/", distribution_info))
            for member in members
        )
        assert not any("service" in member.lower() or "ontology" in member.lower() for member in members)
        entry_points = (name for name in members if name.endswith(".dist-info/entry_points.txt"))
        if wheel_prefix == "aware_goal_native_cli":
            entry_point_path, = entry_points
            assert b"aware-goal-native = aware_goal_native_cli.main:main" in wheel.read(entry_point_path)
        else:
            assert not tuple(entry_points)
        assert hashlib.sha256(wheel.read(distribution_info + "licenses/LICENSE")).hexdigest() == (
            "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
        )
