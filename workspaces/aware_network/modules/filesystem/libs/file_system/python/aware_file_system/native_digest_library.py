from __future__ import annotations

import ctypes
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any


RUST_NATIVE_DIGEST_LIBRARY_NAME = "aware_file_system_native"
RUST_NATIVE_DIGEST_DEBUG_INVOCATION_KIND = "prepared_debug_cdylib"
RUST_NATIVE_DIGEST_RELEASE_INVOCATION_KIND = "prepared_release_cdylib"
RUST_NATIVE_DIGEST_PREPARED_INVOCATION_KIND = "provided_prepared_cdylib"
DEFAULT_RUST_NATIVE_DIGEST_BUILD_TIMEOUT_S = 240.0
SHA256_HEX_LENGTH = 64
SHA256_FFI_STATUS_OK = 0


class NativeDigestLibraryUnavailable(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RustNativeDigestLibraryConfig:
    cargo_path: Path | None = None
    cargo_home: Path | None = None
    manifest_path: Path | None = None
    target_dir: Path | None = None
    prepared_library_path: Path | None = None
    library_name: str = RUST_NATIVE_DIGEST_LIBRARY_NAME
    release: bool = False
    build_timeout_s: float = DEFAULT_RUST_NATIVE_DIGEST_BUILD_TIMEOUT_S


class NativeDigestLibrary:
    def __init__(self, library_path: Path) -> None:
        resolved_path = library_path.expanduser().resolve()
        if not resolved_path.is_file():
            raise NativeDigestLibraryUnavailable(
                f"Native digest library does not exist: {resolved_path.as_posix()}"
            )
        self.library_path = resolved_path
        try:
            self._library = ctypes.CDLL(resolved_path.as_posix())
            self._sha256 = self._library.aware_file_system_native_sha256_hex
            self._backend_kind = (
                self._library.aware_file_system_native_sha256_backend_kind
            )
        except OSError as exc:
            raise NativeDigestLibraryUnavailable(
                f"Native digest library failed to load: {exc}"
            ) from exc
        except AttributeError as exc:
            raise NativeDigestLibraryUnavailable(
                "Native digest library is missing required SHA-256 symbols"
            ) from exc

        self._sha256.argtypes = (
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.c_size_t,
        )
        self._sha256.restype = ctypes.c_int
        self._backend_kind.argtypes = (ctypes.c_void_p, ctypes.c_size_t)
        self._backend_kind.restype = ctypes.c_ssize_t

    @property
    def digest_backend_kind(self) -> str:
        out = ctypes.create_string_buffer(128)
        written = self._backend_kind(ctypes.cast(out, ctypes.c_void_p), len(out))
        if written < 0:
            raise NativeDigestLibraryUnavailable(
                f"Native digest backend-kind query failed with status {written}"
            )
        return out.raw[:written].decode("ascii")

    def sha256_hex(self, payload: bytes | bytearray | memoryview) -> str:
        view = memoryview(payload)
        if view.ndim != 1:
            raise ValueError("Native digest payload must be a one-dimensional buffer")
        if not view.c_contiguous:
            view = memoryview(view.tobytes())
        pointer, keepalive = _payload_pointer(view)
        out = ctypes.create_string_buffer(SHA256_HEX_LENGTH)
        status = self._sha256(
            pointer,
            view.nbytes,
            ctypes.cast(out, ctypes.c_void_p),
            len(out),
        )
        _ = keepalive
        if status != SHA256_FFI_STATUS_OK:
            raise NativeDigestLibraryUnavailable(
                f"Native digest SHA-256 call failed with status {status}"
            )
        return out.raw.decode("ascii")


@dataclass(frozen=True, slots=True)
class PreparedNativeDigestLibrary:
    library_path: Path
    invocation_kind: str
    manifest_path: Path
    target_dir: Path | None
    digest_backend_kind: str
    rust_build: Mapping[str, Any] | None
    _library: NativeDigestLibrary

    def sha256_hex(self, payload: bytes | bytearray | memoryview) -> str:
        return self._library.sha256_hex(payload)


def load_native_digest_library(
    library_path: Path,
    *,
    invocation_kind: str = RUST_NATIVE_DIGEST_PREPARED_INVOCATION_KIND,
    manifest_path: Path | None = None,
    target_dir: Path | None = None,
    rust_build: Mapping[str, Any] | None = None,
) -> PreparedNativeDigestLibrary:
    resolved_manifest_path = (
        manifest_path.expanduser().resolve()
        if manifest_path is not None
        else default_rust_native_digest_manifest_path()
    )
    resolved_target_dir = (
        target_dir.expanduser().resolve() if target_dir is not None else None
    )
    library = NativeDigestLibrary(library_path)
    return PreparedNativeDigestLibrary(
        library_path=library.library_path,
        invocation_kind=invocation_kind,
        manifest_path=resolved_manifest_path,
        target_dir=resolved_target_dir,
        digest_backend_kind=library.digest_backend_kind,
        rust_build=rust_build,
        _library=library,
    )


def prepare_native_digest_library(
    config: RustNativeDigestLibraryConfig | None = None,
) -> PreparedNativeDigestLibrary:
    resolved = config or RustNativeDigestLibraryConfig()
    manifest_path = (
        resolved.manifest_path.expanduser().resolve()
        if resolved.manifest_path is not None
        else default_rust_native_digest_manifest_path()
    )
    target_dir = (
        resolved.target_dir.expanduser().resolve()
        if resolved.target_dir is not None
        else None
    )

    if resolved.prepared_library_path is not None:
        return load_native_digest_library(
            resolved.prepared_library_path,
            invocation_kind=RUST_NATIVE_DIGEST_PREPARED_INVOCATION_KIND,
            manifest_path=manifest_path,
            target_dir=target_dir,
            rust_build=None,
        )

    cargo_api = _load_rust_tooling()
    try:
        request = cargo_api.module.CargoDynamicLibraryBuildRequest(
            manifest_path=manifest_path,
            library_name=resolved.library_name,
            target_dir=target_dir,
            cargo_path=resolved.cargo_path,
            cargo_home=resolved.cargo_home,
            release=resolved.release,
            timeout_s=resolved.build_timeout_s,
        )
        receipt = cargo_api.module.prepare_cargo_dynamic_library(request)
    except cargo_api.unavailable_error as exc:
        raise NativeDigestLibraryUnavailable(str(exc)) from exc

    build_receipt = receipt.to_mapping()
    if receipt.status != "succeeded":
        output = _build_error_output(build_receipt)
        raise NativeDigestLibraryUnavailable(
            "Rust native digest library preparation failed: "
            f"{output or receipt.status}"
        )

    library_path = receipt.artifact_path.expanduser().resolve()
    if not library_path.is_file():
        raise NativeDigestLibraryUnavailable(
            f"Rust native digest library was not built: {library_path.as_posix()}"
        )
    return load_native_digest_library(
        library_path,
        invocation_kind=(
            RUST_NATIVE_DIGEST_RELEASE_INVOCATION_KIND
            if resolved.release
            else RUST_NATIVE_DIGEST_DEBUG_INVOCATION_KIND
        ),
        manifest_path=manifest_path,
        target_dir=target_dir,
        rust_build=build_receipt,
    )


def default_rust_native_digest_manifest_path() -> Path:
    file_system_root = Path(__file__).resolve().parents[2]
    return file_system_root / "rust" / "aware_file_system_native" / "Cargo.toml"


@dataclass(frozen=True, slots=True)
class _RustToolingApi:
    module: ModuleType
    unavailable_error: type[Exception]


def _load_rust_tooling() -> _RustToolingApi:
    try:
        import rust_tooling
        from aware_code.language.toolchain import CodeToolchainUnavailable
    except ModuleNotFoundError as exc:
        raise NativeDigestLibraryUnavailable(
            "rust-tooling is not installed; install aware-file-system[native]"
        ) from exc
    return _RustToolingApi(
        module=rust_tooling,
        unavailable_error=CodeToolchainUnavailable,
    )


def _payload_pointer(view: memoryview) -> tuple[ctypes.c_void_p | None, tuple[object, ...]]:
    if view.nbytes == 0:
        return None, ()
    if view.readonly:
        copied = view.tobytes()
        buffer = ctypes.create_string_buffer(copied, len(copied))
        return ctypes.cast(buffer, ctypes.c_void_p), (buffer,)

    buffer_type = ctypes.c_ubyte * view.nbytes
    buffer = buffer_type.from_buffer(view)
    return ctypes.cast(buffer, ctypes.c_void_p), (buffer, view)


def _build_error_output(build_receipt: Mapping[str, Any]) -> str:
    result = build_receipt.get("result")
    if not isinstance(result, Mapping):
        return ""
    stderr = str(result.get("stderr") or "").strip()
    stdout = str(result.get("stdout") or "").strip()
    return stderr or stdout
