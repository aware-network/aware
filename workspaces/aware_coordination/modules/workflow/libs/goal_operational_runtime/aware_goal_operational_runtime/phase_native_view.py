"""Pure native Goal reading. Recorded state is not operational authorization.

Source adapters own observation; Service owns fulfillment and actor admission.
This module performs no filesystem access, evaluation, event or mutation.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import cast

# Neutral sibling codecs own the canonical leaf contracts, not an SDK copy.
# pyright: reportPrivateUsage=false
from .phase_codec import _dependency, _phase
from .phase_document import (
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    GoalPhaseNativeDocumentV4,
    decode_goal_phase_native_document,
    encode_goal_phase_native_document,
    _decode_definition,
    _decode_execution_authority,
    _decode_unresolved,
)
from .phase_future_schedule import (
    assess_goal_phase_future_schedule,
    decode_goal_phase_future_schedule,
)

SOURCE_SCHEMA = "aware.goal.native-view-source.v2"
STATE_SCHEMA = "aware.goal.landscape.view-state.v2"
API_VIEW_REF = "goal.goal_landscape"
EXPERIENCE_VIEW_REF = "aware_goals.workflow.goal.v2"
NativeDocument = (
    GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3 | GoalPhaseNativeDocumentV4
)


class GoalNativeViewError(ValueError):
    """A read input or transported native state violates the closed contract."""


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise GoalNativeViewError("duplicate JSON field")
        result[key] = value
    return result


def _object(value: object, keys: set[str], name: str) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise GoalNativeViewError(f"{name} fields differ")
    return cast(dict[str, object], value)


def _text(value: object, name: str, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if type(value) is not str or not value or value.strip() != value:
        raise GoalNativeViewError(f"{name} must be canonical text")
    return value


def _enum(value: object, allowed: set[str], name: str) -> str:
    text = _text(value, name)
    if text not in allowed:
        raise GoalNativeViewError(f"{name} is unsupported")
    return cast(str, text)


def _list(value: object, name: str) -> list[object]:
    if type(value) is not list:
        raise GoalNativeViewError(f"{name} must be an array")
    return cast(list[object], value)


def _strings(value: object, name: str) -> list[str]:
    values = [cast(str, _text(v, name)) for v in _list(value, name)]
    if len(set(values)) != len(values):
        raise GoalNativeViewError(f"{name} contains duplicates")
    return values


def _nullable_fields(value: Mapping[str, object], names: tuple[str, ...]) -> None:
    for name in names:
        _text(value[name], name, nullable=True)


_ISSUE_DETAILS = {
    "priority", "acceptance_done", "acceptance_total", "updates",
    "reading_view_ref", "reading_issue_ref", "reading_projection_revision",
}


def goal_native_issue_facets(reading: Mapping[str, object]) -> dict[str, object]:
    """Pure map facets from an Issue-owned reading, never an Issue evaluator.

    Filesystem/Object adapters supply the owner's exact reading. Counting and
    presentation projection stay out of those adapters; Brief/Activity remains
    the separate existing Issue View rather than a Goal-authored second model.
    """
    identity = cast(Mapping[str, object], reading["identity"])
    checks = _list(reading["acceptance_items"], "Issue acceptance items")
    done = 0
    for raw in checks:
        item = cast(Mapping[str, object], raw)
        if type(item["checked"]) not in {bool, type(None)}:
            raise GoalNativeViewError("Issue checklist type differs")
        done += item["checked"] is True
    return {
        "priority": identity["priority"], "acceptance_done": done,
        "acceptance_total": len(checks),
        "updates": [{k: cast(Mapping[str, object], a)[k]
            for k in ("activity_ref", "activity_at", "time_authority")}
            for a in _list(reading["activities"], "Issue activities")],
        "reading_view_ref": "issue.issue_reading",
        "reading_issue_ref": identity["issue_ref"],
        "reading_projection_revision": reading["projection_revision"],
    }


def _issue_details(issue: dict[str, object]) -> None:
    _nullable_fields(issue, ("priority", "reading_view_ref", "reading_issue_ref", "reading_projection_revision"))
    if issue["availability"] == "unavailable":
        if any(issue[n] is not None for n in _ISSUE_DETAILS - {"updates"}) or issue["updates"] != []:
            raise GoalNativeViewError("unavailable Issue claims details")
        return
    if issue["reading_view_ref"] != "issue.issue_reading":
        raise GoalNativeViewError("Issue reading View differs")
    _text(issue["reading_issue_ref"], "reading Issue target")
    canonical_identity = _text(issue["tag"], "Issue tag")
    if issue["reading_issue_ref"] != canonical_identity:
        raise GoalNativeViewError("Issue reading target differs from canonical identity")
    if cast(str, issue["issue_ref"]).startswith("fb/") and issue["issue_ref"] != canonical_identity:
        raise GoalNativeViewError("Issue association tag differs from canonical identity")
    _text(issue["reading_projection_revision"], "Issue reading revision")
    for name in ("acceptance_done", "acceptance_total"):
        if type(issue[name]) is not int or cast(int, issue[name]) < 0:
            raise GoalNativeViewError("Issue check count invalid")
    if cast(int, issue["acceptance_done"]) > cast(int, issue["acceptance_total"]):
        raise GoalNativeViewError("Issue check counts contradictory")
    refs = set()
    for raw in _list(issue["updates"], "Issue updates"):
        update = _object(raw, {"activity_ref", "activity_at", "time_authority"}, "Issue update")
        ref = _text(update["activity_ref"], "Issue activity")
        if ref in refs:
            raise GoalNativeViewError("duplicate Issue activity")
        refs.add(ref)
        instant = _text(update["activity_at"], "Issue activity time", nullable=True)
        authority = _enum(update["time_authority"], {"commit_receipt", "issue_service", "source_declared", "source_observed", "unavailable"}, "Issue time authority")
        if (instant is None) != (authority == "unavailable"):
            raise GoalNativeViewError("Issue time authority differs")
        if instant is not None:
            try:
                parsed = datetime.fromisoformat(instant.replace("Z", "+00:00"))
            except ValueError as error:
                raise GoalNativeViewError("invalid Issue activity time") from error
            if parsed.tzinfo is None:
                raise GoalNativeViewError("Issue activity time lacks timezone")


def _document(value: object) -> tuple[NativeDocument, dict[str, object]]:
    doc = decode_goal_phase_native_document(canonical_json(value))
    if type(doc) not in {
        GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3, GoalPhaseNativeDocumentV4,
    }:
        raise GoalNativeViewError("native V2/V3/V4 required")
    # Compare, do not repair a caller-supplied reference by reconstruction.
    raw = cast(dict[str, object], json.loads(encode_goal_phase_native_document(doc)))
    if raw != value:
        raise GoalNativeViewError("document content differs")
    return cast(NativeDocument, doc), raw


def validate_goal_native_view_source(value: object) -> dict[str, object]:
    """Validate read structure only; this cannot enroll a source provider."""
    root = _object(value, {
        "schema_id", "document", "source", "goal", "lanes", "schedules", "linked_issues",
    }, "source input")
    if root["schema_id"] != SOURCE_SCHEMA:
        raise GoalNativeViewError("unsupported source schema")
    document, _ = _document(root["document"])
    source = _object(root["source"], {
        "profile", "provider_ref", "provider_generation", "source_scope_ref",
        "source_revision", "document_ref", "projection_health", "input_refs",
    }, "source evidence")
    for name in ("profile", "provider_ref", "provider_generation", "source_scope_ref", "source_revision"):
        _text(source[name], name)
    if source["document_ref"] != document.document_ref:
        raise GoalNativeViewError("source document mismatch")
    _enum(source["projection_health"], {"current", "stale", "absent", "unavailable"}, "projection_health")
    _strings(source["input_refs"], "input_refs")
    goal = _object(root["goal"], {
        "goal_tag", "title", "lifecycle_status", "owner_ref", "hold_state",
        "authority_ref", "source_revision",
    }, "Goal reading")
    if goal["goal_tag"] != document.goal_tag or goal["source_revision"] != source["source_revision"]:
        raise GoalNativeViewError("Goal source/identity mismatch")
    for name in ("title", "owner_ref", "authority_ref"):
        _text(goal[name], name)
    _enum(goal["lifecycle_status"], {"proposed", "active", "parked", "held", "completed", "withdrawn"}, "Goal lifecycle")
    _enum(goal["hold_state"], {"clear", "held"}, "Goal hold")
    lane_keys = {d.coordinate.lane_key for d in document.definitions}
    lanes: set[str] = set()
    for raw in _list(root["lanes"], "lanes"):
        lane = _object(raw, {
            "lane_key", "label", "authority_availability", "reason", "owner_ref",
            "operational_state", "state_detail", "current_issue_ref", "authority_ref",
            "source_revision",
        }, "lane reading")
        key = cast(str, _text(lane["lane_key"], "lane_key"))
        if key in lanes or key not in lane_keys:
            raise GoalNativeViewError("lane membership differs")
        lanes.add(key)
        _text(lane["label"], "lane label")
        availability = _enum(lane["authority_availability"], {"source_recorded", "ambiguous", "unavailable"}, "lane availability")
        _nullable_fields(lane, ("reason", "owner_ref", "state_detail", "current_issue_ref", "authority_ref"))
        if lane["source_revision"] != source["source_revision"]:
            raise GoalNativeViewError("lane epoch differs")
        if availability == "unavailable":
            if lane["reason"] is None or any(lane[n] is not None for n in ("owner_ref", "operational_state", "current_issue_ref", "authority_ref", "state_detail")):
                raise GoalNativeViewError("unavailable lane cannot claim authority")
        else:
            _text(lane["owner_ref"], "lane owner")
            _text(lane["authority_ref"], "lane authority")
            state = _enum(lane["operational_state"], {"planned", "active", "held", "blocked", "ready", "complete", "withdrawn"}, "lane state")
            if state in {"held", "blocked"} and lane["state_detail"] is None:
                raise GoalNativeViewError("lane blocker detail required")
            if (availability == "ambiguous") != (lane["reason"] is not None):
                raise GoalNativeViewError("lane ambiguity reason differs")
    if lanes != lane_keys:
        raise GoalNativeViewError("complete lane inventory required")
    schedules: set[str] = set()
    for raw in _list(root["schedules"], "schedules"):
        item = _object(raw, {"lane_key", "status", "reason", "schedule", "source_revision"}, "schedule reading")
        key = cast(str, _text(item["lane_key"], "schedule lane"))
        if key in schedules or key not in lane_keys:
            raise GoalNativeViewError("schedule membership differs")
        schedules.add(key)
        status = _enum(item["status"], {"current", "stale", "absent", "unavailable"}, "schedule status")
        _text(item["reason"], "schedule reason", nullable=True)
        if item["source_revision"] != source["source_revision"]:
            raise GoalNativeViewError("schedule epoch differs")
        if item["schedule"] is None:
            if status not in {"absent", "unavailable"} or item["reason"] is None:
                raise GoalNativeViewError("missing schedule disposition differs")
        else:
            schedule = decode_goal_phase_future_schedule(canonical_json(item["schedule"]) + b"\n")
            if schedule.lane_key != key or schedule.goal_tag != document.goal_tag:
                raise GoalNativeViewError("schedule identity differs")
            if status == "current":
                if type(document) is not GoalPhaseNativeDocumentV2:
                    raise GoalNativeViewError("schedule profile is V2-only")
                if assess_goal_phase_future_schedule(schedule=schedule, document=document) != ("current", None) or item["reason"] is not None:
                    raise GoalNativeViewError("current schedule is inconsistent")
    if schedules != lane_keys:
        raise GoalNativeViewError("complete schedule inventory required")
    issue_refs: set[str] = set()
    work_refs = {w.issue_ref for p in document.operational_bundle.phases for w in p.work_associations}
    for raw in _list(root["linked_issues"], "linked Issues"):
        issue = _object(raw, {
            "issue_ref", "availability", "reason", "tag", "title", "status",
            "owner_execution_id", "source_revision", "source_ref",
        } | _ISSUE_DETAILS, "linked Issue")
        _issue_details(issue)
        ref = cast(str, _text(issue["issue_ref"], "issue_ref"))
        if ref in issue_refs or ref not in work_refs:
            raise GoalNativeViewError("Issue association differs")
        issue_refs.add(ref)
        availability = _enum(issue["availability"], {"available", "unavailable"}, "Issue availability")
        _nullable_fields(issue, ("reason", "tag", "title", "status", "owner_execution_id", "source_ref"))
        if issue["source_revision"] != source["source_revision"]:
            raise GoalNativeViewError("Issue epoch differs")
        if availability == "available":
            for name in ("tag", "title", "owner_execution_id", "source_ref"):
                _text(issue[name], name)
            _enum(issue["status"], {"open", "in_progress", "blocked", "closed"}, "Issue status")
            if issue["reason"] is not None:
                raise GoalNativeViewError("available Issue has reason")
        elif issue["reason"] is None or any(issue[n] is not None for n in ("tag", "title", "status", "owner_execution_id", "source_ref")):
            raise GoalNativeViewError("unavailable Issue claims state")
    if issue_refs != work_refs:
        raise GoalNativeViewError("complete Work/Issue inventory required")
    return root


def project_goal_native_view_v2(value: object, *, observation_ref: str) -> dict[str, object]:
    """Project one complete source reading without evaluating or authorizing it."""
    root = validate_goal_native_view_source(value)
    _text(observation_ref, "observation_ref")
    document, wire = _document(root["document"])
    bundle = cast(dict[str, object], wire["operational_bundle"])
    phases = {}
    for phase_wire in cast(list[dict[str, object]], bundle["phases"]):
        coordinate = cast(dict[str, str], phase_wire["coordinate"])
        phases[(coordinate["lane_key"], coordinate["phase_key"])] = phase_wire
    schedules = {cast(str, cast(dict[str, object], s)["lane_key"]): s for s in _list(root["schedules"], "schedules")}
    lane_readings = {cast(str, cast(dict[str, object], l)["lane_key"]): l for l in _list(root["lanes"], "lanes")}
    lanes: list[dict[str, object]] = []
    # Inventory order is authored, never alphabetical or an execution schedule.
    lane_order = dict.fromkeys(d.coordinate.lane_key for d in document.definitions)
    for key in lane_order:
        entries = []
        for definition in cast(list[dict[str, object]], wire["definitions"]):
            coordinate = cast(dict[str, object], definition["coordinate"])
            if coordinate["lane_key"] != key:
                continue
            phase = phases.get((key, cast(str, coordinate["phase_key"])))
            entries.append({
                "definition": definition, "operational": phase,
                "gate_qualification": "not_evaluated" if phase is None or not cast(dict[str, object], phase)["gate_observations"] else "unavailable",
                "execution_posture": "unavailable",
            })
        lanes.append({"reading": lane_readings[key], "phases": entries, "schedule": schedules[key]})
    dependencies = [{"declaration": d, "declaration_state": "resolved", "observation_state": "not_evaluated"} for d in cast(list[object], bundle["dependencies"])]
    unresolved = [{"declaration": d, "declaration_state": "unresolved", "observation_state": "unresolved"} for d in cast(list[object], wire["unresolved_dependencies"])]
    result = {
        "schema_id": STATE_SCHEMA,
        "goal": root["goal"],
        "source": {**cast(dict[str, object], root["source"]), "observation_ref": observation_ref},
        "execution_authority": wire["execution_authority"],
        "lanes": lanes,
        "dependencies": dependencies,
        "unresolved_dependencies": unresolved,
        "linked_issues": root["linked_issues"],
        "definition_count": len(document.definitions),
        "operational_phase_count": len(document.operational_bundle.phases),
        "activity_availability": "unavailable",
        "capability_availability": "unavailable",
    }
    validate_goal_native_view_state(result)
    return result


def validate_goal_native_view_state(value: object) -> dict[str, object]:
    """Strict transport checks, never repository or operational verification."""
    root = _object(value, {
        "schema_id", "goal", "source", "execution_authority", "lanes",
        "dependencies", "unresolved_dependencies", "linked_issues",
        "definition_count", "operational_phase_count", "activity_availability",
        "capability_availability",
    }, "View state")
    if root["schema_id"] != STATE_SCHEMA:
        raise GoalNativeViewError("unsupported state schema")
    for name in ("activity_availability", "capability_availability"):
        if root[name] != "unavailable":
            raise GoalNativeViewError("read profile cannot claim activity or capabilities")
    for name in ("definition_count", "operational_phase_count"):
        if type(root[name]) is not int or cast(int, root[name]) < 0:
            raise GoalNativeViewError("counts must be nonnegative integers")
    _decode_execution_authority(root["execution_authority"])
    source = _object(root["source"], {
        "profile", "provider_ref", "provider_generation", "source_scope_ref",
        "source_revision", "document_ref", "projection_health", "input_refs",
        "observation_ref",
    }, "View source")
    for name in source.keys() - {"projection_health", "input_refs"}:
        _text(source[name], name)
    _enum(source["projection_health"], {"current", "stale", "absent", "unavailable"}, "projection health")
    _strings(source["input_refs"], "input refs")
    goal = _object(root["goal"], {
        "goal_tag", "title", "lifecycle_status", "owner_ref", "hold_state",
        "authority_ref", "source_revision",
    }, "View Goal")
    for name in goal:
        _text(goal[name], name)
    _enum(goal["lifecycle_status"], {"proposed", "active", "parked", "held", "completed", "withdrawn"}, "Goal lifecycle")
    _enum(goal["hold_state"], {"clear", "held"}, "Goal hold")
    revision = source["source_revision"]
    if goal["source_revision"] != revision:
        raise GoalNativeViewError("Goal epoch differs")
    lanes: set[str] = set()
    definitions = {}
    operational = []
    for raw in _list(root["lanes"], "View lanes"):
        lane = _object(raw, {"reading", "phases", "schedule"}, "View lane")
        reading = _object(lane["reading"], {
            "lane_key", "label", "authority_availability", "reason", "owner_ref",
            "operational_state", "state_detail", "current_issue_ref", "authority_ref",
            "source_revision",
        }, "View lane reading")
        key = cast(str, _text(reading["lane_key"], "lane key"))
        if key in lanes or reading["source_revision"] != revision:
            raise GoalNativeViewError("lane identity/epoch differs")
        lanes.add(key)
        _text(reading["label"], "lane label")
        availability = _enum(reading["authority_availability"], {"source_recorded", "ambiguous", "unavailable"}, "lane availability")
        _nullable_fields(reading, ("reason", "owner_ref", "state_detail", "current_issue_ref", "authority_ref"))
        if availability == "unavailable":
            if reading["reason"] is None or any(reading[n] is not None for n in ("owner_ref", "operational_state", "current_issue_ref", "authority_ref", "state_detail")):
                raise GoalNativeViewError("unavailable lane claims authority")
        else:
            _text(reading["owner_ref"], "owner")
            _text(reading["authority_ref"], "lane authority")
            state = _enum(reading["operational_state"], {"planned", "active", "held", "blocked", "ready", "complete", "withdrawn"}, "lane state")
            if state in {"held", "blocked"} and reading["state_detail"] is None:
                raise GoalNativeViewError("blocker detail absent")
            if (availability == "ambiguous") != (reading["reason"] is not None):
                raise GoalNativeViewError("lane ambiguity differs")
        lane_definitions = []
        for raw_entry in _list(lane["phases"], "View phases"):
            entry = _object(raw_entry, {"definition", "operational", "gate_qualification", "execution_posture"}, "View Phase")
            definition = _decode_definition(entry["definition"])
            coordinate = definition.coordinate
            if coordinate.goal_tag != goal["goal_tag"] or coordinate.lane_key != key or coordinate in definitions:
                raise GoalNativeViewError("Phase coordinate differs/duplicates")
            definitions[coordinate] = definition
            lane_definitions.append(definition)
            phase = None if entry["operational"] is None else _phase(entry["operational"])
            if phase is not None:
                if (phase.coordinate, phase.title, phase.intent, phase.ordinal, phase.gate) != (coordinate, definition.title, definition.intent, definition.ordinal, definition.gate):
                    raise GoalNativeViewError("operational Phase differs from definition")
                operational.append(phase)
            expected = "not_evaluated" if phase is None or not phase.gate_observations else "unavailable"
            if entry["gate_qualification"] != expected or entry["execution_posture"] != "unavailable":
                raise GoalNativeViewError("recorded state cannot claim qualification/execution")
        if not lane_definitions or len({d.ordinal for d in lane_definitions}) != len(lane_definitions):
            raise GoalNativeViewError("lane definition inventory differs")
        item = _object(lane["schedule"], {"lane_key", "status", "reason", "schedule", "source_revision"}, "View schedule")
        if item["lane_key"] != key or item["source_revision"] != revision:
            raise GoalNativeViewError("schedule identity/epoch differs")
        status = _enum(item["status"], {"current", "stale", "absent", "unavailable"}, "schedule status")
        _text(item["reason"], "schedule reason", nullable=True)
        if item["schedule"] is None:
            if status not in {"absent", "unavailable"} or item["reason"] is None:
                raise GoalNativeViewError("schedule absence differs")
        else:
            schedule = decode_goal_phase_future_schedule(canonical_json(item["schedule"]) + b"\n")
            if schedule.goal_tag != goal["goal_tag"] or schedule.lane_key != key:
                raise GoalNativeViewError("schedule target differs")
            if status == "current":
                bindings = {d.coordinate.phase_key: d.definition_ref for d in lane_definitions}
                required = {p.coordinate.phase_key for p in operational if p.coordinate.lane_key == key and p.state.value in {"active", "held"}}
                if dict(schedule.definition_bindings) != bindings or not required.issubset(schedule.authored_order) or item["reason"] is not None:
                    raise GoalNativeViewError("schedule current claim differs")
    if not definitions or len(definitions) != root["definition_count"] or len(operational) != root["operational_phase_count"]:
        raise GoalNativeViewError("inventory counts differ")
    keys: set[str] = set()
    for name, decoder, declared, observed in (
        ("dependencies", _dependency, "resolved", "not_evaluated"),
        ("unresolved_dependencies", _decode_unresolved, "unresolved", "unresolved"),
    ):
        for raw in _list(root[name], name):
            item = _object(raw, {"declaration", "declaration_state", "observation_state"}, "View dependency")
            edge = decoder(item["declaration"])
            if edge.owner_goal_tag != goal["goal_tag"] or edge.dependency_key in keys:
                raise GoalNativeViewError("dependency identity differs")
            keys.add(edge.dependency_key)
            for coordinate in (edge.dependent, edge.prerequisite):
                if coordinate.goal_tag == goal["goal_tag"] and coordinate not in definitions:
                    raise GoalNativeViewError("dependency endpoint absent")
            if declared == "resolved" and edge.prerequisite.goal_tag == goal["goal_tag"]:
                if cast(str, getattr(edge, "required_gate_digest")) != definitions[edge.prerequisite].gate.gate_digest:
                    raise GoalNativeViewError("dependency Gate binding differs")
            if item["declaration_state"] != declared or item["observation_state"] != observed:
                raise GoalNativeViewError("read profile cannot qualify dependencies")
    work_refs = {w.issue_ref for p in operational for w in p.work_associations}
    issue_refs = set()
    for raw in _list(root["linked_issues"], "linked Issues"):
        issue = _object(raw, {
            "issue_ref", "availability", "reason", "tag", "title", "status",
            "owner_execution_id", "source_revision", "source_ref",
        } | _ISSUE_DETAILS, "View Issue")
        _issue_details(issue)
        ref = cast(str, _text(issue["issue_ref"], "Issue ref"))
        if ref in issue_refs or ref not in work_refs or issue["source_revision"] != revision:
            raise GoalNativeViewError("Issue identity/epoch differs")
        issue_refs.add(ref)
        available = _enum(issue["availability"], {"available", "unavailable"}, "Issue availability")
        _nullable_fields(issue, ("reason", "tag", "title", "status", "owner_execution_id", "source_ref"))
        if available == "available":
            for name in ("tag", "title", "owner_execution_id", "source_ref"):
                _text(issue[name], name)
            _enum(issue["status"], {"open", "in_progress", "blocked", "closed"}, "Issue status")
            if issue["reason"] is not None:
                raise GoalNativeViewError("available Issue claims reason")
        elif issue["reason"] is None or any(issue[n] is not None for n in ("tag", "title", "status", "owner_execution_id", "source_ref")):
            raise GoalNativeViewError("unavailable Issue claims authority")
    if issue_refs != work_refs:
        raise GoalNativeViewError("Issue inventory incomplete")
    return root


def decode_goal_native_view_state(payload: bytes) -> dict[str, object]:
    if type(payload) is not bytes:
        raise TypeError("payload must be bytes")
    try:
        value = json.loads(payload, object_pairs_hook=_unique)
    except (ValueError, UnicodeDecodeError) as error:
        raise GoalNativeViewError("invalid state JSON") from error
    return validate_goal_native_view_state(value)


def decode_goal_native_view_source(payload: bytes) -> dict[str, object]:
    if type(payload) is not bytes:
        raise TypeError("payload must be bytes")
    try:
        value = json.loads(payload, object_pairs_hook=_unique)
    except (ValueError, UnicodeDecodeError) as error:
        raise GoalNativeViewError("invalid source JSON") from error
    return validate_goal_native_view_source(value)
