"""One pure initial-facts law shared by portable and Git creation claims.

The returned detached data carries no execution provenance or authority.
"""

from __future__ import annotations

from typing import cast

from .native_creation_request import NativeGoalCreationRequestV1
from .phase_contracts import GOAL_PHASE_BUNDLE_SCHEMA


def derive_native_creation_initial_facts(request: NativeGoalCreationRequestV1) -> dict[str, object]:
    """Revalidate authored input, without a provider or operational effect."""
    if type(request) is not NativeGoalCreationRequestV1:
        raise ValueError("creation_initial_facts_request_type")
    body = request.to_wire()
    lanes = cast(list[dict[str, object]], body["lanes"])
    return {
        "goal_tag": body["goal_tag"], "title": body["title"], "intent": body["intent"],
        "owner_ref": body["owner_ref"], "status": "proposed", "hold": "clear",
        "definition_of_done_ref": body["definition_of_done_ref"],
        "priority": body["priority"], "locks_ref": body["locks_ref"],
        "lanes": [dict(lane, operational_state="ready", current_issue_ref=None,
                       blocker_ref=None, hold_authority_refs=[], current_work_association_ref=None)
                  for lane in lanes],
        "definitions": body["definitions"],
        "operational_bundle": {"schema_id": GOAL_PHASE_BUNDLE_SCHEMA, "phases": [],
                               "dependencies": body["dependencies"]},
        "unresolved_dependencies": body["unresolved_dependencies"], "source_refs": [],
    }
