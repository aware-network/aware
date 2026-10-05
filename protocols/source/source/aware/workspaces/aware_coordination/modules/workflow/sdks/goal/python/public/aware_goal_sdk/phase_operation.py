"""Portable request/result for the read-only native-V2 Goal Phase operation.

The provider, not the caller, resolves repository and compatibility authority.
This first public kind never admits a Goal delta or emits an event.
"""

from __future__ import annotations

import re
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, TypeAlias, cast

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_DOCUMENT = re.compile(r"^goal-phase-document:sha256:[0-9a-f]{64}$")
_MEMBER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_GOAL = re.compile(r"^goal/\d{4}-\d{2}-\d{2}/[a-z0-9]+(?:-[a-z0-9]+)*$")
_REFUSED_FIELDS = {
    "schema_id", "operation_kind", "status", "authority_profile",
    "effect_profile", "event_effect", "dispatch_effect", "source_locator_ref",
    "coordinate", "source_revision_ref", "goal_sha256", "eligibility",
    "reasons", "decision_ref",
}
_OBSERVED_FIELDS = _REFUSED_FIELDS | {
    "source_identity_ref", "native_document_ref", "gate_digest",
    "goal_authority_ref", "lane_authority_ref", "observation_coverage",
    "phase_state", "projection_health", "dependency_gate",
    "unresolved_dependency_keys",
}

# The portable result remains the exact decoded JSON transport. Neutral Goal
# runtime, not this SDK type, decides eligibility from qualified authority.
GoalPhaseObserveEligibilityResultV1: TypeAlias = dict[str, object]


class GoalPhaseObserveEligibilityError(ValueError):
    """The selected provider or portable eligibility transport refused a call."""


@dataclass(frozen=True, slots=True)
class GoalPhaseObserveEligibilityRequestV1:
    source_locator_ref: str
    goal_tag: str
    lane_key: str
    phase_key: str
    expected_goal_sha256: str
    expected_native_document_ref: str
    expected_gate_digest: str
    operation_kind: str = "observe_eligibility"
    schema_id: str = "aware.goal.phase-operation-request.v1"

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseObserveEligibilityRequestV1:
            raise TypeError("request type must be exact")
        if (
            self.operation_kind != "observe_eligibility"
            or self.schema_id != "aware.goal.phase-operation-request.v1"
        ):
            raise ValueError("unsupported Goal Phase operation")
        if (type(self.source_locator_ref) is not str or not self.source_locator_ref
            or any(character in self.source_locator_ref for character in ("\n", "\r"))):
            raise ValueError("source_locator_ref must be a source token")
        if type(self.goal_tag) is not str or _GOAL.fullmatch(self.goal_tag) is None:
            raise ValueError("goal_tag must be an exact Goal tag")
        for name in ("lane_key", "phase_key"):
            value = getattr(self, name)
            if type(value) is not str or _MEMBER.fullmatch(value) is None:
                raise ValueError(f"{name} must be kebab-case")
        if (
            type(self.expected_goal_sha256) is not str
            or _DIGEST.fullmatch(self.expected_goal_sha256) is None
        ):
            raise ValueError("expected_goal_sha256 must be qualified SHA-256")
        if (
            type(self.expected_native_document_ref) is not str
            or _DOCUMENT.fullmatch(self.expected_native_document_ref) is None
        ):
            raise ValueError("expected_native_document_ref must be a native document ref")
        if (
            type(self.expected_gate_digest) is not str
            or _DIGEST.fullmatch(self.expected_gate_digest) is None
        ):
            raise ValueError("expected_gate_digest must be qualified SHA-256")

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "operation_kind": self.operation_kind,
            "source_locator_ref": self.source_locator_ref,
            "goal_tag": self.goal_tag,
            "lane_key": self.lane_key,
            "phase_key": self.phase_key,
            "expected_goal_sha256": self.expected_goal_sha256,
            "expected_native_document_ref": self.expected_native_document_ref,
            "expected_gate_digest": self.expected_gate_digest,
        }


def decode_goal_phase_observe_eligibility_request(
    payload: Mapping[str, object],
) -> GoalPhaseObserveEligibilityRequestV1:
    """Reject unknown fields and non-string or noncanonical request coordinates."""

    if type(payload) is not dict or set(payload) != {
        "schema_id", "operation_kind", "source_locator_ref", "goal_tag", "lane_key",
        "phase_key", "expected_goal_sha256", "expected_native_document_ref",
        "expected_gate_digest",
    }:
        raise ValueError("eligibility request fields differ from schema")
    if any(type(value) is not str for value in payload.values()):
        raise TypeError("eligibility request fields must be exact strings")
    values = cast(dict[str, str], payload)
    request = GoalPhaseObserveEligibilityRequestV1(
        source_locator_ref=values["source_locator_ref"],
        goal_tag=values["goal_tag"],
        lane_key=values["lane_key"],
        phase_key=values["phase_key"],
        expected_goal_sha256=values["expected_goal_sha256"],
        expected_native_document_ref=values["expected_native_document_ref"],
        expected_gate_digest=values["expected_gate_digest"],
        operation_kind=values["operation_kind"],
        schema_id=values["schema_id"],
    )
    if request.to_wire() != payload:
        raise ValueError("eligibility request is not canonical")
    return request


class GoalPhaseObserveEligibilityProvider(Protocol):
    def observe_eligibility(
        self, request: GoalPhaseObserveEligibilityRequestV1
    ) -> GoalPhaseObserveEligibilityResultV1: ...


@dataclass(frozen=True, slots=True)
class GoalPhaseOperationClient:
    provider: GoalPhaseObserveEligibilityProvider

    def observe_eligibility(
        self, request: GoalPhaseObserveEligibilityRequestV1
    ) -> GoalPhaseObserveEligibilityResultV1:
        try:
            if type(request) is not GoalPhaseObserveEligibilityRequestV1:
                raise TypeError("request must be exact GoalPhaseObserveEligibilityRequestV1")
            request.__post_init__()
            return decode_goal_phase_observe_eligibility_result(
                self.provider.observe_eligibility(request), request=request
            )
        except (TypeError, ValueError) as error:
            raise GoalPhaseObserveEligibilityError(str(error)) from error


def issue_goal_phase_eligibility_decision_ref(body: Mapping[str, object]) -> str:
    """Content integrity only; repository authority remains provider-owned."""

    if "decision_ref" in body:
        raise ValueError("decision body cannot contain its own reference")
    encoded = json.dumps(
        body, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "goal-phase-eligibility-observation:sha256:" + hashlib.sha256(encoded).hexdigest()


def decode_goal_phase_observe_eligibility_result(
    payload: Mapping[str, object],
    *,
    request: GoalPhaseObserveEligibilityRequestV1,
) -> GoalPhaseObserveEligibilityResultV1:
    """Strict transport check; it does not replace committed-source verification."""

    if type(request) is not GoalPhaseObserveEligibilityRequestV1:
        raise TypeError("request must be exact GoalPhaseObserveEligibilityRequestV1")
    request.__post_init__()
    if type(payload) is not dict:
        raise TypeError("eligibility result must be an exact JSON object")
    status = payload.get("status")
    if type(status) is not str or status not in {"observed", "refused"}:
        raise ValueError("eligibility status is unsupported")
    expected_keys = _OBSERVED_FIELDS if status == "observed" else _REFUSED_FIELDS
    if set(payload) != expected_keys:
        raise ValueError("eligibility result fields differ from schema")
    constants = {
        "schema_id": "aware.goal.phase-operation-result.v1",
        "operation_kind": "observe_eligibility",
        "authority_profile": "phase_native_operational_v1",
        "effect_profile": "read_only_non_authorizing",
        "event_effect": "none",
        "dispatch_effect": "none",
        "source_locator_ref": request.source_locator_ref,
    }
    if any(
        type(payload[name]) is not str or payload[name] != value
        for name, value in constants.items()
    ):
        raise ValueError("eligibility result effect, profile, or path differs")
    if type(payload["coordinate"]) is not dict or payload["coordinate"] != {
        "goal_tag": request.goal_tag,
        "lane_key": request.lane_key,
        "phase_key": request.phase_key,
    }:
        raise ValueError("eligibility coordinate differs")
    revision = payload["source_revision_ref"]
    if type(revision) is not str or not revision:
        raise ValueError("eligibility source revision is missing")
    digest = payload["goal_sha256"]
    if type(digest) is not str or _DIGEST.fullmatch(digest) is None:
        raise ValueError("eligibility Goal digest is malformed")
    reasons = payload["reasons"]
    if (
        type(reasons) is not list
        or any(type(item) is not str or not item for item in reasons)
        or reasons != sorted(set(reasons))
    ):
        raise ValueError("eligibility reasons are not canonical")
    if status == "refused":
        if payload["eligibility"] != "refused" or not reasons:
            raise ValueError("refused eligibility needs a reason")
    else:
        if digest != request.expected_goal_sha256:
            raise ValueError("observed Goal digest differs from request")
        if (
            payload["native_document_ref"] != request.expected_native_document_ref
            or payload["gate_digest"] != request.expected_gate_digest
        ):
            raise ValueError("observed native document or Gate differs from request")
        source_identity = payload["source_identity_ref"]
        if type(source_identity) is not str or not source_identity:
            raise ValueError("source identity is missing")
        for name in ("goal_authority_ref", "lane_authority_ref"):
            if type(payload[name]) is not str or not payload[name]:
                raise ValueError(f"{name} is missing")
        for name in ("observation_coverage", "phase_state", "projection_health", "eligibility"):
            if type(payload[name]) is not str or not payload[name]:
                raise ValueError(f"{name} must be a nonempty token")
        gate = payload["dependency_gate"]
        if type(gate) is not dict or set(gate) != {
            "state", "incoming_count", "dependency_keys", "satisfied", "pending",
            "not_evaluated", "stale", "unresolved", "rejected",
        }:
            raise ValueError("dependency gate wire is not canonical")
        keys = gate["dependency_keys"]
        if (
            type(keys) is not list
            or any(type(item) is not str for item in keys)
            or keys != sorted(set(keys))
        ):
            raise ValueError("dependency keys are not canonical")
        if type(gate["incoming_count"]) is not int or gate["incoming_count"] != len(keys):
            raise ValueError("dependency count is not canonical")
        if type(gate["state"]) is not str or not gate["state"]:
            raise ValueError("dependency gate state is missing")
        for name in ("satisfied", "pending", "not_evaluated", "stale", "unresolved", "rejected"):
            if type(gate[name]) is not list or any(type(item) is not str for item in gate[name]):
                raise ValueError(f"{name} must be an exact string list")
        unresolved = payload["unresolved_dependency_keys"]
        if (
            type(unresolved) is not list
            or any(type(item) is not str for item in unresolved)
            or unresolved != sorted(set(unresolved))
        ):
            raise ValueError("unresolved dependency keys are not canonical")
    body = {key: value for key, value in payload.items() if key != "decision_ref"}
    if payload["decision_ref"] != issue_goal_phase_eligibility_decision_ref(body):
        raise ValueError("eligibility decision reference differs")
    return dict(payload)
