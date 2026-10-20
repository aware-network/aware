"""Qualified first-Goal reading over original Protocol/Workspace source owners.

Local author correlation is not Identity or Service disclosure authority. This
initial epoch is strict; future membership/source advancement needs its own law.
"""

from __future__ import annotations

import json
import os
from weakref import WeakKeyDictionary

from aware_goal_operational_runtime.planning_initial_plan import (
    decode_goal_planning_initial_plan,
)
from aware_goal_operational_runtime.planning_intent_document import (
    decode_goal_planning_intent_document,
    extract_goal_planning_markdown,
)
from aware_protocol_fs_adapter import require_project_resolver
from aware_protocol_fs_adapter.native_goal_resolver import (
    require_planning_goal_resolver,
)
from aware_workspace_sdk.initial_authoring.goal_publication import (
    InitialGoalPublicationRequest,
)

from .project_create_contract import canonical, reference
from .project_initial_source import _workspace

_READINGS = WeakKeyDictionary()
_PINS = WeakKeyDictionary()


def _binding(owner, capability, source):
    selected = require_project_resolver(capability)
    goal = require_planning_goal_resolver(selected.goal_capability)
    context = source["context"]
    if (
        selected.repository_root != owner._physical._root
        or str(selected.repository_root) != source["repository_root"]
        or selected.manifest_sha256 != context["manifest_sha256"]
        or selected.protocol_digest != context["protocol_digest"]
        or goal.goal_root != context["goal_root"]
        or goal.goal_template != context["goal_template"]
        or goal.goal_record_profile != context["goal_record_profile"]
        or goal.protocol_profile != context["protocol_profile"]
        or owner._execution != source["execution_id"]
    ):
        raise ValueError("initial_goal_reading_caller_or_protocol_mismatch")
    selected.resolve_project_path(context["project_path"])
    goal.resolve_goal_path(source["target_path"])
    return selected


class InitialPlanningGoalReading:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("use show_initial_planning_goal")

    def __copy__(self):
        raise TypeError("initial_goal_reading_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("initial_goal_reading_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("initial_goal_reading_not_serializable")

    def to_wire(self):
        state = _state(self)
        return json.loads(state[5])

    @property
    def document(self):
        return decode_goal_planning_intent_document(
            canonical(self.to_wire()["document"])
        )

    def require_current(self):
        state = _state(self)
        current = show_initial_planning_goal(
            workspace=state[1],
            resolver_capability=state[2],
            publication_request=state[3],
        )
        if canonical(current.to_wire()) != state[5]:
            raise ValueError("initial_goal_reading_stale")
        return current.to_wire()


def _state(reading):
    state = (
        _READINGS.get(reading) if type(reading) is InitialPlanningGoalReading else None
    )
    pins = _PINS.get(reading) if type(reading) is InitialPlanningGoalReading else None
    if state is None or pins is None or state != pins or state[0] != os.getpid():
        raise ValueError("initial_goal_reading_not_issued_or_mutated")
    owner = _workspace(state[1])
    if owner._execution != state[6] or canonical(state[3].to_wire()) != state[4]:
        raise ValueError("initial_goal_reading_execution_or_request_changed")
    return state


def show_initial_planning_goal(*, workspace, resolver_capability, publication_request):
    """Read the authenticated original committed carrier; never install/refresh."""
    owner = _workspace(workspace)
    if type(publication_request) is not InitialGoalPublicationRequest:
        raise ValueError("exact_initial_goal_publication_request_required")
    frozen = canonical(publication_request.to_wire())
    source = publication_request.source
    _binding(owner, resolver_capability, source)
    observed = workspace.observe_initial_goal_projection(publication_request)
    if observed.get("projection_state") != "installed":
        raise ValueError("initial_goal_reading_projection_unavailable")
    result = observed["original_result"]
    plan = decode_goal_planning_initial_plan(canonical(source["goal_plan"]))
    origin = plan.to_wire()["origin_intent"]
    if type(origin) is not dict:
        raise ValueError("initial_goal_reading_origin_invalid")
    content = source["content_utf8"].encode()
    document = extract_goal_planning_markdown(content)
    if (
        plan.carrier_bytes != content
        or canonical(plan.document.to_wire()) != canonical(document.to_wire())
        or origin["source_context_ref"] != source["context"]["source_ref"]
        or origin["intent_permission_ref"]
        != source["intent_permission"]["permission_ref"]
    ):
        raise ValueError("initial_goal_reading_origin_or_document_mismatch")
    blob = owner._physical._git(
        "rev-parse", result.commit_hash + ":" + source["target_path"]
    )
    body = {
        "schema_id": "aware.goal.initial-planning-reading.v1",
        "document": document.to_wire(),
        "planning_status": document.planning_status,
        "source": {
            "revision": result.commit_hash,
            "path": source["target_path"],
            "blob_oid": blob,
            "manifest_sha256": source["context"]["manifest_sha256"],
            "publication_ref": observed["publication"]["publication_ref"],
            "projection_ref": observed["projection"]["projection_ref"],
            "origin_intent_ref": document.to_wire()["origin_intent_ref"],
            "source_context_ref": source["context"]["source_ref"],
            "project_path": source["context"]["project_path"],
            "project_publication_ref": source["context"]["project_publication_ref"],
        },
        "caller": {
            "execution_id": owner._execution,
            "profile": "initial_goal_author_local_v1",
            "assurance": "local_fresh_repository_execution_correlation",
        },
    }
    # Resolutions come before final physical verification. The provider rechecks
    # Goal target/parents AFTER its last participating Project/manifest check.
    _binding(owner, resolver_capability, source)
    terminal = workspace.observe_initial_goal_projection(publication_request)
    if (
        terminal.get("projection_state") != "installed"
        or terminal["publication"]["publication_ref"]
        != observed["publication"]["publication_ref"]
        or terminal["projection"]["projection_ref"]
        != observed["projection"]["projection_ref"]
        or owner._physical._head() != ("refs/heads/main", result.commit_hash)
        or canonical(publication_request.to_wire()) != frozen
    ):
        raise ValueError("initial_goal_reading_source_changed")
    owner._current()
    wire = {**body, "reading_ref": reference("goal-initial-planning-reading", body)}
    reading = object.__new__(InitialPlanningGoalReading)
    state = (
        os.getpid(),
        workspace,
        resolver_capability,
        publication_request,
        frozen,
        canonical(wire),
        owner._execution,
    )
    _READINGS[reading] = _PINS[reading] = state
    _state(reading)
    return reading
