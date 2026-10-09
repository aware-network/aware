"""Offline build accounting, separate from installed consumer parity."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import subprocess
import tomllib
from email.parser import BytesParser
from pathlib import Path
from zipfile import ZipFile

import pytest


@pytest.fixture(scope="module")
def package_root():
    return Path(__file__).resolve().parents[1]


def test_project_has_no_runtime_dependencies_or_entrypoints(package_root):
    project = tomllib.loads((package_root / "pyproject.toml").read_text())["project"]
    assert project["version"] == "0.1.1"
    assert project["dependencies"] == []
    assert "scripts" not in project
    assert "entry-points" not in project
    assert project["license"] == "Apache-2.0"
    assert project["license-files"] == ["LICENSE", "NOTICE"]


def test_wheel_namespace_legal_bytes_and_record(package_root, tmp_path):
    built = subprocess.run(
        [
            "uv",
            "build",
            "--wheel",
            "--offline",
            "--out-dir",
            str(tmp_path),
            str(package_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert built.returncode == 0, built.stderr
    (wheel_path,) = tmp_path.glob("*.whl")
    with ZipFile(wheel_path) as wheel:
        members = wheel.namelist()
        (metadata_path,) = (p for p in members if p.endswith(".dist-info/METADATA"))
        dist = metadata_path.removesuffix("METADATA")
        metadata = BytesParser().parsebytes(wheel.read(metadata_path))
        assert metadata["License-Expression"] == "Apache-2.0"
        assert set(metadata.get_all("License-File", [])) == {"LICENSE", "NOTICE"}
        assert not [
            v for v in metadata.get_all("Requires-Dist", []) if "extra ==" not in v
        ]
        assert not metadata.get("Requires-External")
        assert all(p.startswith(("aware_command_runtime/", dist)) for p in members)
        assert dist + "entry_points.txt" not in members
        for name in ("LICENSE", "NOTICE"):
            assert (
                wheel.read(dist + "licenses/" + name)
                == (package_root / name).read_bytes()
            )
        for name in ("runtime.py", "__init__.py", "py.typed"):
            assert (
                wheel.read("aware_command_runtime/" + name)
                == (package_root / "aware_command_runtime" / name).read_bytes()
            )
        assert hashlib.sha256((package_root / "LICENSE").read_bytes()).hexdigest() == (
            "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
        )
        record = dist + "RECORD"
        rows = list(csv.reader(io.StringIO(wheel.read(record).decode())))
        assert {row[0] for row in rows} == set(members)
        for name, digest, size in rows:
            if name == record:
                assert (digest, size) == ("", "")
                continue
            data = wheel.read(name)
            actual = (
                base64.urlsafe_b64encode(hashlib.sha256(data).digest())
                .rstrip(b"=")
                .decode()
            )
            assert digest == "sha256=" + actual
            assert int(size) == len(data)
