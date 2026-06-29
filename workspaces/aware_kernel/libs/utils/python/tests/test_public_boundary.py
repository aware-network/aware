from __future__ import annotations

from pathlib import Path

import aware_utils


def test_public_aware_utils_does_not_export_root_discovery() -> None:
    assert "find_aware_root" not in aware_utils.__all__


def test_public_aware_utils_package_does_not_ship_root_discovery_module() -> None:
    package_root = Path(aware_utils.__file__).resolve().parent
    assert not (package_root / "find_aware_root.py").exists()
