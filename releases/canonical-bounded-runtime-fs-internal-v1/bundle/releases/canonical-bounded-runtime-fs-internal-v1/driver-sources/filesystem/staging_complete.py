"""Original cooperative whole-stage observation; never installation authority.

Finish is single-use. The parent remains live for separately explicit release.
Unknown read/cursor cleanup retains a blocking child, not a disposal retry right.
This module adds no writer, archive parser, package selector or runtime loader.
"""

from __future__ import annotations

import os
import stat
from dataclasses import astuple, dataclass, field
from pathlib import Path
from uuid import uuid4
from weakref import WeakKeyDictionary

from . import confined_entry as entry
from . import staging_member as member
from . import staging_root as root

PROFILE = "aware.filesystem.cooperative-complete-stage.v1"
MAX_CHILDREN = 10000
MAX_NAME_BYTES = 1024
MAX_ROSTER_BYTES = 1048576
physical = root.physical
_NATIVE_STAT_PORTS = root._observed, os.stat, os.fstat


@dataclass(frozen=True, slots=True)
class StageCompletionEvidence:
    generation: str
    request_digest: str
    plan_digest: str
    group_namespace: str
    phase: str
    occurrences: tuple
    entries: tuple
    postimages: tuple
    original_returns: tuple | root.history.RecordedHistory
    original_errors: tuple
    observation_cleanup: str
    capture_complete: bool
    complete: bool
    parent_evidence: root.StagingRootEvidence
    grade: str = "cooperative_stage_observed"
    authorizes_installation: bool = False


@dataclass
class _Attempt:
    parent: root._State
    observation_profile: str | None = None
    generation: str = field(default_factory=lambda: uuid4().hex)
    phase: str = "finish_spent"
    ledger: physical._ReadLedger = field(default_factory=physical._ReadLedger)
    read_ledgers: list = field(default_factory=list)
    returns: list | root.history.GuardHistory = field(default_factory=list)
    native_stat_history: bool = False
    errors: list = field(default_factory=list)
    occurrences: tuple = ()
    entries: tuple = ()
    postimages: list = field(default_factory=list)
    postimage_seals: list = field(default_factory=list)
    entry_seals: list = field(default_factory=list)
    retained_objects: object = field(default_factory=dict)
    references: set = field(default_factory=set)
    entry_coordinate: tuple[str, int] | None = None
    entry_unsettled: bool = False
    cleanup: str = "unknown"
    capture_complete: bool = True
    complete: bool = False
    settlement_seal: tuple | None = None
    entry_values: object = None


_ATTEMPTS = WeakKeyDictionary()


def _evidence(state):
    parent = state.parent
    return StageCompletionEvidence(
        state.generation,
        parent.request_digest,
        parent.plan_digest,
        parent.namespace,
        state.phase,
        state.occurrences,
        state.entries,
        tuple(state.postimages),
        root.history.snapshot_returns(state.returns),
        tuple(state.errors),
        state.cleanup,
        state.capture_complete,
        state.complete,
        root._evidence(parent),
    )


class StageCompletionRefusal(RuntimeError):
    def __init__(self, code, handle, state=None, cause=None):
        super().__init__(code)
        self.code = code
        self.handle = handle
        self.original_cause = cause
        self.original_cause_traceback = (
            cause.__traceback__ if isinstance(cause, BaseException) else None
        )
        self.original_state = state
        self.evidence = None
        self.evidence_capture_error = None
        if state is not None:
            try:
                self.evidence = _evidence(state)
            except (
                BaseException  # noqa: BLE001
            ) as capture_error:  # Original state/cause precede a fallible projection.
                self.evidence_capture_error = capture_error
        self.authorizes_retry = False


def observe_stage_completion(stage):
    """IO-free retained evidence, including refused or incomplete attempts."""
    root._require(stage)
    if stage not in _ATTEMPTS:
        raise StageCompletionRefusal("stage_finish_not_attempted", stage)
    return _evidence(_ATTEMPTS[stage])


def validate_stage_completion(stage, *, expected_request_digest, expected_plan_digest):
    """Validate retained pre-settlement seals without IO or renewed rights."""
    parent = root._require(stage)
    with parent.lock:
        state = _ATTEMPTS.get(stage)
        if state is None:
            raise StageCompletionRefusal("stage_finish_not_attempted", stage)
        if (
            type(expected_request_digest) is not str
            or expected_request_digest != parent.request_digest
            or type(expected_plan_digest) is not str
            or expected_plan_digest != parent.plan_digest
        ):
            raise StageCompletionRefusal("stage_finish_binding_mismatch", stage, state)
        if (
            state.parent is not parent
            or not state.complete
            or state.phase != "complete"
            or state.cleanup != "confirmed"
            or not state.capture_complete
            or state.settlement_seal is None
            or parent.phase != "stage_finished"
            or parent.release_spent
            or parent.active_child is not None
        ):
            raise StageCompletionRefusal("stage_completion_unavailable", stage, state)
        try:
            _receive_after_settlement(state, state.settlement_seal)
        except BaseException as cause:
            # Preserve rejected originals without replaying IO.
            state.errors.append(cause)
            state.complete = False
            state.phase, parent.phase = "incomplete", "failed"
            parent.active_child = state
            raise StageCompletionRefusal(
                "stage_completion_seal_changed", stage, state, cause
            ) from cause
        return _evidence(state)


def _fresh(state, values):
    # Keep originals, not just ids: object reclamation cannot make reuse invisible.
    if type(state.retained_objects) is root.history.OriginalIdentityRoster:
        state.retained_objects.retain_fresh(values)
        return
    rows = {id(value): value for value in values if value is not None}
    if rows.keys() & state.retained_objects.keys():
        raise ValueError("reused_original_stage_evidence")
    state.retained_objects.update(rows)


def _stat_observation(state, label, kind, *args, **kwargs):
    # A real builtin creates each new native stat object. Its complete values
    # go into the original history; decoded historical values never drive a
    # live guard. Retaining the original port avoids mutable provider aliases.
    if state.native_stat_history:
        return _NATIVE_STAT_PORTS[0](
            state, label, _NATIVE_STAT_PORTS[kind], *args, **kwargs
        )
    return root._observed(
        state, label, os.stat if kind == 1 else os.fstat, *args, **kwargs
    )


def _guard(state):
    parent = state.parent
    if type(parent.returns) is root.history.GuardHistory:
        returned = root._observe_live_bookends(parent)
        values = [
            value
            for value in root._validate_live_bookends(parent, returned)
            if type(value) is os.stat_result
        ]
    else:
        start = len(parent.returns)
        root._bookends(parent)
        values = [
            value
            for _, value in parent.returns[start:]
            if type(value) is os.stat_result
        ]
    _fresh(state, values)
    if root._plan_seal(parent.plan) != parent.plan_seal:
        raise ValueError("staging_plan_changed")


def _validate_roster_terminal(parent, coordinate, pin, terminal):
    if (
        type(terminal) not in (member.MemberEvidence, member._BackedMemberEvidence)
        or terminal.coordinate != coordinate
        or terminal.member_pin != pin
        or terminal.operation_binding != parent.request_digest
        or terminal.root_generation != parent.generation
        or terminal.profile != member.ORDERED_PROFILE
        or terminal.member_finished is not True
        or terminal.capture_complete is not True
        or terminal.cleanup != "confirmed"
        or terminal.directory_sync != "confirmed"
    ):
        raise ValueError("staging_occurrence_terminal_unqualified")
    if parent.history_profile == root.RETIRED_MEMBER_PROFILE:
        retired = parent.retired_members.get(terminal.generation)
        if member._validate_retired(retired) is not terminal:
            raise ValueError("original_retired_terminal_required")
    if pin[0] == "file" and terminal.final_publication != "applied":
        raise ValueError("staging_file_not_published")
    if pin[0] == "file" and (
        terminal.file_sync != "confirmed" or terminal.scratch_disposal != "confirmed"
    ):
        raise ValueError("staging_file_terminal_incomplete")
    if pin[0] == "directory" and terminal.directory_node_sync != "confirmed":
        raise ValueError("staging_directory_terminal_incomplete")


def _roster(state):
    parent = state.parent
    group = next(g for g in parent.plan_seal if g[0] == parent.namespace)
    occurrences = tuple(
        ((p, m), pin)
        for p, partition in enumerate(group[1])
        for m, pin in enumerate(partition[1])
    )
    if member._next_coordinate(parent) != (len(group[1]), 0):
        raise ValueError("staging_occurrences_incomplete")
    if len(parent.child_terminals) != len(occurrences):
        raise ValueError("staging_terminal_roster_mismatch")
    expected = {}
    for (coordinate, pin), terminal in zip(
        occurrences, parent.child_terminals, strict=True
    ):
        _validate_roster_terminal(parent, coordinate, pin, terminal)
        expected[pin[1]] = pin
    if set(expected) != set(parent.completed_entries) or any(
        parent.completed_entries[path][0] != pin for path, pin in expected.items()
    ):
        raise ValueError("staging_completed_roster_changed")
    state.occurrences = occurrences
    state.entries = tuple(sorted(expected.items()))
    return expected


def _entry_mapping_matches(expected, entries):
    """Compare canonical retained rows without another sorted tuple/dict."""
    if (
        type(expected) is not dict
        or type(entries) is not tuple
        or len(expected) != len(entries)
    ):
        return False
    previous = None
    for path, pin in entries:
        if previous is not None and path <= previous:
            return False
        if path not in expected or expected[path] != pin:
            return False
        previous = path
    return True


def _roster_matches(state, entries, occurrences):
    """Fresh original policy checks, with no refreshed whole-roster projection.

    The original immutable occurrence stream fixes every repeated-directory
    occurrence and its order. Completed entries contain the last pin per path;
    do not compare earlier repeats to that last pin or re-charge their history.
    """
    parent = state.parent
    if (
        type(parent.child_terminals) is not list
        or type(parent.completed_entries) is not dict
    ):
        return False
    group = next(g for g in parent.plan_seal if g[0] == parent.namespace)
    if member._next_coordinate(parent) != (len(group[1]), 0):
        raise ValueError("staging_occurrences_incomplete")
    count = sum(len(partition[1]) for partition in group[1])
    if len(parent.child_terminals) != count:
        raise ValueError("staging_terminal_roster_mismatch")
    if type(occurrences) is not tuple or len(occurrences) != count:
        return False
    index = 0
    for p, partition in enumerate(group[1]):
        for m, pin in enumerate(partition[1]):
            coordinate = p, m
            if occurrences[index] != (coordinate, pin):
                return False
            terminal = parent.child_terminals[index]
            _validate_roster_terminal(parent, coordinate, pin, terminal)
            index += 1
    if len(parent.child_terminals) != index:
        raise ValueError("staging_terminal_roster_mismatch")
    if state.entries != entries or state.occurrences != occurrences:
        return False
    # Check the original ordered unique rows against the current completed
    # registry. No IO, guard refresh, seal replacement or repeat disposal.
    if type(entries) is not tuple or len(parent.completed_entries) != len(entries):
        return False
    previous = None
    for path, pin in entries:
        if previous is not None and path <= previous:
            return False
        current = parent.completed_entries.get(path)
        if current is None or current[0] != pin:
            return False
        previous = path
    return True


def _entry(state, path):
    state.entry_unsettled = True
    try:
        value = entry.observe_confined_entry_with_cleanup(
            root=Path(state.parent.root),
            path=path,
            maximum_children=MAX_CHILDREN,
            maximum_name_bytes=MAX_NAME_BYTES,
            maximum_roster_bytes=MAX_ROSTER_BYTES,
            **(
                {"_value_pool": state.entry_values}
                if state.entry_values is not None
                else {}
            ),
            **(
                {"_receipt_profile": state.observation_profile}
                if state.observation_profile is not None
                else {}
            ),
        )
    except entry.ConfinedEntryObservationError as cause:
        # Original failure custody remains on the cause. A later read cannot
        # repair missing acknowledgements from this call.
        if (
            cause.original_descriptor_cleanup is not None
            and cause.original_descriptor_cleanup.outcome == "closed"
            and cause.cursor_cleanup is not None
            and cause.cursor_cleanup.outcome in ("closed", "not_acquired")
        ):
            state.entry_unsettled = False
        raise
    state.returns.append(("entry", value))
    if state.observation_profile is not None:
        entry.validate_confined_entry_receipt(value)
    else:
        if type(value) is not entry._ENTRY_RESULT_TYPE:
            raise ValueError("original_entry_result_required")
        entry._ENTRY_RESULT_TYPE.__post_init__(value)
    if (
        value.root_locator != state.parent.root
        or value.path != path
        or value.request_snapshot
        != entry.EntryRequestSnapshot(
            state.parent.root, path, MAX_CHILDREN, MAX_NAME_BYTES, MAX_ROSTER_BYTES
        )
    ):
        raise ValueError("stage_entry_binding_changed")
    observed_root = value.root_before
    if (
        observed_root.device,
        observed_root.inode,
        stat.S_IFMT(observed_root.mode),
        observed_root.uid,
        observed_root.gid,
        stat.S_IMODE(observed_root.mode),
    ) != state.parent.root_identity:
        raise ValueError("stage_entry_root_identity_changed")
    if state.observation_profile is not None:
        coordinate = entry.confined_entry_receipt_coordinate(value)
        if state.entry_coordinate is not None and (
            coordinate[0] != state.entry_coordinate[0]
            or coordinate[1] <= state.entry_coordinate[1]
        ):
            raise ValueError("reused_original_stage_evidence")
    else:
        coordinate = None
        _fresh(
            state,
            [
                value,
                value.request_snapshot,
                value.root_before,
                value.root_after,
                value.entry_before,
                value.entry_after,
                value.opened_directory,
                *value.descriptor_resources,
                *value.cursor_resources,
                *(
                    stat_value
                    for row in value.ancestor_bookends
                    for stat_value in (
                        row,
                        row.named_before,
                        row.opened_before,
                        row.named_after,
                        row.opened_after,
                    )
                ),
            ],
        )
        refs = {
            value.observation_ref,
            *(
                r.resource_ref
                for r in value.descriptor_resources + value.cursor_resources
            ),
        }
        if refs & state.references:
            raise ValueError("reused_stage_observation_reference")
        state.references.update(refs)
    state.entry_seals.append((value, _retained_entry_fields(state, value)))
    if coordinate is not None:
        state.entry_coordinate = coordinate
    state.entry_unsettled = False
    return value


def _entry_fields(value):
    # Snapshot primitive field values as well as retaining original identities.
    # Holding references alone would miss mutation inside a frozen carrier.
    return astuple(value)


def _postimage_fields(value):
    observed = value.observation
    return (
        observed.leaf,
        observed.identity,
        observed.size_bytes,
        observed.content_digest,
        observed.mode,
        observed.read_calls,
        astuple(value.cleanup),
    )


def _retained_entry_fields(state, value):
    if state.observation_profile is not None:
        return entry.confined_entry_receipt_seal(value)
    return (
        root.history.value_seal(value)
        if type(state.parent.returns) is root.history.GuardHistory
        else _entry_fields(value)
    )


def _retained_postimage_fields(state, value):
    return (
        root.history.value_seal(value)
        if type(state.parent.returns) is root.history.GuardHistory
        else _postimage_fields(value)
    )


def _scan(state, expected):
    children = {None: set()}
    for path, pin in expected.items():
        parent, _, leaf = path.rpartition("/")
        children.setdefault(parent or None, set()).add(leaf)
        if pin[0] == "directory":
            children.setdefault(path, set())
    observations = {}
    for path in (None, *sorted(expected)):
        value = _entry(state, path)
        observations[path] = value
        observed = value.entry_after
        if path is None:
            identity = (
                observed.device,
                observed.inode,
                stat.S_IFMT(observed.mode),
                observed.uid,
                observed.gid,
                stat.S_IMODE(observed.mode),
            )
            if value.kind != "directory" or identity != state.parent.root_identity:
                raise ValueError("stage_roster_root_changed")
        else:
            pin = expected[path]
            identity = state.parent.completed_entries[path][1]
            if (
                value.kind != pin[0]
                or stat.S_IMODE(observed.mode) != pin[2]
                or observed.uid != os.geteuid()
                or (observed.device, observed.inode) != identity[:2]
            ):
                raise ValueError("stage_roster_entry_changed")
            if pin[0] == "file" and (observed.size != pin[3] or observed.nlink != 1):
                raise ValueError("stage_roster_file_changed")
        if (
            value.kind == "directory"
            and set(value.children_after or ()) != children[path]
        ):
            raise ValueError("stage_roster_extra_or_missing_entry")
    return observations


def _file(state, path, pin, descriptor):
    ledger = physical._ReadLedger()
    state.read_ledgers.append(ledger)
    leaf = path.rsplit("/", 1)[-1]
    before = _stat_observation(
        state, "file_before", 1, leaf, dir_fd=descriptor, follow_symlinks=False
    )
    if not state.native_stat_history:
        _fresh(state, [before])
    value = physical._verify_confined_file_postimage(
        parent_descriptor=descriptor,
        leaf=leaf,
        expected_identity=state.parent.completed_entries[path][1][:2],
        size_bytes=pin[3],
        content_digest=pin[4],
        mode=pin[2],
        _ledger=ledger,
    )
    state.postimages.append((path, value))
    root._validate_closed_resources(state, ledger=ledger)
    if (
        type(value) is not physical._FilePostimageVerification
        or type(value.observation) is not physical._FilePostimageObservation
        or len(ledger.resources) != 1
        or ledger.resources[0].acquisition_state != "acquired"
        or not root._ledger_settled(ledger)
        or value.cleanup != ledger.snapshot()
    ):
        raise ValueError("stage_postimage_original_custody_unconfirmed")
    _fresh(state, [value, value.observation, *ledger.resources])
    observed = value.observation
    if (
        observed.leaf,
        observed.identity,
        observed.size_bytes,
        observed.content_digest,
        observed.mode,
    ) != (leaf, state.parent.completed_entries[path][1][:2], pin[3], pin[4], pin[2]):
        raise ValueError("stage_postimage_binding_changed")
    after = _stat_observation(
        state, "file_after", 1, leaf, dir_fd=descriptor, follow_symlinks=False
    )
    if not state.native_stat_history:
        _fresh(state, [after])
    if not physical._same_stat(before, after):
        raise ValueError("stage_file_changed_during_postimage")
    state.postimage_seals.append(
        (value, _retained_postimage_fields(state, value), ledger)
    )


def _receive_after_settlement(state, seal):
    """IO-free check against the pre-disposal originals, not refreshed seals."""
    entries, postimages, projection, roster, occurrences = seal
    for current, retained in (
        (state.entry_seals, entries),
        (state.postimage_seals, postimages),
        (state.postimages, projection),
    ):
        if len(current) != len(retained) or any(
            value is not original
            for value, original in zip(current, retained, strict=True)
        ):
            raise ValueError("stage_projection_changed_after_settlement")
    for value, fields in entries:
        if state.observation_profile is not None:
            entry.validate_confined_entry_receipt(value)
        else:
            entry._ENTRY_RESULT_TYPE.__post_init__(value)
        if _retained_entry_fields(state, value) != fields:
            raise ValueError("stage_entry_carrier_changed_after_settlement")
    for value, fields, ledger in postimages:
        if (
            _retained_postimage_fields(state, value) != fields
            or value.cleanup != ledger.snapshot()
        ):
            raise ValueError("stage_postimage_carrier_changed_after_settlement")
    if state.entries != roster or state.occurrences != occurrences:
        raise ValueError("stage_roster_changed_after_settlement")
    if not _roster_matches(state, roster, occurrences):
        raise ValueError("stage_owner_roster_changed_after_settlement")


def finish_stage(
    stage,
    *,
    profile,
    expected_request_digest,
    expected_plan_digest,
    observation_profile=None,
):
    """Observe one complete selected group; explicit parent release stays separate."""
    parent = root._require(stage)
    with parent.lock:
        if (
            type(profile) is not str
            or profile != PROFILE
            or type(expected_request_digest) is not str
            or expected_request_digest != parent.request_digest
            or type(expected_plan_digest) is not str
            or expected_plan_digest != parent.plan_digest
            or (
                observation_profile is not None
                and (
                    type(observation_profile) is not str
                    or observation_profile != entry.OBSERVATION_RECEIPT_PROFILE
                )
            )
        ):
            raise StageCompletionRefusal("stage_finish_binding_mismatch", stage)
        if (
            stage in _ATTEMPTS
            or parent.phase != "created"
            or parent.release_spent
            or parent.active_child is not None
            or parent.member_profile != member.ORDERED_PROFILE
        ):
            raise StageCompletionRefusal("stage_finish_unavailable", stage)
        state = _Attempt(parent, observation_profile=observation_profile)
        _ATTEMPTS[stage] = state
        parent.phase, parent.busy, parent.active_child = (
            "stage_finish_spent",
            True,
            state,
        )
        primary = None
        settlement_seal = None
        try:
            if (
                state.observation_profile is not None
                and parent.history_pool is not None
                and parent.history_pool.stat_blocks is not None
            ):
                state.returns = root.history.GuardHistory(parent.history_pool)
                state.native_stat_history = True
            if type(parent.returns) is root.history.GuardHistory:
                state.entry_values = entry._new_entry_value_pool(packed_stats=True)
                state.retained_objects = root.history.OriginalIdentityRoster()
            _guard(state)
            expected = _roster(state)
            before = _scan(state, expected)
            directories = {"": parent.root_fd}
            for path, pin in sorted(
                expected.items(), key=lambda row: (row[0].count("/"), row[0])
            ):
                parent_path, _, leaf = path.rpartition("/")
                descriptor = directories[parent_path]
                if pin[0] == "directory":
                    fd = state.ledger.open(
                        leaf,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                        dir_fd=descriptor,
                    )
                    value = _stat_observation(state, "directory_opened", 2, fd)
                    if not state.native_stat_history:
                        _fresh(state, [value])
                    if root._identity(value) != parent.completed_entries[path][1]:
                        raise ValueError("stage_directory_changed")
                    directories[path] = fd
                else:
                    _file(state, path, pin, descriptor)
            _guard(state)
            after = _scan(state, expected)
            if any(
                before[path].entry_after != value.entry_before
                for path, value in after.items()
            ):
                raise ValueError("stage_tree_changed_across_guards")
            # Fresh final named guards detect late file changes without rereading,
            # accepting a refreshed roster, or certifying a simultaneous snapshot.
            for path, value in after.items():
                descriptor = (
                    parent.root_fd
                    if path is None
                    else directories[path.rpartition("/")[0]]
                )
                info = (
                    _stat_observation(state, "final_named_guard", 2, descriptor)
                    if path is None
                    else _stat_observation(
                        state,
                        "final_named_guard",
                        1,
                        path.rsplit("/", 1)[-1],
                        dir_fd=descriptor,
                        follow_symlinks=False,
                    )
                )
                if not state.native_stat_history:
                    _fresh(state, [info])
                fields = (
                    info.st_dev,
                    info.st_ino,
                    info.st_mode,
                    info.st_uid,
                    info.st_gid,
                    info.st_nlink,
                    info.st_size,
                    info.st_mtime_ns,
                    info.st_ctime_ns,
                )
                if fields != value.entry_after.values():
                    raise ValueError("stage_entry_changed_after_final_roster")
            _guard(state)
            state.entry_unsettled = True
            for value, seal in state.entry_seals:
                if state.observation_profile is not None:
                    entry.validate_confined_entry_receipt(value)
                else:
                    entry._ENTRY_RESULT_TYPE.__post_init__(value)
                if _retained_entry_fields(state, value) != seal:
                    state.entry_unsettled = True
                    raise ValueError("stage_entry_carrier_changed_after_guards")
            state.entry_unsettled = False
            for value, seal, ledger in state.postimage_seals:
                if (
                    _retained_postimage_fields(state, value) != seal
                    or value.cleanup != ledger.snapshot()
                ):
                    raise ValueError("stage_postimage_carrier_changed_after_guards")
            if not _entry_mapping_matches(
                expected, state.entries
            ) or not _roster_matches(state, state.entries, state.occurrences):
                raise ValueError("stage_roster_drift")
            settlement_seal = (
                tuple(state.entry_seals),
                tuple(state.postimage_seals),
                tuple(state.postimages),
                state.entries,
                state.occurrences,
            )
            state.settlement_seal = settlement_seal
        except BaseException as cause:  # noqa: BLE001 - retain interruptions before independent observation settlement
            primary = cause
            state.errors.append(cause)
        finally:
            try:
                settled = root._settle_owned_resources(state)
                for ledger in state.read_ledgers:
                    root._validate_closed_resources(state, ledger=ledger)
                    settled = root._ledger_settled(ledger) and settled
                state.cleanup = (
                    "confirmed" if settled and not state.entry_unsettled else "unknown"
                )
            except BaseException as cause:  # noqa: BLE001 - preserve primary cause and uncertain cleanup independently
                state.errors.append(cause)
                if primary is None:
                    primary = cause
            integrity_confirmed = settlement_seal is None
            try:
                if settlement_seal is not None:
                    _receive_after_settlement(state, settlement_seal)
                    integrity_confirmed = True
            except BaseException as cause:  # noqa: BLE001 - reject late evidence drift without replaying settled IO
                state.errors.append(cause)
                if primary is None:
                    primary = cause
            finally:
                parent.busy = False
                # Known cleanup stays confirmed even on evidence rejection.
                # Retained custody grants no repair or disposal retry right.
                if state.cleanup == "confirmed" and integrity_confirmed:
                    parent.active_child = None
        if (
            primary is not None
            or state.cleanup != "confirmed"
            or not state.capture_complete
        ):
            state.phase, parent.phase = "incomplete", "failed"
            raise StageCompletionRefusal(
                "stage_finish_incomplete", stage, state, primary
            ) from primary
        try:
            state.complete = True
            state.phase, parent.phase = "complete", "stage_finished"
            return _evidence(state)
        except BaseException as cause:
            state.complete = False
            state.phase, parent.phase = "incomplete", "failed"
            state.errors.append(cause)
            raise StageCompletionRefusal(
                "stage_finish_capture_incomplete", stage, state, cause
            ) from cause
