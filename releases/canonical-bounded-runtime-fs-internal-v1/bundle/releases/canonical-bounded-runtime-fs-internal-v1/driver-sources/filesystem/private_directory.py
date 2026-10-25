"""Private-directory custody and detached, non-authorizing owner evidence."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
import sys
import threading
import types
import weakref
from _thread import RLock
from dataclasses import dataclass, field, fields, replace
from enum import StrEnum
from pathlib import Path
from typing import Literal, Union, get_args, get_origin, get_type_hints
from uuid import uuid4

from . import confined_mutation as native
from . import private_namespace_values as namespace_values
from . import retained_file_sequence as sequence
from .confined_entry import (
    ConfinedEntryObservation,
    EntryAncestorBookends,
    EntryCursorCleanup,
    EntryRequestSnapshot,
    EntryResource,
    EntryStat,
)
from .confined_mutation import (
    ConfinedFileObservation,
    ConfinedFileObservationWithCleanup,
    ConfinedFileReadCleanup,
)
from .private_namespace_values import (
    PrivateNamespaceAncestorPrefix,
    PrivateNamespaceBinding,
    PrivateNamespaceCleanup,
    PrivateNamespaceControlObservation,
    PrivateNamespaceEntryFailure,
    PrivateNamespaceEntryPrefix,
    PrivateNamespaceFootprint,
    PrivateNamespaceInventoryMember,
    PrivateNamespaceInventoryObservation,
    PrivateNamespaceLimits,
    PrivateNamespacePhysicalEffect,
    PrivateNamespaceRefusalEvidence,
    PrivateNamespaceTransactionObservation,
)
from .retained_file_sequence import (
    ConfinedSequenceBinding,
    ConfinedSequenceCleanup,
    ConfinedSequenceObservation,
    ConfinedSequencePrimaryFailure,
    ConfinedSequenceRefusalEvidence,
    ConfinedSequenceResourceEvidence,
    ConfinedSequenceStepResult,
)

PrivacyProfile = Literal["effective_user_private_namespace_v1"]
PrivateDirectoryPhase = Literal["active", "retired", "released"]


@dataclass(frozen=True, slots=True)
class PrivateDirectoryBinding:
    provider_ref: str
    provider_generation: str
    directory_ref: str
    root_locator: str
    device: int
    inode: int
    effective_uid: int
    owner_uid: int
    mode: int
    privacy_profile: PrivacyProfile
    process_id: int
    thread_id: int


@dataclass(frozen=True, slots=True)
class PrivateRootObservation:
    state: Literal["observed", "unavailable"]
    device: int | None
    inode: int | None
    effective_uid: int | None
    owner_uid: int | None
    mode: int | None
    ctime_ns: int | None


@dataclass(frozen=True, slots=True)
class PrivateDirectoryObservation:
    binding: PrivateDirectoryBinding | None
    phase: PrivateDirectoryPhase
    root: PrivateRootObservation
    validation_ordinal: int
    active_sequence_ref: str | None
    resources: tuple[ConfinedSequenceResourceEvidence, ...]
    primary_failure: ConfinedSequencePrimaryFailure
    ledger_complete: bool


@dataclass(frozen=True, slots=True)
class PrivateSequenceBinding:
    private_sequence_ref: str
    directory: PrivateDirectoryBinding
    sequence: ConfinedSequenceBinding


@dataclass(frozen=True, slots=True)
class PrivateSequenceObservation:
    binding: PrivateSequenceBinding | None
    directory: PrivateDirectoryObservation
    sequence: ConfinedSequenceObservation


@dataclass(frozen=True, slots=True)
class PrivateSequenceStepResult:
    binding: PrivateSequenceBinding
    directory_before: PrivateDirectoryObservation
    directory_after: PrivateDirectoryObservation
    sequence: ConfinedSequenceStepResult


@dataclass(frozen=True, slots=True)
class PrivateSequenceCleanup:
    binding: PrivateSequenceBinding | None
    directory: PrivateDirectoryObservation
    sequence: ConfinedSequenceCleanup


@dataclass(frozen=True, slots=True)
class PrivateDirectoryCleanup:
    observation: PrivateDirectoryObservation
    release: Literal["confirmed", "failed", "unknown"]


@dataclass(frozen=True, slots=True)
class PrivateFileReadResult:
    directory_before: PrivateDirectoryObservation
    directory_after: PrivateDirectoryObservation
    original: ConfinedFileObservationWithCleanup


@dataclass(frozen=True, slots=True)
class PrivateReadFailure:
    code: str
    stage: str
    cause_kind: str
    root_locator: str | None
    path: str | None
    observation: ConfinedFileObservation | None
    cleanup: ConfinedFileReadCleanup


@dataclass(frozen=True, slots=True)
class PrivateDirectoryRefusalEvidence:
    code: str
    cause_type: str | None
    stage: str
    directory: PrivateDirectoryObservation | None
    sequence: ConfinedSequenceRefusalEvidence | None
    read: ConfinedFileObservationWithCleanup | PrivateReadFailure | None
    cleanup: PrivateDirectoryCleanup | PrivateSequenceCleanup | None
    primary_failure: ConfinedSequencePrimaryFailure
    ledger_complete: bool


class PrivateDirectoryRefusal(RuntimeError):
    def __init__(self, code: str, *, evidence: PrivateDirectoryRefusalEvidence):
        self.code = code
        self.evidence = evidence
        super().__init__(code)


type PrivateDirectoryValue = (
    PrivateDirectoryBinding
    | PrivateRootObservation
    | PrivateDirectoryObservation
    | PrivateSequenceBinding
    | PrivateSequenceObservation
    | PrivateSequenceStepResult
    | PrivateSequenceCleanup
    | PrivateDirectoryCleanup
    | PrivateFileReadResult
    | PrivateReadFailure
    | PrivateDirectoryRefusalEvidence
    | PrivateNamespaceControlObservation
    | PrivateNamespaceLimits
    | PrivateNamespaceBinding
    | PrivateNamespacePhysicalEffect
    | PrivateNamespaceInventoryMember
    | PrivateNamespaceInventoryObservation
    | PrivateNamespaceFootprint
    | PrivateNamespaceTransactionObservation
    | PrivateNamespaceCleanup
    | PrivateNamespaceAncestorPrefix
    | PrivateNamespaceEntryPrefix
    | PrivateNamespaceEntryFailure
    | PrivateNamespaceRefusalEvidence
    | EntryRequestSnapshot
    | EntryStat
    | EntryAncestorBookends
    | EntryResource
    | EntryCursorCleanup
    | ConfinedEntryObservation
)

_PRIVATE_TYPES = (
    PrivateDirectoryBinding,
    PrivateRootObservation,
    PrivateDirectoryObservation,
    PrivateSequenceBinding,
    PrivateSequenceObservation,
    PrivateSequenceStepResult,
    PrivateSequenceCleanup,
    PrivateDirectoryCleanup,
    PrivateFileReadResult,
    PrivateReadFailure,
    PrivateDirectoryRefusalEvidence,
)
_PRIVATE_WIRES = (
    "private-directory-binding",
    "private-root-observation",
    "private-directory-observation",
    "private-sequence-binding",
    "private-sequence-observation",
    "private-sequence-step-result",
    "private-sequence-cleanup",
    "private-directory-cleanup",
    "private-file-read-result",
    "private-read-failure",
    "private-directory-refusal-evidence",
)
_READ_TYPES = (
    ConfinedFileObservation,
    ConfinedFileReadCleanup,
    ConfinedFileObservationWithCleanup,
)
_READ_WIRES = (
    "confined-file-observation",
    "confined-file-read-cleanup",
    "confined-file-observation-with-cleanup",
)
_NAMESPACE_TYPES = tuple(
    getattr(namespace_values, name) for name in namespace_values.__all__
)
_NAMESPACE_WIRES = (
    "private-namespace-control",
    "private-namespace-limits",
    "private-namespace-binding",
    "private-namespace-physical-effect",
    "private-namespace-inventory-member",
    "private-namespace-inventory",
    "private-namespace-footprint",
    "private-namespace-observation",
    "private-namespace-cleanup",
    "private-namespace-ancestor-prefix",
    "private-namespace-entry-prefix",
    "private-namespace-entry-failure",
    "private-namespace-refusal",
)
_ENTRY_TYPES = (
    EntryRequestSnapshot,
    EntryStat,
    EntryAncestorBookends,
    EntryResource,
    EntryCursorCleanup,
    ConfinedEntryObservation,
)
_ENTRY_WIRES = (
    "entry-request-snapshot",
    "entry-stat",
    "entry-ancestor-bookends",
    "entry-resource",
    "entry-cursor-cleanup",
    "confined-entry-observation",
)
_CODEC_TYPES = _PRIVATE_TYPES + _NAMESPACE_TYPES + _ENTRY_TYPES
# Bind original private types only after their declarations exist. This avoids
# an import cycle and makes public facade type hints resolve to original owners.
for _private_kind in _PRIVATE_TYPES:
    setattr(namespace_values, _private_kind.__name__, _private_kind)
_WIRES = dict(sequence._WIRE_IDS)
_WIRES.update(
    {
        cls: "aware.file-system." + name + ".v1"
        for cls, name in zip(_PRIVATE_TYPES, _PRIVATE_WIRES, strict=True)
    }
)
_WIRES.update(
    {
        cls: "aware.file-system." + name + ".v1"
        for cls, name in zip(
            _NAMESPACE_TYPES + _ENTRY_TYPES,
            _NAMESPACE_WIRES + _ENTRY_WIRES,
            strict=True,
        )
    }
)
_WIRES.update(
    {
        cls: "aware.file-system." + name + ".v1"
        for cls, name in zip(_READ_TYPES, _READ_WIRES, strict=True)
    }
)
_BY_WIRE = {wire: cls for cls, wire in _WIRES.items()}
_SCHEMAS = {
    cls: (
        tuple(
            (f.name, vars(cls)[f.name], get_type_hints(cls, localns=globals())[f.name])
            for f in fields(cls)
        ),
        cls.__init__,
        cls.__init__.__code__,
        getattr(cls, "__post_init__", None),
        getattr(getattr(cls, "__post_init__", None), "__code__", None),
        cls.__new__,
        cls.__getattribute__,
    )
    for cls in _WIRES
}
_EQUALITY = {cls: (cls.__eq__, getattr(cls.__eq__, "__code__", None)) for cls in _WIRES}
_ENTRY_STAT_VALUES = (EntryStat.values, EntryStat.values.__code__)
_SEQUENCE_ENCODER = sequence.confined_sequence_value_to_payload
_SEQUENCE_ENCODER_CODE = _SEQUENCE_ENCODER.__code__
_OWNER_HELPERS = {
    (module, name): (getattr(module, name), getattr(module, name).__code__)
    for module, name in (
        (sequence, "_confined_sequence_value_from_payload"),
        (native, "_confined_read_value_to_payload"),
        (native, "_confined_read_value_from_payload"),
        (native, "_read_text"),
        (native, "_read_root"),
        (native, "_saved_read_path"),
    )
}
_BYTE_WIRE = "aware.file-system.content-bytes.v1"
_INVENTORY_STAT_WIRE = "aware.file-system.inventory-entry-stat.v1"
_MAX_WIRE = 32 * 1024 * 1024
_MAX_PRIVATE = 1024 * 1024
_MAX_NATIVE = 2 * 1024 * 1024
_MAX_BYTES = 16 * 1024 * 1024


class _Invalid(ValueError):
    pass


class _Capacity(ValueError):
    pass


class _Budget:
    def __init__(self):
        self.wire = _MAX_WIRE
        self.private = _MAX_PRIVATE
        self.native = _MAX_NATIVE
        self.content = _MAX_BYTES
        self.nodes = 0
        self.native_nodes = 0
        self.active = set()

    def visit(self, depth, local_depth=None):
        self.nodes += 1
        if local_depth is not None:
            self.native_nodes += 1
        if (
            depth > 128
            or self.nodes > 524288
            or self.native_nodes > 262144
            or local_depth is not None
            and local_depth > 64
        ):
            raise _Capacity("structure")

    def charge(self, amount, group):
        self.wire -= amount
        if group != "content":
            setattr(self, group, getattr(self, group) - amount)
        if min(self.wire, self.private, self.native) < 0:
            raise _Capacity("metadata")

    def scalar(self, value, group):
        remaining = min(self.wire, getattr(self, group))
        if type(value) is str:
            # Count exact ensure_ascii=False JSON bytes before allocating an
            # escaped/UTF-8 copy. Code points in the surrogate range are not
            # valid UTF-8 input, even if a JSON parser preserved them.
            size = 2
            if len(value) + size > remaining:
                raise _Capacity("text")
            for character in value:
                point = ord(character)
                if 0xD800 <= point <= 0xDFFF:
                    raise _Invalid("invalid_utf8")
                size += (
                    2
                    if character in '\\"\b\f\n\r\t'
                    else 6
                    if point < 32
                    else 1
                    if point < 128
                    else 2
                    if point < 2048
                    else 3
                    if point < 65536
                    else 4
                )
                if size > remaining:
                    raise _Capacity("text")
        else:
            size = len(json.dumps(value, allow_nan=False, separators=(",", ":")))
        self.charge(size, group)


def _auth(cls):
    rows, init, code, post, post_code, new, getattribute = _SCHEMAS[cls]
    if (
        vars(sys.modules[cls.__module__]).get(cls.__name__) is not cls
        or cls.__init__ is not init
        or init.__code__ is not code
        or getattr(cls, "__post_init__", None) is not post
        or post is not None
        and post.__code__ is not post_code
        or any(vars(cls).get(name) is not slot for name, slot, _ in rows)
        or cls.__new__ is not new
        or cls.__getattribute__ is not getattribute
        or cls.__eq__ is not _EQUALITY[cls][0]
        or getattr(cls.__eq__, "__code__", None) is not _EQUALITY[cls][1]
        or cls in _NAMESPACE_TYPES + _ENTRY_TYPES
        and globals().get(cls.__name__) is not cls
        or cls is EntryStat
        and (
            EntryStat.values is not _ENTRY_STAT_VALUES[0]
            or EntryStat.values.__code__ is not _ENTRY_STAT_VALUES[1]
        )
    ):
        raise _Invalid("original_type_changed")
    return rows


def _envelope(source):
    if (
        type(source) is not dict
        or any(type(key) is not str for key in source)
        or set(source) != {"contract", "value"}
        or type(source["contract"]) is not str
        or type(source["value"]) is not dict
        or any(type(key) is not str for key in source["value"])
    ):
        raise _Invalid("envelope")
    return source["contract"], source["value"]


def _owner_helper(module, name):
    original, code = _OWNER_HELPERS[module, name]
    if getattr(module, name) is not original or original.__code__ is not code:
        raise _Invalid("native_helper_changed")
    return original


def _matches(value, annotation, decode, owner=None):
    origin = get_origin(annotation)
    if origin is Literal:
        return any(
            type(value) is type(item) and value == item for item in get_args(annotation)
        )
    if origin is tuple:
        return type(value) is (list if decode else tuple)
    if annotation is type(None):
        return value is None
    if annotation in _SCHEMAS:
        if not decode:
            return type(value) is annotation
        return (
            type(value) is dict
            and all(type(key) is str for key in value)
            and type(value.get("contract")) is str
            and (
                value.get("contract") == _WIRES[annotation]
                or annotation is EntryStat
                and owner == "namespace_inventory"
                and value.get("contract") == _INVENTORY_STAT_WIRE
            )
        )
    if annotation is bytes:
        return type(value) is dict if decode else type(value) is bytes
    return type(value) is annotation


def _content(value, budget, decode):
    if decode:
        wire, data = _envelope(value)
        if wire != _BYTE_WIRE or set(data) != {
            "encoding",
            "byte_count",
            "content_sha256",
            "data",
        }:
            raise _Invalid("bytes_envelope")
        count, encoded, digest = (
            data["byte_count"],
            data["data"],
            data["content_sha256"],
        )
        if (
            type(count) is not int
            or count < 0
            or type(encoded) is not str
            or type(digest) is not str
            or type(data["encoding"]) is not str
            or data["encoding"] != "base64"
            or len(digest) != 71
            or not digest.startswith("sha256:")
            or any(c not in "0123456789abcdef" for c in digest[7:])
        ):
            raise _Invalid("bytes_fields")
        if count > budget.content:
            raise _Capacity("content")
        if len(encoded) != 4 * ((count + 2) // 3) or not encoded.isascii():
            raise _Invalid("bytes_length")
    else:
        count = len(value)
        if count > budget.content:
            raise _Capacity("content")
        digest = "sha256:" + hashlib.sha256(value).hexdigest()
        encoded = None
    budget.content -= count
    skeleton = {
        "contract": _BYTE_WIRE,
        "value": {
            "encoding": "base64",
            "byte_count": count,
            "content_sha256": digest,
            "data": "",
        },
    }
    budget.charge(
        len(json.dumps(skeleton, separators=(",", ":"), ensure_ascii=False).encode()),
        "private",
    )
    budget.charge(4 * ((count + 2) // 3), "content")
    if decode:
        assert encoded is not None  # Already checked as exact str above.
        decoded = base64.b64decode(encoded, validate=True)
        if (
            len(decoded) != count
            or "sha256:" + hashlib.sha256(decoded).hexdigest() != digest
            or base64.b64encode(decoded).decode("ascii") != encoded
        ):
            raise _Invalid("bytes_integrity")
        return decoded
    skeleton["value"]["data"] = base64.b64encode(value).decode("ascii")
    return skeleton


def _invariants(cls, value):
    rows, _, _, post, _, _, _ = _SCHEMAS[cls]
    if cls in _ENTRY_TYPES or cls in _NAMESPACE_TYPES:
        for kind in _ENTRY_TYPES:
            _auth(kind)
    if post is not None:
        post(value)
    if cls is PrivateReadFailure:
        # Preserve the original error's pure field rules without constructing
        # an exception (or acquiring its live-ledger/traceback responsibilities).
        text = _owner_helper(native, "_read_text")
        for name in ("code", "stage", "cause_kind"):
            text(getattr(value, name), 1024)
        if value.root_locator is not None:
            _owner_helper(native, "_read_root")(value.root_locator)
        if value.path is not None:
            _owner_helper(native, "_saved_read_path")(value.path)
    # Metadata assertions describe observed history, not current authority.
    for name, slot, annotation in rows:
        item = slot.__get__(value, cls)
        if (
            annotation is int
            and item < 0
            and not (cls is EntryStat and name in {"mtime_ns", "ctime_ns"})
        ):
            raise _Invalid("negative_integer")
        if annotation is str and (not item or len(item.encode("utf-8")) > 4096):
            raise _Invalid("text_field")
    if cls is PrivateDirectoryBinding and (
        value.mode != 0o700
        or value.owner_uid != value.effective_uid
        or type(value.root_locator) is not str
        or not value.root_locator.startswith("/")
        or len(value.root_locator.encode()) > 4096
    ):
        raise _Invalid("private_binding")
    if cls is PrivateDirectoryObservation and value.validation_ordinal > 65536:
        raise _Invalid("validation_ordinal")
    if (
        cls is PrivateRootObservation
        and value.state == "observed"
        and any(
            getattr(value, name) is None
            for name in (
                "device",
                "inode",
                "effective_uid",
                "owner_uid",
                "mode",
                "ctime_ns",
            )
        )
    ):
        raise _Invalid("observed_root_fields")
    if cls in _ENTRY_TYPES:
        _entry_invariants(cls, value)
    if cls in _NAMESPACE_TYPES:
        _namespace_invariants(cls, value)


def _entry_name(value, maximum=1024):
    # Original roster spelling is observable, not necessarily NFC or public-safe.
    if (
        type(value) is not str
        or not value
        or value in {".", ".."}
        or "/" in value
        or "\0" in value
    ):
        raise _Invalid("entry_name")
    if len(value.encode("utf-8", errors="strict")) > maximum:
        raise _Invalid("entry_name_bytes")


def _entry_invariants(cls, value):
    text = _owner_helper(native, "_read_text")
    root = _owner_helper(native, "_read_root")
    path = _owner_helper(native, "_saved_read_path")
    if cls is EntryRequestSnapshot:
        root(value.root)
        if value.path is not None:
            path(value.path)
        for name, cap in (
            ("maximum_children", 20000),
            ("maximum_name_bytes", 4096),
            ("maximum_roster_bytes", 1048576),
        ):
            if not 0 < getattr(value, name) <= cap:
                raise _Invalid("entry_request_limit")
    elif cls is EntryAncestorBookends:
        root(value.path)
    elif cls is EntryResource:
        text(value.resource_ref, 4096)
        text(value.kind, 1024)
        if value.path is not None:
            # Resource coordinates include absolute ancestor walks.
            (root if value.path.startswith("/") else path)(value.path)
        if value.acquisition_state not in {"not_attempted", "acquired", "unknown"}:
            raise _Invalid("entry_resource_acquisition")
        if value.closed is True and (
            value.close_spent is not True or value.acquisition_state != "acquired"
        ):
            raise _Invalid("entry_resource_close")
    elif cls is ConfinedEntryObservation:
        root(value.root_locator)
        if value.path is not None:
            path(value.path)
        text(value.observation_ref, 4096)
        request = value.request_snapshot
        for names in (value.children_before, value.children_after):
            if names is not None:
                if len(names) > request.maximum_children or len(set(names)) != len(
                    names
                ):
                    raise _Invalid("entry_roster_count")
                size = 0
                for name in names:
                    _entry_name(name, request.maximum_name_bytes)
                    size += len(name.encode("utf-8"))
                if size > request.maximum_roster_bytes:
                    raise _Invalid("entry_roster_bytes")
        if (
            value.link_text is not None
            and not 0
            < len(value.link_text.encode("utf-8"))
            <= request.maximum_name_bytes
        ):
            raise _Invalid("entry_link_text")


def _namespace_invariants(cls, value):
    text = _owner_helper(native, "_read_text")
    root = _owner_helper(native, "_read_root")
    path = _owner_helper(native, "_saved_read_path")
    for name in (
        "transaction_ref",
        "observation_ref",
        "effect_ref",
        "provider_generation",
        "active_sequence_ref",
        "resource_ref",
        "parent_resource_ref",
    ):
        item = getattr(value, name, None)
        if item is not None:
            text(item, 4096)
    if cls is PrivateNamespaceLimits:
        for name, cap in (
            ("inventory_entries", 4096),
            ("name_bytes", 1024),
            ("roster_bytes", 1048576),
            ("inventory_wire_bytes", 1048576),
            ("member_bytes", 1048576),
            ("owned_descriptor_budget", 96),
        ):
            if not 0 < getattr(value, name) <= cap:
                raise _Invalid("namespace_limit")
        if any(
            not 0 < getattr(value.sequence_limits, name) <= cap
            for name, cap in sequence._LIMIT_CAPS.items()
        ):
            raise _Invalid("namespace_sequence_limit")
    elif cls is PrivateNamespaceControlObservation:
        observed = value.original_read.original.observation
        if not 0 <= value.epoch < 2**64 or (
            value.control_stat.uid != value.directory.effective_uid
            or value.control_stat.nlink != 1
            or not stat.S_ISREG(value.control_stat.mode)
            or stat.S_IMODE(value.control_stat.mode) != 0o600
            or value.control_stat.size != 30
            or value.original_read.directory_before.binding != value.directory
            or value.original_read.directory_after.binding != value.directory
            or observed.path != value.control_path
            or observed.content
            != b"AWARE-SOURCE-EPOCH-V1\n" + value.epoch.to_bytes(8, "big")
        ):
            raise _Invalid("namespace_control")
    elif cls is PrivateNamespaceBinding:
        if (
            value.process_id <= 0
            or value.thread_id <= 0
            or value.control_before.directory != value.directory
        ):
            raise _Invalid("namespace_binding")
    elif cls is PrivateNamespacePhysicalEffect:
        if (
            not 0 <= value.epoch_before < 2**64
            or value.epoch_after is not None
            and not 0 <= value.epoch_after < 2**64
        ):
            raise _Invalid("namespace_epoch")
        for item in (value.requested_bytes, value.returned_bytes):
            if item is not None and item < 0:
                raise _Invalid("namespace_effect_bytes")
        if value.dispatch == "not_attempted" and (
            value.effect != "none"
            or value.returned_bytes is not None
            or value.durability != "not_confirmed"
        ):
            raise _Invalid("namespace_undispatched_effect")
    elif cls is PrivateNamespaceInventoryMember:
        path(value.name)
        if "/" in value.name:
            raise _Invalid("namespace_member_flat")
    elif cls is PrivateNamespaceInventoryObservation:
        names = tuple(member.name for member in value.members)
        roster = value.original_roster
        if (
            len(names) > 4096
            or len(set(names)) != len(names)
            or value.encoded_bytes > 1048576
        ):
            raise _Invalid("namespace_inventory_capacity")
        if roster.kind != "directory":
            raise _Invalid("namespace_inventory_roster")
        if value.complete and set(names) != set(roster.children_before):
            raise _Invalid("namespace_inventory_members")
        if not set(names).issubset(roster.children_before):
            raise _Invalid("namespace_inventory_prefix")
        if value.bookends_agree and roster.children_before != roster.children_after:
            raise _Invalid("namespace_inventory_bookends")
    elif cls is PrivateNamespaceFootprint:
        if (
            value.control_effect_paths != (".aware-source-authority.v1",)
            or value.ordered_steps != value.sequence_binding.sequence.ordered_steps
        ):
            raise _Invalid("namespace_footprint_order")
        for name in value.scratch_paths:
            path(name)
        if value.peak_descriptors > 96 or value.cursor_records > 2:
            raise _Invalid("namespace_footprint_capacity")
    elif cls is PrivateNamespaceTransactionObservation:
        if value.footprint is not None and (
            value.footprint.transaction_ref != value.binding.transaction_ref
            or value.footprint.sequence_binding.directory != value.binding.directory
            or value.active_sequence_ref is not None
            and value.active_sequence_ref
            != value.footprint.sequence_binding.private_sequence_ref
        ):
            raise _Invalid("namespace_observation_correlation")
    elif cls is PrivateNamespaceCleanup:
        settlements = (value.lock_release, value.control_close, value.root_close)
        child = value.child_cleanup
        footprint = value.observation.footprint
        expected = None if footprint is None else footprint.sequence_binding
        if child is not None:
            actual = child.binding
            native_binding = child.sequence.binding
            if (
                child.directory.binding is not None
                and child.directory.binding != value.observation.binding.directory
                or actual is not None
                and (
                    actual.directory != value.observation.binding.directory
                    or expected is not None
                    and actual != expected
                    or value.observation.active_sequence_ref is not None
                    and actual.private_sequence_ref
                    != value.observation.active_sequence_ref
                    or native_binding is not None
                    and actual.sequence != native_binding
                )
                or native_binding is not None
                and expected is not None
                and native_binding != expected.sequence
            ):
                raise _Invalid("namespace_cleanup_correlation")
        # Missing correlation remains representable as unknown, never as a
        # confirmed child disposal. A lock-only cleanup with no child claim
        # (no footprint, cleanup or active ref) can still confirm its resources.
        if (
            value.outcome == "confirmed"
            and (
                expected is not None
                or child is not None
                or value.observation.active_sequence_ref is not None
            )
            and (
                expected is None
                or child is None
                or child.binding is None
                or child.sequence.binding is None
                or child.directory.binding is None
            )
        ):
            raise _Invalid("namespace_cleanup_binding_unavailable")
        if value.outcome == "confirmed" and (
            any(item != "confirmed" for item in settlements)
            or value.observation.lock != "confirmed_released"
            or value.secondary_failures
            or value.child_cleanup is not None
            and value.child_cleanup.sequence.release != "confirmed"
        ):
            raise _Invalid("namespace_cleanup_confirmation")
        if value.outcome == "not_acquired" and (
            any(item != "not_acquired" for item in settlements)
            or value.child_cleanup is not None
        ):
            raise _Invalid("namespace_cleanup_acquisition")
    elif cls is PrivateNamespaceAncestorPrefix:
        (root if value.coordinate.startswith("/") else path)(value.coordinate)
    elif cls is PrivateNamespaceEntryPrefix:
        if value.entry_locator is not None:
            (root if value.entry_locator.startswith("/") else path)(value.entry_locator)
        for names in (value.children_before, value.children_after):
            if names is not None:
                for name in names:
                    _entry_name(name)
        if not value.resource_evidence_available and (
            value.descriptor_resources is not None or value.cursor_resources is not None
        ):
            raise _Invalid("namespace_prefix_resources")
    elif cls is PrivateNamespaceEntryFailure:
        text(value.phase, 1024)
        for name in value.roster_prefix:
            _entry_name(name)
        if (value.raw_name_encoding == "unavailable") != (value.raw_name_bytes is None):
            raise _Invalid("namespace_raw_name")
    elif cls is PrivateNamespaceRefusalEvidence:
        text(value.code, 1024)
        text(value.stage, 1024)
        if (
            value.control is not None
            and value.observation is not None
            and value.control.directory != value.observation.binding.directory
        ):
            raise _Invalid("namespace_refusal_control")
        if (
            value.inventory_prefix is not None
            and value.observation is not None
            and value.inventory_prefix.transaction_ref
            != value.observation.binding.transaction_ref
        ):
            raise _Invalid("namespace_refusal_inventory")
        if (
            value.cleanup is not None
            and value.observation is not None
            and value.cleanup.observation.binding != value.observation.binding
        ):
            raise _Invalid("namespace_refusal_cleanup")


def _inventory_stat(value, budget, depth, decode):
    """Compact original nine stat fields only inside namespace inventory.

    Reuse the original closed value engine, budgets, slots and stat validators.
    The separate wire tag never changes the legacy named-field representation.
    """
    rows = _auth(EntryStat)
    if decode:
        wire, data = _envelope(value)
        if wire != _INVENTORY_STAT_WIRE or set(data) != {"values"}:
            raise _Invalid("inventory_stat_fields")
        numbers = data["values"]
        if type(numbers) is not list or len(numbers) != 9:
            raise _Invalid("inventory_stat_arity")
    else:
        if type(value) is not EntryStat:
            raise _Invalid("original_value_required")
        _invariants(EntryStat, value)
        numbers = tuple(slot.__get__(value, EntryStat) for _, slot, _ in rows)
    skeleton = {"contract": _INVENTORY_STAT_WIRE, "value": {"values": None}}
    budget.charge(
        len(json.dumps(skeleton, separators=(",", ":")).encode()) - 4, "private"
    )
    converted = _value(
        numbers,
        tuple[int, ...],
        budget,
        depth + 1,
        "private",
        decode,
        owner="namespace_inventory",
    )
    if decode:
        result = EntryStat(*converted)
        _invariants(EntryStat, result)
        return result
    return {"contract": _INVENTORY_STAT_WIRE, "value": {"values": converted}}


def _value(
    value,
    annotation,
    budget,
    depth=0,
    group="private",
    decode=False,
    native_depth=None,
    owner=None,
):
    budget.visit(depth, native_depth)
    if annotation is PrivateNamespaceInventoryObservation:
        owner = "namespace_inventory"
    if (
        annotation is EntryStat
        and owner == "namespace_inventory"
        and (
            not decode
            or type(value) is dict
            and value.get("contract") == _INVENTORY_STAT_WIRE
        )
    ):
        return _inventory_stat(value, budget, depth, decode)
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (types.UnionType, Union):
        matches = [item for item in args if _matches(value, item, decode, owner)]
        if len(matches) != 1:
            raise _Invalid("union")
        return _value(
            value, matches[0], budget, depth, group, decode, native_depth, owner
        )
    if origin is Literal:
        if not any(type(value) is type(item) and value == item for item in args):
            raise _Invalid("literal")
        budget.scalar(value, group)
        return value
    if origin is tuple:
        if type(value) is not (list if decode else tuple):
            raise _Invalid("array")
        if len(value) > 16384:
            raise _Capacity("array")
        if len(args) != 2 or args[1] is not Ellipsis:
            if len(args) != len(value):
                raise _Invalid("fixed_tuple")
            types_for_items = args
        else:
            types_for_items = (args[0],) * len(value)
        budget.charge(2 + max(0, len(value) - 1), group)
        if id(value) in budget.active:
            raise _Invalid("cycle")
        budget.active.add(id(value))
        try:
            items = [
                _value(
                    item,
                    kind,
                    budget,
                    depth + 1,
                    group,
                    decode,
                    None if native_depth is None else native_depth + 1,
                    owner,
                )
                for item, kind in zip(value, types_for_items, strict=True)
            ]
            return tuple(items) if decode else items
        finally:
            budget.active.remove(id(value))
    if annotation is bytes:
        if not decode and type(value) is not bytes:
            raise _Invalid("bytes")
        return _content(value, budget, decode)
    if annotation in _SCHEMAS:
        cls = annotation
        rows = _auth(cls)
        if cls is PrivateReadFailure or cls in _READ_TYPES:
            # Authenticate before traversing nested read values: their original
            # __post_init__ methods can also call these pure owner validators.
            for name in ("_read_text", "_read_root", "_saved_read_path"):
                _owner_helper(native, name)
        is_native = cls in sequence._WIRE_IDS
        entering_native = is_native and native_depth is None
        if decode and entering_native and owner != "native":
            return _owner_helper(sequence, "_confined_sequence_value_from_payload")(
                cls, value, _budget=budget, _depth=depth
            )
        if cls in _READ_TYPES and owner != "read":
            if decode:
                return _owner_helper(native, "_confined_read_value_from_payload")(
                    cls, value, _budget=budget, _depth=depth
                )
            return _owner_helper(native, "_confined_read_value_to_payload")(
                value, _budget=budget, _depth=depth
            )
        if is_native:
            group = "native"
            native_depth = 0 if native_depth is None else native_depth
        if decode:
            wire, data = _envelope(value)
            if wire != _WIRES[cls] or set(data) != {name for name, _, _ in rows}:
                raise _Invalid("fields_or_type")
        else:
            if type(value) is not cls:
                raise _Invalid("original_value_required")
            data = {}
        if id(value) in budget.active:
            raise _Invalid("cycle")
        skeleton = {
            "contract": _WIRES[cls],
            "value": {name: None for name, _, _ in rows},
        }
        budget.charge(
            len(
                json.dumps(skeleton, ensure_ascii=False, separators=(",", ":")).encode()
            )
            - 4 * len(rows),
            group,
        )
        budget.active.add(id(value))
        try:
            converted = {
                name: _value(
                    data[name] if decode else slot.__get__(value, cls),
                    kind,
                    budget,
                    depth + 1,
                    group,
                    decode,
                    None if native_depth is None else native_depth + 1,
                    owner,
                )
                for name, slot, kind in rows
            }
            result = cls(**converted) if decode else value
            _invariants(cls, result)
            if decode:
                return result
            payload = {"contract": _WIRES[cls], "value": converted}
            if entering_native:
                if (
                    sequence.confined_sequence_value_to_payload is not _SEQUENCE_ENCODER
                    or _SEQUENCE_ENCODER.__code__ is not _SEQUENCE_ENCODER_CODE
                ):
                    raise _Invalid("native_encoder_changed")
                original = _SEQUENCE_ENCODER(value)
                if original != payload:
                    raise _Invalid("native_codec_disagreement")
                return original
            return payload
        finally:
            budget.active.remove(id(value))
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        if decode:
            if type(value) is not str:
                raise _Invalid("enum")
            budget.scalar(value, group)
            return annotation(value)
        if type(value) is not annotation:
            raise _Invalid("enum")
        budget.scalar(value.value, group)
        return value.value
    if annotation not in (str, int, bool, type(None)) or type(value) is not annotation:
        raise _Invalid("scalar")
    budget.scalar(value, group)
    return value


def _refusal(error, stage):
    code = (
        "private_codec_capacity_exceeded"
        if isinstance(error, _Capacity)
        else "private_codec_value_invalid"
    )
    evidence = PrivateDirectoryRefusalEvidence(
        code,
        type(error).__name__,
        stage,
        None,
        None,
        None,
        None,
        ConfinedSequencePrimaryFailure(
            "observed",
            None,
            stage,
            code,
            type(error).__name__,
            not isinstance(error, Exception),
        ),
        False,
    )
    return PrivateDirectoryRefusal(code, evidence=evidence)


def _owner_to_payload_and_size(value, allowed, *, _budget=None, _depth=0, _owner=None):
    """Encode and measure this occurrence through the original shared budget.

    This is an exact retrospective byte count, not a future-output reservation.
    Nested/repeated occurrences consume their original charges independently.
    """
    try:
        if not any(type(value) is item for item in allowed):
            raise _Invalid("original_value_required")
        budget = _budget or _Budget()
        before = budget.wire
        payload = _value(value, type(value), budget, depth=_depth, owner=_owner)
        return payload, before - budget.wire
    except PrivateDirectoryRefusal as error:
        error.__traceback__ = None
        raise
    except BaseException as error:
        error.__traceback__ = None
        raise _refusal(error, "encode") from error
    finally:
        value = None
        _budget = None


def _owner_to_payload(value, allowed, *, _budget=None, _depth=0, _owner=None):
    try:
        payload, _ = _owner_to_payload_and_size(
            value, allowed, _budget=_budget, _depth=_depth, _owner=_owner
        )
        return payload
    finally:
        value = _budget = None


def _owner_from_payload(
    value_type, source, allowed, *, _budget=None, _depth=0, _owner=None
):
    try:
        if not isinstance(value_type, type) or not any(
            value_type is item for item in allowed
        ):
            raise _Invalid("original_type_required")
        return _value(
            source,
            value_type,
            _budget or _Budget(),
            depth=_depth,
            decode=True,
            native_depth=0 if _owner == "native" else None,
            owner=_owner,
        )
    except PrivateDirectoryRefusal as error:
        error.__traceback__ = None
        raise
    except BaseException as error:
        error.__traceback__ = None
        raise _refusal(error, "decode") from error
    finally:
        source = None
        _budget = None


def private_directory_value_to_payload(
    value: PrivateDirectoryValue,
) -> dict[str, object]:
    """Return a detached, bounded owner payload, never physical authority."""
    try:
        return _owner_to_payload(value, _CODEC_TYPES)
    finally:
        del value


def private_directory_value_from_payload[T: PrivateDirectoryValue](
    value_type: type[T], source: object
) -> T:
    """Validate and decode evidence without IO or registry enrollment."""
    try:
        return _owner_from_payload(value_type, source, _CODEC_TYPES)
    finally:
        source = None


class RetainedPrivateDirectory:
    """Original process-local directory custody; snapshots cannot recreate it."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("original_private_directory_required")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("private_directory_subclass_refused")

    def __reduce__(self):
        raise TypeError("private_directory_serialization_refused")

    def __copy__(self):
        raise TypeError("private_directory_copy_refused")

    def __deepcopy__(self, memo):
        raise TypeError("private_directory_copy_refused")


_NO_FAILURE = ConfinedSequencePrimaryFailure("none", None, None, None, None, False)
_UNAVAILABLE_ROOT = PrivateRootObservation("unavailable", *(None,) * 6)
_PHYSICAL = {
    name: getattr(os, name)
    for name in ("open", "close", "dup", "stat", "fstat", "geteuid", "getpid")
}


@dataclass(eq=False)
class _DirectoryState:
    root: Path
    ref: str = field(default_factory=lambda: "private-directory:" + uuid4().hex)
    generation: str = field(default_factory=lambda: "private-generation:" + uuid4().hex)
    pid: int = field(default_factory=os.getpid)
    thread: int = field(default_factory=threading.get_ident)
    fd: int | None = None
    acquisition: str = "not_acquired"
    close_attempted: bool = False
    release: str = "unknown"
    phase: str = "active"
    binding: PrivateDirectoryBinding | None = None
    observed: PrivateRootObservation = _UNAVAILABLE_ROOT
    validations: int = 0
    acquisitions: int = 0
    child: str | None = None
    primary: ConfinedSequencePrimaryFailure = _NO_FAILURE
    complete: bool = True
    lock: RLock = field(default_factory=threading.RLock)
    native_sequence: sequence._SequenceState | None = None
    namespace_claim: object = None


_DIRECTORIES: dict[
    int, tuple[weakref.ReferenceType[RetainedPrivateDirectory], _DirectoryState]
] = {}
_CUSTODY: dict[int, _DirectoryState] = {}
_ORIGINAL_PORTS = {
    name: (
        module,
        attribute,
        getattr(module, attribute),
        getattr(module, attribute).__code__,
    )
    for name, module, attribute in (
        ("read", native, "_observe_confined_file_with_custody"),
        ("prepare", sequence, "_retain_confined_file_sequence"),
        ("observe", sequence, "observe_confined_file_sequence"),
        ("verify", sequence, "verify_confined_file_sequence"),
        ("execute", sequence, "execute_next_confined_file_step"),
        ("cleanup", sequence, "release_confined_file_sequence"),
    )
}


def _original_port(name):
    module, attribute, operation, code = _ORIGINAL_PORTS[name]
    # Cleanup retains the captured original entrance even if its public export
    # changed. Refuse changed original code; never execute a replacement export
    # or strand owned descriptors merely because ordinary work is now held.
    if (
        operation.__code__ is not code
        or name != "cleanup"
        and getattr(module, attribute) is not operation
    ):
        raise _PrivateFault("private_root_validation_unavailable")
    return operation


class _PrivateFault(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _directory_observation(state):
    resources = ()
    if state.acquisition != "not_acquired":
        resources = (
            ConfinedSequenceResourceEvidence(
                state.ref + ":root",
                "aware.filesystem.private-directory.v1",
                "root_descriptor",
                str(state.root),
                "released"
                if state.release == "confirmed"
                else "unknown"
                if state.close_attempted or state.acquisition == "unknown"
                else "owned",
                state.close_attempted,
                "confirmed" if state.release == "confirmed" else "unknown",
                (),
            ),
        )
    return PrivateDirectoryObservation(
        state.binding,
        state.phase,
        state.observed,
        state.validations,
        state.child,
        resources,
        state.primary,
        state.complete,
    )


def _retained_evidence(cls, *values):
    """Emergency data-only carrier from cached original slots, never custody.

    A result-construction failure must not erase an already spent close. This
    path is used only for refused/incomplete evidence, not successful returns.
    """
    rows = _SCHEMAS[cls][0]
    value = object.__new__(cls)
    for (_, slot, _), item in zip(rows, values, strict=True):
        slot.__set__(value, item)
    return value


def _safe_directory_observation(state):
    try:
        return _directory_observation(state)
    except BaseException:  # noqa: BLE001 - known disposal cannot regress after projection failure
        state.complete = False
        resources = ()
        if state.acquisition != "not_acquired":
            resources = (
                _retained_evidence(
                    ConfinedSequenceResourceEvidence,
                    state.ref + ":root",
                    "aware.filesystem.private-directory.v1",
                    "root_descriptor",
                    str(state.root),
                    "released"
                    if state.release == "confirmed"
                    else "unknown"
                    if state.close_attempted or state.acquisition == "unknown"
                    else "owned",
                    state.close_attempted,
                    "confirmed" if state.release == "confirmed" else "unknown",
                    (),
                ),
            )
        return _retained_evidence(
            _PRIVATE_TYPES[2],
            state.binding,
            state.phase,
            state.observed,
            state.validations,
            state.child,
            resources,
            state.primary,
            False,
        )


def _original_failure_cause(error):
    """Carry the original typed sequence cause, not its ordinary wrapper."""
    cause_type = type(error).__name__
    interruption = not isinstance(error, Exception)
    if type(error) is sequence.ConfinedSequenceRefusal:
        evidence = error.evidence
        if type(evidence) is ConfinedSequenceRefusalEvidence:
            primary = evidence.primary_failure
            if (
                type(primary) is ConfinedSequencePrimaryFailure
                and primary.state != "none"
            ):
                cause_type = primary.cause_type
                interruption = interruption or primary.interruption
    return cause_type, interruption


def _private_failure(error, stage, state=None, *, read=None, cleanup=None):
    cause_type, interruption = _original_failure_cause(error)
    code = getattr(error, "code", "private_native_operation_failed")
    primary = ConfinedSequencePrimaryFailure(
        "observed",
        state.ref if state is not None else None,
        stage,
        code,
        cause_type,
        interruption,
    )
    if state is not None:
        if state.primary.state == "none":
            state.primary = primary
        primary = state.primary
        if state.phase != "released":
            state.phase = "retired"
        state.complete = False
    return PrivateDirectoryRefusal(
        code,
        evidence=PrivateDirectoryRefusalEvidence(
            code,
            cause_type,
            stage,
            _safe_directory_observation(state) if state is not None else None,
            getattr(error, "evidence", None)
            if type(error) is sequence.ConfinedSequenceRefusal
            else None,
            read,
            cleanup,
            primary,
            False,
        ),
    )


def _original_directory(handle):
    pair = state = None
    try:
        if type(handle) is not RetainedPrivateDirectory:
            raise _PrivateFault("private_directory_foreign")
        pair = _DIRECTORIES.get(id(handle))
        if pair is None or pair[0]() is not handle:
            raise _PrivateFault("private_directory_foreign")
        state = pair[1]
        if (state.pid, state.thread) != (os.getpid(), threading.get_ident()):
            raise _PrivateFault("private_directory_foreign")
        return state
    except BaseException as error:  # noqa: BLE001 - foreign lookup never touches another custody family
        raise _private_failure(error, "lookup") from None
    finally:
        handle = pair = state = None


def _root_current(state):
    if state.phase != "active" or state.close_attempted:
        raise _PrivateFault("private_directory_retired")
    if state.validations >= 65536:
        raise _PrivateFault("private_directory_capacity_exceeded")
    state.validations += 1
    if any(getattr(os, name) is not operation for name, operation in _PHYSICAL.items()):
        raise _PrivateFault("private_root_validation_unavailable")
    if (
        state.binding is not None
        and _PHYSICAL["geteuid"]() != state.binding.effective_uid
    ):
        raise _PrivateFault("private_root_euid_changed")
    descriptor = _PHYSICAL["fstat"](state.fd)
    located = _PHYSICAL["stat"](state.root, follow_symlinks=False)
    state.observed = PrivateRootObservation(
        "observed",
        descriptor.st_dev,
        descriptor.st_ino,
        _PHYSICAL["geteuid"](),
        descriptor.st_uid,
        stat.S_IMODE(descriptor.st_mode),
        descriptor.st_ctime_ns,
    )
    if (
        not stat.S_ISDIR(located.st_mode)
        or not stat.S_ISDIR(descriptor.st_mode)
        or (descriptor.st_dev, descriptor.st_ino) != (located.st_dev, located.st_ino)
        or state.binding is not None
        and (descriptor.st_dev, descriptor.st_ino)
        != (state.binding.device, state.binding.inode)
        or state.root.resolve(strict=True) != state.root
    ):
        raise _PrivateFault("private_root_changed")
    if descriptor.st_uid != _PHYSICAL["geteuid"]():
        raise _PrivateFault("private_root_owner_mismatch")
    if stat.S_IMODE(descriptor.st_mode) != 0o700:
        raise _PrivateFault("private_root_mode_mismatch")
    return _directory_observation(state)


def _release_directory_state(state):
    if not state.close_attempted:
        state.close_attempted = True  # Spend before dispatch, including interruption.
        state.phase = "released"
        if state.fd is None:
            state.release = (
                "confirmed" if state.acquisition == "not_acquired" else "unknown"
            )
        else:
            state.release = "unknown"
            try:
                _PHYSICAL["close"](state.fd)
            except BaseException as error:  # noqa: BLE001 - a missing close return cannot be retried
                state.complete = False
                if state.primary.state == "none":
                    state.primary = ConfinedSequencePrimaryFailure(
                        "observed",
                        state.ref,
                        "release",
                        "private_release_incomplete",
                        type(error).__name__,
                        not isinstance(error, Exception),
                    )
            else:
                state.release = "confirmed"
        state.fd = None
    return PrivateDirectoryCleanup(_directory_observation(state), state.release)


def _finalize_directory(key, state):
    try:
        _release_directory_state(state)
    except BaseException:  # noqa: BLE001 - finalizer cannot renew cleanup after a failed projection
        state.complete = False
    finally:
        _DIRECTORIES.pop(key, None)
        _CUSTODY.pop(id(state), None)


def retain_private_directory(
    *, root: Path, privacy_profile: PrivacyProfile
) -> RetainedPrivateDirectory:
    """Retain an existing, canonical, effective-user-owned 0700 directory."""
    state = None
    try:
        if type(root) is not type(Path()):
            raise _PrivateFault("private_root_required")
        native._read_root(str(root))
        if (
            type(privacy_profile) is not str
            or privacy_profile != "effective_user_private_namespace_v1"
        ):
            raise _PrivateFault("private_root_required")
        state = _DirectoryState(root)
        if root.is_symlink():
            raise _PrivateFault("private_root_symlink_refused")
        if root.resolve(strict=True) != root:
            raise _PrivateFault("private_root_not_canonical")
        # Custody and unknown acquisition are recorded before the syscall.
        state.acquisition = "unknown"
        state.complete = False
        state.fd = _PHYSICAL["open"](root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        state.acquisition = "owned"
        state.complete = True
        _root_current(state)
        info = state.observed
        state.binding = PrivateDirectoryBinding(
            "aware.filesystem.private-directory.v1",
            state.generation,
            state.ref,
            str(root),
            info.device,
            info.inode,
            info.effective_uid,
            info.owner_uid,
            info.mode,
            privacy_profile,
            state.pid,
            state.thread,
        )
        private_directory_value_to_payload(_directory_observation(state))
        handle = object.__new__(RetainedPrivateDirectory)
        key = id(handle)
        _DIRECTORIES[key] = (weakref.ref(handle), state)
        _CUSTODY[id(state)] = state
        weakref.finalize(handle, _finalize_directory, key, state)
        return handle
    except BaseException as error:
        cleanup = None
        if state is not None:
            try:
                cleanup = _release_directory_state(state)
            except BaseException:  # noqa: BLE001 - failed issuance must preserve original cleanup responsibility
                state.complete = False
                cleanup = _retained_evidence(
                    _PRIVATE_TYPES[7], _safe_directory_observation(state), state.release
                )
        raise _private_failure(error, "issuance", state, cleanup=cleanup) from error
    finally:
        del root


def observe_private_directory(
    directory: RetainedPrivateDirectory,
) -> PrivateDirectoryObservation:
    """Return retained evidence, not fresh authority."""
    try:
        return _directory_observation(_original_directory(directory))
    finally:
        del directory


def validate_private_directory(
    directory: RetainedPrivateDirectory, *, expected_binding: PrivateDirectoryBinding
) -> PrivateDirectoryObservation:
    try:
        state = _original_directory(directory)
        with state.lock:
            try:
                if state.binding is None:
                    raise _PrivateFault("private_directory_foreign")
                if private_directory_value_to_payload(
                    expected_binding
                ) != private_directory_value_to_payload(state.binding):
                    raise _PrivateFault("private_directory_binding_mismatch")
                return _root_current(state)
            except BaseException as error:
                raise _private_failure(error, "validation", state) from error
    finally:
        del directory, expected_binding


def release_private_directory(
    directory: RetainedPrivateDirectory,
) -> PrivateDirectoryCleanup:
    try:
        state = _original_directory(directory)
        with state.lock:
            if state.child is not None:
                raise _private_failure(
                    _PrivateFault("private_directory_in_use"), "release"
                )
            try:
                result = _release_directory_state(state)
            except BaseException as error:
                state.complete = False
                cleanup = _retained_evidence(
                    _PRIVATE_TYPES[7], _safe_directory_observation(state), state.release
                )
                raise _private_failure(
                    error, "release_return", state, cleanup=cleanup
                ) from error
            if result.release != "confirmed":
                raise _private_failure(
                    _PrivateFault("private_release_incomplete"),
                    "release",
                    state,
                    cleanup=result,
                )
            return result
    finally:
        del directory


def _duplicate_private_root(state):
    if type(state) is not _DirectoryState or _CUSTODY.get(id(state)) is not state:
        raise _PrivateFault("private_directory_foreign")
    if (state.pid, state.thread) != (os.getpid(), threading.get_ident()):
        raise _PrivateFault("private_directory_foreign")
    _root_current(state)
    return _PHYSICAL["dup"](state.fd)


def _private_leaf(state, info):
    if type(state) is not _DirectoryState or _CUSTODY.get(id(state)) is not state:
        raise _PrivateFault("private_directory_foreign")
    _root_current(state)
    if not stat.S_ISREG(info.st_mode):
        raise _PrivateFault("private_leaf_not_regular")
    if info.st_uid != _PHYSICAL["geteuid"]():
        raise _PrivateFault("private_leaf_owner_mismatch")
    transient = False
    original = state.native_sequence
    if original is not None and info.st_nlink == 2:
        # Only the original writer's returned target-link effect can explain
        # its owned scratch/target pair. External hard links never qualify.
        transient = (info.st_dev, info.st_ino) in original.scratch.values() and any(
            effect.kind == "target_link" and effect.effect_state == "applied"
            for effect in original.effects
        )
    if info.st_nlink != 1 and not transient:
        raise _PrivateFault("private_leaf_link_count_refused")


def _private_validate_root(state):
    if type(state) is not _DirectoryState or _CUSTODY.get(id(state)) is not state:
        raise _PrivateFault("private_directory_foreign")
    if (state.pid, state.thread) != (os.getpid(), threading.get_ident()):
        raise _PrivateFault("private_directory_foreign")
    return _root_current(state)


def _private_sequence_join(state, original):
    _private_validate_root(state)
    if (
        type(original) is not sequence._SequenceState
        or original.private_root is not state
    ):
        raise _PrivateFault("private_directory_foreign")
    if state.native_sequence is not None:
        raise _PrivateFault("private_directory_in_use")
    _private_io_call("namespace_join", state, "native_prepare", original, None)
    state.native_sequence = original


def _namespace_join(root, stage, original=None, child=None):
    try:
        if root.namespace_claim is None:
            return
        from . import private_namespace as namespace

        operation, code = namespace._NAMESPACE_OWNER_JOIN
        if (
            namespace._namespace_owner_join is not operation
            or operation.__code__ is not code
        ):
            raise _PrivateFault("private_namespace_owner_changed")
        return operation(root, stage, original=original, child=child)
    finally:
        del root, original, child


def _namespace_dispatch(root, original):
    try:
        return _private_io_call("namespace_join", root, "dispatch", original, None)
    finally:
        del root, original


_PRIVATE_IO_PORTS = {
    "duplicate": (_duplicate_private_root, _duplicate_private_root.__code__),
    "leaf": (_private_leaf, _private_leaf.__code__),
    "validate": (_private_validate_root, _private_validate_root.__code__),
    "sequence": (_private_sequence_join, _private_sequence_join.__code__),
    "namespace_dispatch": (_namespace_dispatch, _namespace_dispatch.__code__),
    "namespace_join": (_namespace_join, _namespace_join.__code__),
}


def _private_io_call(name, *args):
    operation, code = _PRIVATE_IO_PORTS[name]
    if (
        globals().get(operation.__name__) is not operation
        or operation.__code__ is not code
    ):
        raise _PrivateFault("private_root_validation_unavailable")
    return operation(*args)


class RetainedPrivateFileSequence:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("original_private_sequence_required")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("private_sequence_subclass_refused")

    def __reduce__(self):
        raise TypeError("private_sequence_serialization_refused")

    def __copy__(self):
        raise TypeError("private_sequence_copy_refused")

    def __deepcopy__(self, memo):
        raise TypeError("private_sequence_copy_refused")


@dataclass
class _PrivateSequenceState:
    parent: RetainedPrivateDirectory
    directory: _DirectoryState
    original: sequence.RetainedConfinedFileSequence
    binding: PrivateSequenceBinding
    last: ConfinedSequenceObservation
    cleanup: ConfinedSequenceCleanup | None = None
    released: bool = False


_PRIVATE_SEQUENCES = {}


def _private_sequence_reservation(root_path, binding, resource_count, *, whole=False):
    """Conservative shared return/refusal/cleanup reservation, before effects.

    Charge repeated native bindings/history separately, as the portable codec
    does. A caller's additional verifications spend additional history budget;
    neither a new snapshot nor a new ordinal renews it.
    """
    files, steps = len(binding.files), len(binding.ordered_steps)
    rows = resource_count + (
        4 * files * steps + 12 * files + 8 if whole else 2 * files + 8
    )
    paths = (
        [str(root_path)]
        + [str(root_path / row.path) for row in binding.files]
        + [str(root_path / row.scratch_path) for row in binding.files]
    )
    longest = max(
        paths, key=lambda path: len(json.dumps(path, ensure_ascii=False).encode())
    )
    resource = ConfinedSequenceResourceEvidence(
        "sequence-resource:" + "f" * 32,
        "aware.filesystem.file-sequence.v1",
        "scratch_descriptor",
        longest,
        "unknown",
        True,
        "unknown",
        ("private_release_incomplete:" + "f" * 128,),
    )
    encode = sequence.confined_sequence_value_to_payload
    size = lambda value: len(
        json.dumps(
            encode(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    )
    # Native evidence appears in original refusal observation/cleanup and the
    # private cleanup carrier. Extra framing and bounded primary diagnostics
    # are reserved rather than dropped to force a late successful encoding.
    reserved = (
        3 * rows * size(resource) + 4 * size(binding) + (steps + 1) * 4096 + 65536
    )
    return reserved, (2 * files + 8) * (2 * steps + 4 if whole else 1)


def _reserve_private_sequence_capacity(root, original, *, whole=False):
    reserved, validations = _private_sequence_reservation(
        root.root, original.binding, len(original.resources), whole=whole
    )
    if reserved > 2097152 or validations > 65536 - root.validations:
        raise _PrivateFault("private_directory_capacity_exceeded")


def _original_private_sequence(handle):
    pair = state = None
    try:
        if type(handle) is not RetainedPrivateFileSequence:
            raise _PrivateFault("private_sequence_foreign")
        pair = _PRIVATE_SEQUENCES.get(id(handle))
        if pair is None or pair[0]() is not handle:
            raise _PrivateFault("private_sequence_foreign")
        state = pair[1]
        _original_directory(state.parent)
        return state
    except BaseException as error:  # noqa: BLE001 - reject without touching an unrelated family
        raise _private_failure(error, "sequence_lookup") from None
    finally:
        handle = pair = state = None


def _sequence_failure(state, error, stage):
    evidence = getattr(error, "evidence", None)
    if (
        type(evidence) is ConfinedSequenceRefusalEvidence
        and evidence.observation is not None
    ):
        state.last = evidence.observation
    try:
        state.last = _original_port("observe")(state.original)
    except BaseException:  # noqa: BLE001 - unavailable recapture cannot erase the known prefix
        state.directory.complete = False
    native_evidence = ConfinedSequenceRefusalEvidence(
        getattr(error, "code", "private_native_operation_failed"),
        type(error).__name__,
        state.binding.sequence.preparation_ref,
        state.last,
        state.cleanup,
        state.last.primary_failure,
        False,
    )
    refusal = _private_failure(error, stage, state.directory)
    refusal.evidence = replace(refusal.evidence, sequence=native_evidence)
    return refusal


def _cleanup_private_sequence(state):
    if not state.released:
        # Mark terminal before disposing; never replay native cleanup after an
        # unavailable return. Native owner separately spends every close right.
        state.released = True
        try:
            state.cleanup = _original_port("cleanup")(state.original)
        finally:
            state.directory.child = None
            state.directory.native_sequence = None
            if state.cleanup is None:
                state.directory.phase = "retired"
                state.directory.complete = False
        if state.cleanup is None or state.cleanup.release != "confirmed":
            state.directory.phase = "retired"
            state.directory.complete = False
    if state.cleanup is None:
        raise _PrivateFault("private_release_incomplete")
    return PrivateSequenceCleanup(
        state.binding, _directory_observation(state.directory), state.cleanup
    )


def _finalize_private_sequence(key, state):
    try:
        _cleanup_private_sequence(state)
    except BaseException:  # noqa: BLE001 - terminal cleanup cannot be retried by finalization
        state.directory.complete = False
    finally:
        _PRIVATE_SEQUENCES.pop(key, None)


def retain_private_file_sequence(
    directory: RetainedPrivateDirectory,
    *,
    expected_binding: PrivateDirectoryBinding,
    requests: tuple[native.ConfinedFileMutationRequest, ...],
    limits: sequence.ConfinedSequenceLimits,
    confinement_profile: native.ConfinedMutationProfile,
) -> RetainedPrivateFileSequence:
    root = original = state = handle = None
    try:
        root = _original_directory(directory)
        original = None
        acquired = False
        with root.lock:
            try:
                _private_io_call("namespace_join", root, "private_prepare", None, None)
            except BaseException as error:
                # Rejected contenders cannot retire the genuine namespace family.
                raise _private_failure(error, "namespace_preparation") from error
            if root.child is not None:
                raise _private_failure(
                    _PrivateFault("private_directory_in_use"), "sequence_preparation"
                )
            try:
                validate_private_directory(directory, expected_binding=expected_binding)
                if root.child is not None:
                    raise _PrivateFault("private_directory_in_use")
                if root.acquisitions >= 128:
                    raise _PrivateFault("private_directory_capacity_exceeded")
                if type(requests) is not tuple:
                    raise _PrivateFault("private_sequence_request_unsupported")
                for request in requests:
                    if type(request) is not native.ConfinedFileMutationRequest:
                        raise _PrivateFault("private_sequence_request_unsupported")
                    native._saved_read_path(request.path)
                    if (
                        request.kind is not native.ConfinedMutationKind.CREATE
                        or "/" in request.path
                        or request.expected_exists
                        or request.expected_content_digest is not None
                    ):
                        raise _PrivateFault("private_sequence_request_unsupported")
                root.acquisitions += 1
                root.child = "private-sequence:" + uuid4().hex
                acquired = True
                original = _original_port("prepare")(
                    root=root.root,
                    requests=requests,
                    limits=limits,
                    confinement_profile=confinement_profile,
                    _private_root=root,
                )
                observed = _original_port("observe")(original)
                _reserve_private_sequence_capacity(
                    root, root.native_sequence, whole=True
                )
                if root.binding is None or observed.binding is None:
                    raise _PrivateFault("private_return_incomplete")
                binding = PrivateSequenceBinding(
                    root.child, root.binding, observed.binding
                )
                private_directory_value_to_payload(binding)
                _root_current(root)
                state = _PrivateSequenceState(
                    directory, root, original, binding, observed
                )
                handle = object.__new__(RetainedPrivateFileSequence)
                key = id(handle)
                _PRIVATE_SEQUENCES[key] = (weakref.ref(handle), state)
                weakref.finalize(handle, _finalize_private_sequence, key, state)
                _private_io_call(
                    "namespace_join",
                    root,
                    "private_child",
                    root.native_sequence,
                    handle,
                )
                return handle
            except BaseException as error:
                cleanup = None
                try:
                    if original is not None:
                        cleanup = _original_port("cleanup")(original)
                    elif acquired and root.native_sequence is not None:
                        cleanup = root.native_sequence.cleanup
                except BaseException:  # noqa: BLE001 - preserve primary failure and unavailable cleanup without retry
                    root.complete = False
                finally:
                    if acquired:
                        root.child = None
                        root.native_sequence = None
                refusal = _private_failure(error, "sequence_preparation", root)
                if type(cleanup) is ConfinedSequenceCleanup:
                    refusal.evidence = replace(
                        refusal.evidence,
                        cleanup=PrivateSequenceCleanup(
                            None, _directory_observation(root), cleanup
                        ),
                    )
                raise refusal from error
    finally:
        del directory, expected_binding, requests, limits, confinement_profile
        root = original = state = handle = None


def observe_private_file_sequence(
    sequence: RetainedPrivateFileSequence,
) -> PrivateSequenceObservation:
    try:
        state = _original_private_sequence(sequence)
        with state.directory.lock:
            try:
                state.last = _original_port("observe")(state.original)
                return PrivateSequenceObservation(
                    state.binding, _directory_observation(state.directory), state.last
                )
            except BaseException as error:
                raise _sequence_failure(state, error, "sequence_observation") from error
    finally:
        del sequence


def verify_private_file_sequence(
    sequence: RetainedPrivateFileSequence, *, expected_binding: PrivateSequenceBinding
) -> PrivateSequenceObservation:
    try:
        state = _original_private_sequence(sequence)
        with state.directory.lock:
            try:
                if state.released:
                    raise _PrivateFault("private_directory_retired")
                if private_directory_value_to_payload(
                    expected_binding
                ) != private_directory_value_to_payload(state.binding):
                    raise _PrivateFault("private_directory_binding_mismatch")
                _root_current(state.directory)
                _reserve_private_sequence_capacity(
                    state.directory, state.directory.native_sequence
                )
                state.last = _original_port("verify")(
                    state.original, expected_binding=state.binding.sequence
                )
                return PrivateSequenceObservation(
                    state.binding, _directory_observation(state.directory), state.last
                )
            except BaseException as error:
                raise _sequence_failure(
                    state, error, "sequence_verification"
                ) from error
    finally:
        del sequence, expected_binding


def execute_next_private_file_step(
    sequence: RetainedPrivateFileSequence, *, expected_ordinal: int
) -> PrivateSequenceStepResult:
    state = None
    try:
        state = _original_private_sequence(sequence)
        with state.directory.lock:
            try:
                if state.released:
                    raise _PrivateFault("private_directory_retired")
                before = _root_current(state.directory)
                _reserve_private_sequence_capacity(
                    state.directory, state.directory.native_sequence
                )
                # Counters cannot be renewed by a new observation. Reserve all
                # checkpoints needed by this original dispatch before spending.
                if (
                    state.directory.validations
                    + 4 * len(state.binding.sequence.files)
                    + 16
                    > 65536
                ):
                    raise _PrivateFault("private_directory_capacity_exceeded")
                result = _original_port("execute")(
                    state.original, expected_ordinal=expected_ordinal
                )
                state.last = _original_port("observe")(state.original)
                after = _root_current(state.directory)
                _auth(_PRIVATE_TYPES[5])
                projected = PrivateSequenceStepResult(
                    state.binding, before, after, result
                )
                private_directory_value_to_payload(projected)
                return projected
            except BaseException as error:
                raise _sequence_failure(state, error, "sequence_dispatch") from error
    finally:
        del sequence, expected_ordinal
        state = None


def release_private_file_sequence(
    sequence: RetainedPrivateFileSequence,
) -> PrivateSequenceCleanup:
    try:
        state = _original_private_sequence(sequence)
        with state.directory.lock:
            try:
                result = _cleanup_private_sequence(state)
                if result.sequence.release != "confirmed":
                    raise _PrivateFault("private_release_incomplete")
                return result
            except BaseException as error:
                raise _sequence_failure(state, error, "sequence_release") from error
    finally:
        del sequence


def observe_private_directory_file(
    directory: RetainedPrivateDirectory,
    *,
    expected_binding: PrivateDirectoryBinding,
    path: str,
    maximum_bytes: int,
) -> PrivateFileReadResult:
    """Read through original bounded IO using the retained root descriptor."""
    try:
        state = _original_directory(directory)
        read = None
        with state.lock:
            if state.child is not None:
                raise _private_failure(
                    _PrivateFault("private_directory_in_use"), "read"
                )
            try:
                before = validate_private_directory(
                    directory, expected_binding=expected_binding
                )
                native._saved_read_path(path)
                if "/" in path:
                    raise _PrivateFault("private_sequence_request_unsupported")
                if state.child is not None:
                    raise _PrivateFault("private_directory_in_use")
                if state.acquisitions >= 128:
                    raise _PrivateFault("private_directory_capacity_exceeded")
                # Reserve bounded private return/refusal metadata before IO. Native
                # content/cleanup remain charged to their original bounded reader.
                private_directory_value_to_payload(before)
                state.acquisitions += 1
                state.child = "private-read:" + uuid4().hex
                try:
                    read, _, _ = _original_port("read")(
                        root=state.root,
                        path=path,
                        maximum_bytes=maximum_bytes,
                        _private_root=state,
                    )
                    if (
                        read.observation.outcome
                        is not native.ConfinedObservationOutcome.OBSERVED
                    ):
                        raise _PrivateFault("private_leaf_not_regular")
                    if not read.observation.exists:
                        raise _PrivateFault("private_leaf_missing")
                    after = _root_current(state)
                    _auth(_PRIVATE_TYPES[8])
                    result = PrivateFileReadResult(before, after, read)
                    private_directory_value_to_payload(result)
                    return result
                finally:
                    state.child = None
            except BaseException as error:
                if type(error) is native.ConfinedFileObservationError:
                    read = PrivateReadFailure(
                        error.code,
                        error.stage,
                        error.cause_kind,
                        error.root_locator,
                        error.path,
                        error.observation,
                        error.cleanup,
                    )
                    cause = error.__cause__
                    if isinstance(cause, _PrivateFault):
                        error = cause
                raise _private_failure(error, "read", state, read=read) from error
    finally:
        del directory, expected_binding, path, maximum_bytes


__all__ = [  # noqa: RUF022 - conserve the accepted evidence export order before additive live ports
    "PrivateDirectoryBinding",
    "PrivateRootObservation",
    "PrivateDirectoryObservation",
    "PrivateSequenceBinding",
    "PrivateSequenceObservation",
    "PrivateSequenceStepResult",
    "PrivateSequenceCleanup",
    "PrivateDirectoryCleanup",
    "PrivateFileReadResult",
    "PrivateReadFailure",
    "PrivateDirectoryRefusalEvidence",
    "PrivacyProfile",
    "PrivateDirectoryPhase",
    "PrivateDirectoryValue",
    "PrivateDirectoryRefusal",
    "private_directory_value_to_payload",
    "private_directory_value_from_payload",
    "RetainedPrivateDirectory",
    "retain_private_directory",
    "observe_private_directory",
    "validate_private_directory",
    "release_private_directory",
    "observe_private_directory_file",
    "RetainedPrivateFileSequence",
    "retain_private_file_sequence",
    "observe_private_file_sequence",
    "verify_private_file_sequence",
    "execute_next_private_file_step",
    "release_private_file_sequence",
]
__all__ += [  # noqa: RUF022 - preserve qualified root order without changing predecessor exports
    "PrivateNamespaceControlObservation",
    "PrivateNamespaceLimits",
    "PrivateNamespaceBinding",
    "PrivateNamespacePhysicalEffect",
    "PrivateNamespaceInventoryMember",
    "PrivateNamespaceInventoryObservation",
    "PrivateNamespaceFootprint",
    "PrivateNamespaceTransactionObservation",
    "PrivateNamespaceCleanup",
    "PrivateNamespaceAncestorPrefix",
    "PrivateNamespaceEntryPrefix",
    "PrivateNamespaceEntryFailure",
    "PrivateNamespaceRefusalEvidence",
]

# Capture the model only after the original owner has finished initialization.
from .private_sequence_capacity import (
    CapacityBound,
    CapacityCode,
    CapacityModelIdentity,
    PrivateSequenceCapacityError,
    PrivateSequenceCapacityForecast,
    _initialize_model,
    decode_private_sequence_capacity_forecast,
    encode_private_sequence_capacity_forecast,
    forecast_private_file_sequence_capacity,
)

PRIVATE_SEQUENCE_CAPACITY_MODEL = _initialize_model()
__all__ += [
    "PRIVATE_SEQUENCE_CAPACITY_MODEL",
    "CapacityBound",
    "CapacityCode",
    "CapacityModelIdentity",
    "PrivateSequenceCapacityError",
    "PrivateSequenceCapacityForecast",
    "decode_private_sequence_capacity_forecast",
    "encode_private_sequence_capacity_forecast",
    "forecast_private_file_sequence_capacity",
]

_NAMESPACE_PUBLIC = (
    "PrivateNamespaceRefusal",
    "RetainedPrivateNamespaceTransaction",
    "observe_private_namespace_control",
    "retain_private_namespace_transaction",
    "observe_private_namespace_inventory",
    "observe_private_namespace_file",
    "retain_private_namespace_file_sequence",
    "arm_private_namespace_transaction",
    "observe_private_namespace_transaction",
    "release_private_namespace_transaction",
)
__all__ += list(_NAMESPACE_PUBLIC)


def __getattr__(name):
    if name not in _NAMESPACE_PUBLIC:
        raise AttributeError(name)
    from . import private_namespace as namespace

    operation, code = namespace._NAMESPACE_FACADE
    if namespace._namespace_export is not operation or operation.__code__ is not code:
        raise AttributeError("namespace_export_changed")
    return operation(name)
