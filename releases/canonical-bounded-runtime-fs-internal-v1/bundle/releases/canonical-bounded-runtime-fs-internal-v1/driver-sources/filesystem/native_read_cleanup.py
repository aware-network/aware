"""Explicit Linux receiving over the original read engine; never a fallback rail.

The selected library is trusted native code in a cooperative immutable-library
profile. Hash and file-identity checks are not protection from a hostile loader
or concurrent binary replacement. No native allocation or handle escapes.
"""

from __future__ import annotations

import ctypes
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import confined_mutation as owner
from ._native_library import (
    load_exact_native_library,
    validate_native_library_selection,
)

METADATA_CAPACITY = 131072


@dataclass(frozen=True, slots=True)
class NativeReadSelection:
    """Caller-selected exact library, not ambient discovery or write authority."""

    library: Path
    sha256: str

    def __post_init__(self) -> None:
        validate_native_library_selection(self.library, self.sha256)


@dataclass(frozen=True, slots=True)
class NativeReadEvidence:
    """Raw initialized outputs, including rejected or incomplete native reports."""

    root: object
    path: object
    maximum_bytes: object
    invoked: bool
    status: int | None
    content: bytes
    metadata: bytes
    content_length: int
    metadata_length: int
    root_bytes: bytes | None = None
    path_bytes: bytes | None = None


class NativeReadCause(RuntimeError):
    """Detached native cause, deliberately not a reconstructed Python OSError."""

    def __init__(self, value: dict[str, Any], evidence: NativeReadEvidence) -> None:
        self.value = value
        self.evidence = evidence
        super().__init__(value["message"])


def _mapping(value: Any, keys: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(keys.split()):
        raise ValueError("native_read_fields_invalid")
    return value


def _pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in rows:
        if key in result:
            raise ValueError("native_read_duplicate_key")
        result[key] = value
    return result


def _nonfinite(value: str) -> Any:
    raise ValueError("native_read_nonfinite:" + value)


def _decode(
    evidence: NativeReadEvidence, root: str, path: str, maximum: int
) -> tuple[
    owner.ConfinedFileObservation | None, owner.ConfinedFileReadCleanup, Any, Any
]:
    if type(evidence.status) is not int or evidence.status not in {0, 1, 2, 3}:
        raise ValueError("native_read_status_invalid")
    row = _mapping(
        json.loads(
            evidence.metadata.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=_nonfinite,
        ),
        "schema root_locator path maximum_bytes status observation cleanup failure native_cause",
    )
    if (
        row["schema"] != "aware.fs.read_cleanup.v1"
        or type(row["status"]) is not int
        or row["status"] != evidence.status
        or type(row["maximum_bytes"]) is not int
        or row["maximum_bytes"] != maximum
        or row["root_locator"] != root
        or row["path"] != path
    ):
        raise ValueError("native_read_correlation_failed")
    cleanup_row = _mapping(
        row["cleanup"],
        "outcome acquired_count release_attempted_count closed_count diagnostics",
    ).copy()
    if type(cleanup_row["diagnostics"]) is not list:
        raise ValueError("native_read_diagnostics_invalid")
    cleanup_row["diagnostics"] = tuple(cleanup_row["diagnostics"])
    cleanup = owner.ConfinedFileReadCleanup(**cleanup_row)
    observation = None
    if row["observation"] is not None:
        observed = _mapping(
            row["observation"],
            "path outcome exists content_digest size_bytes content_length error_code",
        ).copy()
        length = observed.pop("content_length")
        if (
            type(length) is not int
            or length != len(evidence.content)
            or not 0 <= length <= maximum
            or observed["path"] != path
            or observed["size_bytes"] is not None
            and type(observed["size_bytes"]) is not int
        ):
            raise ValueError("native_read_body_invalid")
        if type(observed["outcome"]) is not str:
            raise ValueError("native_read_outcome_invalid")
        observed["outcome"] = owner.ConfinedObservationOutcome(observed["outcome"])
        observed["content"] = evidence.content if observed["exists"] is True else None
        if observed["exists"] is not True and evidence.content:
            raise ValueError("native_read_absent_body")
        if observed["error_code"] is not None:
            owner._read_text(observed["error_code"], 1024)
        observation = owner.ConfinedFileObservation(**observed)
        if observation.exists and (
            cleanup.outcome == "not_acquired"
            or cleanup.acquired_count is not None
            and cleanup.acquired_count < 2
        ):
            raise ValueError("native_read_acquisition_uncorrelated")
    elif evidence.content:
        raise ValueError("native_read_unbound_body")
    failure, cause = row["failure"], row["native_cause"]
    if evidence.status == 0:
        if failure is not None or cause is not None or observation is None:
            raise ValueError("native_read_success_invalid")
    else:
        failure = _mapping(failure, "code stage cause_kind root_locator path")
        for name in ("code", "stage", "cause_kind"):
            owner._read_text(failure[name], 1024)
        if (
            failure["root_locator"] not in (None, root)
            or failure["path"] not in (None, path)
            or observation is not None
            and (failure["root_locator"] != root or failure["path"] != path)
        ):
            raise ValueError("native_read_failure_uncorrelated")
        if evidence.status in {1, 2} and cause is None:
            raise ValueError("native_read_cause_missing")
        if cause is not None:
            cause = _mapping(cause, "kind stage errno message")
            if (
                type(cause["kind"]) is not str
                or cause["kind"] not in {"os", "panic", "internal"}
                or type(cause["stage"]) is not str
                or re.fullmatch(r"[A-Za-z0-9_]{1,128}", cause["stage"]) is None
                or cause["stage"] != failure["stage"]
                or cause["errno"] is not None
                and (
                    type(cause["errno"]) is not int
                    or not -(2**31) <= cause["errno"] < 2**31
                )
                or type(cause["message"]) is not str
                or len(cause["message"].encode("utf-8")) > 4096
                or failure["cause_kind"]
                != {
                    "os": "NativeIoError",
                    "panic": "NativePanic",
                    "internal": "NativeValidationError",
                }[cause["kind"]]
            ):
                raise ValueError("native_read_cause_invalid")
    if evidence.status == 2 and (
        observation is not None or cleanup.outcome != "not_acquired"
    ):
        raise ValueError("native_read_pre_io_evidence_invalid")
    return observation, cleanup, failure, cause


def _load(selection: NativeReadSelection) -> Any:
    if type(selection) is not NativeReadSelection:
        raise TypeError("original_native_read_selection_required")
    loaded = load_exact_native_library(
        selection.library, selection.sha256, platform_error="native_read_linux_required"
    )
    port = loaded.aware_file_system_read_with_cleanup_v1
    port.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(ctypes.c_size_t),
    ]
    port.restype = ctypes.c_int32
    return port


def observe_native_read(
    *, root: Path, path: str, maximum_bytes: int, selection: NativeReadSelection
) -> owner.ConfinedFileObservationWithCleanup:
    """One native call. Every local/native failure keeps the original outer type."""
    root_locator = normalized_path = None
    invoked = False
    status = None
    body = metadata = None
    body_length, metadata_length = ctypes.c_size_t(), ctypes.c_size_t()
    observation = None
    cleanup = owner.ConfinedFileReadCleanup("not_acquired", 0, 0, 0)
    evidence = NativeReadEvidence(
        root, path, maximum_bytes, False, None, b"", b"", 0, 0
    )
    stage = "validation"
    try:
        if not isinstance(root, Path):
            raise TypeError("explicit_path_root_required")
        root_text = str(root)
        owner._read_root(root_text)
        root_locator = root_text
        normalized_path = owner._saved_read_path(path)
        if (
            type(maximum_bytes) is not int
            or not 0 < maximum_bytes <= owner.DEFAULT_CONFINED_MUTATION_MAX_BYTES
        ):
            raise ValueError("invalid_read_byte_bound")
        stage = "native_selection"
        port = _load(selection)
        root_bytes, path_bytes = (
            root_text.encode("utf-8"),
            normalized_path.encode("utf-8"),
        )
        body = ctypes.create_string_buffer(maximum_bytes)
        metadata = ctypes.create_string_buffer(METADATA_CAPACITY)
        stage = "native_dispatch"
        invoked = True
        try:
            status = port(
                root_bytes,
                len(root_bytes),
                path_bytes,
                len(path_bytes),
                maximum_bytes,
                body,
                maximum_bytes,
                metadata,
                METADATA_CAPACITY,
                ctypes.byref(body_length),
                ctypes.byref(metadata_length),
            )
        finally:
            # A Python interrupt delivered on return does not discard initialized
            # buffers or repeat native IO. Missing return status stays unknown.
            evidence = NativeReadEvidence(
                root,
                path,
                maximum_bytes,
                invoked,
                status,
                ctypes.string_at(body, min(body_length.value, maximum_bytes)),
                ctypes.string_at(
                    metadata, min(metadata_length.value, METADATA_CAPACITY)
                ),
                body_length.value,
                metadata_length.value,
                root_bytes,
                path_bytes,
            )
        stage = "native_receiving"
        if (
            body_length.value > maximum_bytes
            or metadata_length.value > METADATA_CAPACITY
        ):
            raise ValueError("native_read_output_length_invalid")
        if status == 2 and not evidence.metadata and not evidence.content:
            # The ABI establishes pre-IO refusal, but supplies no particular
            # reason. Do not guess UTF-8 versus capacity or fabricate a cause.
            error = owner.ConfinedFileObservationError(
                "filesystem_native_read_pre_io_refused",
                stage="native_receiving",
                cause_kind="NativePreIoRefusal",
                root_locator=root_locator,
                path=normalized_path,
                observation=None,
                cleanup=cleanup,
            )
            error.native_evidence = evidence
            raise error
        observation, cleanup, failure, cause = _decode(
            evidence, root_text, normalized_path, maximum_bytes
        )
        if status != 0:
            error = owner.ConfinedFileObservationError(
                failure["code"],
                stage=failure["stage"],
                cause_kind=failure["cause_kind"],
                root_locator=failure["root_locator"],
                path=failure["path"],
                observation=observation,
                cleanup=cleanup,
            )
            error.native_evidence = evidence
            if cause is not None:
                raise error from NativeReadCause(cause, evidence)
            raise error
        if observation is None:
            raise ValueError("native_read_observation_missing")
        return owner.ConfinedFileObservationWithCleanup(
            observation, root_text, normalized_path, cleanup
        )
    except owner.ConfinedFileObservationError:
        raise
    except BaseException as primary:
        if invoked and stage in {"native_dispatch", "native_receiving"}:
            # A rejected report is never partially promoted by a failing decoder.
            observation = None
            cleanup = owner.ConfinedFileReadCleanup(
                "unknown", None, None, None, ("native_capture_unverified",)
            )
        error = owner.ConfinedFileObservationError(
            "filesystem_native_read_failed",
            stage=stage,
            cause_kind=owner._cause_kind(primary),
            root_locator=root_locator,
            path=normalized_path,
            observation=observation,
            cleanup=cleanup,
        )
        error.native_evidence = evidence
        raise error from primary
