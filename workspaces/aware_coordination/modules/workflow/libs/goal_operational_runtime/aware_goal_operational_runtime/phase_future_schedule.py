"""Order-only, Goal-owned schedule for native Phase definitions.

The schedule is deliberately adjacent to, rather than embedded in, the V2
document. It never supplies lifecycle, Gate, dependency, or Issue authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import cast

from .phase_contracts import GoalLanePhaseState
from .phase_document import GoalPhaseNativeDocumentV2

SCHEMA = "aware.goal.phase-future-schedule.v1"
_KEY = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_DEFINITION = re.compile(r"^goal-phase-definition:sha256:[0-9a-f]{64}$")
_OID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")
_DOCUMENT = re.compile(r"^goal-phase-document:sha256:[0-9a-f]{64}$")


class GoalPhaseFutureScheduleError(ValueError):
    """The schedule cannot be admitted or observed as authoritative."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise GoalPhaseFutureScheduleError("duplicate JSON field")
        result[key] = value
    return result


def _path(value: str, name: str) -> str:
    if type(value) is not str or not value or value.startswith("/") or "\\" in value:
        raise GoalPhaseFutureScheduleError(f"{name} must be a relative POSIX path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise GoalPhaseFutureScheduleError(f"{name} is not canonical")
    return value


def schedule_path(*, goal_doc_path: str, lane_key: str) -> str:
    """Derive the one authority path; never discover by directory search."""
    _ = _path(goal_doc_path, "goal_doc_path")
    if (
        not goal_doc_path.endswith(".md")
        or "/" not in goal_doc_path
        or not _KEY.fullmatch(lane_key)
    ):
        raise GoalPhaseFutureScheduleError("invalid Goal path or lane key")
    parent, filename = goal_doc_path.rsplit("/", 1)
    return f"{parent}/schedules/{filename[:-3]}/{lane_key}.json"


@dataclass(frozen=True, slots=True)
class GoalPhaseFutureScheduleV1:
    goal_tag: str
    goal_doc_path: str
    lane_key: str
    definition_bindings: tuple[tuple[str, str], ...]
    authored_order: tuple[str, ...]
    retained_unscheduled: tuple[str, ...]
    decision_issue_path: str
    decision_issue_blob_oid: str
    schedule_ref: str = field(init=False)
    schema_id: str = SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseFutureScheduleV1 or self.schema_id != SCHEMA:
            raise GoalPhaseFutureScheduleError("unsupported schedule schema")
        if type(self.goal_tag) is not str or not self.goal_tag.startswith("goal/"):
            raise GoalPhaseFutureScheduleError("invalid Goal tag")
        _ = schedule_path(goal_doc_path=self.goal_doc_path, lane_key=self.lane_key)
        _ = _path(self.decision_issue_path, "decision_issue_path")
        if (
            not self.decision_issue_path.startswith("docs/issues/")
            or not self.decision_issue_path.endswith(".md")
        ):
            raise GoalPhaseFutureScheduleError("decision Issue path is invalid")
        if (
            type(self.decision_issue_blob_oid) is not str
            or not _OID.fullmatch(self.decision_issue_blob_oid)
        ):
            raise GoalPhaseFutureScheduleError("decision Issue blob is invalid")
        if type(self.definition_bindings) is not tuple or not self.definition_bindings:
            raise GoalPhaseFutureScheduleError("definitions must be nonempty tuple")
        for item in self.definition_bindings:
            if type(item) is not tuple or len(item) != 2:
                raise GoalPhaseFutureScheduleError("definition binding must be exact pair")
            key, ref = item
            if (
                type(key) is not str
                or not _KEY.fullmatch(key)
                or type(ref) is not str
                or not _DEFINITION.fullmatch(ref)
            ):
                raise GoalPhaseFutureScheduleError("invalid definition binding")
        keys = tuple(key for key, _ in self.definition_bindings)
        if keys != tuple(sorted(set(keys))):
            raise GoalPhaseFutureScheduleError("definition bindings must be unique and sorted")
        if type(self.authored_order) is not tuple:
            raise GoalPhaseFutureScheduleError("authored order must be tuple")
        if type(self.retained_unscheduled) is not tuple:
            raise GoalPhaseFutureScheduleError("retained definitions must be tuple")
        for key in self.authored_order + self.retained_unscheduled:
            if type(key) is not str or not _KEY.fullmatch(key):
                raise GoalPhaseFutureScheduleError("invalid Phase key")
        if len(set(self.authored_order)) != len(self.authored_order):
            raise GoalPhaseFutureScheduleError("authored order contains duplicate")
        if self.retained_unscheduled != tuple(sorted(set(self.retained_unscheduled))):
            raise GoalPhaseFutureScheduleError("retained definitions must be unique and sorted")
        if (
            set(self.authored_order) & set(self.retained_unscheduled)
            or set(self.authored_order + self.retained_unscheduled) != set(keys)
        ):
            raise GoalPhaseFutureScheduleError("schedule must partition every definition")
        object.__setattr__(
            self,
            "schedule_ref",
            "goal-phase-future-schedule:sha256:"
            + hashlib.sha256(_canonical(self.to_wire(include_ref=False))).hexdigest(),
        )

    def to_wire(self, *, include_ref: bool = True) -> dict[str, object]:
        body: dict[str, object] = {
            "schema_id": self.schema_id,
            "goal_tag": self.goal_tag,
            "goal_doc_path": self.goal_doc_path,
            "lane_key": self.lane_key,
            "definition_bindings": [
                {"phase_key": key, "definition_ref": ref}
                for key, ref in self.definition_bindings
            ],
            "authored_order": list(self.authored_order),
            "retained_unscheduled": list(self.retained_unscheduled),
            "decision_issue_path": self.decision_issue_path,
            "decision_issue_blob_oid": self.decision_issue_blob_oid,
        }
        if include_ref:
            body["schedule_ref"] = self.schedule_ref
        return body


@dataclass(frozen=True, slots=True)
class GoalPhaseFutureSchedulePublicationReceiptV1:
    before_schedule_ref: str | None
    after_schedule_ref: str
    goal_tag: str
    goal_doc_path: str
    lane_key: str
    definition_closure_ref: str
    changed_path: str
    decision_issue_path: str
    decision_issue_blob_oid: str
    repository_commit_ref: str
    repository_commit_receipt_ref: str
    semantic_intent_ref: str
    receipt_ref: str = field(init=False)
    schema_id: str = "aware.goal.phase-future-schedule-publication.v1"

    def __post_init__(self) -> None:
        if (
            type(self) is not GoalPhaseFutureSchedulePublicationReceiptV1
            or self.schema_id != "aware.goal.phase-future-schedule-publication.v1"
        ):
            raise GoalPhaseFutureScheduleError("unsupported publication receipt")
        if self.changed_path != schedule_path(
            goal_doc_path=self.goal_doc_path, lane_key=self.lane_key
        ):
            raise GoalPhaseFutureScheduleError("publication path is not canonical")
        if self.repository_commit_receipt_ref != f"repository-commit:{self.repository_commit_ref}":
            raise GoalPhaseFutureScheduleError("repository receipt does not bind commit")
        if (
            type(self.repository_commit_ref) is not str
            or not _OID.fullmatch(self.repository_commit_ref)
        ):
            raise GoalPhaseFutureScheduleError("invalid publication commit")
        if (
            type(self.decision_issue_blob_oid) is not str
            or not _OID.fullmatch(self.decision_issue_blob_oid)
        ):
            raise GoalPhaseFutureScheduleError("invalid decision Issue blob")
        for name, value in (
            ("after_schedule_ref", self.after_schedule_ref),
            ("definition_closure_ref", self.definition_closure_ref),
            ("semantic_intent_ref", self.semantic_intent_ref),
        ):
            if type(value) is not str or not value:
                raise GoalPhaseFutureScheduleError(f"invalid {name}")
        if self.before_schedule_ref is not None and type(self.before_schedule_ref) is not str:
            raise GoalPhaseFutureScheduleError("invalid prior schedule reference")
        object.__setattr__(
            self,
            "receipt_ref",
            "goal-phase-future-schedule-publication:sha256:"
            + hashlib.sha256(_canonical(self.to_wire(include_ref=False))).hexdigest(),
        )

    def to_wire(self, *, include_ref: bool = True) -> dict[str, object]:
        body: dict[str, object] = {
            "schema_id": self.schema_id,
            "before_schedule_ref": self.before_schedule_ref,
            "after_schedule_ref": self.after_schedule_ref,
            "goal_tag": self.goal_tag,
            "goal_doc_path": self.goal_doc_path,
            "lane_key": self.lane_key,
            "definition_closure_ref": self.definition_closure_ref,
            "changed_path": self.changed_path,
            "decision_issue_path": self.decision_issue_path,
            "decision_issue_blob_oid": self.decision_issue_blob_oid,
            "repository_commit_ref": self.repository_commit_ref,
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
            "semantic_intent_ref": self.semantic_intent_ref,
        }
        if include_ref:
            body["receipt_ref"] = self.receipt_ref
        return body


@dataclass(frozen=True, slots=True)
class GoalPhaseFutureScheduleRepositoryReconciliationV1:
    """An epoch-bound observation, not a worktree write or new publication."""

    publication_receipt: GoalPhaseFutureSchedulePublicationReceiptV1
    observed_head: str
    goal_sha256: str
    document_ref: str
    schedule_blob_oid: str
    index_blob_oid: str
    worktree_disposition: str = "repository_only_absent"
    reconciliation_ref: str = field(init=False)
    schema_id: str = "aware.goal.phase-future-schedule-repository-reconciliation.v1"

    def __post_init__(self) -> None:
        if (
            type(self) is not GoalPhaseFutureScheduleRepositoryReconciliationV1
            or self.schema_id
            != "aware.goal.phase-future-schedule-repository-reconciliation.v1"
            or type(self.publication_receipt)
            is not GoalPhaseFutureSchedulePublicationReceiptV1
        ):
            raise GoalPhaseFutureScheduleError("unsupported repository reconciliation")
        publication = self.publication_receipt
        if publication.receipt_ref != (
            "goal-phase-future-schedule-publication:sha256:"
            + hashlib.sha256(_canonical(publication.to_wire(include_ref=False))).hexdigest()
        ):
            raise GoalPhaseFutureScheduleError("publication receipt digest differs")
        if (
            type(self.observed_head) is not str
            or not _OID.fullmatch(self.observed_head)
            or type(self.goal_sha256) is not str
            or not _SHA.fullmatch(self.goal_sha256)
            or type(self.document_ref) is not str
            or not _DOCUMENT.fullmatch(self.document_ref)
            or type(self.schedule_blob_oid) is not str
            or not _OID.fullmatch(self.schedule_blob_oid)
            or type(self.index_blob_oid) is not str
            or self.index_blob_oid != self.schedule_blob_oid
            or self.worktree_disposition != "repository_only_absent"
        ):
            raise GoalPhaseFutureScheduleError("repository reconciliation binding is invalid")
        object.__setattr__(
            self,
            "reconciliation_ref",
            "goal-phase-future-schedule-repository-reconciliation:sha256:"
            + hashlib.sha256(_canonical(self.to_wire(include_ref=False))).hexdigest(),
        )

    def to_wire(self, *, include_ref: bool = True) -> dict[str, object]:
        body: dict[str, object] = {
            "schema_id": self.schema_id,
            "publication_receipt": self.publication_receipt.to_wire(),
            "observed_head": self.observed_head,
            "goal_sha256": self.goal_sha256,
            "document_ref": self.document_ref,
            "schedule_blob_oid": self.schedule_blob_oid,
            "index_blob_oid": self.index_blob_oid,
            "worktree_disposition": self.worktree_disposition,
        }
        if include_ref:
            body["reconciliation_ref"] = self.reconciliation_ref
        return body


def encode_goal_phase_future_schedule_repository_reconciliation(
    value: GoalPhaseFutureScheduleRepositoryReconciliationV1,
) -> bytes:
    if type(value) is not GoalPhaseFutureScheduleRepositoryReconciliationV1:
        raise TypeError("value must be an exact repository reconciliation")
    value.__post_init__()
    return _canonical(value.to_wire()) + b"\n"


def decode_goal_phase_future_schedule_repository_reconciliation(
    payload: bytes,
) -> GoalPhaseFutureScheduleRepositoryReconciliationV1:
    if type(payload) is not bytes:
        raise TypeError("payload must be bytes")
    try:
        raw = cast(object, json.loads(payload, object_pairs_hook=_unique_pairs))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoalPhaseFutureScheduleError("invalid reconciliation JSON") from error
    if type(raw) is not dict:
        raise GoalPhaseFutureScheduleError("reconciliation fields are not canonical")
    values = cast(dict[str, object], raw)
    if set(values) != {
        "schema_id", "publication_receipt", "observed_head", "goal_sha256",
        "document_ref", "schedule_blob_oid", "index_blob_oid",
        "worktree_disposition", "reconciliation_ref",
    } or type(values["publication_receipt"]) is not dict:
        raise GoalPhaseFutureScheduleError("reconciliation fields are not canonical")
    nested = cast(dict[str, object], values["publication_receipt"])
    publication_fields = {
        "schema_id", "before_schedule_ref", "after_schedule_ref", "goal_tag",
        "goal_doc_path", "lane_key", "definition_closure_ref", "changed_path",
        "decision_issue_path", "decision_issue_blob_oid", "repository_commit_ref",
        "repository_commit_receipt_ref", "semantic_intent_ref", "receipt_ref",
    }
    if set(nested) != publication_fields or any(
        type(value) is not str
        for key, value in nested.items()
        if key != "before_schedule_ref"
    ):
        raise GoalPhaseFutureScheduleError("publication receipt fields are not canonical")
    publication = GoalPhaseFutureSchedulePublicationReceiptV1(
        before_schedule_ref=cast(str | None, nested["before_schedule_ref"]),
        after_schedule_ref=cast(str, nested["after_schedule_ref"]),
        goal_tag=cast(str, nested["goal_tag"]),
        goal_doc_path=cast(str, nested["goal_doc_path"]),
        lane_key=cast(str, nested["lane_key"]),
        definition_closure_ref=cast(str, nested["definition_closure_ref"]),
        changed_path=cast(str, nested["changed_path"]),
        decision_issue_path=cast(str, nested["decision_issue_path"]),
        decision_issue_blob_oid=cast(str, nested["decision_issue_blob_oid"]),
        repository_commit_ref=cast(str, nested["repository_commit_ref"]),
        repository_commit_receipt_ref=cast(str, nested["repository_commit_receipt_ref"]),
        semantic_intent_ref=cast(str, nested["semantic_intent_ref"]),
        schema_id=cast(str, nested["schema_id"]),
    )
    if nested != publication.to_wire():
        raise GoalPhaseFutureScheduleError("publication receipt differs from digest")
    if any(
        type(values[key]) is not str
        for key in values if key != "publication_receipt"
    ):
        raise GoalPhaseFutureScheduleError("reconciliation fields are not exact strings")
    value = GoalPhaseFutureScheduleRepositoryReconciliationV1(
        publication_receipt=publication,
        observed_head=cast(str, values["observed_head"]),
        goal_sha256=cast(str, values["goal_sha256"]),
        document_ref=cast(str, values["document_ref"]),
        schedule_blob_oid=cast(str, values["schedule_blob_oid"]),
        index_blob_oid=cast(str, values["index_blob_oid"]),
        worktree_disposition=cast(str, values["worktree_disposition"]),
        schema_id=cast(str, values["schema_id"]),
    )
    if values != value.to_wire() or payload != encode_goal_phase_future_schedule_repository_reconciliation(value):
        raise GoalPhaseFutureScheduleError("reconciliation digest or encoding is not canonical")
    return value


def goal_phase_future_schedule_definition_closure_ref(value: GoalPhaseFutureScheduleV1) -> str:
    value.__post_init__()
    return "goal-phase-future-schedule-definitions:sha256:" + hashlib.sha256(_canonical({
        "goal_tag": value.goal_tag,
        "lane_key": value.lane_key,
        "definition_bindings": value.to_wire()["definition_bindings"],
    })).hexdigest()


def goal_phase_future_schedule_intent_ref(
    *, before_schedule_ref: str | None, after: GoalPhaseFutureScheduleV1,
) -> str:
    after.__post_init__()
    return "goal-phase-future-schedule-intent:sha256:" + hashlib.sha256(_canonical({
        "before_schedule_ref": before_schedule_ref,
        "after_schedule_ref": after.schedule_ref,
        "changed_path": schedule_path(goal_doc_path=after.goal_doc_path, lane_key=after.lane_key),
    })).hexdigest()


def encode_goal_phase_future_schedule(value: GoalPhaseFutureScheduleV1) -> bytes:
    if type(value) is not GoalPhaseFutureScheduleV1:
        raise TypeError("value must be exact schedule")
    value.__post_init__()
    return _canonical(value.to_wire()) + b"\n"


def decode_goal_phase_future_schedule(payload: bytes) -> GoalPhaseFutureScheduleV1:
    if type(payload) is not bytes:
        raise TypeError("payload must be bytes")
    try:
        raw = cast(object, json.loads(payload, object_pairs_hook=_unique_pairs))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoalPhaseFutureScheduleError("invalid schedule JSON") from error
    if type(raw) is not dict:
        raise GoalPhaseFutureScheduleError("schedule fields are not canonical")
    values = cast(dict[str, object], raw)
    if set(values) != {
        "schema_id", "goal_tag", "goal_doc_path", "lane_key", "definition_bindings",
        "authored_order", "retained_unscheduled", "decision_issue_path",
        "decision_issue_blob_oid", "schedule_ref",
    }:
        raise GoalPhaseFutureScheduleError("schedule fields are not canonical")
    bindings = values["definition_bindings"]
    if type(bindings) is not list:
        raise GoalPhaseFutureScheduleError("definition bindings must be list")
    parsed: list[tuple[str, str]] = []
    for item in cast(list[object], bindings):
        if type(item) is not dict:
            raise GoalPhaseFutureScheduleError("definition binding fields are invalid")
        item_values = cast(dict[str, object], item)
        if set(item_values) != {"phase_key", "definition_ref"}:
            raise GoalPhaseFutureScheduleError("definition binding fields are invalid")
        parsed.append(
            (cast(str, item_values["phase_key"]), cast(str, item_values["definition_ref"]))
        )
    if (
        type(values["authored_order"]) is not list
        or type(values["retained_unscheduled"]) is not list
    ):
        raise GoalPhaseFutureScheduleError("schedule arrays must be lists")
    value = GoalPhaseFutureScheduleV1(
        goal_tag=cast(str, values["goal_tag"]),
        goal_doc_path=cast(str, values["goal_doc_path"]),
        lane_key=cast(str, values["lane_key"]),
        definition_bindings=tuple(parsed),
        authored_order=tuple(cast(list[str], values["authored_order"])),
        retained_unscheduled=tuple(cast(list[str], values["retained_unscheduled"])),
        decision_issue_path=cast(str, values["decision_issue_path"]),
        decision_issue_blob_oid=cast(str, values["decision_issue_blob_oid"]),
        schema_id=cast(str, values["schema_id"]),
    )
    if (
        values["schedule_ref"] != value.schedule_ref
        or payload != encode_goal_phase_future_schedule(value)
    ):
        raise GoalPhaseFutureScheduleError("schedule digest or encoding is not canonical")
    return value


def make_goal_phase_future_schedule(
    *, document: GoalPhaseNativeDocumentV2, goal_doc_path: str, lane_key: str,
    authored_order: tuple[str, ...], decision_issue_path: str, decision_issue_blob_oid: str,
) -> GoalPhaseFutureScheduleV1:
    if type(document) is not GoalPhaseNativeDocumentV2:
        raise TypeError("schedule requires V2 Goal authority")
    bindings = tuple(sorted(
        (definition.coordinate.phase_key, definition.definition_ref)
        for definition in document.definitions if definition.coordinate.lane_key == lane_key
    ))
    if not bindings:
        raise GoalPhaseFutureScheduleError("lane has no definitions")
    retained = tuple(sorted(set(key for key, _ in bindings) - set(authored_order)))
    value = GoalPhaseFutureScheduleV1(
        goal_tag=document.goal_tag, goal_doc_path=goal_doc_path, lane_key=lane_key,
        definition_bindings=bindings, authored_order=authored_order,
        retained_unscheduled=retained, decision_issue_path=decision_issue_path,
        decision_issue_blob_oid=decision_issue_blob_oid,
    )
    status, reason = assess_goal_phase_future_schedule(schedule=value, document=document)
    if status != "current":
        raise GoalPhaseFutureScheduleError(reason or "schedule is not current")
    return value


def assess_goal_phase_future_schedule(
    *, schedule: GoalPhaseFutureScheduleV1, document: GoalPhaseNativeDocumentV2,
) -> tuple[str, str | None]:
    """Recheck membership on each read, including after unrelated V2 mutation."""
    if (
        type(schedule) is not GoalPhaseFutureScheduleV1
        or type(document) is not GoalPhaseNativeDocumentV2
    ):
        raise TypeError("schedule observation requires exact schedule and V2 Goal")
    schedule.__post_init__()
    document.__post_init__()
    if document.goal_tag != schedule.goal_tag:
        return "stale", "goal_identity_changed"
    bindings = tuple(sorted(
        (item.coordinate.phase_key, item.definition_ref)
        for item in document.definitions if item.coordinate.lane_key == schedule.lane_key
    ))
    if bindings != schedule.definition_bindings:
        return "stale", "lane_definitions_changed"
    authored = set(schedule.authored_order)
    for phase in document.operational_bundle.phases:
        if (phase.coordinate.lane_key == schedule.lane_key
                and phase.state in {GoalLanePhaseState.ACTIVE, GoalLanePhaseState.HELD}
                and phase.coordinate.phase_key not in authored):
            return "stale", "unscheduled_operational_phase"
    return "current", None
