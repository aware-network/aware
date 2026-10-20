"""Neutral, opaque committed-history carriage; decoding is not source admission."""

from __future__ import annotations

import hashlib
import json
import math
import re
import weakref
from collections.abc import Callable
from dataclasses import dataclass, fields
from typing import Protocol, Self, cast

from .owner_values import OntologyObjectSnapshotData

OBJECT_HISTORY_CONTRACT = "aware.ontology.object-history.v1"
OBJECT_HISTORY_CODEC_VERSION = 1
OBJECT_HISTORY_MEDIA_TYPE = (
    "application/vnd.aware.ontology.object-history+json;version=1"
)
_GRADES = (
    "local_operational",
    "deterministic_fixture",
    "canonical_commit",
    "replicated_canonical_commit",
    "historical_canonical_replay",
)


class ObjectHistoryError(ValueError):
    def __init__(self, code: str, message: str = ""):
        self.code = code
        super().__init__(message or code)


def _j(value):
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _text(v):
    if (
        type(v) is not str
        or not v
        or v.strip() != v
        or "\0" in v
        or len(v.encode()) > 4096
    ):
        raise ObjectHistoryError("invalid_wire", "exact bounded text required")
    return v


def _digest(v):
    if type(v) is not str or re.fullmatch(r"sha256:[0-9a-f]{64}", v) is None:
        raise ObjectHistoryError("invalid_wire", "exact SHA required")
    return v


_STATE = {}


@dataclass(frozen=True, slots=True, weakref_slot=True)
class _Value:
    def __post_init__(self):
        prior = _STATE.get(id(self))
        if prior is not None and prior[0]() is self:
            _STATE[id(self)] = (prior[0], None)
            raise ObjectHistoryError(
                "invalid_wire", "issued value cannot be reinitialized"
            )
        body = _build(self)
        identity = id(self)
        _STATE[identity] = (
            weakref.ref(self, lambda _: _STATE.pop(identity, None)),
            body,
        )

    def canonical_bytes(self) -> bytes:
        return encode_object_history(self)

    @classmethod
    def from_canonical_bytes(cls, body: bytes) -> Self:
        result = decode_object_history(body)
        if type(result) is not cls:
            raise ObjectHistoryError("invalid_wire", "foreign tag")
        return cast(Self, result)


@dataclass(frozen=True, slots=True)
class ObjectHistoryCursor(_Value):
    source_cursor_body: bytes
    origin_ref: str
    sequence: int


@dataclass(frozen=True, slots=True)
class ObjectHistoryMember(_Value):
    member_key: str
    original_member_body: bytes
    native_point_body: bytes | None
    predecessor_commit_ref: str | None
    result_commit_ref: str
    configuration_evidence: bytes


@dataclass(frozen=True, slots=True)
class ObjectHistoryGroup(_Value):
    previous: ObjectHistoryCursor
    cursor: ObjectHistoryCursor
    source_group_body: bytes
    members: tuple[ObjectHistoryMember, ...]
    source_grade: str


@dataclass(frozen=True, slots=True)
class ObjectHistoryPage(_Value):
    start: ObjectHistoryCursor
    frontier: ObjectHistoryCursor
    scanned_end: ObjectHistoryCursor
    groups: tuple[ObjectHistoryGroup, ...]
    source_page_body: bytes


@dataclass(frozen=True, slots=True)
class ObjectHistoryDemand(_Value):
    subject_ref: str
    type_ref: str
    field_refs: tuple[str, ...]
    relationship_refs: tuple[str, ...]
    scope_ref: str


@dataclass(frozen=True, slots=True)
class ObjectHistoryCoverage(_Value):
    demand: ObjectHistoryDemand
    before_complete: bool
    after_complete: bool
    configuration_digest: str


@dataclass(frozen=True, slots=True)
class ObjectHistoryCorrespondence(_Value):
    origin_ref: str
    cursor: ObjectHistoryCursor
    demand: ObjectHistoryDemand
    before_snapshot_digest: str | None
    after_snapshot_digest: str | None
    configuration_evidence: bytes
    source_mapping_digest: str


@dataclass(frozen=True, slots=True)
class ObjectHistoryTransition(_Value):
    group: ObjectHistoryGroup
    demand: ObjectHistoryDemand
    before_snapshot_body: bytes | None
    after_snapshot_body: bytes | None
    coverage_body: bytes
    source_correspondence: bytes


_TABLE = (
    ("cursor", ObjectHistoryCursor, ("Bytes", "Digest", "UInt")),
    (
        "member",
        ObjectHistoryMember,
        ("Text", "Bytes", "Bytes?", "Text?", "Text", "Bytes"),
    ),
    ("group", ObjectHistoryGroup, ("Cursor", "Cursor", "Bytes", "Member[]", "Grade")),
    ("page", ObjectHistoryPage, ("Cursor", "Cursor", "Cursor", "Group[]", "Bytes")),
    ("demand", ObjectHistoryDemand, ("Text", "Text", "Text[]", "Text[]", "Text")),
    ("coverage", ObjectHistoryCoverage, ("Demand", "Bool", "Bool", "Digest")),
    (
        "correspondence",
        ObjectHistoryCorrespondence,
        ("Digest", "Cursor", "Demand", "Digest?", "Digest?", "Bytes", "Digest"),
    ),
    (
        "transition",
        ObjectHistoryTransition,
        ("Group", "Demand", "Bytes?", "Bytes?", "Bytes", "Bytes"),
    ),
)
_BY_TYPE = {cls: (tag, types) for tag, cls, types in _TABLE}


def _field(v, t):
    if t.endswith("?"):
        return None if v is None else _field(v, t[:-1])
    if t.endswith("[]"):
        if type(v) is not tuple:
            raise ObjectHistoryError("invalid_wire", "exact tuple required")
        return [_field(x, t[:-2]) for x in v]
    if t == "Bytes":
        if type(v) is not bytes:
            raise ObjectHistoryError("invalid_wire", "exact bytes required")
        return v.hex()
    if t == "UInt":
        if type(v) is not int or not 0 <= v <= 2**63 - 1:
            raise ObjectHistoryError("invalid_wire", "exact UInt required")
        return v
    if t == "Bool":
        if type(v) is not bool:
            raise ObjectHistoryError("invalid_wire", "exact bool required")
        return v
    if t == "Digest":
        return _digest(v)
    if t in ("Text", "Grade"):
        return _text(v)
    cls = next(c for _, c, _ in _TABLE if c.__name__ == "ObjectHistory" + t)
    if type(v) is not cls:
        raise ObjectHistoryError("invalid_wire", "exact nested owner required")
    return json.loads(encode_object_history(v))


def _same(a, b):
    return a.canonical_bytes() == b.canonical_bytes()


def _validate(v):
    if type(v) is ObjectHistoryDemand:
        for refs in (v.field_refs, v.relationship_refs):
            if tuple(sorted(set(refs), key=lambda x: x.encode())) != refs:
                raise ObjectHistoryError(
                    "invalid_wire", "demand order/uniqueness differs"
                )
    elif type(v) is ObjectHistoryGroup:
        if (
            v.source_grade not in _GRADES
            or v.cursor.sequence != v.previous.sequence + 1
            or v.cursor.origin_ref != v.previous.origin_ref
        ):
            raise ObjectHistoryError("invalid_wire", "group origin/order/grade differs")
        keys = [m.member_key for m in v.members]
        if len(keys) != len(set(keys)):
            raise ObjectHistoryError("invalid_wire", "duplicate member")
    elif type(v) is ObjectHistoryPage:
        if (
            not v.start.sequence <= v.scanned_end.sequence <= v.frontier.sequence
            or len({c.origin_ref for c in (v.start, v.frontier, v.scanned_end)}) != 1
        ):
            raise ObjectHistoryError("invalid_wire", "page bounds differ")
        previous = v.start
        for group in v.groups:
            if not _same(group.previous, previous):
                raise ObjectHistoryError("invalid_wire", "page gap")
            previous = group.cursor
        if not _same(previous, v.scanned_end):
            raise ObjectHistoryError("invalid_wire", "page progress differs")
    elif type(v) is ObjectHistoryCorrespondence:
        if v.origin_ref != v.cursor.origin_ref:
            raise ObjectHistoryError("invalid_wire", "correspondence origin differs")
    elif type(v) is ObjectHistoryTransition:
        if v.before_snapshot_body is None and v.after_snapshot_body is None:
            raise ObjectHistoryError("invalid_wire", "empty transition")
        snapshots = [
            None
            if body is None
            else OntologyObjectSnapshotData.from_canonical_bytes(body)
            for body in (v.before_snapshot_body, v.after_snapshot_body)
        ]
        coverage = ObjectHistoryCoverage.from_canonical_bytes(v.coverage_body)
        correspondence = ObjectHistoryCorrespondence.from_canonical_bytes(
            v.source_correspondence
        )
        if (
            not _same(coverage.demand, v.demand)
            or not _same(correspondence.demand, v.demand)
            or not _same(correspondence.cursor, v.group.cursor)
            or coverage.configuration_digest
            != _sha(correspondence.configuration_evidence)
        ):
            raise ObjectHistoryError(
                "invalid_wire", "transition coverage/context differs"
            )
        if (
            correspondence.before_snapshot_digest,
            correspondence.after_snapshot_digest,
        ) != tuple(None if s is None else s.snapshot_digest for s in snapshots):
            raise ObjectHistoryError("invalid_wire", "snapshot correspondence differs")


def _build(v, *, validate=True):
    if type(v) not in _BY_TYPE:
        raise ObjectHistoryError("invalid_wire", "foreign type")
    tag, types = _BY_TYPE[type(v)]
    values = [
        _field(getattr(v, f.name), t) for f, t in zip(fields(v), types, strict=True)
    ]
    if validate:
        _validate(v)
    return _j([OBJECT_HISTORY_CONTRACT, 1, tag, values])


def encode_object_history(v):
    state = _STATE.get(id(v))
    if state is None or state[0]() is not v or state[1] is None:
        raise ObjectHistoryError("invalid_wire", "unissued/retired value")
    try:
        body = _build(v, validate=False)
        if body != state[1]:
            raise ObjectHistoryError("invalid_wire", "issued bytes changed")
        return body
    except BaseException:
        _STATE[id(v)] = (state[0], None)
        raise


def _decode(raw):
    if (
        type(raw) is not list
        or len(raw) != 4
        or raw[0] != OBJECT_HISTORY_CONTRACT
        or type(raw[1]) is not int
        or raw[1] != 1
        or type(raw[2]) is not str
        or type(raw[3]) is not list
    ):
        raise ObjectHistoryError("invalid_wire", "envelope differs")
    entry = next((entry for entry in _TABLE if entry[0] == raw[2]), None)
    if entry is None:
        raise ObjectHistoryError("invalid_wire", "unknown tag")
    _, cls, types = entry

    def field(x, t):
        if t.endswith("?"):
            return None if x is None else field(x, t[:-1])
        if t.endswith("[]"):
            if type(x) is not list:
                raise ObjectHistoryError("invalid_wire")
            return tuple(field(y, t[:-2]) for y in x)
        if t == "Bytes":
            if type(x) is not str or re.fullmatch(r"(?:[0-9a-f]{2})*", x) is None:
                raise ObjectHistoryError("invalid_wire")
            return bytes.fromhex(x)
        if t not in ("Text", "Digest", "Bool", "Grade", "UInt"):
            return _decode(x)
        return x

    constructor = cast(Callable[..., _Value], cls)
    return constructor(*(field(x, t) for x, t in zip(raw[3], types, strict=True)))


def decode_object_history(body):
    if type(body) is not bytes or len(body) > 33554432:
        raise ObjectHistoryError("invalid_wire")
    try:
        value = _decode(
            json.loads(
                body, parse_float=lambda _: (_ for _ in ()).throw(ValueError("float"))
            )
        )
        if value.canonical_bytes() != body:
            raise ValueError("noncanonical bytes")
        return value
    except (TypeError, ValueError, UnicodeError, KeyError, RecursionError) as error:
        raise ObjectHistoryError("invalid_wire", str(error)) from error


class ObjectHistoryPort(Protocol):
    async def read_page(
        self, *, after, frontier, group_limit, byte_limit, scan_limit
    ) -> ObjectHistoryPage: ...
    async def read_group(self, cursor) -> ObjectHistoryGroup: ...
    async def read_transition(self, group, demand) -> ObjectHistoryTransition: ...
    async def wait(self, *, after, timeout_seconds) -> None: ...
    def close(self) -> None: ...


class ObjectHistoryContext:
    """Injected port borrow; implementing the Protocol never issues source grade."""

    def __init__(self, *, port: ObjectHistoryPort):
        self._port = port
        self._closed = False

    def _require(self):
        if self._closed:
            raise ObjectHistoryError("context_closed")
        return self._port

    async def read_page(
        self,
        *,
        after,
        frontier=None,
        group_limit=32,
        byte_limit=8388608,
        scan_limit=128,
    ):
        result = await self._require().read_page(
            after=after,
            frontier=frontier,
            group_limit=group_limit,
            byte_limit=byte_limit,
            scan_limit=scan_limit,
        )
        self._require()
        if type(result) is not ObjectHistoryPage:
            raise ObjectHistoryError("source_mismatch")
        return ObjectHistoryPage.from_canonical_bytes(result.canonical_bytes())

    async def read_group(self, cursor):
        result = await self._require().read_group(cursor)
        self._require()
        if type(result) is not ObjectHistoryGroup:
            raise ObjectHistoryError("source_mismatch")
        return ObjectHistoryGroup.from_canonical_bytes(result.canonical_bytes())

    async def read_transition(self, group, demand):
        result = await self._require().read_transition(group, demand)
        self._require()
        if type(result) is not ObjectHistoryTransition:
            raise ObjectHistoryError("source_mismatch")
        return ObjectHistoryTransition.from_canonical_bytes(result.canonical_bytes())

    async def stream(
        self,
        *,
        after,
        group_limit=32,
        byte_limit=8388608,
        scan_limit=128,
        wait_timeout_seconds=1.0,
    ):
        if (
            type(wait_timeout_seconds) not in (int, float)
            or not math.isfinite(wait_timeout_seconds)
            or not 0 < wait_timeout_seconds <= 60
        ):
            raise ObjectHistoryError("invalid_context", "wait bound differs")
        cursor = after
        while True:
            page = await self.read_page(
                after=cursor,
                group_limit=group_limit,
                byte_limit=byte_limit,
                scan_limit=scan_limit,
            )
            for group in page.groups:
                yield group
                cursor = group.cursor
            if not page.groups:
                await self._require().wait(
                    after=cursor, timeout_seconds=wait_timeout_seconds
                )

    def close(self):
        if not self._closed:
            self._closed = True
            self._port.close()


__all__ = [
    "OBJECT_HISTORY_CODEC_VERSION",
    "OBJECT_HISTORY_CONTRACT",
    "OBJECT_HISTORY_MEDIA_TYPE",
    "ObjectHistoryContext",
    "ObjectHistoryCorrespondence",
    "ObjectHistoryCoverage",
    "ObjectHistoryCursor",
    "ObjectHistoryDemand",
    "ObjectHistoryError",
    "ObjectHistoryGroup",
    "ObjectHistoryMember",
    "ObjectHistoryPage",
    "ObjectHistoryPort",
    "ObjectHistoryTransition",
    "decode_object_history",
    "encode_object_history",
]
