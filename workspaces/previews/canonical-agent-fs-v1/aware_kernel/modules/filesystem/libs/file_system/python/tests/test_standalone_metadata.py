from __future__ import annotations

import tomllib
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
KERNEL_ROOT = PACKAGE_ROOT.parents[4]


def _toml(path: Path) -> dict[str, object]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def test_file_system_does_not_publish_private_native_tooling_metadata() -> None:
    project = _toml(PACKAGE_ROOT / "pyproject.toml")

    optional = project["project"]["optional-dependencies"]
    assert "native" not in optional
    assert "rust-tooling" not in project.get("tool", {}).get("uv", {}).get(
        "sources", {}
    )


def test_kernel_root_remains_native_tooling_source_authority() -> None:
    kernel = _toml(KERNEL_ROOT / "pyproject.toml")

    assert kernel["tool"]["uv"]["sources"]["rust-tooling"] == {
        "workspace": True
    }
    assert "languages/rust/tooling" in kernel["tool"]["uv"]["workspace"][
        "members"
    ]
