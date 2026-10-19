"""Original bootstrap handles; no decoded or caller-built authority."""

from __future__ import annotations

import importlib
import os
import threading
from weakref import WeakKeyDictionary

_ENROLLMENTS = WeakKeyDictionary()
_CLAIMS = WeakKeyDictionary()
_CLAIM_LOCK = threading.Lock()
_STATE_TYPES = set()
_CONFIGURATION_STATES = WeakKeyDictionary()
_CONFIGURATION_TYPES = set()
_RESERVATIONS = WeakKeyDictionary()
_PROJECT_SOURCES = WeakKeyDictionary()
_PROJECT_SOURCE_BINDINGS = WeakKeyDictionary()


class InitialAuthoringEnrollment:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable] -- Python owns the weakref slot

    def __new__(cls):
        raise TypeError("original_workspace_initial_enrollment_required")

    def __copy__(self):
        raise TypeError("initial_enrollment_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("initial_enrollment_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("initial_enrollment_not_serializable")

    def observe(self):
        state = (
            _ENROLLMENTS.get(self) if type(self) is InitialAuthoringEnrollment else None
        )
        if state is None:
            raise ValueError("original_workspace_initial_enrollment_required")
        return state.observe()


class _EnrollmentClaim(InitialAuthoringEnrollment):
    __slots__ = ()


class InitialConfigurationPlan(InitialAuthoringEnrollment):
    __slots__ = ()

    @property
    def request(self):
        from .values import InitialConfigurationRequest

        state = (
            _CONFIGURATION_STATES.get(self)
            if type(self) is InitialConfigurationPlan
            else None
        )
        if state is None:
            raise ValueError("original_initial_configuration_plan_required")
        state.owner._current()
        return InitialConfigurationRequest.from_wire(state.request.to_wire())


class InitialConfigurationAdmission(InitialAuthoringEnrollment):
    __slots__ = ()


class InitialProjectPlan(InitialAuthoringEnrollment):
    __slots__ = ()

    @property
    def request(self):
        from .values import InitialProjectRequest

        state = (
            _CONFIGURATION_STATES.get(self)
            if type(self) is InitialProjectPlan
            else None
        )
        if state is None:
            raise ValueError("original_initial_project_plan_required")
        state.validate()
        return InitialProjectRequest.from_wire(state.request.to_wire())


class InitialProjectAdmission(InitialAuthoringEnrollment):
    __slots__ = ()


class InitialProjectSource(InitialAuthoringEnrollment):
    """Original Workspace exact-byte context, not a Project semantic verdict."""

    __slots__ = ()


def _issue_initial_project_source(owner, state):
    runtime = importlib.import_module("aware_workspace_runtime.initial_authoring")

    if (
        not _selected_owner(owner)
        or type(state) is not runtime.InitialProjectSourceState
        or state.owner is not owner
    ):
        raise ValueError("original_initial_project_source_required")
    handle = object.__new__(InitialProjectSource)
    _PROJECT_SOURCES[handle] = state
    _PROJECT_SOURCE_BINDINGS[handle] = (
        state.workspace,
        state.capability,
        state.protocol_plan,
        state.configuration_key,
        state.pid,
        state.sealed,
    )
    state.observe(owner._physical, current=True)
    return handle


class _ConfigurationReservation(InitialAuthoringEnrollment):
    __slots__ = ()


def _issue_configuration_reservation(owner, state):
    if (
        not _selected_owner(owner)
        or not any(state is item for item in _CONFIGURATION_STATES.values())
        or state.owner is not owner
        or state.phase != "reserving"
    ):
        raise ValueError("original_configuration_reservation_required")
    state.validate()
    claim = object.__new__(_ConfigurationReservation)
    with _CLAIM_LOCK:
        _RESERVATIONS[claim] = (state, os.getpid())
    return claim


def _spend_configuration_reservation(physical, claim):
    with _CLAIM_LOCK:
        value = (
            _RESERVATIONS.pop(claim, None)
            if type(claim) is _ConfigurationReservation
            else None
        )
    if value is None:
        raise ValueError("original_configuration_reservation_claim_required")
    state, pid = value
    state.validate()
    if (
        pid != os.getpid()
        or state.owner._physical is not physical
        or state.phase != "reserving"
    ):
        raise ValueError("configuration_reservation_binding_mismatch")
    return state.request, state.workspace_plan.binding


def _retire_configuration_reservation(claim):
    with _CLAIM_LOCK:
        _RESERVATIONS.pop(claim, None)


def _configuration_state(owner, handle, kind):
    owner._current()
    state = _CONFIGURATION_STATES.get(handle) if type(handle) is kind else None
    if state is None or state.owner is not owner:
        raise ValueError("original_initial_configuration_handle_required")
    state.validate()
    return state


def _issue_configuration_handle(owner, state, kind):
    from .values import InitialProjectRequest

    if (
        not _selected_owner(owner)
        or not any(type(state) is selected for selected in _CONFIGURATION_TYPES)
        or state.owner is not owner
        or kind
        not in (
            InitialConfigurationPlan,
            InitialConfigurationAdmission,
            InitialProjectPlan,
            InitialProjectAdmission,
        )
        or (
            (kind in (InitialProjectPlan, InitialProjectAdmission))
            != (type(state.request) is InitialProjectRequest)
        )
    ):
        raise ValueError("original_initial_configuration_state_required")
    handle = object.__new__(kind)
    _CONFIGURATION_STATES[handle] = state
    return handle


def _issue_enrollment_claim(owner, preparation_client):
    from aware_workspace_sdk.repository_preparation.authority import (
        _consume_fresh_root_witness,
    )

    if not _selected_owner(owner):
        raise ValueError("original_selected_workspace_publisher_required")
    owner._current()
    witness = _consume_fresh_root_witness(
        preparation_client, owner._execution, str(owner._physical._root)
    )
    claim = object.__new__(_EnrollmentClaim)
    with _CLAIM_LOCK:
        _CLAIMS[claim] = (owner, witness, os.getpid(), owner._execution)
    return claim


def _spend_enrollment_claim(physical, claim):
    with _CLAIM_LOCK:
        state = _CLAIMS.pop(claim, None) if type(claim) is _EnrollmentClaim else None
    if state is None:
        raise ValueError("original_initial_enrollment_claim_required")
    owner, witness, pid, execution = state
    owner._current()
    if (
        owner._physical is not physical
        or pid != os.getpid()
        or owner._execution != execution
    ):
        raise ValueError("initial_enrollment_claim_binding_mismatch")
    return witness, execution, owner._provider_ref, owner._generation


def _retire_enrollment_claim(claim):
    with _CLAIM_LOCK:
        _CLAIMS.pop(claim, None)


def _issue_initial_enrollment(owner, state):
    if (
        not _selected_owner(owner)
        or type(state) not in _STATE_TYPES
        or state._owner is not owner
    ):
        raise TypeError("original_workspace_publisher_required")
    handle = object.__new__(InitialAuthoringEnrollment)
    _ENROLLMENTS[handle] = state
    return handle


def _selected_owner(owner):
    # Explicit original-owner selection, as on preparation's SDK port. Keep
    # the provider dependency lazy and avoid a SDK/runtime import cycle.
    selected = importlib.import_module(
        "aware_workspace_sdk.repository_publication.authority"
    )
    runtime = importlib.import_module("aware_workspace_runtime.repository_publication")
    return type(owner) is runtime.WorkspaceRepositoryPublicationRuntime and any(
        owner is provider for provider in selected._CLIENT_PROVIDERS.values()
    )
