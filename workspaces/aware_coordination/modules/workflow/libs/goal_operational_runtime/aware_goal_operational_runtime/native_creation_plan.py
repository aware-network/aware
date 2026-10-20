"""Strict creation intent/initial-plan claims, never an admitted creation plan.

Recompute the initial state from authored inputs and consistency-checked claims.
No source resolver, provider registration, renderer, writer or permission lives
here. The later plan_native_goal_creation entrance requires provider issuance;
these publicly constructible codec values cannot satisfy that entrance.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import cast

from .identity import fingerprint
from .native_creation_claims import (
    NativeCreationClaimV1, check_native_creation_context_claims,
    decode_native_creation_claim,
)
from .native_creation_execution_authority import GoalPhaseExecutionAuthorityV2
from .native_creation_initial_state import derive_native_creation_initial_facts
from .native_creation_request import (
    NativeGoalCreationRequestV1, decode_native_goal_creation_request,
)

INTENT_SCHEMA = "aware.goal.native-creation-intent.v1"
PLAN_SCHEMA = "aware.goal.native-creation-plan.v1"
INITIAL_STATE_SCHEMA = "aware.goal.native-creation-initial-state.v1"
_INTENT_FIELDS = {"schema_id", "request_ref", "context_ref", "intent_ref"}
_CLAIM_FIELDS = ("context", "grant", "source_admission", "identity_absence", "namespace_exclusion")
_PLAN_FIELDS = {"schema_id", "request", *_CLAIM_FIELDS, "intent", "initial_state", "plan_ref"}


class NativeGoalCreationPlanError(ValueError):
    """Invalid contract or consistency join, not a provider verdict."""


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _object(value: object, fields: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(cast(dict[str, object], value)) != fields:
        raise NativeGoalCreationPlanError("creation_plan_fields")
    return cast(dict[str, object], value)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise NativeGoalCreationPlanError("creation_plan_duplicate_field")
        result[key] = value
    return result


def _parse(payload: str) -> object:
    if type(payload) is not str:
        raise NativeGoalCreationPlanError("creation_plan_payload")
    try:
        return cast(object, json.loads(payload, object_pairs_hook=_pairs))
    except (ValueError, RecursionError) as exc:
        raise NativeGoalCreationPlanError("creation_plan_json") from exc


def _ref(value: object, domain: str) -> None:
    if type(value) is not str or re.fullmatch(re.escape(domain) + r"sha256:[0-9a-f]{64}", value) is None:
        raise NativeGoalCreationPlanError("creation_plan_reference")


def _intent(request_ref: object, context_ref: object) -> dict[str, object]:
    _ref(request_ref, "goal-native-creation-request:")
    _ref(context_ref, "goal-native-creation-context:")
    body = {"schema_id": INTENT_SCHEMA, "request_ref": request_ref, "context_ref": context_ref}
    return {**body, "intent_ref": "goal-native-creation-intent:" + fingerprint(body)}


def _validate_intent(value: object) -> dict[str, object]:
    body = _object(value, _INTENT_FIELDS)
    expected = _intent(body["request_ref"], body["context_ref"])
    if _json(body) != _json(expected):
        raise NativeGoalCreationPlanError("creation_intent_identity")
    return body


def _initial_state(request: dict[str, object], intent: dict[str, object]) -> dict[str, object]:
    """Pure initial-state law; claims do not establish current authority."""
    intent_ref = cast(str, intent["intent_ref"])
    return {
        "schema_id": INITIAL_STATE_SCHEMA,
        **derive_native_creation_initial_facts(decode_native_goal_creation_request(_json(request))),
        "execution_authority": GoalPhaseExecutionAuthorityV2(creation_intent_ref=intent_ref).to_wire(),
    }


def _validate_plan(value: object) -> dict[str, object]:
    body = _object(value, _PLAN_FIELDS)
    if body["schema_id"] != PLAN_SCHEMA:
        raise NativeGoalCreationPlanError("creation_plan_schema")
    request = decode_native_goal_creation_request(_json(body["request"]))
    claims = tuple(decode_native_creation_claim(_json(body[field])) for field in _CLAIM_FIELDS)
    check_native_creation_context_claims(*claims)
    ctx = claims[0].to_wire()
    req = request.to_wire()
    if ctx["request_ref"] != request.request_ref or ctx["initial_owner_ref"] != req["owner_ref"]:
        raise NativeGoalCreationPlanError("creation_plan_request_context_join")
    if claims[3].to_wire()["goal_tag"] != req["goal_tag"]:
        raise NativeGoalCreationPlanError("creation_plan_absence_goal_join")
    intent = _validate_intent(body["intent"])
    if intent != _intent(request.request_ref, claims[0].reference):
        raise NativeGoalCreationPlanError("creation_plan_intent_join")
    # Exact canonical bytes avoid bool/int equality and reject every extra or
    # substituted nested initial fact, even with a newly computed outer digest.
    if _json(body["initial_state"]) != _json(_initial_state(req, intent)):
        raise NativeGoalCreationPlanError("creation_plan_initial_state")
    expected_ref = "goal-native-creation-plan:" + fingerprint({key: item for key, item in body.items() if key != "plan_ref"})
    if body["plan_ref"] != expected_ref:
        raise NativeGoalCreationPlanError("creation_plan_digest")
    return body


def _checked_plan(value: object) -> dict[str, object]:
    try:
        return _validate_plan(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise NativeGoalCreationPlanError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class NativeGoalCreationIntentV1:
    """Content identity only; no source or creator is authenticated here."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not NativeGoalCreationIntentV1:
            raise NativeGoalCreationPlanError("creation_intent_type")
        return _validate_intent(_parse(self.canonical_body))

    @property
    def intent_ref(self) -> str:
        return cast(str, self.to_wire()["intent_ref"])


@dataclass(frozen=True, slots=True)
class NativeGoalCreationPlanClaimV1:
    """Detached plan claims; expressly not VerifiedNativeGoalCreationContextV1."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not NativeGoalCreationPlanClaimV1:
            raise NativeGoalCreationPlanError("creation_plan_type")
        return _checked_plan(_parse(self.canonical_body))

    @property
    def plan_ref(self) -> str:
        return cast(str, self.to_wire()["plan_ref"])


def make_native_goal_creation_intent(request_ref: str, context_ref: str) -> NativeGoalCreationIntentV1:
    return NativeGoalCreationIntentV1(_json(_intent(request_ref, context_ref)))


def decode_native_goal_creation_intent(payload: str) -> NativeGoalCreationIntentV1:
    return NativeGoalCreationIntentV1(_json(_validate_intent(_parse(payload))))


def encode_native_goal_creation_intent(value: NativeGoalCreationIntentV1) -> str:
    if type(value) is not NativeGoalCreationIntentV1:
        raise NativeGoalCreationPlanError("creation_intent_type")
    return _json(value.to_wire())


def make_native_goal_creation_plan_claim(
    request: NativeGoalCreationRequestV1, context: NativeCreationClaimV1,
    grant: NativeCreationClaimV1, source_admission: NativeCreationClaimV1,
    identity_absence: NativeCreationClaimV1, namespace_exclusion: NativeCreationClaimV1,
) -> NativeGoalCreationPlanClaimV1:
    """Construct reproducible claims, NOT the authority-requiring planner."""
    if type(request) is not NativeGoalCreationRequestV1:
        raise NativeGoalCreationPlanError("creation_plan_request_type")
    claims = (context, grant, source_admission, identity_absence, namespace_exclusion)
    check_native_creation_context_claims(*claims)
    intent = _intent(request.request_ref, context.reference)
    body: dict[str, object] = {
        "schema_id": PLAN_SCHEMA, "request": request.to_wire(),
        **{key: claim.to_wire() for key, claim in zip(_CLAIM_FIELDS, claims, strict=True)},
        "intent": intent, "initial_state": _initial_state(request.to_wire(), intent),
    }
    body["plan_ref"] = "goal-native-creation-plan:" + fingerprint(body)
    return NativeGoalCreationPlanClaimV1(_json(_checked_plan(body)))


def decode_native_goal_creation_plan_claim(payload: str) -> NativeGoalCreationPlanClaimV1:
    return NativeGoalCreationPlanClaimV1(_json(_checked_plan(_parse(payload))))


def encode_native_goal_creation_plan_claim(value: NativeGoalCreationPlanClaimV1) -> str:
    if type(value) is not NativeGoalCreationPlanClaimV1:
        raise NativeGoalCreationPlanError("creation_plan_type")
    return _json(value.to_wire())
