from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path
from types import ModuleType

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.benchmark_receipt_contract import (  # noqa: E402
    WORKSPACE_FS_BENCHMARK_VERSION,
)
from aware_file_system.native_apply import (  # noqa: E402
    NativeApplyUnavailable,
    WorkspaceApplyDelta,
    collect_python_workspace_apply,
)
import aware_file_system.native_apply_selector as selector  # noqa: E402
from aware_file_system.native_apply_benchmark import (  # noqa: E402
    NATIVE_APPLY_BENCHMARK_VERSION,
    RUST_INVOCATION_KIND,
)
from aware_file_system.native_backend import (  # noqa: E402
    RUST_BACKEND_KIND,
    SCAFFOLD_OPERATION,
    WORKSPACE_APPLY_DELTAS_OPERATION,
)


def test_selector_defaults_to_python_without_receipt(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()

    result = selector.apply_workspace_deltas(
        root,
        _single_create_delta("generated/client.py", "python\n"),
    )

    assert result.backend_kind == "python"
    assert result.native_attempted is False
    assert result.native_gate_passed is False
    assert result.benchmark_receipt_path is None
    assert "disabled" in result.reason
    assert (root / "generated/client.py").read_text(encoding="utf-8") == "python\n"


def test_selector_falls_back_when_native_receipt_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_name = _install_native_capability_module(monkeypatch)
    root = tmp_path / "workspace"
    root.mkdir()

    result = selector.apply_workspace_deltas(
        root,
        _single_create_delta("generated/client.py", "fallback\n"),
        options=selector.NativeApplySelectorOptions(
            prefer_native=True,
            module_name=module_name,
        ),
    )

    assert result.backend_kind == "python"
    assert result.native_attempted is False
    assert result.native_gate_passed is False
    assert "benchmark_receipt_path is required" in result.reason
    assert (root / "generated/client.py").read_text(encoding="utf-8") == "fallback\n"


def test_selector_can_fail_closed_on_invalid_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_name = _install_native_capability_module(monkeypatch)
    receipt_path = tmp_path / "invalid-receipt.json"
    receipt_path.write_text(json.dumps({"receipt_schema": "wrong"}), encoding="utf-8")
    root = tmp_path / "workspace"
    root.mkdir()

    with pytest.raises(
        selector.NativeApplySelectionError,
        match="benchmark receipt",
    ):
        selector.apply_workspace_deltas(
            root,
            _single_create_delta("generated/client.py", "blocked\n"),
            options=selector.NativeApplySelectorOptions(
                prefer_native=True,
                benchmark_receipt_path=receipt_path,
                allow_python_fallback=False,
                module_name=module_name,
            ),
        )

    assert not (root / "generated/client.py").exists()


def test_selector_uses_native_after_capability_and_receipt_gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_name = _install_native_capability_module(monkeypatch)
    receipt_path = _write_valid_receipt(tmp_path)
    root = tmp_path / "workspace"
    root.mkdir()
    rust_calls: list[Path] = []
    rust_options: list[dict[str, object]] = []

    def fake_rust_apply(
        apply_root: Path,
        deltas: tuple[WorkspaceApplyDelta, ...],
        **kwargs: object,
    ):
        rust_calls.append(apply_root)
        rust_options.append(dict(kwargs))
        report = collect_python_workspace_apply(apply_root, deltas)
        return replace(report, backend_kind=RUST_BACKEND_KIND)

    monkeypatch.setattr(selector, "collect_rust_workspace_apply", fake_rust_apply)

    result = selector.apply_workspace_deltas(
        root,
        _single_create_delta("generated/client.py", "rust\n"),
        options=selector.NativeApplySelectorOptions(
            prefer_native=True,
            benchmark_receipt_path=receipt_path,
            allow_python_fallback=False,
            module_name=module_name,
            prepared_binary_path=tmp_path / "prepared-native-apply",
            build_timeout_s=12.0,
        ),
    )

    assert rust_calls == [root]
    assert rust_options == [
        {
            "cargo_path": None,
            "cargo_home": None,
            "manifest_path": None,
            "target_dir": None,
            "prepared_binary_path": tmp_path / "prepared-native-apply",
            "release": False,
            "build_timeout_s": 12.0,
        }
    ]
    assert result.backend_kind == "rust"
    assert result.native_attempted is True
    assert result.native_gate_passed is True
    assert result.benchmark_receipt_path == receipt_path.as_posix()
    assert (root / "generated/client.py").read_text(encoding="utf-8") == "rust\n"


def test_selector_falls_back_when_native_apply_fails_after_gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_name = _install_native_capability_module(monkeypatch)
    receipt_path = _write_valid_receipt(tmp_path)
    root = tmp_path / "workspace"
    root.mkdir()

    def fake_rust_apply(*_: object, **__: object):
        raise NativeApplyUnavailable("cargo is not available on PATH")

    monkeypatch.setattr(selector, "collect_rust_workspace_apply", fake_rust_apply)

    result = selector.apply_workspace_deltas(
        root,
        _single_create_delta("generated/client.py", "fallback\n"),
        options=selector.NativeApplySelectorOptions(
            prefer_native=True,
            benchmark_receipt_path=receipt_path,
            module_name=module_name,
        ),
    )

    assert result.backend_kind == "python"
    assert result.native_attempted is True
    assert result.native_gate_passed is True
    assert "native apply failed after gate passed" in result.reason
    assert (root / "generated/client.py").read_text(encoding="utf-8") == "fallback\n"


def _single_create_delta(path: str, content: str) -> tuple[WorkspaceApplyDelta, ...]:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return (
        WorkspaceApplyDelta(
            operation="create",
            path=path,
            content_text=content,
            expected_sha256=digest,
        ),
    )


def _install_native_capability_module(
    monkeypatch: pytest.MonkeyPatch,
) -> str:
    module_name = "aware_file_system_native_selector_test"
    module = ModuleType(module_name)
    module.CAPABILITIES = {
        "backend_kind": RUST_BACKEND_KIND,
        "benchmark_version": WORKSPACE_FS_BENCHMARK_VERSION,
        "backend_version": "test",
        "supported_operations": [
            SCAFFOLD_OPERATION,
            WORKSPACE_APPLY_DELTAS_OPERATION,
        ],
        "reason": "test native capability report loaded",
    }
    monkeypatch.setitem(sys.modules, module_name, module)
    return module_name


def _write_valid_receipt(tmp_path: Path) -> Path:
    receipt_path = tmp_path / "native-apply-receipt.json"
    sample = {
        "iteration_index": 0,
        "duration_s": 0.001,
        "applied_path_count": 1,
        "bytes_written": 5,
        "bytes_deleted": 0,
        "digest_verified_count": 1,
        "stored_artifact_count": 0,
    }
    summary = {
        "duration_s": {
            "count": 1,
            "min": 0.001,
            "median": 0.001,
            "p95": 0.001,
            "max": 0.001,
        }
    }
    receipt = {
        "receipt_schema": NATIVE_APPLY_BENCHMARK_VERSION,
        "benchmark_version": WORKSPACE_FS_BENCHMARK_VERSION,
        "mode": "synthetic_apply_fixture",
        "iteration_count": 1,
        "fixture_root": tmp_path.as_posix(),
        "target_dir": (tmp_path / "cargo-target").as_posix(),
        "fixture": {
            "files_per_operation": 1,
            "payload_bytes": 64,
            "expected_applied_path_count": 1,
            "expected_stored_artifact_count": 0,
        },
        "python_backend": {
            "backend_kind": "python",
            "invocation_kind": "in_process_python",
            "samples": [sample],
            "summary": summary,
        },
        "rust_backend": {
            "backend_kind": "rust",
            "invocation_kind": RUST_INVOCATION_KIND,
            "samples": [sample],
            "summary": summary,
        },
        "parity": {
            "passed": True,
            "sample_count": 1,
            "checked_fields": list(selector.REQUIRED_NATIVE_APPLY_PARITY_FIELDS),
            "mismatches": [],
        },
        "recommendation": {},
        "receipt_path": receipt_path.as_posix(),
    }
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    return receipt_path
