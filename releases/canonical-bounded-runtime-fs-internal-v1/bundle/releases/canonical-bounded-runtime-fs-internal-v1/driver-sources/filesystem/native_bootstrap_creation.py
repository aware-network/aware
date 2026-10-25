"""Explicit Linux creation selection/binding and detached capture receiving.

Only explicit private binding loads verified native code; it invokes no core
operation. Detached decoding remains IO-free. No live facade custody or cleanup
is implemented here. Neither symbolic captures nor detached values grant rights.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

from ._native_library import (
    load_exact_native_library,
    validate_native_library_selection,
)
from .confined_mutation import ConfinedMutationEffectState, _relative_path
from .retained_mutation import RetainedPhysicalEffect, RetainedPhysicalMutationRefusal

if TYPE_CHECKING:
    from .retained_bootstrap import RetainedBootstrapCreation

MAX_CAPTURE_BYTES = 8_388_608
OPERATIONS = (
    "retain",
    "phase",
    "observe_effects",
    "validate_current",
    "prepare_next_directory",
    "create_next_file",
    "finish",
    "release",
)
PHASES = ("issued", "preparing", "creating", "consumed", "retired")


@dataclass(frozen=True, slots=True)
class NativeBootstrapSelection:
    """Explicit exact code selection, not creation or cleanup authority."""

    library: Path
    sha256: str

    def __post_init__(self) -> None:
        validate_native_library_selection(self.library, self.sha256)


class _CreationFunction(Protocol):
    argtypes: list[object]
    restype: object

    def __call__(self, *arguments: object) -> int: ...


@dataclass(frozen=True, slots=True)
class _NativeCreationPorts:
    library: ctypes.CDLL
    retain: _CreationFunction
    step: _CreationFunction
    capture_info: _CreationFunction
    copy_capture: _CreationFunction
    destroy: _CreationFunction


def _load_creation_ports(selection: NativeBootstrapSelection) -> _NativeCreationPorts:
    """Bind only, without a constructor call or enrollment. No automatic retry.

    The library is held strongly by this binding. A future genuine constructor
    must additionally pin it for process lifetime before issuing any owner.
    Loading/binding errors remain original causes for that future outer receiver.
    """
    if type(selection) is not NativeBootstrapSelection:
        raise TypeError("original_native_bootstrap_selection_required")
    loaded = load_exact_native_library(
        selection.library,
        selection.sha256,
        platform_error="native_bootstrap_linux_required",
    )
    pointer = ctypes.c_void_p
    size = ctypes.c_size_t
    uint64 = ctypes.c_uint64
    signatures: tuple[tuple[str, list[object]], ...] = (
        ("retain", [pointer, size, ctypes.POINTER(pointer), ctypes.POINTER(uint64)]),
        ("step", [pointer, ctypes.c_uint32, uint64, pointer, ctypes.POINTER(uint64)]),
        (
            "capture_info",
            [
                pointer,
                uint64,
                ctypes.POINTER(uint64),
                ctypes.POINTER(ctypes.c_ubyte),
                ctypes.POINTER(ctypes.c_int32),
            ],
        ),
        (
            "copy_capture",
            [pointer, uint64, uint64, pointer, size, ctypes.POINTER(size)],
        ),
        ("destroy", [pointer, ctypes.c_uint32]),
    )
    ports = tuple(
        cast(_CreationFunction, getattr(loaded, f"aware_fs_bootstrap_{name}_v1"))
        for name, _ in signatures
    )
    for port, (_, arguments) in zip(ports, signatures, strict=True):
        port.argtypes = arguments
        port.restype = ctypes.c_int32
    return _NativeCreationPorts(
        loaded, ports[0], ports[1], ports[2], ports[3], ports[4]
    )


@dataclass(frozen=True, slots=True)
class NativeBootstrapRawOutput:
    name: str
    value: bytes | int | None


@dataclass(frozen=True, slots=True)
class NativeBootstrapCallEvidence:
    operation: str
    sequence: int
    call_attempted: bool
    native_status: int | None
    core_status: int | None
    outputs: tuple[NativeBootstrapRawOutput, ...]
    frame: bytes | None
    frame_sha256: str | None
    validated: bool
    python_cause: BaseException | None


class NativeBootstrapFailure(RetainedPhysicalMutationRefusal):
    """Original error family plus lossless receiving evidence, never authority."""

    def __init__(
        self,
        code: str,
        *,
        native_evidence: tuple[NativeBootstrapCallEvidence, ...],
        effects: tuple[RetainedPhysicalEffect, ...] = (),
        residual_scratch_paths: tuple[str, ...] = (),
        effects_complete: bool = False,
        cleanup_handle: RetainedBootstrapCreation | None = None,
    ) -> None:
        super().__init__(code, effects, residual_scratch_paths)
        self.native_evidence: tuple[NativeBootstrapCallEvidence, ...] = native_evidence
        self.effects_complete: bool = effects_complete
        self.cleanup_handle: RetainedBootstrapCreation | None = cleanup_handle
        self.capture_input: tuple[object, ...] | None = None


@dataclass(frozen=True, slots=True)
class _Resource:
    resource_id: int
    kind: str
    path: bytes | None
    acquisition: str
    release_attempted: bool | None
    release: str


@dataclass(frozen=True, slots=True)
class _Cause:
    role: str
    kind: str
    operation: str
    stage: str
    errno: int | None
    message: bytes | None


@dataclass(frozen=True, slots=True)
class _CoreEvidence:
    request_digest: str
    operation: str
    phase_before: str | None
    phase_after: str | None
    next_directory: int | None
    next_file: int | None
    effects: tuple[RetainedPhysicalEffect, ...] | None
    residual_scratch_paths: tuple[str, ...] | None
    capture_complete: bool
    resources: tuple[_Resource, ...] | None
    causes: tuple[_Cause, ...] | None


@dataclass(frozen=True, slots=True)
class _Refusal:
    code: str
    effects: tuple[RetainedPhysicalEffect, ...]
    residual_scratch_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _DecodedCapture:
    raw: bytes
    sha256: str
    sequence: int
    operation: str
    core_kind: str
    value: str | RetainedPhysicalEffect | tuple[RetainedPhysicalEffect, ...] | None
    failure: _Refusal | None
    evidence: _CoreEvidence


def _fields(value: object, names: str) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError("native_bootstrap_fields_invalid")
    row = cast(dict[str, object], value)
    if list(row) != names.split():
        raise ValueError("native_bootstrap_fields_invalid")
    return row


def _pairs(rows: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in rows:
        if key in result:
            raise ValueError("native_bootstrap_duplicate_key")
        result[key] = value
    return result


def _no_float(value: str) -> object:
    raise ValueError("native_bootstrap_noninteger_number:" + value)


def _no_layout_whitespace(raw: bytes) -> None:
    """The original encoder has no layout whitespace; string bytes stay exact."""
    quoted = escaped = False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                quoted = False
        elif byte == 0x22:
            quoted = True
        elif byte in (0x20, 0x09, 0x0A, 0x0D):
            raise ValueError("native_bootstrap_layout_whitespace_invalid")


def _text(value: object) -> str:
    if type(value) is not str or not value.isascii() or not value:
        raise ValueError("native_bootstrap_text_invalid")
    return value


def _choice(value: object, choices: tuple[str, ...]) -> str:
    text = _text(value)
    if text not in choices:
        raise ValueError("native_bootstrap_choice_invalid")
    return text


def _uint(value: object, maximum: int = (1 << 64) - 1) -> int:
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError("native_bootstrap_unsigned_invalid")
    return value


def _bool(value: object) -> bool:
    if type(value) is not bool:
        raise ValueError("native_bootstrap_boolean_invalid")
    return value


def _digest(value: object) -> str:
    if type(value) is not str or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        raise ValueError("native_bootstrap_digest_invalid")
    return value


def _bytes(value: object) -> bytes:
    row = _fields(value, "hex")
    encoded = row["hex"]
    if type(encoded) is not str or re.fullmatch(r"(?:[0-9a-f]{2})*", encoded) is None:
        raise ValueError("native_bootstrap_hex_invalid")
    return bytes.fromhex(encoded)


def _path(value: object) -> str:
    raw = _bytes(value)
    path = os.fsdecode(raw)
    if os.fsencode(path) != raw or b"\x00" in raw:
        raise ValueError("native_bootstrap_path_invalid")
    return _relative_path(path)


def _optional[T](value: object, decode: Callable[[object], T]) -> T | None:
    return None if value is None else decode(value)


def _array[T](value: object, decode: Callable[[object], T]) -> tuple[T, ...]:
    if type(value) is not list:
        raise ValueError("native_bootstrap_array_invalid")
    return tuple(decode(item) for item in cast(list[object], value))


def _effect(value: object) -> RetainedPhysicalEffect:
    row = _fields(
        value,
        "path kind state durability_confirmed mode before_digest after_digest after_identity",
    )
    kind = _choice(row["kind"], ("file", "directory"))
    state = ConfinedMutationEffectState(
        _choice(row["state"], ("none", "applied", "unknown"))
    )
    durable = _bool(row["durability_confirmed"])
    if durable and state is not ConfinedMutationEffectState.APPLIED:
        raise ValueError("native_bootstrap_durability_uncorrelated")
    identity = row["after_identity"]
    if identity is not None:
        if type(identity) is not list:
            raise ValueError("native_bootstrap_identity_invalid")
        pair = cast(list[object], identity)
        if len(pair) != 2:
            raise ValueError("native_bootstrap_identity_invalid")
        identity = (_uint(pair[0]), _uint(pair[1]))
    return RetainedPhysicalEffect(
        _path(row["path"]),
        kind,
        state,
        durable,
        _optional(row["mode"], lambda value: _uint(value, (1 << 32) - 1)),
        _optional(row["before_digest"], _digest),
        _optional(row["after_digest"], _digest),
        identity,
    )


def _resource(value: object) -> _Resource:
    row = _fields(value, "resource_id kind path acquisition release_attempted release")
    resource_id = _uint(row["resource_id"])
    kind = _choice(row["kind"], ("root", "parent", "scratch", "readback"))
    acquisition = _choice(row["acquisition"], ("not_acquired", "acquired", "unknown"))
    attempted = _optional(row["release_attempted"], _bool)
    release = _choice(row["release"], ("not_acquired", "held", "closed", "unknown"))
    required = {
        "closed": ("acquired", True),
        "held": ("acquired", False),
        "not_acquired": ("not_acquired", False),
    }
    if (
        resource_id == 0
        or release in required
        and (acquisition, attempted) != required[release]
    ):
        raise ValueError("native_bootstrap_resource_uncorrelated")
    return _Resource(
        resource_id,
        kind,
        _optional(row["path"], _bytes),
        acquisition,
        attempted,
        release,
    )


def _cause(value: object) -> _Cause:
    row = _fields(value, "role kind operation stage errno message")
    errno = row["errno"]
    if errno is not None and (
        type(errno) is not int or not -(1 << 31) <= errno < (1 << 31)
    ):
        raise ValueError("native_bootstrap_errno_invalid")
    return _Cause(
        _choice(row["role"], ("primary", "cleanup")),
        _choice(row["kind"], ("os", "panic", "internal")),
        _choice(row["operation"], OPERATIONS),
        _text(row["stage"]),
        errno,
        _optional(row["message"], _bytes),
    )


def _core_evidence(value: object, digest: str, operation: str) -> _CoreEvidence:
    row = _fields(
        value,
        "request_digest operation phase_before phase_after next_directory next_file effects residual_scratch_paths capture_complete resources causes",
    )
    if row["request_digest"] != digest or row["operation"] != operation:
        raise ValueError("native_bootstrap_evidence_uncorrelated")
    resources = _optional(row["resources"], lambda value: _array(value, _resource))
    if resources is not None and any(
        first.resource_id >= second.resource_id for first, second in pairwise(resources)
    ):
        raise ValueError("native_bootstrap_resource_order_invalid")
    return _CoreEvidence(
        digest,
        operation,
        _optional(row["phase_before"], lambda value: _choice(value, PHASES)),
        _optional(row["phase_after"], lambda value: _choice(value, PHASES)),
        _optional(row["next_directory"], lambda value: _uint(value, 64)),
        _optional(row["next_file"], lambda value: _uint(value, 3)),
        _optional(row["effects"], lambda value: _array(value, _effect)),
        _optional(row["residual_scratch_paths"], lambda value: _array(value, _path)),
        _bool(row["capture_complete"]),
        resources,
        _optional(row["causes"], lambda value: _array(value, _cause)),
    )


def _decode_value(
    value: object, operation: str, evidence: _CoreEvidence
) -> str | RetainedPhysicalEffect | tuple[RetainedPhysicalEffect, ...] | None:
    if operation == "retain":
        if _fields(value, "kind")["kind"] != "session_issued":
            raise ValueError("native_bootstrap_session_marker_invalid")
        return "session_issued"  # Symbolic only, never a live owner.
    if operation in {"validate_current", "release"}:
        if value is not None:
            raise ValueError("native_bootstrap_unit_invalid")
        return None
    if operation == "phase":
        phase = _choice(value, PHASES)
        if phase != evidence.phase_after:
            raise ValueError("native_bootstrap_phase_uncorrelated")
        return phase
    if operation in {"prepare_next_directory", "create_next_file"}:
        effect = _effect(value)
        expected_kind = "directory" if operation == "prepare_next_directory" else "file"
        if effect.kind != expected_kind:
            raise ValueError("native_bootstrap_operation_effect_invalid")
        if not evidence.effects or effect != evidence.effects[-1]:
            raise ValueError("native_bootstrap_effect_uncorrelated")
        return effect
    effects = _array(value, _effect)
    if effects != evidence.effects:
        raise ValueError("native_bootstrap_effects_uncorrelated")
    return effects


def _complete_invariants(operation: str, evidence: _CoreEvidence) -> None:
    before, after = evidence.phase_before, evidence.phase_after
    active = ("issued", "preparing", "creating")
    if operation == "retain":
        valid = before is None and after == "issued"
    elif operation in {"phase", "observe_effects"}:
        valid = before is not None and before == after
    elif operation == "validate_current":
        valid = before in active and after == before
    elif operation == "prepare_next_directory":
        valid = before in ("issued", "preparing") and after == "preparing"
    elif operation == "create_next_file":
        valid = before in active and after == "creating"
    elif operation == "finish":
        valid = before == "creating" and after == "consumed"
    else:  # An inert release preserves consumed/retired and historical unknowns.
        valid = before is not None and after == (
            before if before in ("consumed", "retired") else "retired"
        )
    if not valid:
        raise ValueError("native_bootstrap_complete_phase_invalid")
    directories, files = evidence.next_directory, evidence.next_file
    effects = evidence.effects
    if directories is None or files is None or effects is None:
        raise ValueError("native_bootstrap_complete_indices_unavailable")
    if (
        after == "issued"
        and (directories != 0 or files != 0)
        or after == "preparing"
        and (directories == 0 or files != 0)
        or after in ("creating", "consumed")
        and files == 0
    ):
        raise ValueError("native_bootstrap_complete_indices_invalid")
    if after != "retired" and (
        len(effects) != directories + files
        or any(effect.kind != "directory" for effect in effects[:directories])
        or any(effect.kind != "file" for effect in effects[directories:])
    ):
        raise ValueError("native_bootstrap_complete_effect_indices_invalid")


def decode_bootstrap_capture(
    raw: bytes,
    *,
    call: NativeBootstrapCallEvidence,
    request_digest: str,
    capture_length: int,
    capture_sha256: bytes,
) -> _DecodedCapture:
    """Validate detached bytes against explicit correlation, without enrolling custody.

    Even a successful result establishes neither original-return authenticity nor
    permission to advance. Callers retain the original call and provider outputs.
    """
    try:
        if type(call) is not NativeBootstrapCallEvidence:
            raise TypeError("exact_native_bootstrap_call_evidence_required")
        operation = _choice(call.operation, OPERATIONS)
        sequence = _uint(call.sequence, 255)
        if (
            (sequence == 0) != (operation == "retain")
            or sequence == 255
            and operation != "release"
        ):
            raise ValueError("native_bootstrap_sequence_invalid")
        if not _bool(call.call_attempted):
            raise ValueError("native_bootstrap_capture_without_call")
        if call.native_status is not None and (
            type(call.native_status) is not int or call.native_status not in {0, 1, 3}
        ):
            raise ValueError("native_bootstrap_transport_status_invalid")
        if type(call.core_status) is not int or call.core_status not in {0, 1, 3}:
            raise ValueError("native_bootstrap_core_status_unavailable")
        if call.native_status in {0, 1} and call.native_status != call.core_status:
            raise ValueError("native_bootstrap_status_uncorrelated")
        digest = _digest(request_digest)
        if (
            type(raw) is not bytes
            or not 0 < _uint(capture_length, MAX_CAPTURE_BYTES) == len(raw)
            or type(capture_sha256) is not bytes
            or len(capture_sha256) != 32
            or hashlib.sha256(raw).digest() != capture_sha256
        ):
            raise ValueError("native_bootstrap_capture_bytes_invalid")
        _no_layout_whitespace(raw)
        row = _fields(
            cast(
                object,
                json.loads(
                    raw.decode("utf-8"),
                    object_pairs_hook=_pairs,
                    parse_float=_no_float,
                    parse_constant=_no_float,
                ),
            ),
            "schema request_digest sequence operation core_kind value failure evidence",
        )
        if (
            row["schema"] != "aware.fs.bootstrap.capture.v1"
            or row["request_digest"] != digest
            or _uint(row["sequence"], 255) != sequence
            or row["operation"] != operation
        ):
            raise ValueError("native_bootstrap_capture_uncorrelated")
        kind = _choice(row["core_kind"], ("complete", "refused", "incomplete"))
        if {"complete": 0, "refused": 1, "incomplete": 3}[kind] != call.core_status:
            raise ValueError("native_bootstrap_kind_uncorrelated")
        evidence = _core_evidence(row["evidence"], digest, operation)
        failure = None
        if row["failure"] is not None:
            item = _fields(row["failure"], "code effects residual_scratch_paths")
            failure = _Refusal(
                _text(item["code"]),
                _array(item["effects"], _effect),
                _array(item["residual_scratch_paths"], _path),
            )
            if (
                evidence.effects is not None
                and evidence.effects != failure.effects
                or evidence.residual_scratch_paths is not None
                and evidence.residual_scratch_paths != failure.residual_scratch_paths
            ):
                raise ValueError("native_bootstrap_failure_uncorrelated")
        value = None
        if kind == "complete":
            if (
                failure is not None
                or not evidence.capture_complete
                or any(
                    field is None
                    for field in (
                        evidence.phase_after,
                        evidence.next_directory,
                        evidence.next_file,
                        evidence.effects,
                        evidence.residual_scratch_paths,
                        evidence.resources,
                        evidence.causes,
                    )
                )
            ):
                raise ValueError("native_bootstrap_complete_invalid")
            _complete_invariants(operation, evidence)
            value = _decode_value(row["value"], operation, evidence)
        elif row["value"] is not None or kind == "refused" and failure is None:
            raise ValueError("native_bootstrap_failure_value_invalid")
        return _DecodedCapture(
            raw,
            capture_sha256.hex(),
            sequence,
            operation,
            kind,
            value,
            failure,
            evidence,
        )
    except BaseException as primary:
        error = NativeBootstrapFailure(
            "native_bootstrap_interrupted"
            if isinstance(primary, (KeyboardInterrupt, SystemExit))
            else "native_bootstrap_capture_invalid",
            native_evidence=(call,)
            if type(call) is NativeBootstrapCallEvidence
            else (),
        )
        # Preserve all rejected original objects without presenting candidate
        # bytes as a verified frame or reconstructing a native exception.
        error.capture_input = (
            raw,
            call,
            request_digest,
            capture_length,
            capture_sha256,
        )
        raise error from primary
