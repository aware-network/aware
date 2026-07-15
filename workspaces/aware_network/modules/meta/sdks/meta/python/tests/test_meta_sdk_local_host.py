from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_SDK_ROOT = Path(__file__).resolve().parents[1]
_SDK_ROOT_TEXT = str(_SDK_ROOT.resolve())
if _SDK_ROOT_TEXT not in sys.path:
    sys.path.insert(0, _SDK_ROOT_TEXT)

import aware_meta_sdk  # noqa: E402


def test_meta_sdk_local_host_module_is_retired() -> None:
    assert importlib.util.find_spec("aware_meta_sdk.local_host") is None
    assert "local_host" not in aware_meta_sdk.__all__


def test_meta_sdk_top_level_does_not_export_local_helpers() -> None:
    local_export_names = {
        "AwareLocalMetaSdk",
        "LocalMetaAwarePackageManifestSdkSession",
        "build_local_meta_sdk_client",
        "build_local_meta_sdk_client_for_aware_package_manifests",
        "build_local_meta_sdk_session_for_aware_package_manifests",
        "build_local_meta_service_api_client",
        "build_local_meta_service_api_session_for_aware_package_manifests",
    }

    assert set(aware_meta_sdk.__all__).isdisjoint(local_export_names)
    for name in local_export_names:
        assert not hasattr(aware_meta_sdk, name)
