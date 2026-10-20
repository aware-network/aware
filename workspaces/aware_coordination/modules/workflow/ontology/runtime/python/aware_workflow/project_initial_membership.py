"""Read-only initial member preparation over the original Goal receipt owner.

This does not issue Project permission, admit publication, replace a worktree
file or qualify H2. Complete creation evidence stays external to the Project
record and is never relabelled a membership receipt.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from weakref import WeakKeyDictionary

from aware_protocol_fs_adapter import require_project_resolver
from aware_protocol_fs_adapter.native_goal_resolver import (
    require_planning_goal_resolver,
)
from aware_workspace_sdk.initial_authoring.goal_publication import (
    InitialGoalPublicationRequest,
)
from aware_workspace_sdk.initial_authoring.values import InitialProjectRequest
from aware_workspace_sdk.repository_publication import (
    WorkspaceRepositoryPublicationClient,
)

from .goal_planning_initial_read import show_initial_planning_goal
from .project_create_contract import canonical, reference
from .project_initial_source import _workspace
from .project_membership_contract import (
    ProjectGoalMembershipPlanV1,
    ProjectGoalMembershipRequestV1,
    plan_project_goal_membership,
)
from .project_source_codec import decode_project_context_toml


@dataclass(frozen=True)
class _PreparationState:
    workspace: WorkspaceRepositoryPublicationClient
    capability: Any
    goal_request: InitialGoalPublicationRequest
    request: ProjectGoalMembershipRequestV1
    pid: int
    frozen_goal: bytes
    frozen_request: bytes
    wire: bytes

    def pins(self) -> tuple[object, ...]:
        return (
            id(self.workspace),
            id(self.capability),
            id(self.goal_request),
            id(self.request),
            self.pid,
            self.frozen_goal,
            self.frozen_request,
            self.wire,
        )


_PREPARATIONS: WeakKeyDictionary[
    InitialProjectMembershipPreparation, _PreparationState
] = WeakKeyDictionary()
_PINS: WeakKeyDictionary[InitialProjectMembershipPreparation, tuple[object, ...]] = (
    WeakKeyDictionary()
)


class InitialProjectMembershipPreparation:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("use prepare_initial_project_membership")

    def __copy__(self):
        raise TypeError("initial_membership_preparation_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("initial_membership_preparation_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("initial_membership_preparation_not_serializable")

    def to_wire(self) -> dict[str, Any]:
        return json.loads(_state(self).wire)

    @property
    def plan(self) -> ProjectGoalMembershipPlanV1:
        return ProjectGoalMembershipPlanV1.from_wire(self.to_wire()["plan"])

    def require_current(self) -> dict[str, Any]:
        state = _state(self)
        current = _observe(
            state.workspace, state.capability, state.goal_request, state.request
        )
        _state(self)
        if canonical(current) != state.wire:
            raise ValueError("initial_membership_preparation_source_changed")
        return json.loads(state.wire)


def _state(handle: InitialProjectMembershipPreparation) -> _PreparationState:
    state = (
        _PREPARATIONS.get(handle)
        if type(handle) is InitialProjectMembershipPreparation
        else None
    )
    if state is None or state.pid != os.getpid() or state.pins() != _PINS.get(handle):
        raise ValueError("initial_membership_preparation_not_issued_or_mutated")
    _workspace(state.workspace)
    if (
        canonical(state.request.to_wire()) != state.frozen_request
        or canonical(state.goal_request.to_wire()) != state.frozen_goal
    ):
        raise ValueError("initial_membership_preparation_inputs_changed")
    return state


def _observe(workspace, capability, goal_request, request) -> dict[str, Any]:
    if (
        type(goal_request) is not InitialGoalPublicationRequest
        or type(request) is not ProjectGoalMembershipRequestV1
    ):
        raise ValueError("exact_initial_membership_inputs_required")
    frozen_goal, frozen_request = (
        canonical(goal_request.to_wire()),
        canonical(request.to_wire()),
    )
    owner = _workspace(workspace)
    reading = show_initial_planning_goal(
        workspace=workspace,
        resolver_capability=capability,
        publication_request=goal_request,
    ).to_wire()
    observed = workspace.observe_initial_goal_projection(goal_request)
    if observed.get("projection_state") != "installed":
        raise ValueError("initial_membership_goal_projection_unavailable")
    source = goal_request.source
    project_request = InitialProjectRequest.from_wire(source["project_request"])
    project_path = project_request.source["target_path"]
    before_content = project_request.source["project_plan"]["content_utf8"]
    before = decode_project_context_toml(before_content.encode())
    if before.goal_tags or request.goal_tag != reading["document"]["goal_tag"]:
        raise ValueError("initial_membership_wrong_created_goal_or_project")
    plan = plan_project_goal_membership(request, before)
    result = observed["original_result"]
    if (
        result.commit_hash != reading["source"]["revision"]
        or observed["publication"]["publication_ref"]
        != reading["source"]["publication_ref"]
        or observed["projection"]["projection_ref"]
        != reading["source"]["projection_ref"]
    ):
        raise ValueError("initial_membership_creation_evidence_changed")
    project_blob = owner._physical._git(
        "rev-parse", result.commit_hash + ":" + project_path
    )
    if project_blob != source["context"]["project_blob_oid"]:
        raise ValueError("initial_membership_project_preimage_changed")
    body = {
        "schema_id": "aware.project.initial-membership-preparation.v1",
        "request": request.to_wire(),
        "plan": plan.to_wire(),
        "source": {
            "repository_root": source["repository_root"],
            "execution_id": source["execution_id"],
            "selected_ref": "refs/heads/main",
            "revision": result.commit_hash,
            "manifest_sha256": reading["source"]["manifest_sha256"],
            "project_path": project_path,
            "project_blob_oid": project_blob,
            "project_content_utf8": before_content,
            "project_creation_request": project_request.to_wire(),
            "goal_creation_request": goal_request.to_wire(),
            "goal_creation_publication": observed["publication"],
            "goal_creation_projection": observed["projection"],
            "goal_reading": reading,
        },
        "assurance": "local_fresh_repository_execution_correlation",
        "permission": "not_issued",
        "membership_state": "not_published",
    }
    # Admission/location resolution precedes the last ORIGINAL three-entry
    # projection/source fence. Never refresh H1 after any intervening movement.
    selected = require_project_resolver(capability)
    selected.resolve_project_path(project_path)
    require_planning_goal_resolver(selected.goal_capability).resolve_goal_path(
        source["target_path"]
    )
    terminal = workspace.observe_initial_goal_projection(goal_request)
    if (
        terminal.get("projection_state") != "installed"
        or canonical(terminal["publication"]) != canonical(observed["publication"])
        or canonical(terminal["projection"]) != canonical(observed["projection"])
        or owner._physical._head() != ("refs/heads/main", result.commit_hash)
        or canonical(goal_request.to_wire()) != frozen_goal
        or canonical(request.to_wire()) != frozen_request
    ):
        raise ValueError("initial_membership_source_or_intent_changed")
    owner._current()
    if len(canonical(body)) > 1024 * 1024:
        raise ValueError("initial_membership_preparation_size_limit")
    return {
        **body,
        "preparation_ref": reference("project-initial-membership-preparation", body),
    }


def prepare_initial_project_membership(
    *,
    workspace,
    resolver_capability,
    goal_publication_request: InitialGoalPublicationRequest,
    request: ProjectGoalMembershipRequestV1,
) -> InitialProjectMembershipPreparation:
    """Read-only H1 preparation. Only later Workspace admission may publish H2."""
    frozen_goal = (
        canonical(goal_publication_request.to_wire())
        if type(goal_publication_request) is InitialGoalPublicationRequest
        else b""
    )
    frozen_request = (
        canonical(request.to_wire())
        if type(request) is ProjectGoalMembershipRequestV1
        else b""
    )
    wire = _observe(workspace, resolver_capability, goal_publication_request, request)
    if (
        canonical(goal_publication_request.to_wire()) != frozen_goal
        or canonical(request.to_wire()) != frozen_request
    ):
        raise ValueError("initial_membership_inputs_changed")
    handle = object.__new__(InitialProjectMembershipPreparation)
    state = _PreparationState(
        workspace,
        resolver_capability,
        goal_publication_request,
        request,
        os.getpid(),
        frozen_goal,
        frozen_request,
        canonical(wire),
    )
    _PREPARATIONS[handle], _PINS[handle] = state, state.pins()
    return handle


def require_membership_publication_input(workspace_owner, preparation):
    """Original Workspace consumes a live source, not its decoded claim."""
    state = _state(preparation)
    if _workspace(state.workspace) is not workspace_owner:
        raise ValueError("initial_membership_foreign_workspace_owner")
    wire = preparation.require_current()
    _state(preparation)
    facts = wire["source"]
    body = {
        "schema_id": "aware.workspace.initial-membership-source.v1",
        "preparation": wire,
        "repository_root": facts["repository_root"],
        "execution_id": facts["execution_id"],
        "expected_head": facts["revision"],
        "target_path": facts["project_path"],
        "before_content_utf8": facts["project_content_utf8"],
        "content_utf8": wire["plan"]["content_utf8"],
    }
    source = {
        **body,
        "source_ref": reference("workspace-initial-membership-source", body),
    }
    validate_membership_publication_input(source)
    return source


def validate_membership_publication_input(source):
    """Recompute Project meaning only; a valid decoded source grants nothing."""
    from aware_goal_operational_runtime.planning_intent_document import (
        extract_goal_planning_markdown,
    )
    from aware_workspace_sdk.initial_authoring.membership import membership_request

    membership_request(source, "descriptor-validation")
    wire = source["preparation"]
    facts = wire["source"]
    plan = ProjectGoalMembershipPlanV1.from_wire(wire["plan"])
    goal = InitialGoalPublicationRequest.from_wire(facts["goal_creation_request"])
    project = InitialProjectRequest.from_wire(facts["project_creation_request"])
    document = extract_goal_planning_markdown(goal.source["content_utf8"].encode())
    reading = facts["goal_reading"]
    expected_reading_fields = {
        "schema_id",
        "document",
        "planning_status",
        "source",
        "caller",
        "reading_ref",
    }
    if type(reading) is not dict or set(reading) != expected_reading_fields:
        raise ValueError("initial_membership_goal_reading_shape")
    reading_body = {k: v for k, v in reading.items() if k != "reading_ref"}
    if (
        canonical(plan.request.to_wire()) != canonical(wire["request"])
        or plan.before.goal_tags
        or plan.request.goal_tag != document.to_wire()["goal_tag"]
        or canonical(plan.before.to_wire())
        != canonical(
            decode_project_context_toml(
                source["before_content_utf8"].encode()
            ).to_wire()
        )
        or source["before_content_utf8"]
        != project.source["project_plan"]["content_utf8"]
        or plan.content != source["content_utf8"].encode()
        or reading["schema_id"] != "aware.goal.initial-planning-reading.v1"
        or reading["planning_status"] != "not_yet_decomposed"
        or canonical(reading["document"]) != canonical(document.to_wire())
        or reading["reading_ref"]
        != reference("goal-initial-planning-reading", reading_body)
        or facts["manifest_sha256"] != goal.source["context"]["manifest_sha256"]
        or facts["project_blob_oid"] != goal.source["context"]["project_blob_oid"]
        or reading["source"]
        != {
            "revision": source["expected_head"],
            "path": goal.source["target_path"],
            "blob_oid": reading["source"].get("blob_oid"),
            "manifest_sha256": facts["manifest_sha256"],
            "publication_ref": facts["goal_creation_publication"]["publication_ref"],
            "projection_ref": facts["goal_creation_projection"]["projection_ref"],
            "origin_intent_ref": document.to_wire()["origin_intent_ref"],
            "source_context_ref": goal.source["context"]["source_ref"],
            "project_path": source["target_path"],
            "project_publication_ref": goal.source["context"][
                "project_publication_ref"
            ],
        }
        or reading["caller"]
        != {
            "execution_id": source["execution_id"],
            "profile": "initial_goal_author_local_v1",
            "assurance": "local_fresh_repository_execution_correlation",
        }
    ):
        raise ValueError("initial_membership_domain_input_mismatch")
    return plan
