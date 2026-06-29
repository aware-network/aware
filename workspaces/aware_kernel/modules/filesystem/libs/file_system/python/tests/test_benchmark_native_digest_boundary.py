from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.scripts import benchmark_native_digest_boundary  # noqa: E402
from aware_file_system.scripts.benchmark_native_digest_boundary import (  # noqa: E402
    NATIVE_DIGEST_BOUNDARY_BENCHMARK_VERSION,
    NativeDigestBoundaryBenchmarkConfig,
    deterministic_payload,
    run_native_digest_boundary_benchmark,
)


@dataclass(frozen=True, slots=True)
class FakePreparedNativeDigestLibrary:
    library_path: Path
    invocation_kind: str
    manifest_path: Path
    target_dir: Path | None
    digest_backend_kind: str
    rust_build: Mapping[str, Any] | None

    def sha256_hex(self, payload: bytes | bytearray | memoryview) -> str:
        return hashlib.sha256(payload).hexdigest()


def test_deterministic_payload_is_stable() -> None:
    assert deterministic_payload(4) == bytearray([17, 48, 79, 110])


def test_native_digest_boundary_benchmark_writes_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake_library = FakePreparedNativeDigestLibrary(
        library_path=tmp_path / "libaware_file_system_native.so",
        invocation_kind="provided_prepared_cdylib",
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
        digest_backend_kind="rustcrypto_sha2_asm_optimized",
        rust_build={"status": "succeeded"},
    )

    monkeypatch.setattr(
        benchmark_native_digest_boundary,
        "prepare_native_digest_library",
        lambda *_args, **_kwargs: fake_library,
    )

    receipt = run_native_digest_boundary_benchmark(
        NativeDigestBoundaryBenchmarkConfig(
            fixture_root=tmp_path / "bench",
            payload_bytes=64,
            iterations=3,
            target_dir=tmp_path / "target",
            write_receipt=True,
        )
    )

    assert receipt["receipt_schema"] == NATIVE_DIGEST_BOUNDARY_BENCHMARK_VERSION
    assert receipt["mode"] == "native_digest_boundary_benchmark"
    assert receipt["payload_boundary"] == "python_bytearray_ctypes_from_buffer_v1"
    assert receipt["payload_bytes"] == 64
    assert receipt["iterations"] == 3
    assert receipt["bytes_hashed"] == 192
    assert receipt["parity_passed"] is True
    assert receipt["digest"] == hashlib.sha256(deterministic_payload(64)).hexdigest()
    assert receipt["native_to_python_median_duration_ratio"] >= 0
    assert receipt["python_hashlib"]["sample_count"] == 3
    assert receipt["rust_native_library"]["sample_count"] == 3
    assert receipt["rust_native_library"]["digest_backend_kind"] == (
        "rustcrypto_sha2_asm_optimized"
    )
    assert receipt["rust_native_library"]["rust_build"] == {"status": "succeeded"}
    assert Path(receipt["receipt_path"]).is_file()
    assert json.loads(Path(receipt["receipt_path"]).read_text()) == receipt


def test_native_digest_boundary_benchmark_rejects_empty_payload(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="payload_bytes"):
        run_native_digest_boundary_benchmark(
            NativeDigestBoundaryBenchmarkConfig(
                fixture_root=tmp_path,
                payload_bytes=0,
            )
        )
