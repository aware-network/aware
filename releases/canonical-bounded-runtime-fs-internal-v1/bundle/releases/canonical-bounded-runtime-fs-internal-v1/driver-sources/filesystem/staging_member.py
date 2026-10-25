"""Original member writer. Ordered finish is explicit, not legacy activation.

The legacy begin_member remains scratch/write/abort only. The separately named
ordered entrance enables directories and member finish, not stage/install approval.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import types
from collections.abc import Callable
from dataclasses import dataclass, field, fields
from typing import Any, cast
from uuid import uuid4
from weakref import WeakKeyDictionary

from . import retained_bootstrap as bootstrap
from . import staging_root as root

physical = root.physical
MAX_SPANS = MAX_WRITE_CALLS = 4096
ORDERED_PROFILE = "aware.filesystem.staging-ordered-finish.v1"
CLOSED_TERMINAL_PROFILE = "aware.filesystem.closed-member-backed-values.v1"
PROGRESS_PROFILE = "aware.filesystem.staging-compact-progress.v1"
_CLOSED_BODY_BACKING = None


def _closed_body_storage():
    global _CLOSED_BODY_BACKING
    if _CLOSED_BODY_BACKING is None:
        from ._observation_receipt import _BodyBacking

        _CLOSED_BODY_BACKING = _BodyBacking()
    return _CLOSED_BODY_BACKING


def _closed_custody_seal(custody, size):
    from ._observation_receipt import _SharedBody

    if type(custody) is bytes:
        return hashlib.sha256(size.to_bytes(4, "little") + custody).digest()
    if type(custody) is not _SharedBody or _CLOSED_BODY_BACKING is None:
        raise ValueError("original_closed_member_storage_required")
    obtained = _CLOSED_BODY_BACKING.validate(custody)
    if obtained != size:
        raise ValueError("original_closed_member_size_changed")
    return hashlib.sha256(
        b"original_shared_member_body_v1:"
        + custody.offset.to_bytes(8, "little")
        + size.to_bytes(4, "little")
        + custody.digest
    ).digest()


class StagingMember:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use begin_member")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Staging member cannot be subclassed")

    def __copy__(self):
        raise TypeError("Staging member cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Staging member cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Staging member cannot be serialized")


@dataclass(frozen=True, slots=True)
class MemberEvidence:
    generation: str
    root_generation: str
    operation_binding: str
    coordinate: tuple[int, int]
    member_pin: tuple
    phase: str
    scratch_path: str
    creation: str
    accepted_prefix: int
    write_attempts: tuple
    original_returns: tuple | root.history.RecordedHistory
    original_errors: tuple
    active_span: tuple | None
    release_spent: bool
    cleanup: str
    capture_complete: bool
    write_outcome_unknown: bool
    final_publication: str = "not_attempted"
    member_finished: bool = False
    profile: str = "scratch_abort_v1"
    postimages: tuple = ()
    scratch_disposal: str = "not_attempted"
    directory_sync: str = "not_attempted"
    file_sync: str = "not_attempted"
    directory_node_sync: str = "not_attempted"
    finish_phase: str = "not_attempted"
    scratch_guard: object = None
    final_guard: object = None


class _BackedMemberEvidence(MemberEvidence):
    """Original closed values backed by the member's existing retained frame.

    There is no second receipt/registry/history. Decoded fields are historical
    values, never a fresh observation, reconstructed handle or close right.
    """

    __slots__ = ()

    def __getattribute__(self, name: str) -> Any:
        value = super().__getattribute__(name)
        if type(value) is _RetiredMember:
            return _backed_terminal_field(value, name)
        return value


_BACKED_FIELDS = ("write_attempts", "postimages", "scratch_guard", "final_guard")


def _frozen_rows(value: Any) -> Any:
    return tuple(_frozen_rows(part) for part in value) if type(value) is list else value


def _backed_terminal_field(record, name):
    if (
        type(record) is not _RetiredMember
        or _closed_custody_seal(record.custody, record.custody_size)
        != record.custody_seal
    ):
        raise ValueError("original_closed_member_backing_changed")
    encoded = _decode_closed_history(record.custody, record.custody_size)
    # Retirement already validates the complete canonical root frame, and the
    # custody seal above binds every byte. The terminal is its final element.
    # Decode that original suffix with the original JSON decoder instead of
    # materializing all earlier resource/history rows for each field access.
    marker = b"[" + json.dumps(CLOSED_TERMINAL_PROFILE).encode("ascii") + b","
    offset = encoded.rfind(marker)
    if offset < 1 or not encoded.endswith(b"]"):
        raise ValueError("complete_closed_member_backing_required")
    tail = json.loads(encoded[offset:-1])
    if type(tail) is not list or len(tail) != 5 or tail[0] != CLOSED_TERMINAL_PROFILE:
        raise ValueError("original_closed_terminal_fields_required")
    if name == "write_attempts":
        return tuple(
            (record.source_keys[row[0]], *_frozen_rows(row[1:])) for row in tail[1]
        )
    if name == "postimages":
        return tuple(
            physical._FilePostimageVerification(
                physical._FilePostimageObservation(*_frozen_rows(row[0])),
                physical.ConfinedFileReadCleanup(*_frozen_rows(row[1])),
            )
            for row in tail[2]
        )
    if name in ("scratch_guard", "final_guard"):
        value = tail[3 if name == "scratch_guard" else 4]
        return (
            None
            if value is None
            else root.history._stat_from_bytes(bytes.fromhex(value))
        )
    raise AttributeError(name)


def snapshot_closed_member_terminal(handle):
    """Original-owner validated full detached values; no IO or authority."""
    if type(handle) is not StagingMember or handle not in _HANDLES:
        raise StagingMemberRefusal("original_staging_member_required")
    record = _HANDLES[handle]
    if type(record) is not _RetiredMember:
        raise StagingMemberRefusal("original_retired_member_required")
    terminal = _validate_retired(record)
    return MemberEvidence(*(getattr(terminal, f.name) for f in fields(MemberEvidence)))


@dataclass(frozen=True, slots=True, eq=False)
class MemberProgress:
    """Original per-span return; complete history remains in the same owner.

    This is not a terminal, cleanup claim, independent history or renewed
    write right. The final/failed MemberEvidence retains the entire history.
    """

    generation: str
    root_generation: str
    operation_binding: str
    coordinate: tuple[int, int]
    member_pin: tuple
    source_span_key: object
    prior_prefix: int
    accepted_prefix: int
    first_attempt: int
    original_attempts: tuple
    capture_complete: bool
    profile: str = PROGRESS_PROFILE


class StagingMemberRefusal(RuntimeError):
    def __init__(self, code, handle=None, state=None, cause=None):
        super().__init__(code)
        self.code = code
        self.handle = handle
        self.original_state = state
        self.original_cause = cause
        self.evidence = None if state is None else _evidence(state)


class _ProgressRegistry:
    """Shared storage of original objects/seals, never a source of rights."""

    def __init__(self):
        self.pages = tuple([] for _ in range(32))
        self.pending = None
        self.failure = None
        self.charged = 0

    def _find(self, key):
        if type(key) is not int or not 0 <= key < 2**64:
            raise ValueError("original_progress_identity_required")
        page = self.pages[(key >> 4) & 31]
        if type(page) is not list or len(page) % 3:
            raise ValueError("original_progress_storage_changed")
        lower, upper = 0, len(page) // 3
        while lower < upper:
            middle = (lower + upper) // 2
            if id(page[middle * 3 + 1]) < key:
                lower = middle + 1
            else:
                upper = middle
        return page, lower * 3

    def get(self, owner, key, default=None):
        if self.pending is not None and self.pending[1] == key:
            raise ValueError("original_progress_capture_incomplete")
        page, offset = self._find(key)
        if offset == len(page) or id(page[offset + 1]) != key:
            return default
        if page[offset] is not owner:
            return default
        if (
            type(page[offset + 1]) is not MemberProgress
            or type(page[offset + 2]) is not bytes
            or len(page[offset + 2]) != 32
        ):
            raise ValueError("original_progress_storage_changed")
        return page[offset + 1], page[offset + 2]

    @staticmethod
    def _store(page, offset, owner, value, seal):
        page[offset:offset] = owner, value, seal

    def insert(self, owner, key, data):
        if self.pending is not None or self.failure is not None:
            raise ValueError("original_progress_capture_spent")
        if (
            type(data) is not tuple
            or len(data) != 2
            or type(data[0]) is not MemberProgress
            or id(data[0]) != key
            or type(data[1]) is not bytes
            or len(data[1]) != 32
        ):
            raise ValueError("original_progress_record_required")
        page, offset = self._find(key)
        if offset < len(page) and id(page[offset + 1]) == key:
            raise ValueError("original_progress_already_enrolled")
        self.charged += 1
        self.pending = owner, key, data
        try:
            self._store(page, offset, owner, *data)
            owner.count += 1
            self.pending = None
        except BaseException as cause:
            self.failure = cause
            raise


class _ProgressView:
    __slots__ = ("count", "registry")

    def __init__(self, registry):
        self.registry = registry
        self.count = 0

    def __len__(self):
        return self.count

    def get(self, key, default=None):
        return self.registry.get(self, key, default)

    def __setitem__(self, key, data):
        self.registry.insert(self, key, data)


@dataclass(slots=True)
class _WriteAttempt:
    source_key: object
    member_offset: int
    requested: int
    invocation: str = "not_invoked"
    original_return: object = None
    accepted: int | None = None


@dataclass(slots=True)
class _State:
    root_handle: root.StagingRoot
    parent: root._State
    coordinate: tuple[int, int]
    pin: tuple
    scratch: str
    generation: str = field(default_factory=lambda: uuid4().hex)
    phase: str = "acquiring"
    ledger: physical._ReadLedger = field(default_factory=physical._ReadLedger)
    descriptor: int | None = None
    identity: tuple | None = None
    creation: str = "not_attempted"
    generator: object = None
    write_step: object = None
    returns: list | root.history.GuardHistory = field(default_factory=list)
    errors: list = field(default_factory=list)
    attempts: list[_WriteAttempt] = field(default_factory=list)
    keys: list = field(default_factory=list)
    active_span: tuple | None = None
    release_spent: bool = False
    cleanup: str = "not_released"
    capture_complete: bool = True
    busy: bool = False
    ordered: bool = False
    terminal_profile: str | None = None
    terminal_capture_original: MemberEvidence | None = None
    parent_fd: int | None = None
    path_parents: list = field(default_factory=list)
    mode: int = 0o600
    finish_spent: bool = False
    finished: bool = False
    publication: str = "not_attempted"
    postimages: list = field(default_factory=list)
    read_ledgers: list = field(default_factory=list)
    scratch_disposal: str = "not_attempted"
    directory_sync: str = "not_attempted"
    file_sync: str = "not_attempted"
    directory_node_sync: str = "not_attempted"
    finish_phase: str = "not_attempted"
    scratch_guard: object = None
    final_guard: object = None
    residual_scratch_paths: list = field(default_factory=list)
    effects: list = field(default_factory=list)
    progress_seals: dict | _ProgressView = field(default_factory=dict)
    root_fd: int | None = None  # original scratch-disposal helper must not close parent

    @property
    def accepted(self):
        return sum(a.accepted for a in self.attempts if a.accepted is not None)


@dataclass(frozen=True, slots=True)
class _RetiredMember:
    """Historical complete receipt, never a descriptor/disposal capability."""

    root_handle: root.StagingRoot
    parent: root._State
    terminal: MemberEvidence
    terminal_seal: bytes
    custody: object
    custody_size: int
    custody_seal: bytes
    progress_seals: dict | _ProgressView
    source_keys: tuple = ()


def _terminal_seal(value, *, backed=False):
    rows = []
    item: Any
    for declared in fields(MemberEvidence):
        if backed and declared.name in _BACKED_FIELDS:
            record = object.__getattribute__(value, declared.name)
            if type(record) is not _RetiredMember or record.terminal is not value:
                raise ValueError("original_closed_terminal_reference_changed")
            # Capture proves the complete original values round-trip before
            # this seal is enrolled. Revalidation checks the unchanged entire
            # custody bytes separately; it need not decode each backed field
            # merely to prove that the same original representation remains.
            item = (
                "original_closed_terminal_field",
                declared.name,
                id(record),
                record.custody_size,
                record.custody_seal,
                tuple(id(key) for key in record.source_keys),
            )
        else:
            item = getattr(value, declared.name)
        if declared.name == "write_attempts" and not backed:
            item = tuple(
                (("original_source_key", id(type(row[0])), id(row[0])), *row[1:])
                for row in item
            )
        elif type(item) is os.stat_result:
            item = ("original_stat_values", root.history._stat_bytes(item))
        elif type(item) is root.history.RecordedHistory:
            item = ("original_history_prefix", root.history.history_seal(item))
        rows.append((declared.name, item))
    return root.history.value_seal(tuple(rows))


def _closed_ledger_values(ledger: physical._ReadLedger):
    if (
        type(ledger) is not physical._ReadLedger
        or not root._ledger_settled(ledger)
        or ledger.first_cleanup_error is not None
        or ledger.private_root is not None
    ):
        raise ValueError("original_confirmed_closed_ledger_required")
    resources = []
    for value in ledger.resources:
        if type(value) is not physical._ReadResource:
            raise TypeError("original_closed_resource_required")
        row = tuple(getattr(value, declared.name) for declared in fields(value))
        if any(type(part) not in (int, str, bool, type(None)) for part in row):
            raise TypeError("closed_resource_scalar_required")
        resources.append(row)
    return (
        tuple(resources),
        ledger.stage,
        ledger.acquisition_unknown,
        ledger.release_unknown,
        ledger.context_unknown,
        ledger.attempted,
        ledger.attempts_unknown,
        ledger.closed,
        tuple(ledger.diagnostics),
        None,
        None,
    )


def _capture_closed_member(state, terminal):
    """Capture known settled facts before replacing computational custody."""
    if (
        not state.finished
        or not state.finish_spent
        or not state.release_spent
        or state.cleanup != "confirmed"
        or not state.capture_complete
        or state.errors
        or state.active_span is not None
        or state.returns.failure is not None
        or (
            state.pin[0] == "file"
            and (
                not isinstance(state.generator, types.GeneratorType)
                or state.generator.gi_frame is not None
            )
        )
    ):
        raise ValueError("complete_original_member_required_for_retirement")
    values = (
        "aware.filesystem.closed-member-history.v1",
        state.generation,
        state.parent.generation,
        state.parent.request_digest,
        state.coordinate,
        state.pin,
        state.scratch,
        state.phase,
        state.identity,
        state.creation,
        state.descriptor,
        state.parent_fd,
        tuple(state.path_parents),
        state.mode,
        state.finish_spent,
        state.finished,
        state.publication,
        state.scratch_disposal,
        state.directory_sync,
        state.file_sync,
        state.directory_node_sync,
        state.finish_phase,
        tuple(state.residual_scratch_paths),
        tuple(state.effects),
        _closed_ledger_values(state.ledger),
        tuple(_closed_ledger_values(value) for value in state.read_ledgers),
        "exhausted_original_writer" if state.generator is not None else "not_created",
        False,  # Historical data cannot authorize write, close or observation.
    )
    source_keys = ()
    original_terminal = terminal
    if state.terminal_profile is not None:
        state.terminal_capture_original = terminal
        source_keys = tuple(state.keys)
        rows = []
        for row in terminal.write_attempts:
            index = next(
                (i for i, key in enumerate(source_keys) if key is row[0]), None
            )
            if index is None:
                raise ValueError("original_terminal_source_key_required")
            rows.append((index, *row[1:]))
        postimages = tuple(
            (
                tuple(
                    getattr(item.observation, f.name)
                    for f in fields(physical._FilePostimageObservation)
                ),
                tuple(
                    getattr(item.cleanup, f.name)
                    for f in fields(physical.ConfinedFileReadCleanup)
                ),
            )
            for item in terminal.postimages
        )
        values += (
            (
                CLOSED_TERMINAL_PROFILE,
                tuple(rows),
                postimages,
                None
                if terminal.scratch_guard is None
                else root.history._stat_bytes(terminal.scratch_guard).hex(),
                None
                if terminal.final_guard is None
                else root.history._stat_bytes(terminal.final_guard).hex(),
            ),
        )
        terminal = _BackedMemberEvidence(
            *(getattr(terminal, f.name) for f in fields(MemberEvidence))
        )
    body = json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode()
    if len(body) > 262144:
        raise ValueError("closed_member_history_capacity")
    # Bound and prove exact canonical bytes before one replacement commit.
    if (
        json.dumps(json.loads(body), ensure_ascii=False, separators=(",", ":")).encode()
        != body
    ):
        raise ValueError("closed_member_history_roundtrip")
    encoded = root.history._low_memory_block(body)
    if _decode_closed_history(encoded, len(body)) != body:
        raise ValueError("closed_member_compression_roundtrip")
    custody = (
        _closed_body_storage().append(body)
        if state.terminal_profile is not None
        else encoded
    )
    record = _RetiredMember(
        state.root_handle,
        state.parent,
        terminal,
        _terminal_seal(terminal),
        custody,
        len(body),
        _closed_custody_seal(custody, len(body)),
        state.progress_seals,
        source_keys,
    )
    if state.terminal_profile is not None:
        for name in _BACKED_FIELDS:
            object.__setattr__(terminal, name, record)
        if _terminal_seal(terminal) != _terminal_seal(original_terminal):
            raise ValueError("complete_original_terminal_backing_roundtrip_required")
        object.__setattr__(
            record, "terminal_seal", _terminal_seal(terminal, backed=True)
        )
    return record


def _decode_closed_history(encoded, size):
    from ._observation_receipt import _SharedBody

    if type(encoded) is _SharedBody:
        if (
            _CLOSED_BODY_BACKING is None
            or type(size) is not int
            or not 0 < size <= 262144
        ):
            raise ValueError("bounded_closed_member_history_required")
        body = _CLOSED_BODY_BACKING.read(encoded)
        if len(body) != size:
            raise ValueError("original_closed_member_size_changed")
        return body
    if type(encoded) is not bytes or type(size) is not int or not 0 < size <= 262144:
        raise ValueError("bounded_closed_member_history_required")
    if len(encoded) > size + 1024:
        raise ValueError("bounded_closed_member_frame_required")
    decoder = root.history.zlib.decompressobj()
    body = decoder.decompress(encoded, size + 1)
    if (
        len(body) != size
        or not decoder.eof
        or decoder.unused_data
        or decoder.unconsumed_tail
    ):
        raise ValueError("complete_closed_member_history_required")
    return body


def _validate_retired(record):
    if (
        type(record) is not _RetiredMember
        or record.parent.retired_members.get(record.terminal.generation) is not record
        or type(record.custody_size) is not int
        or not 0 < record.custody_size <= 262144
        or _closed_custody_seal(record.custody, record.custody_size)
        != record.custody_seal
        or _terminal_seal(
            record.terminal, backed=type(record.terminal) is _BackedMemberEvidence
        )
        != record.terminal_seal
    ):
        raise ValueError("original_retired_member_evidence_changed")
    return record.terminal


def observe_closed_member_history(member):
    """IO-free exact historical bytes; no live resource reconstruction."""
    if type(member) is not StagingMember or member not in _HANDLES:
        raise StagingMemberRefusal("original_staging_member_required")
    record = _HANDLES[member]
    if type(record) is not _RetiredMember:
        raise StagingMemberRefusal("original_retired_member_required")
    root._require(record.root_handle)
    _validate_retired(record)
    return _decode_closed_history(record.custody, record.custody_size)


_HANDLES = WeakKeyDictionary()
_CUSTODY = {}


def _evidence(state):
    if type(state) is _RetiredMember:
        return _validate_retired(state)
    return MemberEvidence(
        state.generation,
        state.parent.generation,
        state.parent.request_digest,
        state.coordinate,
        state.pin,
        state.phase,
        _scratch_path(state),
        state.creation,
        state.accepted,
        tuple(
            (
                a.source_key,
                a.member_offset,
                a.requested,
                a.invocation,
                a.original_return,
                a.accepted,
            )
            for a in state.attempts
        ),
        root.history.snapshot_returns(state.returns),
        tuple(state.errors),
        state.active_span,
        state.release_spent,
        state.cleanup,
        state.capture_complete
        and (
            type(state.returns) is not root.history.GuardHistory
            or state.returns.failure is None
        ),
        any(
            a.invocation != "not_invoked" and a.accepted is None for a in state.attempts
        ),
        state.publication,
        state.finished,
        ORDERED_PROFILE if state.ordered else "scratch_abort_v1",
        tuple(state.postimages),
        state.scratch_disposal,
        state.directory_sync,
        state.file_sync,
        state.directory_node_sync,
        state.finish_phase,
        state.scratch_guard,
        state.final_guard,
    )


def _progress_snapshot(value):
    def seal(item, recur):
        if type(item) is tuple:
            return "tuple", tuple(recur(part, recur) for part in item)
        if type(item) in (str, int, bool, type(None)):
            return type(item).__name__, item
        return "reference", id(type(item)), id(item)

    # Only built-in scalar/tuple values above reach repr; no caller repr hook.
    # Keep one fixed-size private seal, not a second retained field graph.
    body = repr(
        tuple(seal(getattr(value, f.name), seal) for f in fields(MemberProgress))
    )
    return hashlib.sha256(body.encode("utf-8")).digest()


def _span_progress(state, source_key, before, first):
    if (
        state.terminal_profile is not None
        and type(state.progress_seals) is dict
        and not state.progress_seals
        and state.parent.history_pool is not None
    ):
        pool = state.parent.history_pool
        registry = getattr(pool, "_member_progress_registry", None)
        if registry is None:
            registry = _ProgressRegistry()
            pool._member_progress_registry = registry
        if type(registry) is not _ProgressRegistry:
            raise ValueError("original_progress_registry_required")
        state.progress_seals = _ProgressView(registry)
    value = MemberProgress(
        state.generation,
        state.parent.generation,
        state.parent.request_digest,
        state.coordinate,
        state.pin,
        source_key,
        before,
        state.accepted,
        first,
        tuple(
            (
                a.source_key,
                a.member_offset,
                a.requested,
                a.invocation,
                a.original_return,
                a.accepted,
            )
            for a in state.attempts[first:]
        ),
        state.capture_complete,
    )
    # Retain the genuine return and its immutable field seal together. No
    # history prefix is recopied; each raw native attempt appears once here.
    state.progress_seals[id(value)] = value, _progress_snapshot(value)
    return value


def validate_member_progress(
    member, value: object, *, expected_source_span_key
) -> MemberProgress:
    """IO-free original-owner correlation; detached copies confer no rights."""
    state = _HANDLES.get(member) if type(member) is StagingMember else None
    if type(state) is _RetiredMember:
        root._require(state.root_handle)
        terminal = _validate_retired(state)
        retained = state.progress_seals.get(id(value))
        if (
            type(value) is not MemberProgress
            or retained is None
            or retained[0] is not value
            or _progress_snapshot(value) != retained[1]
            or value.source_span_key is not expected_source_span_key
            or value.generation != terminal.generation
            or value.root_generation != terminal.root_generation
            or value.operation_binding != terminal.operation_binding
            or not _pin_matches(value.member_pin, terminal.member_pin)
        ):
            raise StagingMemberRefusal("staging_progress_binding_mismatch", member)
        return value
    state = _require(member)
    retained = state.progress_seals.get(id(value))
    if (
        type(value) is not MemberProgress
        or retained is None
        or retained[0] is not value
        or _progress_snapshot(value) != retained[1]
        or value.source_span_key is not expected_source_span_key
        or value.generation != state.generation
        or value.root_generation != state.parent.generation
        or value.operation_binding != state.parent.request_digest
        or not _pin_matches(value.member_pin, state.pin)
    ):
        raise StagingMemberRefusal("staging_progress_binding_mismatch", member, state)
    return value


def _scratch_path(state):
    prefix = state.pin[1].rpartition("/")[0]
    return (
        ""
        if state.pin[0] == "directory"
        else (prefix + "/" if prefix else "") + state.scratch
    )


def _require(handle):
    if type(handle) is not StagingMember or handle not in _HANDLES:
        raise StagingMemberRefusal("original_staging_member_required")
    state = _HANDLES[handle]
    parent = root._require(state.root_handle)
    if type(state) is _RetiredMember:
        _validate_retired(state)
        raise StagingMemberRefusal("staging_member_retired_spent", handle)

    if state.busy:
        raise StagingMemberRefusal("staging_member_reentrant", handle, state)
    if not state.release_spent and parent.active_child is not state:
        raise StagingMemberRefusal("staging_member_parent_mismatch", handle, state)
    return state


def _pin_matches(expected, retained):
    return (
        type(expected) is tuple
        and len(expected) == len(retained)
        and all(type(a) is type(b) for a, b in zip(expected, retained, strict=True))
        and expected == retained
    )


def _current(state):
    root._bookends(state.parent)
    if state.parent.history_profile in (
        root.RETAINED_DIRECTORY_PROFILE,
        root.RETIRED_MEMBER_PROFILE,
    ):
        if not root._plan_matches(state.parent.plan, state.parent.plan_seal):
            raise ValueError("staging_plan_changed")
    elif root._plan_seal(state.parent.plan) != state.parent.plan_seal:
        raise ValueError("staging_plan_changed")
    for parent_fd, name, fd, expected in state.path_parents:
        opened = root._observed(state, "ancestor_opened", os.fstat, fd)
        named = root._observed(
            state,
            "ancestor_named",
            os.stat,
            name,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        if root._identity(opened) != expected or root._identity(named) != expected:
            raise ValueError("staging_member_ancestor_changed")
    if state.descriptor is not None:
        row = next(
            r for r in state.ledger.resources if r.descriptor == state.descriptor
        )
        if row.spent:
            guarded = (
                state.final_guard
                if state.publication == "applied"
                else state.scratch_guard
            )
            if guarded is not None and state.publication in (
                "not_attempted",
                "applied",
            ):
                leaf = (
                    state.pin[1].rsplit("/", 1)[-1]
                    if state.publication == "applied"
                    else state.scratch
                )
                named = root._observed(
                    state,
                    "finished_file_guard",
                    os.stat,
                    leaf,
                    dir_fd=state.parent_fd,
                    follow_symlinks=False,
                )
                if not physical._same_stat(guarded, named):
                    raise ValueError("staging_finished_file_changed")
            return  # postimage owner verifies closed-file bytes; never reuse fd
        opened = root._observed(state, "scratch_stat", os.fstat, state.descriptor)
        named = root._observed(
            state,
            "scratch_named",
            os.stat,
            state.pin[1].rsplit("/", 1)[-1]
            if state.pin[0] == "directory"
            else state.scratch,
            dir_fd=state.parent_fd,
            follow_symlinks=False,
        )
        if state.pin[0] == "directory":
            if (
                not stat.S_ISDIR(opened.st_mode)
                or root._identity(opened) != root._identity(named)
                or (opened.st_dev, opened.st_ino) != state.identity
                or opened.st_uid != os.geteuid()
                or stat.S_IMODE(opened.st_mode) != state.mode
            ):
                raise ValueError("staging_directory_changed")
        elif (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or opened.st_uid != os.geteuid()
            or stat.S_IMODE(opened.st_mode) != state.mode
            or (opened.st_dev, opened.st_ino) != state.identity
            or not physical._same_stat(opened, named)
            or opened.st_size != state.accepted
        ):
            raise ValueError("staging_member_changed")


class _MemberIO:
    """Original-owner adapter only; never accepted from a consumer."""

    def __init__(self, state):
        self.state = state

    def open(self, name, flags, mode, *, dir_fd):
        state = self.state
        if name != state.scratch or dir_fd != state.parent_fd:
            raise ValueError("staging_scratch_binding_changed")
        state.creation = "unknown"
        fd = state.ledger.open(name, flags | os.O_CLOEXEC, mode=mode, dir_fd=dir_fd)
        state.descriptor = fd
        state.creation = "applied"
        state.returns.append(("scratch_open", fd))
        info = root._observed(state, "scratch_acquired_stat", os.fstat, fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_uid != os.geteuid()
        ):
            raise ValueError("staging_scratch_identity_invalid")
        state.identity = info.st_dev, info.st_ino
        return fd

    def write(self, descriptor, view):
        state = self.state
        if descriptor != state.descriptor or state.active_span is None:
            raise ValueError("staging_write_binding_changed")
        if len(state.attempts) >= MAX_WRITE_CALLS:
            raise ValueError("staging_native_write_count_exceeded")
        attempt = _WriteAttempt(state.active_span[0], state.accepted, len(view))
        state.attempts.append(attempt)
        attempt.invocation = "unknown"
        value = os.write(descriptor, view)
        attempt.original_return = value
        attempt.invocation = "returned"
        if type(value) is not int or not 0 < value <= len(view):
            raise ValueError("staging_native_write_return_invalid")
        attempt.accepted = value
        return value

    def close(self, descriptor):
        if descriptor != self.state.descriptor:
            raise ValueError("staging_close_binding_changed")
        self.state.ledger.close(descriptor)

    def fsync(self, descriptor):
        if descriptor != self.state.descriptor:
            raise ValueError("staging_sync_binding_changed")
        return root._observed(self.state, "scratch_sync", os.fsync, descriptor)


def begin_member(stage, *, partition_ordinal, member_ordinal, expected_member_pin):
    return _begin_member(
        stage,
        partition_ordinal=partition_ordinal,
        member_ordinal=member_ordinal,
        expected_member_pin=expected_member_pin,
        ordered=False,
    )


def begin_ordered_member(
    stage,
    *,
    profile,
    partition_ordinal,
    member_ordinal,
    expected_member_pin,
    terminal_profile=None,
):
    if type(profile) is not str or profile != ORDERED_PROFILE:
        raise StagingMemberRefusal("explicit_ordered_staging_profile_required")
    return _begin_member(
        stage,
        partition_ordinal=partition_ordinal,
        member_ordinal=member_ordinal,
        expected_member_pin=expected_member_pin,
        ordered=True,
        terminal_profile=terminal_profile,
    )


def _next_coordinate(parent):
    group = next(g for g in parent.plan_seal if g[0] == parent.namespace)
    p, m = parent.next_coordinate
    while p < len(group[1]) and m >= len(group[1][p][1]):
        p, m = p + 1, 0
    return p, m


def _walk_parent(state):
    descriptor = state.parent.root_fd
    prefix = []
    for name in state.pin[1].split("/")[:-1]:
        if state.parent.history_pool is not None:
            name = state.parent.history_pool.path_name(name)
        prefix.append(name)
        entry = state.parent.completed_entries.get("/".join(prefix))
        if entry is None or entry[0][0] != "directory":
            raise ValueError("completed_original_parent_required")
        if state.parent.history_profile in (
            root.RETAINED_DIRECTORY_PROFILE,
            root.RETIRED_MEMBER_PROFILE,
        ):
            row = root._borrow_directory(
                state.parent,
                state,
                path="/".join(prefix),
                parent_fd=descriptor,
                name=name,
                expected=entry[1],
            )
            child = row[2]
        else:
            child = state.ledger.open(
                name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=descriptor,
            )
            opened = root._observed(state, "parent_acquired", os.fstat, child)
            if root._identity(opened) != entry[1]:
                raise ValueError("completed_parent_changed")
            row = descriptor, name, child, entry[1]
        state.path_parents.append(
            state.parent.history_pool.path_row(row)
            if state.parent.history_pool is not None
            else row
        )
        descriptor = child
    state.parent_fd = descriptor


def _begin_member(
    stage,
    *,
    partition_ordinal,
    member_ordinal,
    expected_member_pin,
    ordered,
    terminal_profile=None,
):
    parent = root._require(stage)
    with parent.lock:
        if terminal_profile is not None and (
            terminal_profile != CLOSED_TERMINAL_PROFILE
            or parent.history_profile != root.RETIRED_MEMBER_PROFILE
            or not ordered
        ):
            raise StagingMemberRefusal("explicit_closed_terminal_profile_required")
        if parent.phase != "created" or parent.active_child is not None:
            raise StagingMemberRefusal("staging_member_begin_unavailable")
        selected_profile = ORDERED_PROFILE if ordered else "scratch_abort_v1"
        if (
            parent.member_profile is not None
            and parent.member_profile != selected_profile
        ):
            raise StagingMemberRefusal("staging_member_profile_changed")
        coordinate = _next_coordinate(parent) if ordered else (0, 0)
        if (
            type(partition_ordinal) is not int
            or type(member_ordinal) is not int
            or (partition_ordinal, member_ordinal) != coordinate
        ):
            raise StagingMemberRefusal("staging_initial_member_coordinate_required")
        group = next(g for g in parent.plan_seal if g[0] == parent.namespace)
        if coordinate[0] >= len(group[1]):
            raise StagingMemberRefusal("staging_member_missing")
        rows = group[1][coordinate[0]][1]
        if not rows:
            raise StagingMemberRefusal("staging_member_missing")
        pin = rows[coordinate[1]]
        if not ordered and (pin[0] != "file" or "/" in pin[1]):
            raise StagingMemberRefusal("staging_flat_file_checkpoint_only")
        if not _pin_matches(expected_member_pin, pin):
            raise StagingMemberRefusal("staging_member_pin_mismatch")
        state = _State(
            stage,
            parent,
            coordinate,
            pin,
            ".aware-stage-" + uuid4().hex,
            ordered=ordered,
            terminal_profile=terminal_profile,
            parent_fd=parent.root_fd,
        )
        if parent.history_pool is not None:
            state.returns = root.history.GuardHistory(parent.history_pool)
        handle = object.__new__(StagingMember)
        _HANDLES[handle] = state
        parent.busy, state.busy = True, True
        try:
            # Original handle enrollment precedes child publication and all IO.
            # A failed publication still returns the original releasable handle.
            parent.active_child = state
            parent.member_profile = selected_profile
            _CUSTODY[id(state)] = state
            if ordered:
                _walk_parent(state)
            _current(state)
            if pin[0] == "directory":
                leaf = pin[1].rsplit("/", 1)[-1]
                existing = parent.completed_entries.get(pin[1])
                if existing is None:
                    state.mode = 0o700
                    state.creation = "unknown"
                    root._observed(
                        state,
                        "directory_create",
                        root.retained._mkdir_explicit,
                        leaf,
                        mode=0o700,
                        dir_fd=state.parent_fd,
                    )
                    state.creation = "applied"
                else:
                    if existing[0] != pin:
                        raise ValueError("shared_directory_pin_changed")
                    state.creation, state.mode = "none", pin[2]
                named = root._observed(
                    state,
                    "directory_named",
                    os.stat,
                    leaf,
                    dir_fd=state.parent_fd,
                    follow_symlinks=False,
                )
                state.descriptor = state.ledger.open(
                    leaf,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                    dir_fd=state.parent_fd,
                )
                opened = root._observed(
                    state, "directory_opened", os.fstat, state.descriptor
                )
                if root._identity(named) != root._identity(opened) or (
                    existing is not None and root._identity(opened) != existing[1]
                ):
                    raise ValueError("directory_creation_bookend_mismatch")
                state.identity = opened.st_dev, opened.st_ino
                _current(state)
                state.phase = "active"
                return handle, _evidence(state)
            if state.parent_fd is None:
                raise ValueError("staging_member_parent_unavailable")
            state.generator = physical._write_temporary_steps(
                parent_descriptor=state.parent_fd,
                name=state.scratch,
                content=b"",
                mode=0o600,
                _io=_MemberIO(state),
                _path=pin[1],
            )
            step = next(state.generator)
            if step.kind != "scratch_create":
                raise ValueError("original_scratch_create_step_required")
            fd = cast(Callable[..., Any], step.function)(
                *step.arguments, **step.keywords
            )
            state.write_step = state.generator.send(fd)
            if (
                state.write_step.kind != "scratch_write"
                or state.write_step.function is not physical._write_confined_bytes
            ):
                raise ValueError("original_scratch_write_step_required")
            _current(state)
            state.phase = "active"
            return handle, _evidence(state)
        except BaseException as cause:
            state.phase, parent.phase = "failed", "failed"
            state.errors.append(cause)
            raise StagingMemberRefusal(
                "staging_member_acquisition_failed", handle, state, cause
            ) from cause
        finally:
            parent.busy, state.busy = False, False


def write_span(
    member,
    *,
    source_span_key,
    body,
    source_offset,
    length,
    expected_member_offset,
    progress_profile=None,
):
    state = _require(member)
    parent = state.parent
    with parent.lock:
        if progress_profile is not None and (
            type(progress_profile) is not str or progress_profile != PROGRESS_PROFILE
        ):
            raise StagingMemberRefusal(
                "staging_progress_profile_unsupported", member, state
            )
        if state.phase != "active":
            raise StagingMemberRefusal("staging_member_write_spent", member, state)
        if (
            state.pin[0] != "file"
            or state.finish_spent
            or type(body) is not bytes
            or len(body) > 65536
            or type(source_offset) is not int
            or type(length) is not int
            or not 0 <= source_offset < len(body)
            or not 1 <= length <= 65536
            or source_offset + length > len(body)
            or type(expected_member_offset) is not int
            or expected_member_offset != state.accepted
            or state.accepted + length > state.pin[3]
            or source_span_key is None
            or any(key is source_span_key for key in state.keys)
            or len(state.keys) >= MAX_SPANS
        ):
            raise StagingMemberRefusal("staging_span_invalid", member, state)
        state.keys.append(source_span_key)
        state.active_span = source_span_key, body, source_offset, length
        parent.busy, state.busy = True, True
        before = state.accepted
        first_attempt = len(state.attempts)
        try:
            _current(state)
            step = state.write_step
            # Exact original loop; its internal IO adapter retains and validates
            # each actual return before the loop may consume a known suffix.
            step.function(
                step.arguments[0],
                step.arguments[1],
                body[source_offset : source_offset + length],
            )
            _current(state)
            state.active_span = None
            evidence = (
                _evidence(state)
                if progress_profile is None
                else _span_progress(state, source_span_key, before, first_attempt)
            )
            return state.accepted - before, evidence
        except BaseException as cause:
            state.errors.append(cause)
            state.phase, parent.phase = "failed", "failed"
            raise StagingMemberRefusal(
                "staging_member_write_failed", member, state, cause
            ) from cause
        finally:
            parent.busy, state.busy = False, False


class _AbortMember(BaseException):
    pass


def release_member(member, *, expected_operation_binding, expected_member_pin):
    state = _require(member)
    parent = state.parent
    with parent.lock:
        if state.release_spent or state.phase not in ("active", "failed"):
            raise StagingMemberRefusal("staging_member_release_spent", member, state)
        if (
            type(expected_operation_binding) is not str
            or expected_operation_binding != parent.request_digest
            or not _pin_matches(expected_member_pin, state.pin)
        ):
            raise StagingMemberRefusal(
                "staging_member_release_binding_mismatch", member, state
            )
        state.release_spent, parent.busy, state.busy = True, True, True
        parent.phase, state.phase, state.cleanup = "failed", "release_spent", "unknown"
        abort = _AbortMember()
        try:
            if state.generator is not None:
                try:
                    step = state.generator.throw(abort)
                except (_AbortMember, StopIteration):
                    pass
                else:
                    if step.kind != "scratch_close" or not step.cleanup:
                        raise ValueError("original_scratch_close_step_required")
                    value = step.function(*step.arguments, **step.keywords)
                    try:
                        state.generator.send(value)
                    except (_AbortMember, StopIteration):
                        pass
                    else:
                        raise ValueError("original_abort_terminal_required")
            settled = root._settle_owned_resources(state)
            for ledger in state.read_ledgers:
                settled = root._settle_owned_resources(state, ledger=ledger) and settled
            state.cleanup = "confirmed" if settled else "unknown"
            state.phase = "released" if settled else "release_unknown"
            terminal = _evidence(state)
            parent.child_terminals.append(terminal)
            if settled:
                parent.active_child = None
                _CUSTODY.pop(id(state), None)
            return terminal
        except BaseException as cause:
            state.errors.append(cause)
            state.phase, state.capture_complete = "release_unknown", False
            raise StagingMemberRefusal(
                "staging_member_release_failed", member, state, cause
            ) from cause
        finally:
            parent.busy, state.busy = False, False


def observe_staging_member(member):
    record = _HANDLES.get(member) if type(member) is StagingMember else None
    if type(record) is _RetiredMember:
        root._require(record.root_handle)
        return _validate_retired(record)
    return _evidence(_require(member))


def _verify_member_file(state, leaf):
    ledger = physical._ReadLedger()
    state.read_ledgers.append(ledger)
    _current(state)
    before = root._observed(
        state,
        "postimage_named_before",
        os.stat,
        leaf,
        dir_fd=state.parent_fd,
        follow_symlinks=False,
    )
    result = physical._verify_confined_file_postimage(
        parent_descriptor=state.parent_fd,
        leaf=leaf,
        expected_identity=state.identity,
        size_bytes=state.pin[3],
        content_digest=state.pin[4],
        mode=state.pin[2],
        _ledger=ledger,
    )
    state.postimages.append(result)
    root._validate_closed_resources(state, ledger=ledger)
    if (
        type(result) is not physical._FilePostimageVerification
        or type(result.observation) is not physical._FilePostimageObservation
        or len(ledger.resources) != 1
        or ledger.resources[0].acquisition_state != "acquired"
        or not root._ledger_settled(ledger)
        or result.cleanup != ledger.snapshot()
    ):
        raise ValueError("original_postimage_custody_unconfirmed")
    expected = leaf, state.identity, state.pin[3], state.pin[4], state.pin[2]

    def fields():
        value = result.observation
        return (
            value.leaf,
            value.identity,
            value.size_bytes,
            value.content_digest,
            value.mode,
        )

    if fields() != expected:
        raise ValueError("original_postimage_binding_changed")
    _current(state)
    after = root._observed(
        state,
        "postimage_named_after",
        os.stat,
        leaf,
        dir_fd=state.parent_fd,
        follow_symlinks=False,
    )
    if not physical._same_stat(before, after):
        raise ValueError("postimage_changed_across_final_guards")
    if fields() != expected or result.cleanup != ledger.snapshot():
        raise ValueError("original_postimage_changed_after_guards")
    if leaf == state.scratch:
        state.scratch_guard = after
    else:
        state.final_guard = after
    return result


def _finish_writer(state):
    value = root._observed(
        state, "final_file_mode", os.fchmod, state.descriptor, state.pin[2]
    )
    if value is not None:
        raise ValueError("staging_mode_return_invalid")
    state.mode = state.pin[2]
    _current(state)
    step = state.generator.send(None)
    if step.kind != "scratch_sync":
        raise ValueError("original_scratch_sync_step_required")
    state.file_sync = "unknown"
    value = step.function(*step.arguments, **step.keywords)
    if value is not None:
        raise ValueError("staging_sync_return_invalid")
    state.file_sync = "confirmed"
    step = state.generator.send(value)
    if step.kind != "scratch_close" or not step.cleanup:
        raise ValueError("original_scratch_close_step_required")
    value = step.function(*step.arguments, **step.keywords)
    try:
        state.generator.send(value)
    except StopIteration:
        pass
    else:
        raise ValueError("original_writer_terminal_required")
    root._validate_closed_resources(state)
    if state.ledger.release_unknown or state.ledger.first_cleanup_error is not None:
        raise ValueError("original_writer_close_unconfirmed")


def _publish_file(state):
    leaf = state.pin[1].rsplit("/", 1)[-1]
    state.publication = "unknown"
    try:
        result = root._observed(
            state,
            "publish_link",
            os.link,
            state.scratch,
            leaf,
            src_dir_fd=state.parent_fd,
            dst_dir_fd=state.parent_fd,
            follow_symlinks=False,
        )
    except FileExistsError:
        state.publication = "none"
        raise
    state.publication = "applied"
    if result is not None:
        raise ValueError("staging_link_return_invalid")
    state.scratch_disposal = "unknown"
    state.finish_phase = "scratch_disposal"
    # Original identity-qualified scratch disposal; its failure path has no
    # root descriptor to release and cannot dispose the retained parent owner.
    cast(Callable[..., Any], bootstrap._dispose_scratch)(
        state, state.parent_fd, state.scratch, _scratch_path(state), state.identity
    )
    try:
        root._observed(
            state,
            "scratch_absence",
            os.stat,
            state.scratch,
            dir_fd=state.parent_fd,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        state.scratch_disposal = "confirmed"
    else:
        raise ValueError("original_scratch_disposal_unconfirmed")
    state.finish_phase = "final_postimage"
    _verify_member_file(state, leaf)


def finish_member(member, *, expected_member_pin):
    state = _require(member)
    parent = state.parent
    with parent.lock:
        if not state.ordered:
            raise StagingMemberRefusal("ordered_finish_not_admitted", member, state)
        if state.phase != "active" or state.finish_spent:
            raise StagingMemberRefusal("staging_member_finish_spent", member, state)
        if not _pin_matches(expected_member_pin, state.pin):
            raise StagingMemberRefusal("staging_member_pin_mismatch", member, state)
        state.finish_spent, parent.busy, state.busy = True, True, True
        state.phase = "finishing"
        state.finish_phase = "precheck"
        try:
            _current(state)
            if state.pin[0] == "file":
                if state.accepted != state.pin[3]:
                    raise ValueError("staging_member_length_incomplete")
                state.finish_phase = "write_terminal"
                _finish_writer(state)
                state.finish_phase = "prepublication_postimage"
                _verify_member_file(state, state.scratch)
                state.finish_phase = "publication"
                _publish_file(state)
                identity = state.identity
            else:
                state.finish_phase = "directory_postimage"
                if state.creation == "applied":
                    result = root._observed(
                        state,
                        "final_directory_mode",
                        os.fchmod,
                        state.descriptor,
                        state.pin[2],
                    )
                    if result is not None:
                        raise ValueError("staging_directory_mode_return_invalid")
                    state.mode = state.pin[2]
                _current(state)
                state.directory_node_sync = "unknown"
                result = root._observed(
                    state, "directory_sync", os.fsync, state.descriptor
                )
                if result is not None:
                    raise ValueError("staging_sync_return_invalid")
                state.directory_node_sync = "confirmed"
                identity = root._identity(
                    root._observed(
                        state, "directory_postimage", os.fstat, state.descriptor
                    )
                )
            state.finish_phase = "parent_sync"
            state.directory_sync = "unknown"
            value = root._observed(
                state, "parent_directory_sync", os.fsync, state.parent_fd
            )
            if value is not None:
                raise ValueError("staging_sync_return_invalid")
            state.directory_sync = "confirmed"
            _current(state)
            state.finish_phase = "resource_release"
            settled = root._settle_owned_resources(state)
            for ledger in state.read_ledgers:
                root._validate_closed_resources(state, ledger=ledger)
                settled = root._ledger_settled(ledger) and settled
            if not settled:
                raise ValueError("staging_member_finish_cleanup_unconfirmed")
            state.finish_phase = "progress"
            state.phase, state.cleanup = "finished", "confirmed"
            state.finished, state.release_spent = True, True
            if type(state.returns) is root.history.GuardHistory:
                state.returns.pack_events()
            terminal = _evidence(state)
            retired = (
                _capture_closed_member(state, terminal)
                if parent.history_profile == root.RETIRED_MEMBER_PROFILE
                else None
            )
            if retired is not None:
                terminal = retired.terminal
            parent.child_terminals.append(terminal)
            if retired is not None:
                # Keep both originals in local state if either enrollment fails.
                # Parent advancement stays blocked until both indices commit.
                parent.retired_members[state.generation] = retired
                _HANDLES[member] = retired
            parent.completed_entries[state.pin[1]] = state.pin, identity
            parent.next_coordinate = state.coordinate[0], state.coordinate[1] + 1
            parent.active_child = None
            _CUSTODY.pop(id(state), None)
            if retired is not None:
                # The complete closed record is enrolled and the original
                # generator is exhausted. This inactive step retains its IO
                # adapter, which points back to state. Break that computational
                # cycle; all evidence/charges remain in the original record.
                # Failed retirement above preserves the unmodified step.
                state.write_step = None
            return terminal
        except BaseException as cause:
            _HANDLES[member] = state
            state.finished = False
            if state.finish_phase == "progress":
                state.capture_complete = False
            state.errors.append(cause)
            state.phase, parent.phase = "failed", "failed"
            raise StagingMemberRefusal(
                "staging_member_finish_failed", member, state, cause
            ) from cause
        finally:
            parent.busy, state.busy = False, False
