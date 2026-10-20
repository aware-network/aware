"""Qualified H2 Project/Goal reading; original creation remains historical.

No permission, receipt reissuance, implicit authoring or eligibility. A genuine
retained Protocol capability and original Workspace observation are mandatory.
"""

from __future__ import annotations

import json
import os
from weakref import WeakKeyDictionary

from aware_goal_operational_runtime.planning_initial_plan import (
    decode_goal_planning_initial_plan,
)
from aware_goal_operational_runtime.planning_intent_document import (
    extract_goal_planning_markdown,
)
from aware_workspace_sdk.initial_authoring.goal_publication import (
    InitialGoalPublicationRequest,
)
from aware_workspace_sdk.initial_authoring.membership import InitialMembershipRequest

from .goal_planning_initial_read import _binding
from .project_create_contract import canonical, reference
from .project_initial_membership import validate_membership_publication_input
from .project_initial_source import _workspace
from .project_source_codec import decode_project_context_toml

_READINGS = WeakKeyDictionary()
_PINS = WeakKeyDictionary()


class InitialProjectMembershipReading:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("use show_initial_project_membership")

    def __copy__(self):
        raise TypeError("membership_reading_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("membership_reading_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("membership_reading_not_serializable")

    def to_wire(self):
        return json.loads(_state(self)[5])

    def require_current(self):
        state = _state(self)
        current = show_initial_project_membership(
            workspace=state[1],
            resolver_capability=state[2],
            publication_request=state[3],
        ).to_wire()
        if canonical(current) != state[5]:
            raise ValueError("membership_reading_stale")
        return current


def _state(reading):
    state = (
        _READINGS.get(reading)
        if type(reading) is InitialProjectMembershipReading
        else None
    )
    pins = (
        _PINS.get(reading) if type(reading) is InitialProjectMembershipReading else None
    )
    if state is None or pins is None or state != pins or state[0] != os.getpid():
        raise ValueError("membership_reading_not_issued_or_mutated")
    owner = _workspace(state[1])
    if owner._execution != state[6] or canonical(state[3].to_wire()) != state[4]:
        raise ValueError("membership_reading_execution_or_request_changed")
    return state


def show_initial_project_membership(
    *, workspace, resolver_capability, publication_request
):
    owner = _workspace(workspace)
    if type(publication_request) is not InitialMembershipRequest:
        raise ValueError("exact_initial_membership_request_required")
    frozen = canonical(publication_request.to_wire())
    source = publication_request.source
    validate_membership_publication_input(source)
    facts = source["preparation"]["source"]
    goal_request = InitialGoalPublicationRequest.from_wire(
        facts["goal_creation_request"]
    )
    _binding(owner, resolver_capability, goal_request.source)
    observed = workspace.observe_initial_membership_projection(publication_request)
    if observed.get("projection_state") != "installed":
        raise ValueError("membership_reading_projection_unavailable")
    project = decode_project_context_toml(source["content_utf8"].encode())
    document = extract_goal_planning_markdown(
        goal_request.source["content_utf8"].encode()
    )
    plan = decode_goal_planning_initial_plan(
        canonical(goal_request.source["goal_plan"])
    )
    if (
        canonical(plan.document.to_wire()) != canonical(document.to_wire())
        or project.to_wire() != source["preparation"]["plan"]["after"]
        or document.to_wire()["goal_tag"] not in project.goal_tags
        or canonical(observed["goal_creation_publication"])
        != canonical(facts["goal_creation_publication"])
        or observed["original_result"].commit_hash
        == facts["goal_reading"]["source"]["revision"]
    ):
        raise ValueError("membership_reading_document_or_epoch_mismatch")
    revision = observed["original_result"].commit_hash
    source_entries = {}
    for kind, path in (
        ("project", source["target_path"]),
        ("goal", goal_request.source["target_path"]),
    ):
        source_entries[kind] = {
            "path": path,
            "blob_oid": owner._physical._git("rev-parse", revision + ":" + path),
        }
    body = {
        "schema_id": "aware.project.initial-membership-reading.v1",
        "project": project.to_wire(),
        "goal": document.to_wire(),
        "planning_status": document.planning_status,
        "source": {
            "revision": revision,
            **source_entries,
            "manifest_sha256": facts["manifest_sha256"],
            "goal_creation_revision": facts["goal_reading"]["source"]["revision"],
        },
        "goal_creation_publication": observed["goal_creation_publication"],
        "membership_publication": observed["publication"],
        "membership_projection": observed["projection"],
        "caller": {
            "execution_id": owner._execution,
            "assurance": "local_fresh_repository_execution_correlation",
        },
    }
    # No source lookups after the final original three-entry fence. Discovery
    # is not refreshed if capability, request or source advances meanwhile.
    _binding(owner, resolver_capability, goal_request.source)
    owner._current()
    terminal = workspace.observe_initial_membership_projection(publication_request)
    if (
        terminal.get("projection_state") != "installed"
        or canonical(terminal["publication"]) != canonical(observed["publication"])
        or canonical(terminal["goal_creation_publication"])
        != canonical(observed["goal_creation_publication"])
        or canonical(terminal["projection"]) != canonical(observed["projection"])
        or canonical(publication_request.to_wire()) != frozen
    ):
        raise ValueError("membership_reading_source_changed")
    wire = {
        **body,
        "reading_ref": reference("project-initial-membership-reading", body),
    }
    reading = object.__new__(InitialProjectMembershipReading)
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
