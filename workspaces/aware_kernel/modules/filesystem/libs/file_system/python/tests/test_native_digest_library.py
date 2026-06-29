from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.native_digest_library import (  # noqa: E402
    NativeDigestLibraryUnavailable,
    RustNativeDigestLibraryConfig,
    load_native_digest_library,
    prepare_native_digest_library,
)


def test_load_native_digest_library_requires_existing_file(tmp_path: Path) -> None:
    with pytest.raises(NativeDigestLibraryUnavailable, match="does not exist"):
        load_native_digest_library(tmp_path / "missing.so")


def test_prepared_native_digest_library_hashes_like_hashlib(tmp_path: Path) -> None:
    try:
        library = prepare_native_digest_library(
            RustNativeDigestLibraryConfig(
                target_dir=tmp_path / "cargo-target",
                build_timeout_s=240.0,
            )
        )
    except NativeDigestLibraryUnavailable as exc:
        pytest.skip(str(exc))

    payload = bytearray(b"abc\x00def")
    assert library.sha256_hex(payload) == hashlib.sha256(payload).hexdigest()
    assert library.digest_backend_kind in {
        "rustcrypto_sha2_asm_optimized",
        "rustcrypto_sha2_software",
    }
    assert library.library_path.is_file()
    assert library.rust_build is not None
