"""Acyclic planning origin and exact carrier claims, never execution authority.

Reuse the accepted request/document/renderer laws. Concrete owners separately
qualify complete source and permission referenced by these claims; decoding a
coherent plan does not authenticate either or admit a repository effect.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import cast

from .identity import fingerprint
from .native_creation_request import (
    _json,  # pyright: ignore[reportPrivateUsage]
    _object,  # pyright: ignore[reportPrivateUsage]
    _parse,  # pyright: ignore[reportPrivateUsage]
)
from .planning_creation_request import (
    PlanningGoalCreationRequestV2,
    decode_planning_goal_creation_request,
)
from .planning_intent_document import (
    ORIGIN_PROFILE,
    GoalPlanningIntentDocumentV1,
    _creator,  # pyright: ignore[reportPrivateUsage]
    _reference,  # pyright: ignore[reportPrivateUsage]
    decode_goal_planning_intent_document,
    make_goal_planning_intent_document,
    render_goal_planning_markdown,
    validate_planning_goal_creator,
)

ORIGIN_SCHEMA = "aware.goal.planning-creation-intent.v1"
ORIGIN_DOMAIN = "goal-planning-creation-intent"
PLAN_SCHEMA = "aware.goal.planning-initial-plan.v1"
PLAN_DOMAIN = "goal-planning-initial-plan"
_ORIGIN_FIELDS = {
    "schema_id",
    "origin_profile",
    "request_ref",
    "source_context_ref",
    "intent_permission_ref",
    "creator_binding",
    "origin_intent_ref",
}
_PLAN_FIELDS = {
    "schema_id",
    "request",
    "origin_intent",
    "document",
    "carrier_utf8",
    "carrier_sha256",
    "publication_admission",
    "plan_ref",
}


class GoalPlanningPlanError(ValueError):
    """Inconsistent/noncanonical claims; not a provider authority verdict."""


def _origin(raw: object) -> dict[str, object]:
    body = _object(raw, _ORIGIN_FIELDS)
    if body["schema_id"] != ORIGIN_SCHEMA or body["origin_profile"] != ORIGIN_PROFILE:
        raise GoalPlanningPlanError("planning_origin_profile")
    for key, domain in (
        ("request_ref", "goal-planning-creation-request"),
        ("source_context_ref", "workspace-initial-goal-source-context"),
        ("intent_permission_ref", "workspace-initial-goal-intent-permission"),
    ):
        _ = _reference(body[key], domain)
    creator = _object(body["creator_binding"], {"kind", "execution_id", "evidence_ref"})
    _ = _creator(creator, creator["execution_id"])
    expected = (
        ORIGIN_DOMAIN
        + ":"
        + fingerprint(
            {key: value for key, value in body.items() if key != "origin_intent_ref"}
        )
    )
    if (
        type(body["origin_intent_ref"]) is not str
        or body["origin_intent_ref"] != expected
    ):
        raise GoalPlanningPlanError("planning_origin_digest")
    return body


@dataclass(frozen=True, slots=True)
class GoalPlanningOriginIntentV1:
    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not GoalPlanningOriginIntentV1:
            raise GoalPlanningPlanError("planning_origin_type")
        return _origin(_parse(self.canonical_body))

    @property
    def origin_intent_ref(self) -> str:
        return cast(str, self.to_wire()["origin_intent_ref"])


def make_goal_planning_origin_intent(
    request: PlanningGoalCreationRequestV2,
    *,
    creator_binding: object,
    source_context_ref: str,
    intent_permission_ref: str,
) -> GoalPlanningOriginIntentV1:
    creator = validate_planning_goal_creator(request, creator_binding)
    body: dict[str, object] = {
        "schema_id": ORIGIN_SCHEMA,
        "origin_profile": ORIGIN_PROFILE,
        "request_ref": request.request_ref,
        "source_context_ref": source_context_ref,
        "intent_permission_ref": intent_permission_ref,
        "creator_binding": creator,
    }
    body["origin_intent_ref"] = ORIGIN_DOMAIN + ":" + fingerprint(body)
    return GoalPlanningOriginIntentV1(_json(_origin(body)))


def decode_goal_planning_origin_intent(payload: bytes) -> GoalPlanningOriginIntentV1:
    if type(payload) is not bytes:
        raise GoalPlanningPlanError("planning_origin_bytes")
    try:
        return GoalPlanningOriginIntentV1(
            _json(_origin(_parse(payload.decode("utf-8"))))
        )
    except UnicodeError as error:
        raise GoalPlanningPlanError("planning_origin_encoding") from error


def _components(
    request: PlanningGoalCreationRequestV2,
    origin: GoalPlanningOriginIntentV1,
) -> dict[str, object]:
    claim = origin.to_wire()
    if claim["request_ref"] != request.request_ref:
        raise GoalPlanningPlanError("planning_origin_request_mismatch")
    creator = validate_planning_goal_creator(request, claim["creator_binding"])
    document = make_goal_planning_intent_document(
        request, creator_binding=creator, origin_intent_ref=origin.origin_intent_ref
    )
    content = render_goal_planning_markdown(document)
    body: dict[str, object] = {
        "schema_id": PLAN_SCHEMA,
        "request": request.to_wire(),
        "origin_intent": claim,
        "document": document.to_wire(),
        "carrier_utf8": content.decode("utf-8"),
        "carrier_sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
        "publication_admission": "not_issued",
    }
    body["plan_ref"] = PLAN_DOMAIN + ":" + fingerprint(body)
    return body


def _plan(raw: object) -> dict[str, object]:
    body = _object(raw, _PLAN_FIELDS)
    request = decode_planning_goal_creation_request(_json(body["request"]))
    origin = GoalPlanningOriginIntentV1(_json(_origin(body["origin_intent"])))
    expected = _components(request, origin)
    # Exact recursive JSON equality distinguishes Boolean/numeric substitutions
    # and recomputes the complete carrier, not just submitted reference strings.
    if _json(body) != _json(expected):
        raise GoalPlanningPlanError("planning_initial_plan_mismatch")
    return body


@dataclass(frozen=True, slots=True)
class GoalPlanningInitialPlanV1:
    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not GoalPlanningInitialPlanV1:
            raise GoalPlanningPlanError("planning_initial_plan_type")
        return _plan(_parse(self.canonical_body))

    @property
    def plan_ref(self) -> str:
        return cast(str, self.to_wire()["plan_ref"])

    @property
    def carrier_bytes(self) -> bytes:
        return cast(str, self.to_wire()["carrier_utf8"]).encode("utf-8")

    @property
    def document(self) -> GoalPlanningIntentDocumentV1:
        return decode_goal_planning_intent_document(
            _json(self.to_wire()["document"]).encode("utf-8")
        )


def make_goal_planning_initial_plan(
    request: PlanningGoalCreationRequestV2,
    *,
    creator_binding: object,
    source_context_ref: str,
    intent_permission_ref: str,
) -> GoalPlanningInitialPlanV1:
    origin = make_goal_planning_origin_intent(
        request,
        creator_binding=creator_binding,
        source_context_ref=source_context_ref,
        intent_permission_ref=intent_permission_ref,
    )
    return GoalPlanningInitialPlanV1(_json(_components(request, origin)))


def decode_goal_planning_initial_plan(payload: bytes) -> GoalPlanningInitialPlanV1:
    if type(payload) is not bytes:
        raise GoalPlanningPlanError("planning_initial_plan_bytes")
    try:
        return GoalPlanningInitialPlanV1(_json(_plan(_parse(payload.decode("utf-8")))))
    except UnicodeError as error:
        raise GoalPlanningPlanError("planning_initial_plan_encoding") from error


def encode_goal_planning_initial_plan(plan: GoalPlanningInitialPlanV1) -> bytes:
    if type(plan) is not GoalPlanningInitialPlanV1:
        raise GoalPlanningPlanError("planning_initial_plan_type")
    return _json(plan.to_wire()).encode("utf-8")
