"""Original Protocol absent-to-published selection; never Issue or write authority.

Fixed optional FileSystem integration is lazy. SPEC owns semantic validation and
Issue owns effect authorization. This module neither parses nor publishes SPEC.
"""

from __future__ import annotations

import os
import threading
import unicodedata
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import NoReturn, Protocol, SupportsIndex, cast, final, override
from weakref import WeakKeyDictionary, finalize, ref

from aware_protocol_runtime import ProtocolContractError

from .specification_selection import (
    SpecificationSelectionError,
    SpecificationSourceSelection,
    _attach_original_postimage,  # pyright: ignore[reportPrivateUsage] -- same Protocol owner
    _identity,  # pyright: ignore[reportPrivateUsage] -- same Protocol owner
    _release_owned_selection,  # pyright: ignore[reportPrivateUsage] -- same Protocol owner
    _retained,  # pyright: ignore[reportPrivateUsage] -- same Protocol owner
    _SelectionResources,  # pyright: ignore[reportPrivateUsage] -- original same-owner cleanup ledger
    _walk,  # pyright: ignore[reportPrivateUsage] -- same Protocol owner
    admit_specification_selection,
    require_specification_selection,
)


class SpecificationDraftSelectionError(ProtocolContractError):
    code: str
    diagnostics: tuple[str, ...]

    def __init__(self, code: str, *, diagnostics: tuple[str, ...] = ()) -> None:
        self.code = code
        self.diagnostics = (code, *diagnostics)
        super().__init__(code)


class _Binding(Protocol):
    root_locator: str
    root_identity: tuple[int, int, int]
    parent_path: str
    parent_identity: tuple[int, int, int]
    namespace_identity: tuple[int, int]
    target_path: str


class _Plan(Protocol):
    @property
    def phase(self) -> str: ...


class _PhysicalOwner(Protocol):
    def require_retained_package_plan(
        self, value: object, *, input_claim: object = None
    ) -> _Plan: ...
    def observe_package_plan(
        self, value: object, *, input_claim: object = None
    ) -> _Binding: ...
    def require_retained_package_postimage(
        self, value: object, *, plan: object, input_claim: object = None
    ) -> object: ...
    def retain_package_postimage_read(
        self, value: object, *, input_claim: object = None
    ) -> object: ...
    def release_package_postimage_read(self, value: object) -> None: ...


class _PackageInput(Protocol):
    attempt_ref: str
    client_intent_id: str
    resource_state: str
    transfer_state: str
    binding: _Binding | None


class _CustodyOwner(_PhysicalOwner, Protocol):
    def reserve_package_input(
        self, plan: object, *, attempt_ref: str, client_intent_id: str
    ) -> object: ...
    def observe_package_input(self, value: object) -> _PackageInput: ...
    def require_package_input_claim(
        self, value: object, *, plan: object, receiver: object
    ) -> object: ...
    def release_package_input(self, value: object) -> _PackageInput: ...


def _owner() -> ModuleType:
    try:
        module = import_module("aware_file_system.retained_package")
        for name in (
            "require_retained_package_plan",
            "observe_package_plan",
            "require_retained_package_postimage",
            "retain_package_postimage_read",
            "require_package_postimage_read",
            "validate_package_postimage_read",
            "release_package_postimage_read",
        ):
            if not callable(cast(object, getattr(module, name))):
                raise TypeError(name)
        return module
    except (ImportError, AttributeError, TypeError) as error:
        raise SpecificationDraftSelectionError(
            "specification_draft_integration_unavailable"
        ) from error


@dataclass
class _State:
    selection: SpecificationSourceSelection
    selected_path: str
    target: str
    parent: str
    root_mode: int
    parent_mode: int
    root_locator: str
    manifest_locator: str
    manifest_sha256: str
    root_identity: tuple[int, int, int]
    parent_identity: tuple[int, int, int]
    namespace_identity: tuple[int, int]
    cleanup_resources: _SelectionResources = field(kw_only=True)
    pid: int = field(default_factory=os.getpid)
    phase: str = "absent"
    plan: object | None = None
    owner_module: ModuleType | None = None
    read_ref: ref[SpecificationSourceSelection] | None = None
    lock: threading.RLock = field(default_factory=threading.RLock)
    base_released: bool = False
    cleanup_attempted: bool = False
    cleanup_outcome: str = "not_attempted"
    cleanup_diagnostics: tuple[str, ...] = ()
    input_custody: _InputRecord | None = None


@dataclass(frozen=True, slots=True)
class SpecificationDraftInputObservation:
    """Detached historical custody, never freshness or a disposal grant."""

    attempt_ref: str
    client_intent_id: str
    resource_state: str
    transfer_state: str
    release_invocation: str
    owner_cleanup_attempted: bool | None
    owner_cleanup_outcome: str
    diagnostics: tuple[str, ...]
    root_locator: str | None
    manifest_locator: str | None
    manifest_sha256: str | None
    target_locator: str | None
    physical: _PackageInput | None


class SpecificationDraftInputCustodyRefusal(SpecificationDraftSelectionError):
    input_observation: SpecificationDraftInputObservation | None

    def __init__(
        self, code: str, *, input_observation: SpecificationDraftInputObservation | None
    ) -> None:
        self.input_observation = input_observation
        super().__init__(code)


@final
class SpecificationDraftInputReservation:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls) -> SpecificationDraftInputReservation:
        raise TypeError("use reserve_specification_draft_input")

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Original reservation cannot be subclassed")

    def __copy__(self) -> NoReturn:
        raise TypeError("Reservation cannot be copied")

    def __deepcopy__(self, memo: object) -> NoReturn:
        raise TypeError("Reservation cannot be copied")

    @override
    def __reduce_ex__(self, protocol: SupportsIndex) -> NoReturn:
        raise TypeError("Reservation cannot be serialized")

    @property
    def physical_reservation(self) -> object:
        entry, state = _input_entry(self)
        with state.lock:
            if entry.record.physical_reservation is None:
                raise _input_refusal("specification_draft_physical_unavailable", state)
            return entry.record.physical_reservation


@final
class SpecificationDraftInputClaim:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls) -> SpecificationDraftInputClaim:
        raise TypeError("use transfer_specification_draft_input")

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Original claim cannot be subclassed")

    def __copy__(self) -> NoReturn:
        raise TypeError("Claim cannot be copied")

    def __deepcopy__(self, memo: object) -> NoReturn:
        raise TypeError("Claim cannot be copied")

    @override
    def __reduce_ex__(self, protocol: SupportsIndex) -> NoReturn:
        raise TypeError("Claim cannot be serialized")


@dataclass
class _InputRecord:
    attempt_ref: str
    client_intent_id: str
    physical_plan: object
    resource_state: str = "reserved"
    transfer_state: str = "not_attempted"
    release_invocation: str = "not_invoked"
    receiver: object = None
    physical_reservation: object = None
    physical_claim: object = None
    physical_observation: _PackageInput | None = None
    physical_release_attempted: bool = False
    owner_module: ModuleType | None = None
    diagnostics: list[str] = field(default_factory=list)


@dataclass
class _InputEntry:
    target: SpecificationDraftTargetSelection
    record: _InputRecord
    role: str


_INPUTS: WeakKeyDictionary[object, _InputEntry] = WeakKeyDictionary()


_ISSUED: WeakKeyDictionary[SpecificationDraftTargetSelection, _State] = (
    WeakKeyDictionary()
)


def _cleanup(state: _State) -> None:
    if state.base_released:
        return
    state.base_released = True
    state.cleanup_attempted = True
    state.cleanup_outcome = "unknown"
    try:
        _release_owned_selection(state.selection)
    except BaseException as error:
        state.cleanup_outcome = "incomplete"
        state.cleanup_diagnostics = (
            f"draft_target_cleanup_failed:{type(error).__name__}",
            *state.cleanup_resources.cleanup_diagnostics,
        )
        raise
    # A returned call, missing registry entry, phase or descriptor count cannot
    # prove disposal. Only the retained ledger of these original resources can.
    resources = state.cleanup_resources
    if not resources.cleanup_attempted or resources.cleanup_outcome != "completed":
        state.cleanup_outcome = (
            "incomplete" if resources.cleanup_outcome == "incomplete" else "unknown"
        )
        state.cleanup_diagnostics = (
            "draft_target_cleanup_completion_unverified",
            *resources.cleanup_diagnostics,
        )
        raise SpecificationDraftSelectionError(
            "specification_draft_cleanup_completion_unverified",
            diagnostics=state.cleanup_diagnostics,
        )
    state.cleanup_outcome = "completed"


def _abandon(state: _State) -> None:
    with state.lock:
        state.phase = "released"
        _cleanup(state)


def _retire(state: _State, error: BaseException) -> NoReturn:
    state.phase = "retired"
    try:
        _cleanup(state)
    except BaseException as cleanup_error:  # noqa: BLE001 -- retain primary interruption/refusal
        diagnostic = f"draft_target_cleanup_failed:{type(cleanup_error).__name__}"
        error.add_note(diagnostic)
        if isinstance(error, SpecificationDraftSelectionError):
            error.diagnostics = (*error.diagnostics, diagnostic)
    if isinstance(error, SpecificationDraftSelectionError):
        raise error
    if not isinstance(error, Exception):
        raise error
    raise SpecificationDraftSelectionError(
        "specification_draft_currentness_failed",
        diagnostics=(
            f"owner_detail:{type(error).__name__}",
            *getattr(error, "__notes__", ()),
        ),
    ) from error


def _issued(target: object) -> _State:
    if type(target) is not SpecificationDraftTargetSelection:
        raise SpecificationDraftSelectionError("specification_draft_original_required")
    state = _ISSUED.get(target)
    if state is None:
        raise SpecificationDraftSelectionError("specification_draft_original_required")
    if state.pid != os.getpid():
        if state.input_custody is not None:
            raise _input_refusal("specification_draft_input_foreign_process")
        with state.lock:
            _retire(
                state,
                SpecificationDraftSelectionError("specification_draft_foreign_process"),
            )
    return state


def _input_entry(value: object) -> tuple[_InputEntry, _State]:
    if type(value) not in {
        SpecificationDraftInputReservation,
        SpecificationDraftInputClaim,
    }:
        raise _input_refusal("original_specification_draft_input_required")
    entry = _INPUTS.get(value)
    state = None if entry is None else _ISSUED.get(entry.target)
    if entry is None or state is None or state.pid != os.getpid():
        raise _input_refusal("original_local_specification_draft_input_required")
    return entry, state


def _guard_input(state: _State, claim: object) -> None:
    record = state.input_custody
    if record is None:
        if claim is not None:
            raise _input_refusal("unexpected_specification_draft_input_claim")
        return
    entry = _INPUTS.get(claim) if type(claim) is SpecificationDraftInputClaim else None
    if (
        entry is None
        or entry.role != "claim"
        or entry.record is not record
        or _ISSUED.get(entry.target) is not state
        or record.transfer_state != "completed"
    ):
        raise _input_refusal("specification_draft_input_claim_required", state)


def _custody_owner() -> ModuleType:
    module = _owner()
    try:
        for name in (
            "reserve_package_input",
            "observe_package_input",
            "require_package_input_claim",
            "release_package_input",
        ):
            if not callable(cast(object, getattr(module, name))):
                raise TypeError(name)
    except (AttributeError, TypeError) as error:
        raise SpecificationDraftSelectionError(
            "specification_draft_custody_integration_unavailable"
        ) from error
    return module


def _physical_observation(record: _InputRecord) -> _PackageInput | None:
    if record.owner_module is not None and record.physical_reservation is not None:
        try:
            owner = cast(_CustodyOwner, cast(object, record.owner_module))
            record.physical_observation = owner.observe_package_input(
                record.physical_reservation
            )
        except BaseException as error:  # noqa: BLE001 -- retain known historical evidence
            diagnostic = "physical_input_observation:" + type(error).__name__
            if diagnostic not in record.diagnostics:
                record.diagnostics.append(diagnostic)
    return record.physical_observation


def _retain_physical_error(record: _InputRecord, error: BaseException) -> None:
    observed = getattr(error, "input_observation", None)
    if record.owner_module is not None and type(observed) is getattr(
        record.owner_module, "PackageInputObservation", None
    ):
        original = cast(_PackageInput, observed)
        if (original.attempt_ref, original.client_intent_id) == (
            record.attempt_ref,
            record.client_intent_id,
        ):
            record.physical_observation = original


def _input_observation(
    state: _State, record: _InputRecord
) -> SpecificationDraftInputObservation:
    physical = _physical_observation(record)
    # Preserve the append-only ordering consumed by Issue/SPEC even if a later
    # physical observation fails after Protocol's terminal cleanup was observed.
    for diagnostic in state.cleanup_diagnostics:
        if diagnostic not in record.diagnostics:
            record.diagnostics.append(diagnostic)
    return SpecificationDraftInputObservation(
        record.attempt_ref,
        record.client_intent_id,
        record.resource_state,
        record.transfer_state,
        record.release_invocation,
        state.cleanup_attempted,
        state.cleanup_outcome,
        tuple(record.diagnostics),
        state.root_locator,
        state.manifest_locator,
        state.manifest_sha256,
        state.target,
        physical,
    )


def _input_refusal(
    code: str, state: _State | None = None
) -> SpecificationDraftInputCustodyRefusal:
    observation = None
    if state is not None and state.input_custody is not None:
        try:
            observation = _input_observation(state, state.input_custody)
        except BaseException as error:  # noqa: BLE001 -- missing evidence is unknown, never authority
            state.input_custody.diagnostics.append(
                "input_refusal_observation:" + type(error).__name__
            )
    return SpecificationDraftInputCustodyRefusal(code, input_observation=observation)


def _release_input_state(state: _State, record: _InputRecord) -> None:
    if record.release_invocation != "not_invoked":
        return
    record.release_invocation = "invoked"
    record.resource_state = "released"
    failed = False
    # A joint reservation owns the child only until FileSystem transfers it.
    # A Protocol claim never disposes Issue's independently owned physical claim.
    if record.transfer_state != "completed" and record.physical_reservation is not None:
        physical = _physical_observation(record)
        if (
            physical is None or physical.transfer_state != "completed"
        ) and not record.physical_release_attempted:
            record.physical_release_attempted = True
            try:
                # The original owner arbitrates this capability atomically;
                # unavailable or stale observations are never disposal permission.
                owner = cast(_CustodyOwner, cast(object, record.owner_module))
                record.physical_observation = owner.release_package_input(
                    record.physical_reservation
                )
            except BaseException as error:  # noqa: BLE001 -- attempt target cleanup independently
                failed = True
                _retain_physical_error(record, error)
                record.diagnostics.append(
                    "physical_input_release:" + type(error).__name__
                )
    try:
        state.phase = "released"
        _cleanup(state)
    except BaseException as error:  # noqa: BLE001 -- preserve interruption and terminality
        failed = True
        record.diagnostics.append("protocol_input_release:" + type(error).__name__)
    record.release_invocation = "raised" if failed else "returned"


def _abandon_input(entry: _InputEntry) -> None:
    state = _ISSUED.get(entry.target)
    if state is None or state.pid != os.getpid():
        return
    with state.lock:
        if entry.role == "reservation" and entry.record.transfer_state == "completed":
            return
        _release_input_state(state, entry.record)


def _correlation(value: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or unicodedata.normalize("NFC", value) != value
        or any(ord(c) < 32 or 0x7F <= ord(c) <= 0x9F for c in value)
        or len(value.encode("utf-8")) > 1024
    ):
        raise ValueError("Bounded exact custody correlation required")
    return value


def reserve_specification_draft_input(
    target: object, *, physical_plan: object, attempt_ref: str, client_intent_id: str
) -> SpecificationDraftInputReservation:
    attempt_ref, client_intent_id = (
        _correlation(attempt_ref),
        _correlation(client_intent_id),
    )
    state = (
        _ISSUED.get(target)
        if type(target) is SpecificationDraftTargetSelection
        else None
    )
    if state is None or state.pid != os.getpid():
        raise _input_refusal("original_local_specification_draft_input_required")
    with state.lock:
        if state.input_custody is not None:
            raise _input_refusal("specification_draft_input_already_owned", state)
        if state.phase not in {"absent", "retired", "released"}:
            raise _input_refusal("specification_draft_input_already_spent")
        record = _InputRecord(attempt_ref, client_intent_id, physical_plan)
        state.input_custody = record
        try:
            module = _custody_owner()
            record.owner_module = module
            owner = cast(_CustodyOwner, cast(object, module))
            record.physical_reservation = owner.reserve_package_input(
                physical_plan,
                attempt_ref=attempt_ref,
                client_intent_id=client_intent_id,
            )
            physical = _physical_observation(record)
            binding = None if physical is None else physical.binding
            if (
                physical is None
                or binding is None
                or physical.attempt_ref != attempt_ref
                or physical.client_intent_id != client_intent_id
                or binding.root_locator != state.root_locator
                or binding.target_path != state.target
                or binding.parent_path != state.parent
                or binding.root_identity != state.root_identity
                or binding.parent_identity != state.parent_identity
                or binding.namespace_identity != state.namespace_identity
            ):
                raise SpecificationDraftSelectionError(
                    "specification_draft_input_plan_mismatch"
                )
            handle = object.__new__(SpecificationDraftInputReservation)
            entry = _InputEntry(
                cast(SpecificationDraftTargetSelection, target), record, "reservation"
            )
            _INPUTS[handle] = entry
            _ = finalize(handle, _abandon_input, entry)
            return handle
        except BaseException as error:
            record.diagnostics.append("input_issuance:" + type(error).__name__)
            # Lower issuance may already have disposed its newly acquired child.
            _retain_physical_error(record, error)
            _release_input_state(state, record)
            raise _input_refusal(
                "specification_draft_input_reservation_failed", state
            ) from error


def observe_specification_draft_input(
    value: object,
) -> SpecificationDraftInputObservation:
    entry, state = _input_entry(value)
    with state.lock:
        try:
            return _input_observation(state, entry.record)
        except BaseException as error:
            raise SpecificationDraftInputCustodyRefusal(
                "specification_draft_input_observation_unavailable",
                input_observation=None,
            ) from error


def transfer_specification_draft_input(
    reservation: object, *, physical_claim: object, receiver: object
) -> SpecificationDraftInputClaim:
    entry, state = _input_entry(reservation)
    if (
        type(reservation) is not SpecificationDraftInputReservation
        or entry.role != "reservation"
    ):
        raise _input_refusal("original_specification_draft_reservation_required")
    if receiver is None:
        raise ValueError("Opaque receiver identity required")
    with state.lock:
        record = entry.record
        if (
            record.resource_state != "reserved"
            or record.transfer_state != "not_attempted"
        ):
            raise _input_refusal("specification_draft_input_transfer_replay", state)
        if state.phase != "absent" or state.base_released:
            raise _input_refusal("specification_draft_input_cleanup_only", state)
        if _custody_owner() is not record.owner_module:
            raise _input_refusal("specification_draft_input_owner_changed", state)
        owner = cast(_CustodyOwner, cast(object, record.owner_module))
        # Mismatch is checked before spending/cleanup; the original remains usable.
        try:
            verified = owner.require_package_input_claim(
                physical_claim, plan=record.physical_plan, receiver=receiver
            )
            physical = owner.observe_package_input(physical_claim)
        except BaseException as error:
            raise _input_refusal(
                "specification_draft_input_physical_claim_mismatch", state
            ) from error
        if verified is not physical_claim:
            raise _input_refusal(
                "specification_draft_input_physical_claim_mismatch", state
            )
        if (physical.attempt_ref, physical.client_intent_id) != (
            record.attempt_ref,
            record.client_intent_id,
        ):
            raise _input_refusal(
                "specification_draft_input_correlation_mismatch", state
            )
        record.transfer_state = "attempted"
        try:
            handle = object.__new__(SpecificationDraftInputClaim)
            claimed = _InputEntry(entry.target, record, "claim")
            _INPUTS[handle] = claimed
            _ = finalize(handle, _abandon_input, claimed)
            record.receiver = receiver
            record.physical_claim = physical_claim
            record.transfer_state = "completed"
            record.resource_state = "transferred"
            return handle
        except BaseException as error:
            record.diagnostics.append("input_transfer:" + type(error).__name__)
            _release_input_state(state, record)
            raise _input_refusal(
                "specification_draft_input_transfer_failed", state
            ) from error


def release_specification_draft_input(
    value: object,
) -> SpecificationDraftInputObservation:
    entry, state = _input_entry(value)
    with state.lock:
        if entry.role == "reservation" and entry.record.transfer_state == "completed":
            raise _input_refusal("specification_draft_input_cleanup_transferred", state)
        _release_input_state(state, entry.record)
        try:
            observation = _input_observation(state, entry.record)
        except BaseException as error:
            raise SpecificationDraftInputCustodyRefusal(
                "specification_draft_input_release_observation_unavailable",
                input_observation=None,
            ) from error
        if entry.record.release_invocation == "raised":
            raise SpecificationDraftInputCustodyRefusal(
                "specification_draft_input_release_incomplete",
                input_observation=observation,
            )
        return observation


def _absence(state: _State) -> None:
    retained = _retained(state.selection)
    parent, _ = _walk(
        retained.repository_fd, tuple(state.parent.split("/")), missing_allowed=False
    )
    assert parent is not None
    try:
        if (
            os.fstat(retained.repository_fd).st_mode != state.root_mode
            or os.fstat(parent).st_mode != state.parent_mode
        ):
            raise SpecificationDraftSelectionError(
                "specification_draft_topology_changed"
            )
        try:
            _ = os.stat(
                state.target.split("/")[-1], dir_fd=parent, follow_symlinks=False
            )
        except FileNotFoundError:
            return
        raise SpecificationDraftSelectionError("specification_draft_target_exists")
    finally:
        os.close(parent)


def _physical(state: _State) -> _Plan:
    module = _owner()
    if module is not state.owner_module or state.plan is None:
        raise SpecificationDraftSelectionError("specification_draft_owner_changed")
    plan = cast(_PhysicalOwner, cast(object, module)).require_retained_package_plan(
        state.plan,
        **(
            {"input_claim": state.input_custody.physical_claim}
            if state.input_custody
            else {}
        ),
    )
    if plan is not state.plan:
        raise SpecificationDraftSelectionError(
            "specification_draft_original_plan_required"
        )
    return plan


def _correlated(state: _State) -> SpecificationSourceSelection:
    selection = state.read_ref() if state.read_ref is not None else None
    if selection is None:
        raise SpecificationDraftSelectionError(
            "specification_draft_correlated_read_required"
        )
    return require_specification_selection(selection)


def _check(state: _State) -> None:
    if state.phase in {"released", "retired"}:
        raise SpecificationDraftSelectionError("specification_draft_terminal")
    try:
        if state.phase in {"read_issued", "consumed"}:
            _ = _correlated(state)
            return  # Never revalidate a released write plan in the consumed phase.
        state.selection.revalidate()
        if state.phase == "absent":
            _absence(state)
        else:
            plan = _physical(state)  # Owner validates absence or original postimage.
            if state.phase == "bound" or plan.phase in {"planned", "staging", "staged"}:
                _absence(state)
            elif state.phase != "publication_spent" or plan.phase not in {
                "published",
                "consumed",
            }:
                raise SpecificationDraftSelectionError(
                    "specification_draft_publication_unproven"
                )
        state.selection.revalidate()
    except BaseException as error:  # noqa: BLE001 -- freshness interruptions retire authority
        _retire(state, error)


@final
class SpecificationDraftTargetSelection:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls) -> SpecificationDraftTargetSelection:
        raise TypeError("use admit_specification_draft_target")

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Draft target cannot be subclassed")

    @override
    def __reduce_ex__(self, protocol: SupportsIndex) -> NoReturn:
        raise TypeError("Draft target cannot be copied or serialized")

    @property
    def manifest_sha256(self) -> str:
        return _issued(self).selection.manifest_sha256

    @property
    def manifest_locator(self) -> str:
        """Original repository-relative Protocol source, never a write permit.

        Obtain this guarded coordinate before constructing the exact Issue
        request. Detached text may survive cleanup but cannot renew a holder.
        """
        state = _issued(self)
        with state.lock:
            _guard_input(state, None)
            _check(state)
            return _retained(state.selection).manifest_relative

    @property
    def selected_manifest_path(self) -> str:
        return _issued(self).selected_path

    @property
    def target_locator(self) -> str:
        return _issued(self).target

    @property
    def parent_locator(self) -> str:
        return _issued(self).parent

    @property
    def phase(self) -> str:
        return _issued(self).phase

    def revalidate(self, *, input_claim: object = None) -> None:
        state = _issued(self)
        with state.lock:
            _guard_input(state, input_claim)
            _check(state)


def admit_specification_draft_target(
    *,
    repository_root: Path,
    manifest_path: Path,
    selected_manifest_path: str,
    expected_manifest_sha256: str,
) -> SpecificationDraftTargetSelection:
    selection = None
    try:
        result = admit_specification_selection(
            repository_root=repository_root,
            manifest_path=manifest_path,
            selected_manifest_paths=(selected_manifest_path,),
            expected_manifest_sha256=expected_manifest_sha256,
        )
        selection = result.selection
        if selection is None:
            raise SpecificationDraftSelectionError(
                "specification_draft_admission_unavailable",
                diagnostics=result.admission.diagnostics,
            )
        # Missing digests are not accepted through the ordinary optional entrance.
        if (
            type(expected_manifest_sha256) is not str
            or selection.manifest_sha256 != expected_manifest_sha256
        ):
            raise SpecificationDraftSelectionError(
                "specification_draft_manifest_mismatch"
            )
        retained = _retained(selection)
        target = retained.roots[0]
        parent = target.rsplit("/", 1)[0]
        descriptor, _ = _walk(
            retained.repository_fd, tuple(parent.split("/")), missing_allowed=False
        )
        assert descriptor is not None
        try:
            state = _State(
                selection,
                selected_manifest_path,
                target,
                parent,
                os.fstat(retained.repository_fd).st_mode,
                os.fstat(descriptor).st_mode,
                str(retained.repository_root),
                retained.manifest_relative,
                retained.manifest_sha256,
                (
                    *retained.repository_identity[:2],
                    os.fstat(retained.repository_fd).st_mode,
                ),
                (*_identity(descriptor)[:2], os.fstat(descriptor).st_mode),
                retained.namespace[:2],
                cleanup_resources=retained.resources,
            )
        finally:
            os.close(descriptor)
        _check(state)
        handle = object.__new__(SpecificationDraftTargetSelection)
        _ISSUED[handle] = state
        _ = finalize(handle, _abandon, state)
        selection = None  # Original handle now owns the base selection.
        return handle
    except BaseException as error:
        if selection is not None:
            try:
                _release_owned_selection(selection)
            except BaseException as cleanup_error:  # noqa: BLE001 -- retain primary failure
                error.add_note(
                    f"draft_admission_cleanup_failed:{type(cleanup_error).__name__}"
                )
        if isinstance(error, SpecificationDraftSelectionError):
            raise
        if not isinstance(error, Exception):
            raise
        raise SpecificationDraftSelectionError(
            "specification_draft_admission_failed",
            diagnostics=(
                f"source_detail:{type(error).__name__}",
                *(
                    error.diagnostics
                    if isinstance(error, SpecificationSelectionError)
                    else ()
                ),
                *getattr(error, "__notes__", ()),
            ),
        ) from error


def require_specification_draft_target(
    target: object,
    *,
    input_claim: object = None,
) -> SpecificationDraftTargetSelection:
    state = _issued(target)
    with state.lock:
        _guard_input(state, input_claim)
        _check(state)
    return cast(SpecificationDraftTargetSelection, target)


def bind_specification_draft_physical_plan(
    target: object,
    *,
    physical_plan: object,
    input_claim: object = None,
    physical_input_claim: object = None,
) -> None:
    state = _issued(target)
    with state.lock:
        _guard_input(state, input_claim)
        if state.input_custody is not None and (
            physical_plan is not state.input_custody.physical_plan
            or physical_input_claim is not state.input_custody.physical_claim
        ):
            raise _input_refusal(
                "specification_draft_input_physical_claim_mismatch", state
            )
        try:
            _check(state)
            if state.phase != "absent":
                raise SpecificationDraftSelectionError(
                    "specification_draft_binding_replay"
                )
            module = _owner()
            owner = cast(_PhysicalOwner, cast(object, module))
            kwargs = (
                {"input_claim": physical_input_claim}
                if state.input_custody or physical_input_claim is not None
                else {}
            )
            plan = owner.require_retained_package_plan(physical_plan, **kwargs)
            binding = owner.observe_package_plan(plan, **kwargs)
            retained = _retained(state.selection)
            descriptor, _ = _walk(
                retained.repository_fd,
                tuple(state.parent.split("/")),
                missing_allowed=False,
            )
            assert descriptor is not None
            try:
                parent_identity = _identity(descriptor)
            finally:
                os.close(descriptor)
            if (
                plan is not physical_plan
                or plan.phase != "planned"
                or binding.root_locator != str(retained.repository_root)
                or binding.target_path != state.target
                or binding.parent_path != state.parent
                or binding.root_identity
                != (*retained.repository_identity[:2], state.root_mode)
                or binding.parent_identity != (*parent_identity[:2], state.parent_mode)
                or binding.namespace_identity != retained.namespace[:2]
            ):
                raise SpecificationDraftSelectionError(
                    "specification_draft_plan_mismatch"
                )
            state.plan, state.owner_module, state.phase = physical_plan, module, "bound"
            _check(state)
        except BaseException as error:  # noqa: BLE001 -- interruptions retire binding
            _retire(state, error)


def spend_specification_draft_publication(
    target: object, *, input_claim: object = None
) -> None:
    state = _issued(target)
    with state.lock:
        _guard_input(state, input_claim)
        try:
            _check(state)
            if state.phase != "bound" or _physical(state).phase != "staged":
                raise SpecificationDraftSelectionError(
                    "specification_draft_spend_refused"
                )
            state.phase = "publication_spent"
            _check(state)
        except BaseException as error:  # noqa: BLE001 -- spending is terminal on interruption
            _retire(state, error)


def admit_specification_draft_published_read(
    target: object,
    *,
    physical_postimage: object,
    input_claim: object = None,
) -> SpecificationSourceSelection:
    state = _issued(target)
    with state.lock:
        _guard_input(state, input_claim)
        reader = None
        selection = None
        try:
            _check(state)
            if state.phase != "publication_spent":
                raise SpecificationDraftSelectionError(
                    "specification_draft_read_replay"
                )
            owner = cast(_PhysicalOwner, cast(object, state.owner_module))
            kwargs = (
                {"input_claim": state.input_custody.physical_claim}
                if state.input_custody
                else {}
            )
            _ = owner.require_retained_package_postimage(
                physical_postimage, plan=state.plan, **kwargs
            )
            reader = owner.retain_package_postimage_read(physical_postimage, **kwargs)
            retained = _retained(state.selection)
            result = admit_specification_selection(
                repository_root=retained.repository_root,
                manifest_path=retained.manifest_path,
                selected_manifest_paths=(state.selected_path,),
                expected_manifest_sha256=retained.manifest_sha256,
            )
            selection = result.selection
            if selection is None:
                raise SpecificationDraftSelectionError(
                    "specification_draft_read_unavailable"
                )
            _attach_original_postimage(selection, reader=reader, plan=state.plan)
            reader = None  # New selection owns reader and descriptor cleanup.
            _check(state)
            state.read_ref = ref(selection)
            state.phase = "read_issued"
            _check(state)
            return selection
        except BaseException as error:  # noqa: BLE001 -- clean partial original read issuance
            if selection is not None:
                try:
                    _release_owned_selection(selection)
                except BaseException as cleanup_error:  # noqa: BLE001 -- retain original refusal
                    error.add_note(
                        f"draft_read_cleanup_failed:{type(cleanup_error).__name__}"
                    )
            if reader is not None and state.owner_module is not None:
                try:
                    cast(
                        _PhysicalOwner, cast(object, state.owner_module)
                    ).release_package_postimage_read(reader)
                except BaseException as cleanup_error:  # noqa: BLE001 -- attempt every original cleanup
                    error.add_note(
                        f"postimage_cleanup_failed:{type(cleanup_error).__name__}"
                    )
            _retire(state, error)


def finish_specification_draft_target(
    target: object,
    *,
    read_selection: object,
    input_claim: object = None,
) -> None:
    state = _issued(target)
    with state.lock:
        _guard_input(state, input_claim)
        try:
            _check(state)
            if state.phase != "read_issued" or _correlated(state) is not read_selection:
                raise SpecificationDraftSelectionError(
                    "specification_draft_finish_refused"
                )
            state.phase = "consumed"
            _check(state)
        except BaseException as error:  # noqa: BLE001 -- return-time interruption is terminal
            _retire(state, error)


def release_specification_draft_target(
    target: object, *, input_claim: object = None
) -> None:
    state = _issued(target)
    with state.lock:
        _guard_input(state, input_claim)
        if state.input_custody is not None:
            _ = release_specification_draft_input(input_claim)
            return
        state.phase = "released"
        _cleanup(state)  # Does not close consumer-owned independent readers/plans.
