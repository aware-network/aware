"""Original C transitions and custody under cooperative descriptor confinement.

Only the issued sequence executes; FileSystem supplies no Issue permission.
Original reader, temporary writer, directory and disposal mechanisms are reused.
"""

from __future__ import annotations

import json
import os
import stat
import threading
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path, PurePosixPath
from uuid import uuid4
from weakref import WeakKeyDictionary, finalize

from .confined_mutation import (
    ConfinedMutationEffectState,
    ConfinedMutationKind,
    ConfinedMutationProfile,
    ConfinedTreeAncestorTransition,
    ConfinedTreeCleanupObservation,
    ConfinedTreeEffectObservation,
    ConfinedTreeEntryPin,
    ConfinedTreeFileTransition,
    ConfinedTreePhysicalEffect,
    ConfinedTreePreparationObservation,
    ConfinedTreeProjectionRequest,
    ConfinedTreeResourceCleanup,
    ConfinedTreeScratchEffect,
    ConfinedTreeTransitionResult,
    _content_digest,
    _open_parent,
    _read_current,
    _ReadLedger,
    _same_stat,
    _tree_digest,
    _tree_identity,
    _tree_integer,
    _tree_path,
    _tree_text,
    _write_temporary,
)
from .retained_mutation import _mkdir_explicit


class RetainedPhysicalTreeProjectionRefusal(RuntimeError):
    """Original refusal and partial cleanup, including failed factory issuance."""

    def __init__(self, code, *, observation=None, cleanup=None, transition=None):
        self.code = code
        self.observation = observation
        self.cleanup = cleanup
        self.transition = transition
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ConfinedTreeCapacitySchedule:
    profile: str
    full_validation_calls_remaining: int
    ordinal_validation_calls_remaining: int
    transition_calls_remaining: int
    finish_calls_remaining: int
    consumed_validation_calls_remaining: int
    release_attempts_remaining: int

    def __post_init__(self):
        if type(self.profile) is not str or self.profile != "native_tree_c_capacity_v1":
            raise ValueError("original_capacity_schedule_required")
        _capacity_integers(self, exclude=("profile",))
        if (
            self.full_validation_calls_remaining != 1
            or self.finish_calls_remaining != 1
            or self.consumed_validation_calls_remaining != 2
            or self.release_attempts_remaining != 1
            or self.ordinal_validation_calls_remaining
            != self.transition_calls_remaining
            or self.transition_calls_remaining > 8192
        ):
            raise ValueError("invalid_capacity_schedule")


@dataclass(frozen=True, slots=True)
class ConfinedTreeEncodingBounds:
    maximum_resource_record_bytes: int
    maximum_effect_record_bytes: int
    maximum_error_reference_bytes: int
    maximum_pin_bytes: int
    maximum_diagnostic_bytes: int
    maximum_ledger_diagnostics: int
    maximum_uncertain_resource_rows: int
    maximum_dispositions_per_resource: int
    maximum_subeffects_per_transition: int
    native_history_copy_count: int

    def __post_init__(self):
        _capacity_integers(self)
        if (
            self.maximum_ledger_diagnostics != 16
            or self.maximum_uncertain_resource_rows != 65
            or self.maximum_dispositions_per_resource != 5
            or self.maximum_subeffects_per_transition != 16
            or self.native_history_copy_count != 2
        ):
            raise ValueError("invalid_capacity_encoding_bounds")


@dataclass(frozen=True, slots=True)
class ConfinedTreePrefixCapacity:
    completed_prefix: int
    maximum_acquisition_history_rows: int
    maximum_scratch_history_rows: int
    maximum_resource_variant_rows: int
    maximum_cleanup_wire_bytes: int
    maximum_effect_rows: int
    maximum_effect_wire_bytes: int
    maximum_postimage_wire_bytes: int
    maximum_latest_return_wire_bytes: int
    terminal_extra_acquisition_rows: int
    terminal_extra_resource_variant_rows: int
    terminal_extra_wire_bytes: int
    release_extra_wire_bytes: int

    def __post_init__(self):
        _capacity_integers(self)
        if self.completed_prefix > 8192:
            raise ValueError("invalid_capacity_prefix")
        if (
            self.maximum_resource_variant_rows
            < self.maximum_acquisition_history_rows + self.maximum_scratch_history_rows
            or self.maximum_effect_rows > self.completed_prefix * 16
            or self.terminal_extra_resource_variant_rows
            < self.terminal_extra_acquisition_rows
        ):
            raise ValueError("invalid_capacity_dimensions")


@dataclass(frozen=True, slots=True)
class ConfinedTreeCapacityForecast:
    schema: str
    preparation_ref: str
    request_ref: str
    request_digest: str
    root_identity: tuple[int, int]
    transition_order: tuple[tuple[int, str, str], ...]
    forecast_revision: int
    observed_acquisition_rows: int
    observed_scratch_rows: int
    observed_history_wire_bytes: int
    remaining_acquisition_rows: int
    remaining_scratch_rows: int
    remaining_history_wire_bytes: int
    schedule: ConfinedTreeCapacitySchedule
    encoding: ConfinedTreeEncodingBounds
    prefixes: tuple[ConfinedTreePrefixCapacity, ...]
    forecast_wire_bytes: int

    def __post_init__(self):
        if (
            type(self.schema) is not str
            or self.schema != "aware.filesystem.tree-capacity-forecast.v1"
        ):
            raise ValueError("original_capacity_forecast_required")
        for value in (self.preparation_ref, self.request_ref):
            _tree_text(value)
        _tree_digest(self.request_digest)
        _tree_identity(self.root_identity)
        _capacity_integers(
            self,
            exclude=(
                "schema",
                "preparation_ref",
                "request_ref",
                "request_digest",
                "root_identity",
                "transition_order",
                "schedule",
                "encoding",
                "prefixes",
            ),
        )
        if (
            type(self.schedule) is not ConfinedTreeCapacitySchedule
            or type(self.encoding) is not ConfinedTreeEncodingBounds
        ):
            raise ValueError("original_capacity_values_required")
        self.schedule.__post_init__()
        self.encoding.__post_init__()
        count = self.schedule.transition_calls_remaining
        if (
            type(self.transition_order) is not tuple
            or len(self.transition_order) != count
        ):
            raise ValueError("invalid_capacity_transition_order")
        for ordinal, row in enumerate(self.transition_order):
            if type(row) is not tuple or len(row) != 3:
                raise ValueError("invalid_capacity_transition_order")
            _tree_integer(row[0])
            _tree_path(row[1])
            if (
                type(row[2]) is not str
                or row[2]
                not in (
                    "CREATE",
                    "UPDATE",
                    "DELETE",
                    "directory_create",
                    "directory_preserve",
                )
                or row[0] != ordinal
            ):
                raise ValueError("invalid_capacity_transition_order")
        if type(self.prefixes) is not tuple or len(self.prefixes) != count + 1:
            raise ValueError("invalid_capacity_prefixes")
        for ordinal, row in enumerate(self.prefixes):
            if type(row) is not ConfinedTreePrefixCapacity:
                raise ValueError("original_capacity_prefix_required")
            row.__post_init__()
            if (
                row.completed_prefix != ordinal
                or row.maximum_acquisition_history_rows < self.observed_acquisition_rows
                or row.maximum_scratch_history_rows < self.observed_scratch_rows
                or row.maximum_acquisition_history_rows
                > self.observed_acquisition_rows + self.remaining_acquisition_rows
                or row.maximum_scratch_history_rows
                > self.observed_scratch_rows + self.remaining_scratch_rows
            ):
                raise ValueError("invalid_capacity_prefixes")
            if ordinal and any(
                getattr(row, name) < getattr(self.prefixes[ordinal - 1], name)
                for name in (
                    "maximum_acquisition_history_rows",
                    "maximum_scratch_history_rows",
                    "maximum_effect_rows",
                    "maximum_effect_wire_bytes",
                )
            ):
                raise ValueError("invalid_capacity_prefix_order")
        if self.forecast_wire_bytes != len(_wire(asdict(self))):
            raise ValueError("invalid_capacity_forecast_wire_bytes")


def _capacity_integers(value, *, exclude=()):
    for declaration in fields(type(value)):
        if declaration.name not in exclude:
            _tree_integer(getattr(value, declaration.name))


_CAPACITY_TYPES = (
    ConfinedTreeCapacitySchedule,
    ConfinedTreeEncodingBounds,
    ConfinedTreePrefixCapacity,
    ConfinedTreeCapacityForecast,
)
_CAPACITY_DEFINITIONS = tuple(
    (
        cls,
        cls.__init__,
        cls.__init__.__code__,
        cls.__post_init__,
        cls.__post_init__.__code__,
        tuple(
            (definition.name, vars(cls)[definition.name]) for definition in fields(cls)
        ),
    )
    for cls in _CAPACITY_TYPES
)


def _check_capacity_definitions():
    for (
        cls,
        constructor,
        constructor_code,
        validate,
        validate_code,
        slots,
    ) in _CAPACITY_DEFINITIONS:
        if (
            globals().get(cls.__name__) is not cls
            or vars(cls).get("__init__") is not constructor
            or constructor.__code__ is not constructor_code
            or vars(cls).get("__post_init__") is not validate
            or validate.__code__ is not validate_code
            or any(vars(cls).get(name) is not descriptor for name, descriptor in slots)
        ):
            raise RetainedPhysicalTreeProjectionRefusal(
                "tree_capacity_definitions_changed"
            )


@dataclass
class _Resource:
    ref: str
    path: str | None
    record: object = None
    state: str = "not_acquired"
    attempted: bool = False
    diagnostics: tuple[str, ...] = ()
    index: int = 0


class _TreeLedger(_ReadLedger):
    """Attach C coordinates to the original once-only acquisition/close rights."""

    def __init__(self, limits, root_identity):
        super().__init__()
        self.limits = limits
        self.root_identity = root_identity
        self.history: list[_Resource] = []
        self.active: dict[int, _Resource] = {}
        self.fd_paths: dict[int, str] = {}
        self.current_path = None
        self.peak_live = 0
        self.directory_pins = {}
        self.current_directories = {}
        self.current_absences = set()
        self.metadata_reserved = 0
        self.request_metadata = 0
        self.resource_reserved = 0
        self.future_resource_reserved = 0
        self.future_resource_rows = 0
        self.scratch_resource_rows = 0
        self.planned_reads = False
        self.metadata_other = 0
        self.snapshots = []
        self.snapshot_tuple = None
        self.invalid_snapshots = set()
        self.root_descriptor = None
        self.root_path = None
        self.root_borrows = 0

    def reserve(self, amount, *, resource=False):
        actual = self.resource_reserved + (amount if resource else 0)
        future = max(
            0,
            self.future_resource_reserved
            - (amount if resource and self.planned_reads else 0),
        )
        requested = self.request_metadata + (0 if resource else amount)
        remaining_rows = max(
            0, self.future_resource_rows - (1 if resource and self.planned_reads else 0)
        )
        if resource and (
            len(self.history) + 1 + remaining_rows + self.scratch_resource_rows > 8192
        ):
            raise RetainedPhysicalTreeProjectionRefusal(
                "tree_cleanup_resource_capacity_exceeded"
            )
        if (
            self.metadata_other + requested + 2 * (actual + future)
            > self.limits.maximum_metadata_bytes
        ):
            raise RetainedPhysicalTreeProjectionRefusal(
                "tree_metadata_capacity_exceeded"
            )
        self.request_metadata = requested
        self.resource_reserved = actual
        self.future_resource_reserved = future
        self.future_resource_rows = remaining_rows
        self.metadata_reserved = requested + actual

    def open(self, path, flags, *, dir_fd=None, mode=None):
        if self.acquisition_unknown or self.release_unknown or self.context_unknown:
            raise RetainedPhysicalTreeProjectionRefusal(
                "tree_descriptor_custody_unknown"
            )
        if (
            dir_fd is None
            and mode is None
            and flags == _DIRECTORY_FLAGS
            and path == self.root_path
            and self.root_descriptor is not None
        ):
            descriptor = self.root_descriptor
            retained = self.active.get(descriptor)
            if retained is None or retained.state != "owned":
                raise RetainedPhysicalTreeProjectionRefusal(
                    "tree_root_custody_unavailable"
                )
            live = os.stat(path, follow_symlinks=False)
            opened = os.fstat(descriptor)
            pin = self.directory_pins[""]
            if any(
                not stat.S_ISDIR(value.st_mode)
                or (value.st_dev, value.st_ino, stat.S_IMODE(value.st_mode))
                != (pin.device, pin.inode, pin.mode)
                for value in (live, opened)
            ):
                raise RetainedPhysicalTreeProjectionRefusal(
                    "tree_root_identity_changed"
                )
            # A scoped borrow of the one original acquisition, not a fresh fd
            # or a replacement cleanup right. Actual history is never cropped.
            self.root_borrows += 1
            return descriptor
        if len(self.active) + 1 > self.limits.maximum_live_descriptors:
            raise RetainedPhysicalTreeProjectionRefusal(
                "tree_descriptor_capacity_exceeded"
            )
        self.reserve(_resource_slot_capacity(self.current_path), resource=True)
        slot = _Resource(
            "descriptor:" + uuid4().hex, self.current_path, index=len(self.history)
        )
        self.history.append(slot)
        self.snapshots.append(None)
        self.refresh(slot)
        index = len(self.resources)
        acquired = None
        try:
            acquired = super().open(path, flags, dir_fd=dir_fd, mode=mode)
            slot.record = self.resources[index]
            slot.state = "owned"
            self.active[acquired] = slot
            self.refresh(slot)
            self.peak_live = max(self.peak_live, len(self.active))
            if flags & os.O_DIRECTORY:
                relative = (
                    ""
                    if dir_fd is None
                    else "/".join(filter(None, (self.fd_paths[dir_fd], str(path))))
                )
                observed = os.fstat(acquired)
                if observed.st_dev != self.root_identity[0]:
                    raise RetainedPhysicalTreeProjectionRefusal(
                        "tree_mount_boundary_unavailable"
                    )
                if (
                    not relative
                    and (observed.st_dev, observed.st_ino) != self.root_identity
                ):
                    raise RetainedPhysicalTreeProjectionRefusal(
                        "tree_root_identity_changed"
                    )
                old = self.directory_pins.get(relative)
                current = _entry(observed)
                if old is not None and (old.device, old.inode, old.mode) != (
                    current.device,
                    current.inode,
                    current.mode,
                ):
                    raise RetainedPhysicalTreeProjectionRefusal(
                        "tree_ancestor_identity_changed"
                    )
                self.directory_pins[relative] = current
                self.current_directories[relative] = current
                self.fd_paths[acquired] = relative
                if dir_fd is None:
                    self.root_descriptor = acquired
                    self.root_path = path
            return acquired
        except BaseException as error:
            if index < len(self.resources):
                slot.record = self.resources[index]
            if acquired is None and (
                not isinstance(error, OSError) or self.acquisition_unknown
            ):
                slot.state = "unknown"
                slot.diagnostics = ("acquisition_return_unavailable",)
            if (
                acquired is None
                and isinstance(error, FileNotFoundError)
                and dir_fd is not None
            ):
                relative = "/".join(filter(None, (self.fd_paths[dir_fd], str(path))))
                self.current_absences.add(relative)
            self.refresh(slot)
            raise

    def close(self, descriptor):
        if descriptor == self.root_descriptor and self.root_borrows:
            self.root_borrows -= 1
            return
        slot = self.active.get(descriptor)
        if slot is None:
            # A spent integer, even after unknown close, is never dispatched again.
            return
        # Disposal changes original custody even if allocating its descriptive
        # snapshot fails. Never retain a pre-close cached ownership observation.
        self.invalidate_snapshot(slot)
        self.active.pop(descriptor)
        self.fd_paths.pop(descriptor, None)
        slot.attempted = True
        before = self.closed
        super().close(descriptor)
        slot.state = "released" if self.closed == before + 1 else "unknown"
        if slot.state == "unknown":
            slot.diagnostics = ("descriptor_close_return_unavailable",)
        if descriptor == self.root_descriptor:
            self.root_descriptor = None
        self.refresh(slot)
        # Historical rights stay in C evidence; original IO lookup stays bounded.
        self.resources[:] = [
            record for record in self.resources if record is not slot.record
        ]

    def release_all(self):
        if self.root_borrows:
            # Owner retirement is serialized after the worker. Drain only the
            # still-owned original root right; never retry a borrowed integer.
            self.context_unknown = True
            self.diagnostic("tree_root_borrow_unsettled")
            self.root_borrows = 0
        try:
            super().close_unspent()
        except BaseException as error:  # noqa: BLE001 - keep the primary and drain independent originals
            self.cleanup_failure(error, "tree_cleanup_drain")
        for descriptor in tuple(self.active):
            self.close(descriptor)

    def invalidate_snapshot(self, slot):
        self.invalid_snapshots.add(slot.index)
        self.snapshots[slot.index] = None
        self.snapshot_tuple = None

    def refresh(self, slot):
        self.invalidate_snapshot(slot)
        self.snapshots[slot.index] = ConfinedTreeResourceCleanup(
            slot.ref,
            "acquisition_reservation" if slot.state == "not_acquired" else "descriptor",
            slot.path,
            "owned"
            if slot.state == "owned"
            else "released"
            if slot.state in {"released", "not_acquired"}
            else "unknown",
            slot.attempted,
            "completed"
            if slot.state in {"released", "not_acquired"}
            else "not_attempted"
            if slot.state == "owned"
            else "unknown",
            slot.diagnostics,
        )
        self.invalid_snapshots.discard(slot.index)

    def resource_observations(self):
        if self.snapshot_tuple is None:
            for index in tuple(self.invalid_snapshots):
                self.refresh(self.history[index])
            self.snapshot_tuple = tuple(self.snapshots)
        return self.snapshot_tuple


@dataclass
class _State:
    root: Path
    root_fd: int | None
    request: ConfinedTreeProjectionRequest | None
    request_ref: str
    preparation_ref: str
    ledger: _TreeLedger
    pid: int = field(default_factory=os.getpid)
    phase: str = "preparing"
    preparation: ConfinedTreePreparationObservation | None = None
    pins: dict[str, ConfinedTreeEntryPin] = field(default_factory=dict)
    lock: threading.RLock = field(default_factory=threading.RLock)
    busy: bool = False
    next_ordinal: int = 0
    completed_prefix: int = 0
    pending_ordinal: int | None = None
    effects: list = field(default_factory=list)
    scratch: dict = field(default_factory=dict)
    ledger_complete: bool = True
    diagnostics: list = field(default_factory=list)
    last_transition: ConfinedTreeTransitionResult | None = None
    execution_reserve: int = 0
    unverified_paths: set = field(default_factory=set)
    preparation_bytes: int = 0
    final_pin_reserve: int = 0
    scratch_paths: dict = field(default_factory=dict)
    next_guard_ordinal: int = -1
    consumed_checks: int = 0
    operation_revision: int = 0
    capacity_model: object = None
    capacity_effects: tuple = ()
    capacity_scratch: tuple = ()
    forecast_seen: bool = False
    forecast_full_spent: bool = False


@dataclass
class _Scratch:
    path: str
    ordinal: int
    identity: tuple | None = None
    descriptor: int | None = None
    created: bool = False
    removed: bool = False
    attempted_cleanup: bool = False
    unknown: bool = False
    cleanup_key: tuple | None = None
    cleanup_snapshot: ConfinedTreeResourceCleanup | None = None


_HANDLES: WeakKeyDictionary = WeakKeyDictionary()
_DIRECTORY_FLAGS = (
    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
)


class RetainedPhysicalTreeProjection:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use retain_confined_tree_projection")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Retained tree originals cannot be subclassed")

    def __copy__(self):
        raise TypeError("Retained tree originals cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Retained tree originals cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Retained tree originals cannot be serialized")

    def observe_preparation(self):
        state = _issued(self)
        with state.lock:
            return state.preparation

    def observe_capacity_forecast(self) -> ConfinedTreeCapacityForecast:
        state = _issued(self, retire_on_change=False)
        with state.lock:
            if (
                state.busy
                or state.phase != "prepared"
                or state.next_ordinal != 0
                or state.effects
                or state.request is None
                or not state.ledger_complete
                or state.ledger.acquisition_unknown
                or state.ledger.release_unknown
                or state.ledger.context_unknown
                or state.ledger.root_borrows
                or state.root_fd is None
                or set(state.ledger.active) != {state.root_fd}
                or state.next_guard_ordinal != -1
                or state.forecast_full_spent
            ):
                raise RetainedPhysicalTreeProjectionRefusal(
                    "tree_capacity_forecast_unavailable"
                )
            try:
                _check_capacity_definitions()
                _metadata_check(state)
                forecast = _capacity_forecast(state)
                _check_capacity_definitions()
                # This marks the observation point, not permission or capacity.
                # Its one full-read allowance was reserved by the original factory.
                state.forecast_seen = True
                return forecast
            except RetainedPhysicalTreeProjectionRefusal:
                raise
            except BaseException as error:
                raise RetainedPhysicalTreeProjectionRefusal(
                    "tree_capacity_forecast_unavailable"
                ) from error

    def validate_current(self):
        state = _issued(self)
        with state.lock:
            if state.phase not in ("prepared", "active"):
                raise _refusal(state, "tree_preparation_terminal")
            if state.busy:
                raise _refusal(state, "tree_operation_in_progress")
            state.busy = True
            state.operation_revision += 1
            if state.forecast_seen and not state.forecast_full_spent:
                state.forecast_full_spent = True
                state.ledger.planned_reads = True
            try:
                _capture(state, expected=state.pins)
                _metadata_check(state)
            except BaseException as error:
                _retire(state)
                raise _refusal(
                    state, getattr(error, "code", "tree_currentness_unavailable")
                ) from error
            finally:
                state.busy = False
                state.ledger.planned_reads = False

    def validate_next_current(self) -> None:
        state = _issued(self)
        with state.lock:
            if state.busy:
                raise _refusal(state, "tree_operation_in_progress")
            if state.phase not in ("prepared", "active") or state.next_ordinal >= len(
                state.preparation.transition_order
            ):
                raise _refusal(state, "tree_next_transition_unavailable")
            state.busy = True
            state.operation_revision += 1
            try:
                ordinal, path, kind = state.preparation.transition_order[
                    state.next_ordinal
                ]
                state.ledger.planned_reads = state.next_guard_ordinal != ordinal
                _check_path(state, path, directory=kind.startswith("directory_"))
                scratch_path = state.scratch_paths.get(ordinal)
                if scratch_path is not None:
                    _check_path(state, scratch_path)
                _metadata_check(state)
                state.next_guard_ordinal = ordinal
            except BaseException as error:
                _retire(state)
                raise _refusal(
                    state, getattr(error, "code", "tree_next_currentness_unavailable")
                ) from error
            finally:
                state.busy = False
                state.ledger.planned_reads = False

    def observe_effects(self):
        state = _issued(self)
        with state.lock:
            return _effects(state)

    def release(self):
        state = _issued(self)
        with state.lock:
            if state.busy:
                raise _refusal(state, "tree_operation_in_progress")
            _retire(state)
            observation = _cleanup(state)
            if observation.cleanup_state == "unknown":
                raise _refusal(state, "tree_cleanup_unknown")
            return observation

    def apply_next_transition(self):
        state = _issued(self)
        with state.lock:
            if state.busy:
                raise _refusal(state, "tree_operation_in_progress")
            if state.phase not in ("prepared", "active") or state.next_ordinal >= len(
                state.preparation.transition_order
            ):
                raise _refusal(state, "tree_transition_terminal")
            state.busy = True
            state.ledger.planned_reads = True
            ordinal, path, kind = state.preparation.transition_order[state.next_ordinal]
            state.pending_ordinal = ordinal
            # Spend before the freshness checks or any effect. A missing return
            # or partial ordinal cannot be dispatched again.
            state.next_ordinal += 1
            state.last_transition = None
            start = len(state.effects)
            before = state.pins[path]
            try:
                _check_path(state, path, directory=kind.startswith("directory_"))
                if kind.startswith("directory_"):
                    _apply_directory(state, ordinal, path, kind)
                else:
                    _apply_file(state, ordinal, path)
                _metadata_check(state)
                if not _cleanup(state).ledger_complete:
                    raise _refusal(state, "tree_transition_cleanup_unknown")
                state.completed_prefix += 1
                state.pending_ordinal = None
                state.phase = "active"
                result = _transition(
                    state, ordinal, path, kind, before, start, complete=True
                )
                state.last_transition = result
                return result
            except BaseException as error:
                code = getattr(error, "code", "tree_transition_failed")
                state.diagnostics.append(code)
                _retire(state)
                try:
                    result = _transition(
                        state,
                        ordinal,
                        path,
                        kind,
                        before,
                        start,
                        complete=False,
                        code=code,
                    )
                    state.last_transition = result
                except BaseException:  # noqa: BLE001 - return failure cannot erase original effect ledger
                    state.ledger_complete = False
                    state.diagnostics.append("tree_transition_return_unavailable")
                raise _refusal(state, code) from error
            finally:
                state.busy = False
                state.ledger.planned_reads = False

    def finish(self):
        state = _issued(self)
        with state.lock:
            if state.busy:
                raise _refusal(state, "tree_operation_in_progress")
            if state.phase == "consumed":
                raise _refusal(state, "tree_transition_terminal")
            if state.phase not in (
                "prepared",
                "active",
            ) or state.completed_prefix != len(state.preparation.transition_order):
                _retire(state)
                raise _refusal(state, "tree_transitions_incomplete")
            state.busy = True
            state.ledger.planned_reads = True
            try:
                _capture(state, expected=state.pins)
                _metadata_check(state)
                state.phase = "consumed"
                return _effects(state)
            except BaseException as error:
                _retire(state)
                raise _refusal(
                    state, getattr(error, "code", "tree_finish_failed")
                ) from error
            finally:
                state.busy = False
                state.ledger.planned_reads = False

    def validate_consumed_current(self):
        state = _issued(self)
        with state.lock:
            if state.busy:
                raise _refusal(state, "tree_operation_in_progress")
            if state.phase != "consumed":
                raise _refusal(state, "tree_consumed_postimage_required")
            state.busy = True
            state.ledger.planned_reads = state.consumed_checks < 2
            state.consumed_checks += 1
            try:
                _capture(state, expected=state.pins)
                _metadata_check(state)
            except BaseException as error:
                _retire(state)
                raise _refusal(
                    state, getattr(error, "code", "tree_consumed_currentness_failed")
                ) from error
            finally:
                state.busy = False
                state.ledger.planned_reads = False


_HANDLE_METHODS = {
    name: method
    for name, method in vars(RetainedPhysicalTreeProjection).items()
    if callable(method)
}


def _issued(handle, *, retire_on_change=True):
    if type(handle) is not RetainedPhysicalTreeProjection:
        raise RetainedPhysicalTreeProjectionRefusal("original_tree_handle_required")
    state = _HANDLES.get(handle)
    if state is None:
        raise RetainedPhysicalTreeProjectionRefusal("tree_handle_not_issued")
    # Process rejection must precede inherited locks and any IO/cleanup.
    if state.pid != os.getpid():
        raise _refusal(state, "tree_handle_foreign_process")
    if any(
        vars(RetainedPhysicalTreeProjection).get(name) is not method
        for name, method in _HANDLE_METHODS.items()
    ):
        if retire_on_change:
            _retire(state)
        raise _refusal(state, "tree_handle_methods_changed")
    return state


def _entry(observed, body=None):
    return ConfinedTreeEntryPin(
        True,
        observed.st_dev,
        observed.st_ino,
        observed.st_size,
        observed.st_mtime_ns,
        observed.st_ctime_ns,
        stat.S_IMODE(observed.st_mode),
        observed.st_nlink,
        None if body is None else _content_digest(body),
    )


def _read_entry(state, path, *, directory=False):
    ledger = state.ledger
    ledger.current_path = path
    descriptors = []
    try:
        try:
            parent = _open_parent(
                root=state.root,
                path=path,
                descriptors=descriptors,
                _read_ledger=ledger,
                _release_previous=True,
            )
        except FileNotFoundError:
            if ledger.stage == "root_open":
                raise
            return ConfinedTreeEntryPin(False), None
        leaf = PurePosixPath(path).name
        if directory:
            try:
                before = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                ledger.current_absences.add(path)
                return ConfinedTreeEntryPin(False), None
            if not stat.S_ISDIR(before.st_mode):
                raise RetainedPhysicalTreeProjectionRefusal(
                    "tree_ancestor_not_directory"
                )
            opened = ledger.open(leaf, _DIRECTORY_FLAGS, dir_fd=parent)
            try:
                current = os.fstat(opened)
                if not _same_stat(before, current):
                    raise RetainedPhysicalTreeProjectionRefusal("tree_ancestor_changed")
                return _entry(current), None
            finally:
                ledger.close(opened)
        current = _read_current(
            parent_descriptor=parent,
            leaf=leaf,
            maximum_bytes=state.request.limits.maximum_file_bytes,
            _read_ledger=ledger,
        )
        if isinstance(current, str):
            raise RetainedPhysicalTreeProjectionRefusal(current)
        body, observed = current
        if observed is None:
            return ConfinedTreeEntryPin(False), None
        if observed.st_nlink != 1 or stat.S_IMODE(observed.st_mode) & 0o7000:
            raise RetainedPhysicalTreeProjectionRefusal(
                "tree_ordinary_single_link_preimage_required"
            )
        after = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        if not _same_stat(observed, after):
            raise RetainedPhysicalTreeProjectionRefusal("tree_leaf_identity_changed")
        return _entry(observed, body), body
    finally:
        for descriptor in reversed(descriptors):
            ledger.close(descriptor)
        ledger.current_path = None


def _capture(state, *, expected=None):
    request = state.request
    if state.root_fd is None or request is None:
        raise _refusal(state, "tree_preparation_terminal")
    opened_root = os.fstat(state.root_fd)
    live_root = os.stat(state.root, follow_symlinks=False)
    if (
        not _same_stat(opened_root, live_root)
        or (live_root.st_dev, live_root.st_ino) != request.root_identity
    ):
        raise RetainedPhysicalTreeProjectionRefusal("tree_root_identity_changed")
    root_pin = state.ledger.directory_pins[""]
    if stat.S_IMODE(live_root.st_mode) != root_pin.mode:
        raise RetainedPhysicalTreeProjectionRefusal("tree_root_mode_changed")
    pins = {}
    scratch_candidates = []
    state.ledger.current_directories = {"": _entry(live_root)}
    state.ledger.current_absences.clear()
    # One original walk captures every intermediate directory pin. Avoid
    # reopening each prefix separately (quadratic in a deep explicit chain).
    directory_parents = {
        str(parent)
        for row in request.ancestors
        for parent in PurePosixPath(row.path).parents
    }
    for row in request.ancestors:
        if row.path not in directory_parents:
            _read_entry(state, row.path, directory=True)
    for row in request.ancestors:
        actual = state.ledger.current_directories.get(row.path)
        if actual is None:
            if any(
                row.path == missing or row.path.startswith(missing + "/")
                for missing in state.ledger.current_absences
            ):
                actual = ConfinedTreeEntryPin(False)
            else:
                actual, _ = _read_entry(state, row.path, directory=True)
        # A directory preimage guards identity/mode, not unrelated child writes.
        before = row.before if expected is None else expected[row.path]
        if actual.exists != before.exists or (
            actual.exists
            and (actual.device, actual.inode, actual.mode)
            != (before.device, before.inode, before.mode)
        ):
            raise RetainedPhysicalTreeProjectionRefusal(
                "tree_ancestor_preimage_changed"
            )
        pins[row.path] = actual
    for index, row in enumerate(request.files, len(request.ancestors)):
        actual, body = _read_entry(state, row.path)
        before = row.before if expected is None else expected[row.path]
        if actual != before:
            raise RetainedPhysicalTreeProjectionRefusal("tree_file_preimage_changed")
        pins[row.path] = actual
        if row.kind is not ConfinedMutationKind.DELETE and (
            not actual.exists or body != row.content
        ):
            scratch_candidates.append((index, row))
    if state.preparation is None:
        scratch = []
        used = set(pins)
        for ordinal, row in scratch_candidates:
            path = str(PurePosixPath(row.path).parent / (".aware-tree-" + uuid4().hex))
            if len(path.encode("utf-8")) > request.limits.maximum_path_utf8_bytes:
                raise RetainedPhysicalTreeProjectionRefusal(
                    "tree_scratch_path_capacity_exceeded"
                )
            if path in used:
                raise RetainedPhysicalTreeProjectionRefusal("tree_scratch_collision")
            used.add(path)
            pin, _ = _read_entry(state, path)
            if pin.exists:
                raise RetainedPhysicalTreeProjectionRefusal("tree_scratch_collision")
            pins[path] = pin
            scratch.extend(
                ConfinedTreeScratchEffect(path, "replacement_body", ordinal, kind, mode)
                for kind, mode in (
                    ("create", 0o600),
                    ("mode", row.requested_mode),
                    ("sync", None),
                    ("unlink", None),
                )
            )
        state.preparation = ConfinedTreePreparationObservation(
            state.preparation_ref,
            request.request_ref,
            _content_digest(_wire(_request_descriptor(request))),
            request.root_identity,
            tuple(
                (i, row.path, "directory_" + row.intent)
                for i, row in enumerate(request.ancestors)
            )
            + tuple(
                (i, row.path, row.kind.name)
                for i, row in enumerate(request.files, len(request.ancestors))
            ),
            tuple(sorted(pins.items())),
            tuple(scratch),
            request.limits.maximum_live_descriptors,
        )
        state.pins = pins
        state.preparation_bytes = len(_wire(asdict(state.preparation)))
        state.scratch_paths = {row.ordinal: row.path for row in scratch}
    else:
        for path in {effect.path for effect in state.preparation.scratch_effects}:
            actual, _ = _read_entry(state, path)
            pins[path] = actual
        for path, actual in pins.items():
            old = expected[path]
            if path in {row.path for row in request.ancestors}:
                matches = actual.exists == old.exists and (
                    not actual.exists
                    or (actual.device, actual.inode, actual.mode)
                    == (old.device, old.inode, old.mode)
                )
            else:
                matches = actual == old
            if not matches:
                raise RetainedPhysicalTreeProjectionRefusal("tree_read_pin_changed")
    if (
        state.ledger.release_unknown
        or state.ledger.acquisition_unknown
        or state.ledger.context_unknown
    ):
        raise RetainedPhysicalTreeProjectionRefusal("tree_read_cleanup_unknown")
    final_root = os.stat(state.root, follow_symlinks=False)
    if (final_root.st_dev, final_root.st_ino, stat.S_IMODE(final_root.st_mode)) != (
        root_pin.device,
        root_pin.inode,
        root_pin.mode,
    ):
        raise RetainedPhysicalTreeProjectionRefusal("tree_root_identity_changed")


def _wire(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _reserve_execution(state):
    # Reserve the reachable native records, not 18 oversized generic slots per
    # file. The accepted 16-subeffect ceiling is not a claim that every branch
    # emits 16 effects. All fields below take their longest native encoding;
    # path escaping is measured by the original JSON encoder, not UTF-8 length.
    request = state.request
    paths = [row.path for row in (*request.files, *request.ancestors)]
    required_live = 1 + bool(paths) + any("/" in path for path in paths)
    if required_live > request.limits.maximum_live_descriptors:
        raise RetainedPhysicalTreeProjectionRefusal("tree_descriptor_capacity_exceeded")
    scratch = {row.ordinal: row.path for row in state.preparation.scratch_effects}
    amount = 0
    largest_return = 0
    effect_capacities = []
    scratch_capacities = []
    for ordinal, path, kind in state.preparation.transition_order:
        scratch_path = scratch.get(ordinal)

        def slot(
            name,
            *,
            body=False,
            before=False,
            after=False,
            path=path,
            scratch_path=scratch_path,
            ordinal=ordinal,
            kind=kind,
        ):
            return _effect_slot_capacity(
                scratch_path if body else path,
                ordinal,
                kind=name,
                role="replacement_body"
                if body
                else "directory"
                if kind.startswith("directory_")
                else "file",
                before=before,
                after=after,
                error=False,
            )

        if scratch_path is not None:
            # Seven successful effects. An uncertain scratch unlink can add
            # cleanup unlink + directory sync instead of the normal final sync:
            # at most eight records, including descriptor close and cleanup.
            capacity = (
                slot("scratch_create", body=True)
                + slot("mode_update", body=True)
                + slot("file_sync", body=True)
                + _effect_slot_capacity(
                    scratch_path,
                    ordinal,
                    before_identity_only=True,
                    before=False,
                    after=False,
                    error=False,
                )
                + slot(
                    "file_create" if kind == "CREATE" else "file_replace",
                    before=kind != "CREATE",
                    after=True,
                )
                + slot("scratch_unlink", body=True, before=kind != "CREATE")
                + slot("scratch_unlink", body=True)
                + max(slot("directory_sync", body=True), slot("directory_sync"))
            )
        elif kind == "DELETE":
            capacity = slot("file_delete", before=True) + slot("directory_sync")
        elif kind == "directory_preserve":
            capacity = 0
        elif kind == "directory_create":
            capacity = (
                slot("directory_create", after=True)
                + slot("mode_update", before=True, after=True)
                + slot("directory_sync")
            )
        else:
            capacity = (
                slot("mode_update", before=True, after=True)
                + slot("file_sync")
                + slot("directory_sync")
            )
        # Scratch ownership and residual diagnostics are separate from effects.
        cleanup = 0
        if scratch_path is not None:
            cleanup = (
                len(
                    _wire(
                        asdict(
                            ConfinedTreeResourceCleanup(
                                "scratch:" + scratch_path,
                                "scratch",
                                scratch_path,
                                "unknown",
                                False,
                                "not_attempted",
                                ("scratch_cleanup_unverified",),
                            )
                        )
                    )
                )
                + len(_wire(scratch_path))
                + 2
            )
        amount += capacity + cleanup
        amount += cleanup  # The latest return also retains full scratch cleanup.
        largest_return = max(largest_return, capacity)
        effect_capacities.append(capacity)
        scratch_capacities.append(cleanup)
    # Only the latest transition result is retained. Reserve its duplicated
    # effect tuple and bounded frame once, not once for every past ordinal.
    # Only one ordinal may fail: keep its unknown/error frame in addition to
    # the complete successful prefix, not an error traceback for every effect.
    amount += largest_return + 16 * 44 + 8192 + len(_wire(request.request_ref))
    if amount + state.ledger.metadata_reserved > request.limits.maximum_metadata_bytes:
        raise RetainedPhysicalTreeProjectionRefusal(
            "tree_execution_evidence_capacity_exceeded"
        )
    state.execution_reserve = amount
    scratch_names = set(scratch.values())
    maximum_pin = ConfinedTreeEntryPin(
        True,
        *(2**64 - 1 for _ in range(5)),
        0o7777,
        2**64 - 1,
        "sha256:" + "f" * 64,
    )
    absent_pin_bytes = len(_wire(asdict(ConfinedTreeEntryPin(False))))
    maximum_pin_bytes = len(_wire(asdict(maximum_pin)))
    state.final_pin_reserve = sum(
        len(_wire(path))
        + (absent_pin_bytes if path in scratch_names else maximum_pin_bytes)
        + 3
        for path in state.pins
    )
    state.capacity_effects = tuple(effect_capacities)
    state.capacity_scratch = tuple(scratch_capacities)
    state.capacity_model = _compile_read_capacity(state)
    future, count = _future_read_capacity(state)
    state.ledger.future_resource_reserved = future
    state.ledger.future_resource_rows = count
    state.ledger.scratch_resource_rows = len(scratch)
    # Native records are bounded once. The other copy is the latest immutable
    # transition cleanup snapshot; known released rows are not charged again
    # as both actual encoded bytes and their original allocation reservation.
    state.ledger.metadata_other = (
        state.preparation_bytes + state.final_pin_reserve + amount + 2 * 65 * 128
    )
    if len(state.ledger.history) + count + len(scratch) > 8192:
        raise RetainedPhysicalTreeProjectionRefusal(
            "tree_cleanup_resource_capacity_exceeded"
        )
    _metadata_check(state)


def _effect_slot_capacity(
    path,
    ordinal,
    *,
    kind="descriptor_release",
    role="replacement_body",
    before=True,
    after=True,
    before_identity_only=False,
    error=True,
):
    maximum = 2**64 - 1
    return 1 + len(
        _wire(
            asdict(
                ConfinedTreePhysicalEffect(
                    "tree-effect:" + "f" * 32,
                    ordinal,
                    path,
                    role,
                    kind,
                    ConfinedMutationEffectState.UNKNOWN,
                    (maximum, maximum) if before or before_identity_only else None,
                    (maximum, maximum) if after else None,
                    "sha256:" + "f" * 64 if before else None,
                    "sha256:" + "f" * 64 if after else None,
                    maximum
                    if before and role == "directory"
                    else 16 * 1024 * 1024
                    if before
                    else None,
                    maximum
                    if after and role == "directory"
                    else 16 * 1024 * 1024
                    if after
                    else None,
                    0o7777 if before else None,
                    0o7777 if after else None,
                    False,
                    "tree-error:" + "f" * 32 if error else None,
                )
            )
        )
    )


def _resource_slot_capacity(path):
    # One complete successful/owned/unacquired record. At most 64 live rights
    # plus a lost acquisition can become unknown; their diagnostics have a
    # separately reserved 65-row margin, not a per-history-row surcharge.
    return 1 + len(
        _wire(
            asdict(
                ConfinedTreeResourceCleanup(
                    "descriptor:" + "f" * 32,
                    "acquisition_reservation",
                    path,
                    "released",
                    False,
                    "not_attempted",
                    (),
                )
            )
        )
    )


@dataclass(frozen=True, slots=True)
class _ReadCapacity:
    steps: tuple
    final: tuple
    terminal: tuple
    full: tuple


def _compile_read_capacity(state):
    """One owner compiler for reservations and original prefix forecasts."""
    request = state.request
    steps = [(0, 0)] * len(state.preparation.transition_order)
    final = full = (0, 0)

    def add(pair, path, acquisitions):
        return pair[0] + acquisitions, pair[1] + acquisitions * _resource_slot_capacity(
            path
        )

    max_cleanup = (0, None)
    for ordinal, row in enumerate(request.files, len(request.ancestors)):
        depth = row.path.count("/")
        scratch = state.scratch_paths.get(ordinal)
        if scratch is not None:
            step = add((0, 0), scratch, 1 + 4 * depth)
            steps[ordinal] = add(step, row.path, 1 + 4 * row.before.exists + 7 * depth)
            final = add(final, row.path, 3 * (depth + 1))
            full = add(full, scratch, depth)
            if depth > max_cleanup[0]:
                max_cleanup = (depth, scratch)
        else:
            deleted = row.kind is ConfinedMutationKind.DELETE
            steps[ordinal] = add((0, 0), row.path, (4 if deleted else 6) + 6 * depth)
            final = add(final, row.path, 3 * (depth + (not deleted)))
        full = add(full, row.path, depth + row.before.exists)
    # Full final capture walks only maximal ancestor paths. Intermediate pins
    # come from that original walk, exactly as in _capture (not new cached IO).
    parents = {
        str(p) for row in request.ancestors for p in PurePosixPath(row.path).parents
    }
    for ordinal, row in enumerate(request.ancestors):
        depth = row.path.count("/")
        steps[ordinal] = add(
            (0, 0),
            row.path,
            4 * depth + 2 if row.intent == "create" else 2 * (depth + 1),
        )
        if row.path not in parents:
            final = add(final, row.path, 3 * (depth + 1))
            full = add(full, row.path, depth + row.before.exists)
    terminal = (
        add((0, 0), max_cleanup[1], max_cleanup[0])
        if max_cleanup[1] is not None
        else (0, 0)
    )
    return _ReadCapacity(tuple(steps), final, terminal, full)


def _future_read_capacity(state):
    model = state.capacity_model or _compile_read_capacity(state)
    count = (
        sum(row[0] for row in model.steps)
        + model.final[0]
        + model.terminal[0]
        + model.full[0]
    )
    amount = (
        sum(row[1] for row in model.steps)
        + model.final[1]
        + model.terminal[1]
        + model.full[1]
    )
    return amount, count


def _capacity_forecast(state):
    model = state.capacity_model
    preparation, request, ledger = state.preparation, state.request, state.ledger
    if type(model) is not _ReadCapacity:
        raise RetainedPhysicalTreeProjectionRefusal(
            "tree_capacity_compiler_unavailable"
        )
    count = len(model.steps)
    # The held mutation parent and an independent postimage walk can coexist.
    # Do not reinterpret v0's declared live limit as a proof of that suffix.
    required_live = (
        4
        if any("/" in row.path for row in request.files)
        else 3
        if any("/" in row.path for row in request.ancestors)
        else 2
        if count
        else 1
    )
    if required_live > request.limits.maximum_live_descriptors:
        raise RetainedPhysicalTreeProjectionRefusal("tree_descriptor_capacity_exceeded")
    paths = tuple(state.pins)
    maximum = 2**64 - 1
    maximum_pin = ConfinedTreeEntryPin(
        True, *(maximum for _ in range(5)), 0o7777, maximum, "sha256:" + "f" * 64
    )
    maximum_pin_bytes = len(_wire(asdict(maximum_pin)))
    error_ref_bytes = max(
        len(_wire("tree-error:" + preparation.preparation_ref)),
        len(_wire("tree-error:" + "f" * 32)),
    )
    resource_bytes = max(_resource_slot_capacity(path) + 128 for path in (None, *paths))
    scratch_row_bytes = {}
    for path in set(state.scratch_paths.values()):
        scratch_row_bytes[path] = 2 + len(
            _wire(
                asdict(
                    ConfinedTreeResourceCleanup(
                        "scratch:" + path,
                        "scratch",
                        path,
                        "released",
                        True,
                        "not_attempted",
                        ("scratch_cleanup_unverified",),
                    )
                )
            )
        )
    if scratch_row_bytes:
        resource_bytes = max(resource_bytes, max(scratch_row_bytes.values()))
    effect_bytes = max(
        (
            _effect_slot_capacity(
                path, count, role="directory", kind="descriptor_release"
            )
            for path in paths
        ),
        default=1024,
    )
    encoding = ConfinedTreeEncodingBounds(
        resource_bytes,
        effect_bytes,
        error_ref_bytes,
        maximum_pin_bytes,
        256,
        16,
        65,
        5,
        16,
        2,
    )
    observed_rows = len(ledger.history)
    observed_wire = len(_wire([asdict(row) for row in ledger.resource_observations()]))
    header = (
        8192 + len(_wire(request.request_ref)) + len(_wire(preparation.preparation_ref))
    )
    release_extra = resource_bytes + 65 * 128 + 16 * encoding.maximum_diagnostic_bytes
    # A terminal interruption can expose held rows before independent release.
    # Charge their changed records once, never five variants for all history.
    terminal_dispositions = min(
        encoding.maximum_uncertain_resource_rows,
        request.limits.maximum_live_descriptors + 1,
    )
    acquisition_rows = observed_rows + model.full[0]
    acquisition_bytes = ledger.resource_reserved + model.full[1]
    scratch_rows = scratch_bytes = effect_rows = effect_wire = 0
    largest_return = max(state.capacity_effects, default=0)
    prefixes = []
    for prefix in range(count + 1):
        # Full final captures belong only to the complete-prefix suffix.
        current_rows = acquisition_rows + (model.final[0] if prefix == count else 0)
        current_bytes = acquisition_bytes + (model.final[1] if prefix == count else 0)
        if prefix < count:
            ordinal, _path, kind = preparation.transition_order[prefix]
            failed_scratch = int(ordinal in state.scratch_paths)
            terminal_rows = model.steps[prefix][0] + model.terminal[0]
            terminal_bytes = (
                model.steps[prefix][1]
                + model.terminal[1]
                + failed_scratch * resource_bytes
                + 16 * effect_bytes
                + header
                + release_extra
            )
        else:
            failed_scratch, terminal_rows = 0, model.terminal[0]
            terminal_bytes = model.terminal[1] + header + release_extra
        cleanup_wire = header + current_bytes + scratch_bytes
        prefixes.append(
            ConfinedTreePrefixCapacity(
                prefix,
                current_rows,
                scratch_rows,
                current_rows + scratch_rows + 1,
                cleanup_wire,
                effect_rows,
                effect_wire + 2,
                state.final_pin_reserve + 2 + len(state.pins),
                cleanup_wire + largest_return + header,
                terminal_rows,
                terminal_rows + failed_scratch + terminal_dispositions,
                terminal_bytes,
                release_extra,
            )
        )
        if prefix < count:
            acquisition_rows += model.steps[prefix][0]
            acquisition_bytes += model.steps[prefix][1]
            _, _, kind = preparation.transition_order[prefix]
            scratch_path = state.scratch_paths.get(prefix)
            if scratch_path is not None:
                scratch_rows += 1
                scratch_bytes += scratch_row_bytes[scratch_path]
                effect_rows += 7
            else:
                effect_rows += (
                    2 if kind == "DELETE" else 0 if kind == "directory_preserve" else 3
                )
            successful_wire = state.capacity_effects[prefix]
            if scratch_path is not None:
                # The eighth allocator slot is cleanup after a failed unlink.
                # _dispatch raises, so that branch retires before another ordinal.
                # Successful prefixes keep all seven effects; the original
                # terminal sixteen-effect reserve and allocator stay unchanged.
                successful_wire -= _effect_slot_capacity(
                    scratch_path,
                    prefix,
                    role="replacement_body",
                    kind="scratch_unlink",
                    before=False,
                    after=False,
                    error=False,
                )
            effect_wire += successful_wire
    values = {
        "schema": "aware.filesystem.tree-capacity-forecast.v1",
        "preparation_ref": preparation.preparation_ref,
        "request_ref": preparation.request_ref,
        "request_digest": preparation.request_digest,
        "root_identity": preparation.root_identity,
        "transition_order": preparation.transition_order,
        "forecast_revision": state.operation_revision,
        "observed_acquisition_rows": observed_rows,
        "observed_scratch_rows": len(state.scratch),
        "observed_history_wire_bytes": observed_wire,
        "remaining_acquisition_rows": ledger.future_resource_rows,
        "remaining_scratch_rows": ledger.scratch_resource_rows,
        "remaining_history_wire_bytes": ledger.future_resource_reserved,
        "schedule": ConfinedTreeCapacitySchedule(
            "native_tree_c_capacity_v1", 1, count, count, 1, 2, 1
        ),
        "encoding": encoding,
        "prefixes": tuple(prefixes),
        "forecast_wire_bytes": 0,
    }
    descriptor = dict(values)
    descriptor["schedule"] = asdict(values["schedule"])
    descriptor["encoding"] = asdict(encoding)
    descriptor["prefixes"] = tuple(asdict(row) for row in prefixes)
    for _ in range(21):
        encoded_size = len(_wire(descriptor))
        if encoded_size == descriptor["forecast_wire_bytes"]:
            if encoded_size > request.limits.maximum_metadata_bytes:
                raise RetainedPhysicalTreeProjectionRefusal(
                    "tree_capacity_forecast_bytes_exceeded"
                )
            values["forecast_wire_bytes"] = encoded_size
            return ConfinedTreeCapacityForecast(**values)
        descriptor["forecast_wire_bytes"] = encoded_size
    raise RetainedPhysicalTreeProjectionRefusal(
        "tree_capacity_forecast_size_unavailable"
    )


def _check_root(state):
    if state.root_fd is None or state.request is None:
        raise _refusal(state, "tree_preparation_terminal")
    live = os.stat(state.root, follow_symlinks=False)
    retained = state.ledger.directory_pins[""]
    if (live.st_dev, live.st_ino, stat.S_IMODE(live.st_mode)) != (
        retained.device,
        retained.inode,
        retained.mode,
    ):
        raise RetainedPhysicalTreeProjectionRefusal("tree_root_identity_changed")


def _check_path(state, path, *, directory=False):
    _check_root(state)
    actual, body = _read_entry(state, path, directory=directory)
    expected = state.pins[path]
    matches = (
        actual == expected
        if not directory
        else actual.exists == expected.exists
        and (
            not actual.exists
            or (actual.device, actual.inode, actual.mode)
            == (expected.device, expected.inode, expected.mode)
        )
    )
    if not matches:
        raise RetainedPhysicalTreeProjectionRefusal("tree_read_pin_changed")
    return actual, body


def _identity(pin):
    return (pin.device, pin.inode) if pin is not None and pin.exists else None


def _dispatch(state, ordinal, path, role, kind, operation, *, before=None, after=None):
    _metadata_check(state)
    index = len(state.effects)
    error_ref = "tree-error:" + uuid4().hex
    pending = ConfinedTreePhysicalEffect(
        "tree-effect:" + uuid4().hex,
        ordinal,
        path,
        role,
        kind,
        ConfinedMutationEffectState.UNKNOWN,
        _identity(before),
        _identity(after),
        before.content_digest if before else None,
        after.content_digest if after else None,
        before.size_bytes if before else None,
        after.size_bytes if after else None,
        before.mode if before else None,
        after.mode if after else None,
        False,
        error_ref,
    )
    state.effects.append(pending)  # Retain uncertainty before dispatch.
    if role in ("file", "directory") and kind not in ("file_sync", "directory_sync"):
        state.unverified_paths.add(path)
    try:
        result = operation()
    except FileExistsError:
        # Atomic no-replace refuses without replacing the competing occupant.
        state.effects[index] = replace(pending, state=ConfinedMutationEffectState.NONE)
        raise
    except BaseException:
        state.ledger_complete = False
        raise
    state.effects[index] = replace(
        pending,
        state=ConfinedMutationEffectState.APPLIED,
        error_ref=None,
        durability_confirmed=kind in ("directory_sync", "file_sync"),
    )
    return result, index


def _parent(state, path, descriptors):
    state.ledger.current_path = path
    return _open_parent(
        root=state.root,
        path=path,
        descriptors=descriptors,
        _read_ledger=state.ledger,
        _release_previous=True,
    )


def _apply_directory(state, ordinal, path, kind):
    if kind == "directory_preserve":
        return
    descriptors = []
    ledger = state.ledger
    try:
        parent = _parent(state, path, descriptors)
        leaf = PurePosixPath(path).name

        class DirectoryIO:
            def mkdir(self, name, *, mode, dir_fd):
                _dispatch(
                    state,
                    ordinal,
                    path,
                    "directory",
                    "directory_create",
                    lambda: os.mkdir(name, mode=mode, dir_fd=dir_fd),
                    before=state.pins[path],
                )

        _mkdir_explicit(leaf, mode=0o755, dir_fd=parent, _io=DirectoryIO())
        observed = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISDIR(observed.st_mode):
            raise RetainedPhysicalTreeProjectionRefusal(
                "tree_created_directory_unverified"
            )
        created = _entry(observed)
        state.pins[path] = created
        _complete_effect_pins(state, path, created)
        fd = ledger.open(
            leaf, _DIRECTORY_FLAGS | getattr(os, "O_PATH", 0), dir_fd=parent
        )
        try:
            if _identity(_entry(os.fstat(fd))) != _identity(created):
                raise RetainedPhysicalTreeProjectionRefusal(
                    "tree_created_directory_changed"
                )
            if created.mode != 0o755:
                # O_PATH permits metadata custody even under a restrictive umask.
                # This Linux proc locator comes only from our live original fd,
                # never from a caller path or a borrowed descriptor.
                chmod = (
                    (lambda: os.chmod(f"/proc/self/fd/{fd}", 0o755))
                    if getattr(os, "O_PATH", 0)
                    else (lambda: os.fchmod(fd, 0o755))
                )
                _dispatch(
                    state,
                    ordinal,
                    path,
                    "directory",
                    "mode_update",
                    chmod,
                    before=created,
                )
            exact = _entry(os.fstat(fd))
            if exact.mode != 0o755:
                raise RetainedPhysicalTreeProjectionRefusal(
                    "tree_created_directory_mode_unverified"
                )
            state.pins[path] = exact
            ledger.directory_pins[path] = exact
        finally:
            ledger.close(fd)
        _check_path(state, path, directory=True)
        state.unverified_paths.discard(path)
        _complete_effect_pins(state, path, state.pins[path])
        _dispatch(
            state,
            ordinal,
            path,
            "directory",
            "directory_sync",
            lambda: os.fsync(parent),
        )
    finally:
        for fd in reversed(descriptors):
            ledger.close(fd)
        ledger.current_path = None


class _TreeWriteIO:
    """Internal recording for the original temporary writer, not a new writer."""

    def __init__(self, state, ordinal, path, parent):
        self.state, self.ordinal, self.path, self.parent = state, ordinal, path, parent
        self.scratch = _Scratch(path, ordinal)
        state.scratch[path] = self.scratch

    def open(self, name, flags, mode, *, dir_fd):
        state = self.state
        previous_path = state.ledger.current_path
        state.ledger.current_path = self.path
        try:
            fd, _ = _dispatch(
                state,
                self.ordinal,
                self.path,
                "replacement_body",
                "scratch_create",
                lambda: state.ledger.open(name, flags, dir_fd=dir_fd, mode=0o600),
                before=ConfinedTreeEntryPin(False),
            )
        except BaseException as error:
            self.scratch.unknown = not isinstance(error, FileExistsError)
            self.scratch.removed = isinstance(error, FileExistsError)
            raise
        finally:
            state.ledger.current_path = previous_path
        self.scratch.created = True
        self.scratch.descriptor = fd
        self.scratch.identity = _identity(_entry(os.fstat(fd)))
        return fd

    def write(self, fd, body):
        try:
            return os.write(fd, body)
        except BaseException:
            self.state.ledger_complete = False
            self.scratch.unknown = True
            raise

    def fchmod(self, fd, mode):
        _dispatch(
            self.state,
            self.ordinal,
            self.path,
            "replacement_body",
            "mode_update",
            lambda: os.fchmod(fd, mode),
        )

    def fsync(self, fd):
        _dispatch(
            self.state,
            self.ordinal,
            self.path,
            "replacement_body",
            "file_sync",
            lambda: os.fsync(fd),
        )

    def close(self, fd):
        # Original read ledger spends the close right before dispatch and never
        # retries a possibly reused integer. Preserve its returned uncertainty.
        state = self.state
        state.ledger.close(fd)
        resource = next(
            row
            for row in reversed(state.ledger.history)
            if row.record is not None and row.record.descriptor == fd
        )
        effect = ConfinedTreePhysicalEffect(
            "tree-effect:" + uuid4().hex,
            self.ordinal,
            self.path,
            "replacement_body",
            "descriptor_release",
            ConfinedMutationEffectState.APPLIED
            if resource.state == "released"
            else ConfinedMutationEffectState.UNKNOWN,
            self.scratch.identity,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            False,
            None if resource.state == "released" else "tree-error:descriptor-close",
        )
        state.effects.append(effect)
        if resource.state != "released":
            state.ledger_complete = False
            raise RetainedPhysicalTreeProjectionRefusal("tree_descriptor_close_unknown")


def _adopt_target(state, row, identity):
    actual, _ = _read_entry(state, row.path)
    if row.kind is ConfinedMutationKind.DELETE:
        if actual.exists:
            raise RetainedPhysicalTreeProjectionRefusal(
                "tree_delete_postimage_unverified"
            )
    elif (
        _identity(actual) != identity
        or actual.content_digest != row.content_digest
        or actual.size_bytes != row.size_bytes
        or actual.mode != row.requested_mode
    ):
        raise RetainedPhysicalTreeProjectionRefusal("tree_file_postimage_unverified")
    state.pins[row.path] = actual
    state.unverified_paths.discard(row.path)
    _complete_effect_pins(state, row.path, actual)


def _complete_effect_pins(state, path, actual):
    for index in range(len(state.effects) - 1, -1, -1):
        effect = state.effects[index]
        if (
            effect.path == path
            and effect.role in ("file", "directory")
            and effect.state is ConfinedMutationEffectState.APPLIED
            and effect.kind not in ("file_sync", "directory_sync")
        ):
            state.effects[index] = replace(
                effect,
                after_identity=_identity(actual),
                after_digest=actual.content_digest,
                after_size_bytes=actual.size_bytes,
                after_mode=actual.mode,
            )
            break


def _apply_file(state, ordinal, path):
    row = state.request.files[ordinal - len(state.request.ancestors)]
    before, body = _check_path(state, path)
    if (
        row.kind is not ConfinedMutationKind.DELETE
        and body == row.content
        and before.mode == row.requested_mode
    ):
        return
    descriptors = []
    ledger = state.ledger
    try:
        parent = _parent(state, path, descriptors)
        leaf = PurePosixPath(path).name
        if row.kind is ConfinedMutationKind.DELETE:
            _check_path(state, path)
            _dispatch(
                state,
                ordinal,
                path,
                "file",
                "file_delete",
                lambda leaf=leaf, parent=parent: os.unlink(leaf, dir_fd=parent),
                before=before,
                after=ConfinedTreeEntryPin(False),
            )
            state.pins[path] = ConfinedTreeEntryPin(False)
            _adopt_target(state, row, None)
        elif body == row.content:
            fd = ledger.open(
                leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
            )
            try:
                if _entry(os.fstat(fd), body) != before:
                    raise RetainedPhysicalTreeProjectionRefusal(
                        "tree_file_preimage_changed"
                    )
                _dispatch(
                    state,
                    ordinal,
                    path,
                    "file",
                    "mode_update",
                    lambda: os.fchmod(fd, row.requested_mode),
                    before=before,
                )
                _adopt_target(state, row, _identity(before))
                _dispatch(
                    state, ordinal, path, "file", "file_sync", lambda: os.fsync(fd)
                )
            finally:
                ledger.close(fd)
            _adopt_target(state, row, _identity(before))
        else:
            scratch_path = next(
                effect.path
                for effect in state.preparation.scratch_effects
                if effect.ordinal == ordinal
            )
            _check_path(state, scratch_path)
            temporary = PurePosixPath(scratch_path).name
            io = _TreeWriteIO(state, ordinal, scratch_path, parent)
            _write_temporary(
                parent_descriptor=parent,
                name=temporary,
                content=row.content,
                mode=row.requested_mode,
                preserve_mode=True,
                _io=io,
            )
            _check_path(state, path)
            current = os.stat(temporary, dir_fd=parent, follow_symlinks=False)
            if (
                not stat.S_ISREG(current.st_mode)
                or (current.st_dev, current.st_ino) != io.scratch.identity
                or current.st_nlink != 1
            ):
                raise RetainedPhysicalTreeProjectionRefusal(
                    "tree_original_scratch_required"
                )
            successor = _entry(current, row.content)
            try:
                if row.kind is ConfinedMutationKind.CREATE:
                    _dispatch(
                        state,
                        ordinal,
                        path,
                        "file",
                        "file_create",
                        lambda: os.link(
                            temporary,
                            leaf,
                            src_dir_fd=parent,
                            dst_dir_fd=parent,
                            follow_symlinks=False,
                        ),
                        before=before,
                        after=successor,
                    )
                    _dispatch(
                        state,
                        ordinal,
                        scratch_path,
                        "replacement_body",
                        "scratch_unlink",
                        lambda: os.unlink(temporary, dir_fd=parent),
                    )
                else:
                    _dispatch(
                        state,
                        ordinal,
                        path,
                        "file",
                        "file_replace",
                        lambda: os.replace(
                            temporary, leaf, src_dir_fd=parent, dst_dir_fd=parent
                        ),
                        before=before,
                        after=successor,
                    )
                    # The successful rename consumed this exact original name.
                    state.effects.append(
                        ConfinedTreePhysicalEffect(
                            "tree-effect:" + uuid4().hex,
                            ordinal,
                            scratch_path,
                            "replacement_body",
                            "scratch_unlink",
                            ConfinedMutationEffectState.APPLIED,
                            io.scratch.identity,
                            None,
                            row.content_digest,
                            None,
                            row.size_bytes,
                            None,
                            row.requested_mode,
                            None,
                            False,
                            None,
                        )
                    )
                io.scratch.removed = True
                state.pins[scratch_path] = ConfinedTreeEntryPin(False)
            except BaseException:
                io.scratch.unknown = True
                raise
            _adopt_target(state, row, io.scratch.identity)
        _dispatch(
            state, ordinal, path, "file", "directory_sync", lambda: os.fsync(parent)
        )
    finally:
        for fd in reversed(descriptors):
            ledger.close(fd)
        ledger.current_path = None


def _cleanup_scratch(state):
    for row in state.scratch.values():
        if row.removed or row.attempted_cleanup:
            continue
        row.attempted_cleanup = True
        descriptors = []
        try:
            _check_root(state)
            parent = _parent(state, row.path, descriptors)
            leaf = PurePosixPath(row.path).name
            try:
                current = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                if row.unknown:
                    raise RetainedPhysicalTreeProjectionRefusal(
                        "tree_scratch_disposition_unknown"
                    )
                row.removed = True
                continue
            if (
                row.identity is None
                or not stat.S_ISREG(current.st_mode)
                or (current.st_dev, current.st_ino) != row.identity
            ):
                raise RetainedPhysicalTreeProjectionRefusal(
                    "tree_original_scratch_required"
                )
            _dispatch(
                state,
                row.ordinal,
                row.path,
                "replacement_body",
                "scratch_unlink",
                lambda leaf=leaf, parent=parent: os.unlink(leaf, dir_fd=parent),
            )
            row.removed = True
            state.pins[row.path] = ConfinedTreeEntryPin(False)
            _dispatch(
                state,
                row.ordinal,
                row.path,
                "replacement_body",
                "directory_sync",
                lambda parent=parent: os.fsync(parent),
            )
        except BaseException as error:  # noqa: BLE001 - independent original scratch cleanup continues
            row.unknown = True
            state.ledger_complete = False
            state.diagnostics.append(
                getattr(error, "code", "tree_scratch_cleanup_unknown")
            )
        finally:
            for fd in reversed(descriptors):
                state.ledger.close(fd)
            state.ledger.current_path = None


def _transition(state, ordinal, path, kind, before, start, *, complete, code=None):
    effects = tuple(state.effects[start:])
    primary = tuple(
        effect
        for effect in effects
        if effect.role in ("file", "directory")
        and effect.kind not in ("file_sync", "directory_sync", "descriptor_release")
    )
    outcome = (
        ConfinedMutationEffectState.UNKNOWN
        if any(row.state is ConfinedMutationEffectState.UNKNOWN for row in primary)
        else ConfinedMutationEffectState.APPLIED
        if any(row.state is ConfinedMutationEffectState.APPLIED for row in primary)
        else ConfinedMutationEffectState.NONE
    )
    return ConfinedTreeTransitionResult(
        state.preparation_ref,
        state.request_ref,
        ordinal,
        path,
        kind,
        effects,
        before,
        state.pins.get(path) if complete else None,
        state.next_ordinal
        if complete and state.next_ordinal < len(state.preparation.transition_order)
        else None
        if complete
        else ordinal,
        outcome,
        "complete"
        if complete
        else "unknown"
        if not state.ledger_complete
        else "partial",
        complete and bool(effects),
        "matched" if complete else "unknown",
        None if complete else "tree-error:" + state.preparation_ref,
        code,
        _cleanup(state),
    )


def _request_descriptor(request):
    descriptor = asdict(request)
    for row in descriptor["files"]:
        # Native bytes never enter JSON. Their exact immutable bytes were checked
        # against the digest/size fields; preserve the native slot as explicit null.
        row["content"] = None
    return descriptor


def _metadata_check(state):
    ledger = state.ledger
    if (
        ledger.metadata_other
        + ledger.request_metadata
        + 2 * (ledger.resource_reserved + ledger.future_resource_reserved)
        > ledger.limits.maximum_metadata_bytes
    ):
        raise RetainedPhysicalTreeProjectionRefusal("tree_metadata_capacity_exceeded")


def _cleanup(state):
    resources = state.ledger.resource_observations()
    unknown = (
        state.ledger.acquisition_unknown
        or state.ledger.release_unknown
        or state.ledger.context_unknown
        or any(row.ownership == "unknown" for row in resources)
    )
    held = any(row.ownership == "owned" for row in resources)

    def snapshot(row):
        key = (row.removed, row.unknown, row.identity is None, row.attempted_cleanup)
        if row.cleanup_key == key:
            return row.cleanup_snapshot
        row.cleanup_snapshot = ConfinedTreeResourceCleanup(
            "scratch:" + row.path,
            "scratch",
            row.path,
            "released"
            if row.removed
            else "unknown"
            if row.unknown or row.identity is None
            else "owned",
            row.attempted_cleanup,
            "completed"
            if row.removed
            else "unknown"
            if row.unknown
            else "not_attempted",
            ("scratch_cleanup_unverified",) if row.unknown else (),
        )
        row.cleanup_key = key
        return row.cleanup_snapshot

    scratch_resources = tuple(snapshot(row) for row in state.scratch.values())
    residual = tuple(
        sorted(row.path for row in state.scratch.values() if not row.removed)
    )
    unknown = (
        unknown
        or not state.ledger_complete
        or any(row.unknown for row in state.scratch.values())
    )
    return ConfinedTreeCleanupObservation(
        state.preparation_ref,
        state.request_ref,
        (*resources, *scratch_resources),
        residual,
        "unknown"
        if unknown
        else "incomplete"
        if residual
        else "not_attempted"
        if held
        else "completed",
        (*state.ledger.diagnostics, *state.diagnostics),
        not unknown,
    )


def _effects(state):
    preparation = state.preparation
    count = 0 if preparation is None else len(preparation.transition_order)
    cleanup = _cleanup(state)
    return ConfinedTreeEffectObservation(
        state.preparation_ref,
        state.request_ref,
        tuple(state.effects),
        state.completed_prefix,
        state.pending_ordinal
        if state.pending_ordinal is not None
        else state.next_ordinal
        if state.next_ordinal < count
        else None,
        state.phase,
        tuple(
            sorted(
                (path, pin)
                for path, pin in state.pins.items()
                if path not in state.unverified_paths
                and not (path in state.scratch and not state.scratch[path].removed)
            )
        ),
        cleanup.ledger_complete,
        cleanup.diagnostics,
        cleanup.residual_scratch,
    )


def _refusal(state, code):
    return RetainedPhysicalTreeProjectionRefusal(
        code,
        observation=_effects(state),
        cleanup=_cleanup(state),
        transition=state.last_transition,
    )


def _retire(state):
    if state.pid != os.getpid():
        return
    with state.lock:
        state.phase = "released"
        try:
            _cleanup_scratch(state)
            state.ledger.release_all()
        finally:
            state.root_fd = None
            state.request = None


def retain_confined_tree_projection(
    *,
    root: Path,
    request: ConfinedTreeProjectionRequest,
    confinement_profile: ConfinedMutationProfile = ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
) -> RetainedPhysicalTreeProjection:
    if (
        type(confinement_profile) is not ConfinedMutationProfile
        or confinement_profile is not ConfinedMutationProfile.DESCRIPTOR_WALK_V1
    ):
        raise RetainedPhysicalTreeProjectionRefusal(
            "tree_confinement_profile_unavailable"
        )
    if type(request) is not ConfinedTreeProjectionRequest:
        raise TypeError("original_tree_request_required")
    if type(root) is not type(Path()) or not root.is_absolute():
        raise RetainedPhysicalTreeProjectionRefusal("canonical_tree_root_required")
    # Reconstruct native values instead of retaining a caller-mutated DTO graph.
    request = ConfinedTreeProjectionRequest(
        request.request_ref,
        request.root_identity,
        tuple(
            ConfinedTreeFileTransition(
                row.path,
                row.kind,
                replace(row.before),
                row.content,
                row.content_digest,
                row.size_bytes,
                row.requested_mode,
            )
            for row in request.files
        ),
        tuple(
            ConfinedTreeAncestorTransition(
                row.path, row.intent, replace(row.before), row.requested_mode
            )
            for row in request.ancestors
        ),
        replace(request.limits),
    )
    ledger = _TreeLedger(request.limits, request.root_identity)
    state = _State(
        root,
        None,
        request,
        request.request_ref,
        "tree-preparation:" + uuid4().hex,
        ledger,
    )
    try:
        ledger.reserve(len(_wire(_request_descriptor(request))) + 4096)
        if root.resolve(strict=True) != root:
            raise RetainedPhysicalTreeProjectionRefusal("canonical_tree_root_required")
        state.root_fd = ledger.open(root, _DIRECTORY_FLAGS)
        _capture(state)
        _reserve_execution(state)
        state.phase = "prepared"
        _metadata_check(state)
        handle = object.__new__(RetainedPhysicalTreeProjection)
        _HANDLES[handle] = state
        finalize(handle, _retire, state)
        return handle
    except BaseException as error:
        _retire(state)
        raise _refusal(
            state, getattr(error, "code", "tree_preparation_unavailable")
        ) from error
    finally:
        request = None


__all__ = (
    "ConfinedTreeCapacityForecast",
    "ConfinedTreeCapacitySchedule",
    "ConfinedTreeEncodingBounds",
    "ConfinedTreePrefixCapacity",
    "RetainedPhysicalTreeProjection",
    "RetainedPhysicalTreeProjectionRefusal",
    "retain_confined_tree_projection",
)
