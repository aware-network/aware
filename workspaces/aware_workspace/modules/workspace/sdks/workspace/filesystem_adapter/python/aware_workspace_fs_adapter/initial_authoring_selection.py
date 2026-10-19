"""Bounded selection in the ORIGINAL private initial-authoring retention.

No arbitrary path, new store, creation, live token, source-currentness claim or
missing-record retry permission. Original attempt recovery verifies provenance.
"""

from __future__ import annotations

import os

from aware_workspace_sdk.initial_authoring.goal_publication import (
    InitialGoalPublicationRequest,
)
from aware_workspace_sdk.initial_authoring.membership import InitialMembershipRequest
from aware_workspace_sdk.initial_authoring.values import (
    InitialConfigurationRequest,
    InitialProjectRequest,
    _canonical,
)

from .initial_authoring import (
    _DIR_FLAGS,
    _DIRECTORY,
    _directory_current,
    _identity,
    _private,
    _read_record,
    _root_and_metadata,
    configuration_attempt,
    observe,
)


def observe_initial_authoring_request(port, kind, *, execution_id):
    if type(kind) is not str or kind not in {
        "configuration",
        "project",
        "goal",
        "membership",
    }:
        raise ValueError("initial_retained_request_kind_unsupported")
    evidence = observe(port, _attempt=True)
    if evidence.execution_id != execution_id:
        raise ValueError("initial_retained_request_execution_mismatch")
    selected_type = {
        "configuration": InitialConfigurationRequest,
        "project": InitialProjectRequest,
        "goal": InitialGoalPublicationRequest,
        "membership": InitialMembershipRequest,
    }[kind]
    with _root_and_metadata(port) as (_, metadata_fd, _, _):
        directory = os.open(_DIRECTORY, _DIR_FLAGS, dir_fd=metadata_fd)
        retained = None
        try:
            _private(os.fstat(directory), 0o700)
            names = set(os.listdir(directory))
            if kind not in names:
                # Absence is a historical observation, NEVER new permission.
                successors = {
                    "configuration": {"project", "goal", "membership"},
                    "project": {"goal", "membership"},
                    "goal": {"membership"},
                    "membership": set(),
                }[kind]
                if names & successors:
                    raise ValueError("initial_retained_request_predecessor_missing")
                _directory_current(metadata_fd, directory)
                if kind in os.listdir(directory):
                    raise ValueError("initial_retained_request_changed")
                return {
                    "kind": kind,
                    "state": "absent",
                    "request": None,
                    "recovery": None,
                    "authorizes_redispatch": False,
                }
            retained = os.open(kind, _DIR_FLAGS, dir_fd=directory)
            _private(os.fstat(retained), 0o700)
            before = _read_record(retained, "admission.json")
            if type(before) is not dict or "request" not in before:
                raise ValueError("initial_retained_request_record_invalid")
            request = selected_type.from_wire(before["request"])
            source = (
                request.source
                if not isinstance(request, InitialConfigurationRequest)
                else request.to_wire()["configuration"]
            )
            if (
                type(source) is not dict
                or source["repository_root"] != str(port._root)
                or request.execution_id != execution_id
                or request.enrollment_ref != evidence.enrollment_ref
            ):
                raise ValueError("initial_retained_request_binding_mismatch")
            # Selection never trusts the candidate request as authority. The
            # fixed original entrance independently resolves retention, verifies
            # the exact profile/enrollment/source/commit, and confirms durability.
            with configuration_attempt(
                port,
                request,
                _project=kind == "project",
                _goal=kind == "goal",
                _membership=kind == "membership",
            ) as attempt:
                if _canonical(attempt.record) != _canonical(before):
                    raise ValueError("initial_retained_request_changed")
                recovered = attempt.recover()
            terminal_enrollment = observe(port, _attempt=True)
            _private(os.fstat(retained), 0o700)
            if (
                _canonical(_read_record(retained, "admission.json"))
                != _canonical(before)
                or _identity(os.stat(kind, dir_fd=directory, follow_symlinks=False))
                != _identity(os.fstat(retained))
                or terminal_enrollment != evidence
            ):
                raise ValueError("initial_retained_request_changed")
            _directory_current(metadata_fd, directory)
            # Detached typed request and historical original result only. No
            # live plan/admission or caller-supplied verification is returned.
            return {
                "kind": kind,
                "state": "retained",
                "request": request,
                "recovery": recovered,
                "authorizes_redispatch": False,
            }
        finally:
            if retained is not None:
                os.close(retained)
            os.close(directory)
