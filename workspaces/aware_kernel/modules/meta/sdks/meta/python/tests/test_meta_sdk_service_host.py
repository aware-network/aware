from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_SDK_ROOT = Path(__file__).resolve().parents[1]
_SDK_ROOT_TEXT = str(_SDK_ROOT.resolve())
if _SDK_ROOT_TEXT not in sys.path:
    sys.path.insert(0, _SDK_ROOT_TEXT)

import aware_meta_sdk  # noqa: E402


def test_meta_sdk_service_host_module_is_retired() -> None:
    assert importlib.util.find_spec("aware_meta_sdk.service_host") is None
    assert "service_host" not in aware_meta_sdk.__all__


def test_meta_sdk_top_level_does_not_export_service_host_helpers() -> None:
    retired_export_names = {
        "LaneCommitReceiptBus",
        "LaneHeadReceiptRelay",
        "LocalMetaLaneStore",
        "MaterializationLaneContext",
        "MetaSdkLaneStore",
        "build_local_meta_commit_store",
        "build_local_meta_lane_store",
        "build_local_meta_oig_materializer",
        "build_local_meta_sdk_lane_store",
        "build_local_meta_sdk_service_graph_gateway",
        "load_local_meta_graph_context",
        "materialize_local_meta_lane_oig",
        "read_local_meta_workspace_api_activation_read_model",
        "read_local_meta_workspace_runtime_read_model",
        "start_local_meta_lane_head_receipt_relay",
    }

    assert set(aware_meta_sdk.__all__).isdisjoint(retired_export_names)
    for name in retired_export_names:
        assert not hasattr(aware_meta_sdk, name)
