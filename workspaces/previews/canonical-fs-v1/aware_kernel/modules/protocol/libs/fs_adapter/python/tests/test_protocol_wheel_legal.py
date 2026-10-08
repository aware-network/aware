"""Verify Protocol-owned neutral wheels carry scoped in-wheel legal files."""

from __future__ import annotations

import hashlib
import subprocess
import tomllib
from email.parser import BytesParser
from pathlib import Path
from zipfile import ZipFile

import pytest


PROTOCOL_WHEELS = (
    ("workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python", "aware_protocol_fs_adapter"),
    ("workspaces/aware_kernel/modules/protocol/libs/runtime/python", "aware_protocol_runtime"),
    ("workspaces/aware_kernel/modules/protocol/sdks/protocol/python", "aware_protocol_sdk"),
)


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return next(
        parent for parent in Path(__file__).resolve().parents
        if (parent / "aware.repo.toml").is_file()
    )


@pytest.mark.parametrize(("relative_root", "wheel_prefix"), PROTOCOL_WHEELS)
def test_protocol_wheel_has_exact_aware_license_and_scoped_notice(
    repo_root: Path, tmp_path: Path, relative_root: str, wheel_prefix: str
) -> None:
    source = repo_root / relative_root
    manifest = tomllib.loads((source / "pyproject.toml").read_text(encoding="utf-8"))
    assert manifest["project"]["license"] == "Apache-2.0"
    assert manifest["project"]["license-files"] == ["LICENSE", "NOTICE"]
    root_license = (repo_root / "LICENSE").read_bytes()
    license_bytes = (source / "LICENSE").read_bytes()
    assert license_bytes == root_license
    assert hashlib.sha256(license_bytes).hexdigest() == (
        "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
    )
    notice = (source / "NOTICE").read_bytes()
    assert b"Copyright 2025-2026 Luis Lechuga Ruiz" in notice
    assert b"Separately distributed dependencies retain their own licenses" in notice
    assert b"THIRD_PARTY_NOTICES.md" not in notice

    built = subprocess.run(
        ("uv", "build", "--wheel", "--offline", "--out-dir", str(tmp_path), str(source)),
        cwd=repo_root, text=True, capture_output=True, check=False,
    )
    assert built.returncode == 0, built.stderr
    wheels = tuple(tmp_path.glob("*.whl"))
    assert len(wheels) == 1
    with ZipFile(wheels[0]) as wheel:
        members = wheel.namelist()
        metadata_path, = (name for name in members if name.endswith(".dist-info/METADATA"))
        dist_info = metadata_path.removesuffix("METADATA")
        metadata = BytesParser().parsebytes(wheel.read(metadata_path))
        assert metadata["License-Expression"] == "Apache-2.0"
        assert set(metadata.get_all("License-File", [])) == {"LICENSE", "NOTICE"}
        assert wheel.read(dist_info + "licenses/LICENSE") == root_license
        assert wheel.read(dist_info + "licenses/NOTICE") == notice
        assert all(member.startswith((wheel_prefix + "/", dist_info)) for member in members)
        assert not tuple(name for name in members if name.endswith(".dist-info/entry_points.txt"))
