"""Neutral creation claim codecs, not issuers or executable decisions.

Profile references are data, never dynamic verifier selection. Decoding any
value here grants no permission, seal, provider enrollment or publication.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import cast

from .identity import fingerprint
from .native_creation_claims import _instant  # pyright: ignore[reportPrivateUsage]
from .native_creation_execution_authority import (
    GoalPhaseExecutionAuthorityV2, decode_goal_genesis_execution_authority,
)
from .native_creation_initial_state import derive_native_creation_initial_facts
from .native_creation_request import (
    NativeGoalCreationRequestV1, decode_native_goal_creation_request,
    make_native_goal_creation_request,
)

AUTHORITY_SCHEMA = "aware.goal.creation-authority-input.v2"
STATE_SCHEMA = "aware.goal.creation-semantic-state.v1"
INTENT_SCHEMA = "aware.goal.creation-intent.v2"
DECISION_SCHEMA = "aware.goal.creation-decision.v2"
_AUTHORITY_FIELDS = {
    "schema_id", "request_ref", "provider_ref", "provider_generation_ref", "authority_profile_ref",
    "namespace_ref", "namespace_revision_ref", "target_locator_ref", "creator_ref", "initial_owner_ref",
    "source_binding_ref", "permission_ref", "identity_absence_ref", "publication_concurrency_ref", "verified_at",
}
_STATE_FIELDS = {
    "schema_id", "goal_tag", "title", "intent", "owner_ref", "status", "hold", "definition_of_done_ref",
    "priority", "locks_ref", "lanes", "definitions", "operational_bundle", "unresolved_dependencies", "source_refs",
}
_INTENT_FIELDS = {"schema_id", "request_ref", "authority_input_ref", "semantic_state_ref"}
_DECISION_FIELDS = {"schema_id", "request", "authority_input", "semantic_state", "intent", "genesis"}
_CONTRACTS = {
    AUTHORITY_SCHEMA: (_AUTHORITY_FIELDS, "authority_input_ref", "goal-creation-authority-input:"),
    STATE_SCHEMA: (_STATE_FIELDS, "semantic_state_ref", "goal-creation-semantic-state:"),
    INTENT_SCHEMA: (_INTENT_FIELDS, "intent_ref", "goal-native-creation-intent:"),
    DECISION_SCHEMA: (_DECISION_FIELDS, "decision_ref", "goal-creation-decision:"),
}
_REFERENCE_DOMAINS = {
    "request_ref": "goal-native-creation-request:",
    "authority_input_ref": "goal-creation-authority-input:",
    "semantic_state_ref": "goal-creation-semantic-state:",
}
_LANE_FACT_FIELDS = {
    "lane_key", "title", "role", "owner_ref", "operational_state", "current_issue_ref",
    "blocker_ref", "hold_authority_refs", "current_work_association_ref",
}


class NeutralCreationContractError(ValueError):
    """Malformed claims/joins, not authenticated refusal or execution authority."""


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _object(value: object, fields: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(cast(dict[str, object], value)) != fields:
        raise NeutralCreationContractError("neutral_creation_fields")
    return cast(dict[str, object], value)


def _token(value: object) -> str:
    if type(value) is not str or not value or re.search(r"[\s|\x00-\x1f\x7f]", value):
        raise NeutralCreationContractError("neutral_creation_token")
    _ = value.encode("utf-8")
    return value


def _ref(value: object, domain: str) -> None:
    if re.fullmatch(re.escape(domain) + r"sha256:[0-9a-f]{64}", _token(value)) is None:
        raise NeutralCreationContractError("neutral_creation_reference")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    body: dict[str, object] = {}
    for key, value in pairs:
        if key in body:
            raise NeutralCreationContractError("neutral_creation_duplicate_field")
        body[key] = value
    return body


def _parse(payload: str) -> object:
    if type(payload) is not str:
        raise NeutralCreationContractError("neutral_creation_payload")
    try:
        return cast(object, json.loads(payload, object_pairs_hook=_pairs))
    except (ValueError, RecursionError) as exc:
        raise NeutralCreationContractError("neutral_creation_json") from exc


def _body(schema: str, fields: dict[str, object]) -> dict[str, object]:
    expected, ref_field, domain = _CONTRACTS[schema]
    fields = _object(fields, expected - {"schema_id"})
    result: dict[str, object] = {"schema_id": schema, **fields}
    result[ref_field] = domain + fingerprint(result)
    return result


def _state(request: NativeGoalCreationRequestV1) -> dict[str, object]:
    return _body(STATE_SCHEMA, derive_native_creation_initial_facts(request))


def _validate_state(body: dict[str, object]) -> None:
    # Standalone decoding reuses the owning authored graph codec. The temporary
    # key is for structural validation only, never returned as an invocation or
    # idempotency identity. A decision separately binds the actual full request.
    if type(body["lanes"]) is not list:
        raise NeutralCreationContractError("neutral_creation_lanes")
    lanes = [_object(lane, _LANE_FACT_FIELDS) for lane in cast(list[object], body["lanes"])]
    bundle = _object(body["operational_bundle"], {"schema_id", "phases", "dependencies"})
    request = make_native_goal_creation_request({
        "idempotency_key": "semantic-codec-validation-only",
        **{field: body[field] for field in (
            "goal_tag", "title", "intent", "owner_ref", "definition_of_done_ref", "priority", "locks_ref",
            "definitions", "unresolved_dependencies",
        )},
        "lanes": [{key: lane[key] for key in ("lane_key", "title", "role", "owner_ref")} for lane in lanes],
        "dependencies": bundle["dependencies"],
    })
    if _json(body) != _json(_state(request)):
        raise NeutralCreationContractError("neutral_creation_initial_state")


def _intent(request_ref: object, authority_ref: object, state_ref: object) -> dict[str, object]:
    fields = {"request_ref": request_ref, "authority_input_ref": authority_ref, "semantic_state_ref": state_ref}
    for key, value in fields.items():
        _ref(value, _REFERENCE_DOMAINS[key])
    return _body(INTENT_SCHEMA, fields)


def _validate_decision(body: dict[str, object]) -> None:
    request = decode_native_goal_creation_request(_json(body["request"]))
    authority = _validate(body["authority_input"], AUTHORITY_SCHEMA)
    state = _validate(body["semantic_state"], STATE_SCHEMA)
    intent = _validate(body["intent"], INTENT_SCHEMA)
    genesis = decode_goal_genesis_execution_authority(_json(body["genesis"]))
    if authority["request_ref"] != request.request_ref or authority["initial_owner_ref"] != request.to_wire()["owner_ref"]:
        raise NeutralCreationContractError("neutral_creation_request_authority_join")
    if _json(state) != _json(_state(request)):
        raise NeutralCreationContractError("neutral_creation_request_state_join")
    expected_intent = _intent(request.request_ref, authority["authority_input_ref"], state["semantic_state_ref"])
    if _json(intent) != _json(expected_intent) or genesis.creation_intent_ref != intent["intent_ref"]:
        raise NeutralCreationContractError("neutral_creation_intent_genesis_join")


def _validate(value: object, expected_schema: str | None = None) -> dict[str, object]:
    if type(value) is not dict:
        raise NeutralCreationContractError("neutral_creation_object")
    schema = _token(cast(dict[str, object], value).get("schema_id"))
    if schema not in _CONTRACTS or expected_schema is not None and schema != expected_schema:
        raise NeutralCreationContractError("neutral_creation_schema")
    fields, ref_field, domain = _CONTRACTS[schema]
    body = _object(cast(dict[str, object], value), fields | {ref_field})
    if schema == AUTHORITY_SCHEMA:
        for key, item in body.items():
            _ = _token(item)
            if key in _REFERENCE_DOMAINS:
                _ref(item, _REFERENCE_DOMAINS[key])
        _instant(body["verified_at"])
        if body["creator_ref"] != body["initial_owner_ref"]:
            raise NeutralCreationContractError("neutral_creation_creator_owner_join")
    elif schema == STATE_SCHEMA:
        _validate_state(body)
    elif schema == INTENT_SCHEMA:
        if _json(body) != _json(_intent(body["request_ref"], body["authority_input_ref"], body["semantic_state_ref"])):
            raise NeutralCreationContractError("neutral_creation_intent_identity")
    else:
        _validate_decision(body)
    _ref(body[ref_field], domain)
    expected_ref = domain + fingerprint({key: item for key, item in body.items() if key != ref_field})
    if body[ref_field] != expected_ref:
        raise NeutralCreationContractError("neutral_creation_digest")
    return body


def _checked(value: object, expected_schema: str | None = None) -> dict[str, object]:
    try:
        return _validate(value, expected_schema)
    except (ValueError, TypeError, RecursionError, OverflowError) as exc:
        raise NeutralCreationContractError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class NeutralGoalCreationClaim:
    """Detached, publicly constructible data. Explicitly no verifier output."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not NeutralGoalCreationClaim:
            raise NeutralCreationContractError("neutral_creation_type")
        return _checked(_parse(self.canonical_body))

    @property
    def reference(self) -> str:
        body = self.to_wire()
        return cast(str, body[_CONTRACTS[cast(str, body["schema_id"])][1]])


def decode_neutral_goal_creation_claim(payload: str, *, expected_schema: str | None = None) -> NeutralGoalCreationClaim:
    return NeutralGoalCreationClaim(_json(_checked(_parse(payload), expected_schema)))


def encode_neutral_goal_creation_claim(value: NeutralGoalCreationClaim) -> str:
    if type(value) is not NeutralGoalCreationClaim:
        raise NeutralCreationContractError("neutral_creation_type")
    return _json(value.to_wire())


def make_goal_creation_authority_input_claim(fields: dict[str, object]) -> NeutralGoalCreationClaim:
    """Author consistency claims; profile text cannot enroll a provider."""
    return NeutralGoalCreationClaim(_json(_checked(_body(AUTHORITY_SCHEMA, fields))))


def make_goal_creation_semantic_state(request: NativeGoalCreationRequestV1) -> NeutralGoalCreationClaim:
    return NeutralGoalCreationClaim(_json(_checked(_state(request))))


def make_goal_creation_intent_claim(request_ref: str, authority_input_ref: str, semantic_state_ref: str) -> NeutralGoalCreationClaim:
    return NeutralGoalCreationClaim(_json(_checked(_intent(request_ref, authority_input_ref, semantic_state_ref))))


def make_goal_creation_decision_claim(request: NativeGoalCreationRequestV1, authority: NeutralGoalCreationClaim) -> NeutralGoalCreationClaim:
    """NOT decide_native_goal_creation_v2: no independently qualified input."""
    if type(request) is not NativeGoalCreationRequestV1 or type(authority) is not NeutralGoalCreationClaim:
        raise NeutralCreationContractError("neutral_creation_operand_type")
    req = request.to_wire()
    auth = _checked(authority.to_wire(), AUTHORITY_SCHEMA)
    state = _state(request)
    intent = _intent(request.request_ref, auth["authority_input_ref"], state["semantic_state_ref"])
    genesis = GoalPhaseExecutionAuthorityV2(creation_intent_ref=cast(str, intent["intent_ref"]))
    body = _body(DECISION_SCHEMA, {"request": req, "authority_input": auth, "semantic_state": state,
                                  "intent": intent, "genesis": genesis.to_wire()})
    return NeutralGoalCreationClaim(_json(_checked(body)))
