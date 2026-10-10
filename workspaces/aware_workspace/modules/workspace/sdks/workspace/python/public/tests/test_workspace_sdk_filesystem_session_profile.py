from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from filesystem_rust_session_receipt_contract import (
    assert_workspace_rust_session_close_receipt_contract,
    assert_workspace_rust_session_profile_sample_contract,
)


def test_workspace_filesystem_rust_session_profile_receipt(
    tmp_path: Path,
) -> None:
    pytest.importorskip("rust_tooling.cargo")
    profile = _load_profile_module()
    case = profile.WorkspaceFileSystemRustSessionProfileCase(
        name="tiny_mixed",
        create_file_count=2,
        update_file_count=1,
        delete_file_count=1,
        payload_bytes=64,
    )

    receipt = profile.run_workspace_filesystem_rust_session_profile_matrix_sync(
        profile.WorkspaceFileSystemRustSessionProfileConfig(
            fixture_root=tmp_path / "profile",
            iterations=2,
            cases=(case,),
            write_receipt=True,
        )
    )

    assert receipt["receipt_schema"] == (
        "aware.workspace_sdk.filesystem_rust_session_profile_matrix.v1"
    )
    assert receipt["workspace_sdk_boundary"] == (
        "WorkspaceSdkClient.materialize_and_apply"
    )
    assert receipt["iteration_count"] == 2
    assert receipt["case_count"] == 1
    assert receipt["analysis"]["all_parity_passed"] is True
    assert_workspace_rust_session_close_receipt_contract(
        receipt["rust_session_close_receipt"]
    )
    receipt_path = Path(receipt["receipt_path"])
    assert receipt_path.is_file()

    case_receipt = receipt["cases"][0]
    assert case_receipt["parity"]["passed"] is True
    assert case_receipt["summary"]["rust_to_python_duration_ratio"] is not None
    assert case_receipt["summary"]["rust_warm_cached_before_values"] == [
        False,
        True,
    ]

    python_sample = case_receipt["python_samples"][0]
    rust_sample = case_receipt["rust_samples"][0]
    assert python_sample["backend_kind"] == "python"
    assert python_sample["file_system_api_session"] is False
    assert_workspace_rust_session_profile_sample_contract(rust_sample)
    assert rust_sample["digest_verified_count"] == 3


def _load_profile_module() -> ModuleType:
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "profile_filesystem_rust_session.py"
    )
    spec = importlib.util.spec_from_file_location(
        "workspace_profile_filesystem_rust_session",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
