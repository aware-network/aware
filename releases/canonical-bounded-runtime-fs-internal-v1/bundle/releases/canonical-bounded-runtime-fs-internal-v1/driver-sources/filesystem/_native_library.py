"""Shared exact-library acquisition, extracted from the original read loader.

Only explicit callers load code. This cooperative immutable-library profile is
not authentication against a hostile loader or concurrent binary replacement.
No operation symbol, native owner, retry, fallback or unload rail lives here.
"""

from __future__ import annotations

import ctypes
import hashlib
import re
import stat
import sys
from os import stat_result
from pathlib import Path


def validate_native_library_selection(library: Path, sha256: str) -> None:
    if type(library) is not type(Path()) or not library.is_absolute():
        raise ValueError("explicit_native_library_path_required")
    if type(sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise ValueError("exact_native_library_digest_required")


def load_exact_native_library(
    library: Path, sha256: str, *, platform_error: str
) -> ctypes.CDLL:
    """Verify original coordinates/bytes, load once, then recheck identity.

    Loading trusted native code can execute its initializers; this is not a
    claim that CDLL is effect-free. No FileSystem operation is invoked here.
    """
    validate_native_library_selection(library, sha256)
    if sys.platform != "linux":
        raise ValueError(platform_error)
    if library.resolve(strict=True) != library:
        raise ValueError("native_library_alias_refused")
    before = library.stat()
    if (
        not stat.S_ISREG(before.st_mode)
        or hashlib.sha256(library.read_bytes()).hexdigest() != sha256
    ):
        raise ValueError("native_library_digest_mismatch")
    loaded = ctypes.CDLL(str(library))
    after = library.stat()

    def identity(value: stat_result) -> tuple[int, int, int, int, int, int]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if identity(before) != identity(after):
        raise ValueError("native_library_changed")
    return loaded
