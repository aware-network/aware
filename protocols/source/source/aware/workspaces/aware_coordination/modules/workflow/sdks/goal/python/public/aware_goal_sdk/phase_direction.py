"""Provider-neutral transport for read-only native Phase direction.

The neutral Goal runtime issues and evaluates the receipts. This module only
checks the portable request and result envelope; it never decides currentness.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Protocol, TypeAlias, cast

_MEMBER = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_GOAL = re.compile(r"^goal/\d{4}-\d{2}-\d{2}/[a-z0-9]+(?:-[a-z0-9]+)*$")
_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT = re.compile(r"^(?:git:|repository-commit:)?[0-9a-f]{40}$")
_BLOB = re.compile(r"^(?:git-blob:)?(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_REASON_ORDER = (
    "phase_unavailable", "document_advanced", "definition_changed",
    "gate_changed", "compatibility_profile_changed", "goal_digest_changed",
    "goal_blob_changed", "source_revision_lineage_unproven",
)
_RECEIPT_FIELDS = {
    "schema_id", "effect_profile", "coordinate", "ordinal", "definition_ref",
    "gate_digest", "document_ref", "compatibility_profile", "source", "pursuit_ref",
}
_CURRENTNESS_FIELDS = {
    "schema_id", "effect_profile", "expected_pursuit_ref", "observed_pursuit_ref",
    "status", "projection_currentness", "replay_disposition", "reasons",
    "expected_document_ref", "observed_document_ref",
    "expected_source_revision_ref", "observed_source_revision_ref",
    "source_revision_lineage", "source_revision_lineage_ref", "currentness_ref",
}

GoalPhaseDirectionReceiptV1: TypeAlias = dict[str, object]
GoalPhaseDirectionCurrentnessV1: TypeAlias = dict[str, object]


class GoalPhaseDirectionError(ValueError):
    """The provider or portable Phase-direction transport refused a call."""


def _object(value: object, fields: set[str], name: str) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{name} fields are not canonical")
    result = cast(dict[str, object], value)
    if set(result) != fields:
        raise ValueError(f"{name} fields are not canonical")
    return result


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be non-empty text")
    return value


def _pattern(value: object, pattern: re.Pattern[str], name: str) -> str:
    result = _text(value, name)
    if pattern.fullmatch(result) is None:
        raise ValueError(f"{name} is not canonical")
    return result


def _ref(value: object, domain: str, name: str) -> str:
    return _pattern(
        value, re.compile(rf"^{re.escape(domain)}:sha256:[0-9a-f]{{64}}$"), name
    )


def _canonical_ref(body: Mapping[str, object], domain: str) -> str:
    encoded = json.dumps(
        body, ensure_ascii=True, separators=(",", ":"), sort_keys=True, allow_nan=False
    ).encode("utf-8")
    return f"{domain}:sha256:" + hashlib.sha256(encoded).hexdigest()


def _receipt(value: object) -> dict[str, object]:
    receipt = _object(value, _RECEIPT_FIELDS, "direction receipt")
    if _text(receipt["schema_id"], "schema_id") != "aware.goal.phase-pursuit.v1":
        raise ValueError("direction receipt schema differs")
    if _text(receipt["effect_profile"], "effect_profile") != "direction_only_non_authorizing":
        raise ValueError("direction receipt effect differs")
    coordinate = _object(
        receipt["coordinate"], {"goal_tag", "lane_key", "phase_key"}, "coordinate"
    )
    _ = _pattern(coordinate["goal_tag"], _GOAL, "goal_tag")
    for name in ("lane_key", "phase_key"):
        member = _pattern(coordinate[name], _MEMBER, name)
        if len(member.encode("utf-8")) > 96:
            raise ValueError(f"{name} exceeds portable Phase key length")
    if type(receipt["ordinal"]) is not int or receipt["ordinal"] < 1:
        raise ValueError("ordinal must be a positive integer")
    _ = _ref(receipt["definition_ref"], "goal-phase-definition", "definition_ref")
    _ = _pattern(receipt["gate_digest"], _SHA, "gate_digest")
    _ = _ref(receipt["document_ref"], "goal-phase-document", "document_ref")
    _ = _text(receipt["compatibility_profile"], "compatibility_profile")
    source = _object(
        receipt["source"],
        {"repository_revision_ref", "goal_sha256", "goal_blob_oid"},
        "source",
    )
    _ = _pattern(source["repository_revision_ref"], _COMMIT, "repository_revision_ref")
    _ = _pattern(source["goal_sha256"], _SHA, "goal_sha256")
    _ = _pattern(source["goal_blob_oid"], _BLOB, "goal_blob_oid")
    _ = _ref(receipt["pursuit_ref"], "goal-phase-pursuit", "pursuit_ref")
    body = {key: item for key, item in receipt.items() if key != "pursuit_ref"}
    if receipt["pursuit_ref"] != _canonical_ref(body, "goal-phase-pursuit"):
        raise ValueError("direction receipt reference is not canonical")
    return receipt


def _currentness(value: object, expected: dict[str, object]) -> dict[str, object]:
    currentness = _object(value, _CURRENTNESS_FIELDS, "direction currentness")
    if _text(currentness["schema_id"], "schema_id") != "aware.goal.phase-pursuit-currentness.v1":
        raise ValueError("direction currentness schema differs")
    if _text(currentness["effect_profile"], "effect_profile") != "read_only_non_authorizing":
        raise ValueError("direction currentness effect differs")
    if _ref(
        currentness["expected_pursuit_ref"], "goal-phase-pursuit", "expected_pursuit_ref"
    ) != expected["pursuit_ref"]:
        raise ValueError("currentness differs from retained direction receipt")
    observed_ref = currentness["observed_pursuit_ref"]
    if observed_ref is not None:
        _ = _ref(observed_ref, "goal-phase-pursuit", "observed_pursuit_ref")
    status = _text(currentness["status"], "status")
    projection = _text(currentness["projection_currentness"], "projection_currentness")
    replay = _text(currentness["replay_disposition"], "replay_disposition")
    lineage = _text(currentness["source_revision_lineage"], "source_revision_lineage")
    if status not in {"current", "stale", "ambiguous"}:
        raise ValueError("currentness status is invalid")
    if lineage not in {"equal", "descendant", "unproven"}:
        raise ValueError("currentness lineage is invalid")
    if projection != {"equal": "current", "descendant": "advanced", "unproven": "unproven"}[lineage]:
        raise ValueError("projection and lineage disagree")
    expected_replay = (
        "refuse" if status != "current" else
        ("reobserved_unchanged" if lineage == "descendant" else "exact")
    )
    if replay != expected_replay:
        raise ValueError("status and replay disposition disagree")
    reasons_value = currentness["reasons"]
    if type(reasons_value) is not list:
        raise ValueError("reasons must be exact text list")
    reasons_items = cast(list[object], reasons_value)
    if any(type(reason) is not str for reason in reasons_items):
        raise ValueError("reasons must be exact text list")
    reasons = cast(list[str], reasons_value)
    if (
        any(reason not in _REASON_ORDER for reason in reasons)
        or reasons != sorted(set(reasons), key=_REASON_ORDER.index)
        or (status == "current") != (not reasons)
    ):
        raise ValueError("status and reasons disagree")
    semantic_reasons = [reason for reason in reasons if reason != "source_revision_lineage_unproven"]
    if ("phase_unavailable" in reasons) != (observed_ref is None):
        raise ValueError("observed receipt and Phase availability disagree")
    if "phase_unavailable" in reasons and len(semantic_reasons) != 1:
        raise ValueError("Phase-unavailable reasons are contradictory")
    if lineage == "unproven":
        if not reasons or reasons[-1] != "source_revision_lineage_unproven":
            raise ValueError("unproven lineage reason is missing")
        if status != ("stale" if semantic_reasons else "ambiguous"):
            raise ValueError("unproven lineage status disagrees")
    elif "source_revision_lineage_unproven" in reasons or status == "ambiguous":
        raise ValueError("proven lineage cannot be ambiguous")
    elif status == "stale" and not semantic_reasons:
        raise ValueError("stale result lacks a semantic reason")
    _ = _ref(currentness["expected_document_ref"], "goal-phase-document", "expected_document_ref")
    _ = _ref(currentness["observed_document_ref"], "goal-phase-document", "observed_document_ref")
    if currentness["expected_document_ref"] != expected["document_ref"]:
        raise ValueError("expected document differs from retained receipt")
    if observed_ref is not None and (
        (currentness["expected_document_ref"] != currentness["observed_document_ref"])
        != ("document_advanced" in reasons)
    ):
        raise ValueError("document reason contradicts document references")
    expected_source = cast(dict[str, object], expected["source"])
    expected_revision = _pattern(
        currentness["expected_source_revision_ref"], _COMMIT, "expected_source_revision_ref"
    )
    observed_revision = _pattern(
        currentness["observed_source_revision_ref"], _COMMIT, "observed_source_revision_ref"
    )
    if expected_revision != expected_source["repository_revision_ref"]:
        raise ValueError("expected source differs from retained receipt")
    if (expected_revision == observed_revision) != (lineage == "equal"):
        raise ValueError("lineage relation contradicts revisions")
    if status == "current" and lineage == "equal" and observed_ref != expected["pursuit_ref"]:
        raise ValueError("exact currentness has a different observed receipt")
    lineage_body: dict[str, object] = {
        "schema_id": "aware.goal.phase-revision-lineage.v1",
        "authority_profile": "repository_revision_lineage_v1",
        "expected_revision_ref": expected_revision,
        "observed_revision_ref": observed_revision,
        "relation": lineage,
    }
    _ = _ref(currentness["source_revision_lineage_ref"], "goal-phase-revision-lineage", "source_revision_lineage_ref")
    if currentness["source_revision_lineage_ref"] != _canonical_ref(
        lineage_body, "goal-phase-revision-lineage"
    ):
        raise ValueError("lineage reference is not canonical")
    _ = _ref(currentness["currentness_ref"], "goal-phase-pursuit-currentness", "currentness_ref")
    body = {key: item for key, item in currentness.items() if key != "currentness_ref"}
    if currentness["currentness_ref"] != _canonical_ref(body, "goal-phase-pursuit-currentness"):
        raise ValueError("currentness reference is not canonical")
    return currentness


@dataclass(frozen=True, slots=True)
class GoalPhaseDirectionObserveRequestV1:
    goal_path: str
    goal_tag: str
    lane_key: str
    phase_key: str

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseDirectionObserveRequestV1:
            raise TypeError("direction request must be exact")
        if type(self.goal_path) is not str or not self.goal_path:
            raise ValueError("goal_path must be nonempty")
        if type(self.goal_tag) is not str or _GOAL.fullmatch(self.goal_tag) is None:
            raise ValueError("goal_tag is invalid")
        for key in (self.lane_key, self.phase_key):
            if type(key) is not str or _MEMBER.fullmatch(key) is None or len(key) > 96:
                raise ValueError("lane/phase key is invalid")


@dataclass(frozen=True, slots=True)
class GoalPhaseDirectionCurrentnessRequestV1:
    goal_path: str
    expected_receipt: Mapping[str, object]

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseDirectionCurrentnessRequestV1:
            raise TypeError("currentness request must be exact")
        if type(self.goal_path) is not str or not self.goal_path:
            raise ValueError("goal_path must be nonempty")
        if type(self.expected_receipt) is not dict:
            raise TypeError("expected_receipt must be an exact object")


class GoalPhaseDirectionProvider(Protocol):
    def observe_phase_direction(
        self, request: GoalPhaseDirectionObserveRequestV1
    ) -> GoalPhaseDirectionReceiptV1: ...

    def verify_phase_direction_currentness(
        self, request: GoalPhaseDirectionCurrentnessRequestV1
    ) -> GoalPhaseDirectionCurrentnessV1: ...


@dataclass(frozen=True, slots=True)
class GoalPhaseDirectionClient:
    provider: GoalPhaseDirectionProvider

    def observe_phase_direction(
        self, request: GoalPhaseDirectionObserveRequestV1
    ) -> GoalPhaseDirectionReceiptV1:
        try:
            request.__post_init__()
            coordinate = {
                "goal_tag": request.goal_tag,
                "lane_key": request.lane_key,
                "phase_key": request.phase_key,
            }
            result = self.provider.observe_phase_direction(request)
            receipt = _receipt(result)
            if receipt["coordinate"] != coordinate:
                raise ValueError("direction receipt coordinate differs from request")
            return receipt
        except (TypeError, ValueError) as error:
            raise GoalPhaseDirectionError(str(error)) from error

    def verify_phase_direction_currentness(
        self, request: GoalPhaseDirectionCurrentnessRequestV1
    ) -> GoalPhaseDirectionCurrentnessV1:
        try:
            request.__post_init__()
            expected = deepcopy(_receipt(request.expected_receipt))
            result = self.provider.verify_phase_direction_currentness(request)
            return _currentness(result, expected)
        except (TypeError, ValueError) as error:
            raise GoalPhaseDirectionError(str(error)) from error
