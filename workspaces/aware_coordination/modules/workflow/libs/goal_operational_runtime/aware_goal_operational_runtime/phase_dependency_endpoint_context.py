"""Canonical endpoint source context, not Gate or execution qualification.

Pure projections retain carrier evidence as claims. Only a concrete provider
can authenticate this context; construction/digests do not establish issuance.
"""
# pyright: reportPrivateUsage=false
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import cast

from .identity import fingerprint
from .phase_contracts import GoalLanePhaseWorkDisposition, GoalPhaseCoordinate
from .phase_native_scope_advancement import GoalGlobalDirectionAuthorityV1, GoalLaneDirectionAuthorityV1
from .phase_codec import _coordinate, _coordinate_wire, _phase, _phase_wire, _mapping, _keys, _list, _string, _optional_string
from .phase_document import (
    _decode_definition, _definition_wire, _decode_journal_entry, _journal_entry_wire,
    _exact_json_equal, _qualified, GoalPhaseOperationJournalV1,
    GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3,
    encode_goal_phase_native_document, decode_goal_phase_native_document, _text,
)

CONTEXT_SCHEMA = "aware.goal.dependency-endpoint-context.v2"
SCOPE_PROFILE = "dependency_endpoint_context_v2"
ABSENT_CONTEXT_SCHEMA = "aware.goal.dependency-endpoint-context.v3"
ABSENT_SCOPE_PROFILE = "dependency_endpoint_context_v3"
Document = GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3


def _json_tokens(raw: object, name: str) -> tuple[str, ...]:
    return tuple(_text(value, name) for value in _list(raw, name))


def _optional_token(raw: object, name: str) -> str | None:
    return None if raw is None else _text(raw, name)


def _decode_global(raw: object) -> GoalGlobalDirectionAuthorityV1:
    values = _mapping(raw, "Goal-global authority")
    _keys(values, {"schema_id", "goal_tag", "lifecycle_status", "owner_ref", "governance_authority_refs",
        "hold_state", "hold_authority_refs", "execution_authority_ref", "compatibility_guard_ref",
        "source_revision_ref", "projector_ref", "projection_receipt_ref", "authority_ref"}, "Goal-global authority")
    authority = GoalGlobalDirectionAuthorityV1(
        schema_id=_text(values["schema_id"], "schema_id"), goal_tag=_text(values["goal_tag"], "goal_tag"),
        lifecycle_status=_text(values["lifecycle_status"], "lifecycle_status"), owner_ref=_text(values["owner_ref"], "owner_ref"),
        governance_authority_refs=_json_tokens(values["governance_authority_refs"], "governance_authority_refs"),
        hold_state=_text(values["hold_state"], "hold_state"), hold_authority_refs=_json_tokens(values["hold_authority_refs"], "hold_authority_refs"),
        execution_authority_ref=_text(values["execution_authority_ref"], "execution_authority_ref"),
        compatibility_guard_ref=_text(values["compatibility_guard_ref"], "compatibility_guard_ref"),
        source_revision_ref=_text(values["source_revision_ref"], "source_revision_ref"),
        projector_ref=_text(values["projector_ref"], "projector_ref"), projection_receipt_ref=_text(values["projection_receipt_ref"], "projection_receipt_ref"),
    )
    if not _exact_json_equal(authority.to_wire(), values):
        raise ValueError("endpoint_global_authority_not_canonical")
    return authority


def _decode_lane(raw: object) -> GoalLaneDirectionAuthorityV1:
    values = _mapping(raw, "lane authority")
    _keys(values, {"schema_id", "goal_tag", "lane_key", "role", "owner_ref", "operational_state", "state_detail",
        "blocker_authority_refs", "current_issue_ref", "current_issue_authority_ref", "compatibility_guard_ref",
        "source_revision_ref", "projector_ref", "projection_receipt_ref", "qualification", "ambiguity_reasons", "authority_ref"}, "lane authority")
    authority = GoalLaneDirectionAuthorityV1(
        schema_id=_text(values["schema_id"], "schema_id"), goal_tag=_text(values["goal_tag"], "goal_tag"),
        lane_key=_text(values["lane_key"], "lane_key"), role=_string(values["role"], "role"), owner_ref=_text(values["owner_ref"], "owner_ref"),
        operational_state=_text(values["operational_state"], "operational_state"), state_detail=_optional_string(values["state_detail"], "state_detail"),
        blocker_authority_refs=_json_tokens(values["blocker_authority_refs"], "blocker_authority_refs"),
        current_issue_ref=_optional_token(values["current_issue_ref"], "current_issue_ref"),
        current_issue_authority_ref=_optional_token(values["current_issue_authority_ref"], "current_issue_authority_ref"),
        compatibility_guard_ref=_text(values["compatibility_guard_ref"], "compatibility_guard_ref"),
        source_revision_ref=_text(values["source_revision_ref"], "source_revision_ref"),
        projector_ref=_text(values["projector_ref"], "projector_ref"), projection_receipt_ref=_text(values["projection_receipt_ref"], "projection_receipt_ref"),
        qualification=_text(values["qualification"], "qualification"), ambiguity_reasons=_json_tokens(values["ambiguity_reasons"], "ambiguity_reasons"),
    )
    if not _exact_json_equal(authority.to_wire(), values):
        raise ValueError("endpoint_lane_authority_not_canonical")
    return authority


def decode_dependency_endpoint_context(raw: object) -> dict[str, object]:
    """Strict neutral transport validation; no source issuance or eligibility.

    Reconstruct all nested contracts and compare derived references without
    repairing the submitted value. Provider authentication remains separate.
    """
    values = _mapping(raw, "endpoint context")
    absent = values.get("schema_id") == ABSENT_CONTEXT_SCHEMA
    extra: set[str] = {"lane_authority_profile", "lane_authority_reason"} if absent else set()
    _keys(values, {"schema_id", "scope_profile", "coordinate", "endpoint_profile", "document_ref",
        "source_revision_ref", "definition", "phase", "goal_global", "lane", "lane_issue_context",
        "operation_journal_profile", "phase_operation_entries", "gate_authority_profile", "effect_profile", "context_ref"} | extra, "endpoint context")
    schema = ABSENT_CONTEXT_SCHEMA if absent else CONTEXT_SCHEMA
    profile = ABSENT_SCOPE_PROFILE if absent else SCOPE_PROFILE
    if (_text(values["schema_id"], "schema_id") != schema or _text(values["scope_profile"], "scope_profile") != profile
        or _text(values["effect_profile"], "effect_profile") != "source_context_only_non_authorizing"):
        raise ValueError("endpoint_context_profile_invalid")
    if absent and (values["lane"] is not None or values["lane_authority_profile"] != "absent_native_only_v1"
        or values["lane_authority_reason"] != "lane_authority_absent"):
        raise ValueError("endpoint_absent_lane_profile_invalid")
    endpoint_profile = _text(values["endpoint_profile"], "endpoint_profile")
    journal_profile = _text(values["operation_journal_profile"], "operation_journal_profile")
    gate_profile = _text(values["gate_authority_profile"], "gate_authority_profile")
    coordinate = _coordinate(values["coordinate"])
    source_revision = _text(values["source_revision_ref"], "source_revision_ref")
    document_ref = _qualified(values["document_ref"], "document_ref", "goal-phase-document")
    definition = _decode_definition(values["definition"])
    phase = None if values["phase"] is None else _phase(values["phase"])
    global_authority = _decode_global(values["goal_global"])
    lane = None if absent else _decode_lane(values["lane"])
    if (definition.coordinate != coordinate or global_authority.goal_tag != coordinate.goal_tag
        or global_authority.source_revision_ref != source_revision
        or (lane is not None and (lane.goal_tag != coordinate.goal_tag or lane.lane_key != coordinate.lane_key
            or lane.source_revision_ref != source_revision or lane.qualification != "qualified"))):
        raise ValueError("endpoint_authority_source_mismatch")
    issues: list[dict[str, object]] = []
    for raw_issue in _list(values["lane_issue_context"], "lane_issue_context"):
        issue = _mapping(raw_issue, "endpoint Issue")
        issues.append(_issue_wire({**issue, "scope": tuple(_string(path, "Issue scope") for path in _list(issue.get("scope"), "Issue scope"))}))
    paths = tuple(cast(str, issue["path"]) for issue in issues)
    if paths != tuple(sorted(set(paths))) or (lane is not None and any(issue["owner"] != lane.owner_ref for issue in issues)):
        raise ValueError("endpoint_issue_set_mismatch")
    selected_issue = None if lane is None else lane.current_issue_ref
    if selected_issue is not None and not selected_issue.startswith("TBD:") and selected_issue not in paths:
        raise ValueError("endpoint_issue_set_mismatch")
    entries = tuple(_decode_journal_entry(entry) for entry in _list(values["phase_operation_entries"], "phase_operation_entries"))
    if journal_profile not in {"none", "v1"}:
        raise ValueError("endpoint_journal_profile_invalid")
    if entries:
        if journal_profile != "v1":
            raise ValueError("endpoint_journal_profile_invalid")
        # Scoped entries retain their append order and complete causal chain.
        _ = GoalPhaseOperationJournalV1(entries=entries)
        if any(entry.coordinate != coordinate or entry.gate_digest != definition.gate.gate_digest for entry in entries):
            raise ValueError("endpoint_journal_binding_invalid")
    if phase is None:
        if (endpoint_profile != "definition_only_v1" or entries or gate_profile != "not_evaluated"):
            raise ValueError("endpoint_definition_only_claim_invalid")
    else:
        if (endpoint_profile != "operational_v1" or phase.coordinate != coordinate
            or (phase.title, phase.intent, phase.ordinal, phase.gate) != (definition.title, definition.intent, definition.ordinal, definition.gate)
            or gate_profile != ("unqualified_carrier_claim" if phase.gate_observations else "not_evaluated")):
            raise ValueError("endpoint_operational_context_invalid")
        current = tuple(work for work in phase.work_associations if work.disposition is GoalLanePhaseWorkDisposition.CURRENT)
        for work in current:
            if work.issue_ref not in paths or (lane is not None and work.issue_ref != selected_issue):
                raise ValueError("endpoint_operational_lane_work_disagreement")
            if next(issue for issue in issues if issue["path"] == work.issue_ref)["status"] != "in_progress":
                raise ValueError("endpoint_current_work_issue_not_active")
    body: dict[str, object] = {
        "schema_id": schema, "scope_profile": profile, "coordinate": _coordinate_wire(coordinate),
        "endpoint_profile": "definition_only_v1" if phase is None else "operational_v1", "document_ref": document_ref,
        "source_revision_ref": source_revision, "definition": _definition_wire(definition),
        "phase": None if phase is None else _phase_wire(phase), "goal_global": global_authority.to_wire(), "lane": None if lane is None else lane.to_wire(),
        "lane_issue_context": issues, "operation_journal_profile": journal_profile,
        "phase_operation_entries": [_journal_entry_wire(entry) for entry in entries],
        "gate_authority_profile": gate_profile, "effect_profile": "source_context_only_non_authorizing",
    }
    if absent:
        body.update(lane_authority_profile="absent_native_only_v1", lane_authority_reason="lane_authority_absent")
    canonical = {**body, "context_ref": "goal-dependency-endpoint-context:" + fingerprint(body)}
    if not _exact_json_equal(canonical, values):
        raise ValueError("endpoint_context_not_canonical")
    return canonical


def _issue_wire(issue: Mapping[str, object]) -> dict[str, object]:
    if set(issue) != {"path", "tag", "blob_oid", "owner", "status", "scope", "scope_digest"}:
        raise ValueError("endpoint_issue_fields_invalid")
    for name in ("path", "tag", "blob_oid", "owner", "status", "scope_digest"):
        value = issue[name]
        if type(value) is not str or not value or value.strip() != value:
            raise ValueError("endpoint_issue_text_invalid")
    scope = issue["scope"]
    if type(scope) is not tuple:
        raise ValueError("endpoint_issue_scope_invalid")
    paths = cast(tuple[object, ...], scope)
    if not paths or any(type(p) is not str or not p or p.strip() != p for p in paths):
        raise ValueError("endpoint_issue_scope_invalid")
    scope = cast(tuple[str, ...], scope)
    if len(set(scope)) != len(scope):
        raise ValueError("endpoint_issue_scope_invalid")
    if issue["scope_digest"] != fingerprint({"ownership_scope": list(scope)}):
        raise ValueError("endpoint_issue_scope_digest_invalid")
    if issue["status"] not in {"open", "in_progress", "blocked", "closed"}:
        raise ValueError("endpoint_issue_status_invalid")
    return {**issue, "scope": list(scope)}


def _derive_dependency_endpoint_context(*, document: Document, coordinate: GoalPhaseCoordinate,
    global_authority: GoalGlobalDirectionAuthorityV1, lane_authority: GoalLaneDirectionAuthorityV1 | None,
    issues: tuple[Mapping[str, object], ...], source_revision_ref: str) -> dict[str, object]:
    """Derive semantics from source facts without claiming provider issuance."""
    if type(document) not in {GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3}:
        raise ValueError("endpoint_carrier_unsupported")
    original_ref = document.document_ref
    payload = encode_goal_phase_native_document(document)
    restored = decode_goal_phase_native_document(payload)
    if restored != document or restored.document_ref != original_ref:
        raise ValueError("endpoint_document_not_canonical")
    document = cast(Document, restored)
    if type(coordinate) is not GoalPhaseCoordinate:
        raise TypeError("endpoint coordinate requires exact type")
    coordinate.__post_init__()
    if type(global_authority) is not GoalGlobalDirectionAuthorityV1 or (lane_authority is not None and type(lane_authority) is not GoalLaneDirectionAuthorityV1):
        raise TypeError("endpoint authority requires exact profiles")
    global_authority.__post_init__()
    if lane_authority is not None:
        lane_authority.__post_init__()
    if (coordinate.goal_tag != document.goal_tag or global_authority.goal_tag != document.goal_tag
        or global_authority.source_revision_ref != source_revision_ref
        or (lane_authority is not None and (lane_authority.goal_tag != document.goal_tag
            or lane_authority.lane_key != coordinate.lane_key or lane_authority.source_revision_ref != source_revision_ref))):
        raise ValueError("endpoint_authority_source_mismatch")
    if lane_authority is not None and lane_authority.qualification != "qualified":
        raise ValueError("endpoint_lane_authority_ambiguous")
    definitions = tuple(d for d in document.definitions if d.coordinate == coordinate)
    if len(definitions) != 1:
        raise ValueError("endpoint_definition_unavailable")
    phases = tuple(p for p in document.operational_bundle.phases if p.coordinate == coordinate)
    phase = phases[0] if phases else None
    current = tuple(w for p in document.operational_bundle.phases if p.coordinate.lane_key == coordinate.lane_key
        for w in p.work_associations if w.disposition is GoalLanePhaseWorkDisposition.CURRENT)
    declared_issue = None if lane_authority is None else lane_authority.current_issue_ref
    if declared_issue is not None and declared_issue.startswith("TBD:"):
        declared_issue = None
    # Definition-only endpoints do not inherit any native Work in their lane.
    # Operational endpoints retain the strict lane-selection agreement.
    if lane_authority is not None and phase is not None and tuple(w.issue_ref for w in current) != (() if declared_issue is None else (declared_issue,)):
        raise ValueError("endpoint_operational_lane_work_disagreement")
    required = {w.issue_ref for w in current}
    if declared_issue is not None:
        required.add(declared_issue)
    if type(issues) is not tuple:
        raise TypeError("endpoint Issues require exact tuple")
    issue_wires = tuple(_issue_wire(i) for i in issues)
    actual = tuple(cast(str, i["path"]) for i in issue_wires)
    if actual != tuple(sorted(required)):
        raise ValueError("endpoint_issue_set_mismatch")
    for issue in issue_wires:
        if lane_authority is not None and issue["owner"] != lane_authority.owner_ref:
            raise ValueError("endpoint_issue_owner_mismatch")
        if issue["path"] in {w.issue_ref for w in current} and issue["status"] != "in_progress":
            raise ValueError("endpoint_current_work_issue_not_active")
    wire = cast(dict[str, object], json.loads(payload))
    coord = {"goal_tag": coordinate.goal_tag, "lane_key": coordinate.lane_key, "phase_key": coordinate.phase_key}
    definition = next(d for d in cast(list[dict[str, object]], wire["definitions"]) if d["coordinate"] == coord)
    bundle = cast(dict[str, object], wire["operational_bundle"])
    phase_wire = next((p for p in cast(list[dict[str, object]], bundle["phases"]) if p["coordinate"] == coord), None)
    journal = wire.get("phase_operation_journal")
    entries = [] if journal is None else cast(list[dict[str, object]], cast(dict[str, object], journal)["entries"])
    body: dict[str, object] = {
        "schema_id": CONTEXT_SCHEMA if lane_authority is not None else ABSENT_CONTEXT_SCHEMA,
        "scope_profile": SCOPE_PROFILE if lane_authority is not None else ABSENT_SCOPE_PROFILE, "coordinate": coord,
        "endpoint_profile": "definition_only_v1" if phase is None else "operational_v1",
        "document_ref": document.document_ref, "source_revision_ref": source_revision_ref,
        "definition": definition, "phase": phase_wire,
        "goal_global": global_authority.to_wire(), "lane": None if lane_authority is None else lane_authority.to_wire(),
        "lane_issue_context": list(issue_wires),
        "operation_journal_profile": "none" if journal is None else "v1",
        "phase_operation_entries": [e for e in entries if e["coordinate"] == coord],
        "gate_authority_profile": "not_evaluated" if phase is None or not phase.gate_observations else "unqualified_carrier_claim",
        "effect_profile": "source_context_only_non_authorizing",
    }
    if lane_authority is None:
        body.update(lane_authority_profile="absent_native_only_v1", lane_authority_reason="lane_authority_absent")
    return decode_dependency_endpoint_context({**body, "context_ref": "goal-dependency-endpoint-context:" + fingerprint(body)})


def derive_dependency_endpoint_context(*, document: Document, coordinate: GoalPhaseCoordinate,
    global_authority: GoalGlobalDirectionAuthorityV1, lane_authority: GoalLaneDirectionAuthorityV1,
    issues: tuple[Mapping[str, object], ...], source_revision_ref: str) -> dict[str, object]:
    """Existing qualified V2 projection: unchanged wire and reference algorithm."""
    if type(lane_authority) is not GoalLaneDirectionAuthorityV1:
        raise TypeError("endpoint authority requires exact profiles")
    return _derive_dependency_endpoint_context(document=document, coordinate=coordinate,
        global_authority=global_authority, lane_authority=lane_authority,
        issues=issues, source_revision_ref=source_revision_ref)


def derive_absent_lane_endpoint_context(*, document: Document, coordinate: GoalPhaseCoordinate,
    global_authority: GoalGlobalDirectionAuthorityV1, issues: tuple[Mapping[str, object], ...],
    source_revision_ref: str) -> dict[str, object]:
    """V3 non-authorizing facts; the provider must independently prove absence.

    No lane owner, state, selection or qualification is inferred from Work.
    This projection cannot be used as the selected admission authority.
    """
    return _derive_dependency_endpoint_context(document=document, coordinate=coordinate,
        global_authority=global_authority, lane_authority=None,
        issues=issues, source_revision_ref=source_revision_ref)


def dependency_endpoint_scope_profile(records: tuple[dict[str, object], ...]) -> str:
    """Derive a closed source-context profile, never an eligibility decision."""
    profiles = {
        decode_dependency_endpoint_context(_mapping(record[role], "endpoint")["context"])["scope_profile"]
        for record in records if record["evaluation_profile"] == "source_context_only_non_authorizing"
        for role in ("dependent", "prerequisite")
    }
    return ABSENT_SCOPE_PROFILE if ABSENT_SCOPE_PROFILE in profiles else SCOPE_PROFILE


def validate_forward_admission_direction(*, coordinate: GoalPhaseCoordinate, issue_ref: str,
    global_authority: GoalGlobalDirectionAuthorityV1, lane_authority: GoalLaneDirectionAuthorityV1,
    selected_issue: Mapping[str, object]) -> None:
    """Shared neutral consistency checks; the provider authenticates facts."""
    global_authority.__post_init__()
    lane_authority.__post_init__()
    issue = _issue_wire(selected_issue)
    if (global_authority.goal_tag != coordinate.goal_tag or lane_authority.goal_tag != coordinate.goal_tag
        or lane_authority.lane_key != coordinate.lane_key or lane_authority.qualification != "qualified"):
        raise ValueError("forward_admission_lane_authority_unavailable")
    if global_authority.lifecycle_status != "active" or global_authority.hold_state != "clear":
        raise ValueError("forward_admission_goal_not_open")
    if lane_authority.operational_state not in {"planned", "ready", "active"}:
        raise ValueError("forward_admission_lane_not_open")
    if (issue["path"] != issue_ref or issue["status"] != "in_progress"
        or issue["owner"] != lane_authority.owner_ref
        or lane_authority.current_issue_ref != issue_ref):
        raise ValueError("forward_admission_selected_work_disagreement")
