"""Original-provider read-only intake; no domain decisions or effect admission."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from aware_workspace_sdk.initial_authoring.values import (
    InitialProjectRequest,
    _canonical,
)


@dataclass
class InitialGoalSourceState:
    owner: Any
    project_request: InitialProjectRequest
    capability: object
    target_path: str
    request_wire: bytes
    sealed: bytes
    pid: int
    provider_ref: str
    provider_generation: str

    def pins(self):
        return (
            self.owner,
            self.project_request,
            self.capability,
            self.target_path,
            self.request_wire,
            self.sealed,
            self.pid,
            self.provider_ref,
            self.provider_generation,
        )

    def observe(self, *, current):
        self.owner._current()
        if (
            self.pid != os.getpid()
            or self.provider_ref != self.owner._provider_ref
            or self.provider_generation != self.owner._generation
            or _canonical(self.project_request.to_wire()) != self.request_wire
        ):
            raise ValueError("initial_goal_context_not_issued_or_mutated")
        original = json.loads(self.sealed)
        if original["execution_id"] != self.owner._execution:
            raise ValueError("initial_goal_context_execution_mismatch")
        if current:
            observed = self.owner._physical.observe_initial_goal_source(
                self.project_request, self.capability, self.target_path
            )
            if _canonical(observed) != self.sealed:
                raise ValueError("initial_goal_source_changed")
        self.owner._current()
        return json.loads(self.sealed)


def observe_initial_goal_source(owner, project_request, capability, target_path):
    from aware_workspace_sdk.initial_authoring.goal_source import _issue

    owner._current()
    if type(project_request) is not InitialProjectRequest:
        raise ValueError("exact_initial_project_request_required")
    wire = _canonical(project_request.to_wire())
    if project_request.execution_id != owner._execution:
        raise ValueError("initial_goal_context_execution_mismatch")
    facts = owner._physical.observe_initial_goal_source(
        project_request, capability, target_path
    )
    return _issue(
        owner,
        InitialGoalSourceState(
            owner,
            project_request,
            capability,
            target_path,
            wire,
            _canonical(facts),
            os.getpid(),
            owner._provider_ref,
            owner._generation,
        ),
    )


from aware_workspace_sdk.initial_authoring.goal_source import _STATE_TYPES

_STATE_TYPES.add(InitialGoalSourceState)
