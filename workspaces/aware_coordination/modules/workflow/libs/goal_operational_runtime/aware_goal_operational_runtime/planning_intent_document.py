"""Non-authorizing planning document and deterministic Markdown structure.

Origin/creator references are claims. A provider must independently resolve
their original issuance and the actual publication before qualified reading.
No native execution authority or permission is manufactured here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .identity import fingerprint
from .native_creation_request import (
    _json,  # pyright: ignore[reportPrivateUsage]
    _object,  # pyright: ignore[reportPrivateUsage]
    _parse,  # pyright: ignore[reportPrivateUsage]
    _token,  # pyright: ignore[reportPrivateUsage]
)
from .planning_creation_request import (
    GRAPH_FIELDS,
    METADATA_FIELDS,
    PlanningGoalCreationRequestV2,
    validate_planning_metadata,
    validate_undecomposed_graph,
)

DOCUMENT_SCHEMA = "aware.goal.intent.document.v1"
DOCUMENT_DOMAIN = "goal-intent-document"
ORIGIN_PROFILE = "repository_initial_authoring_v1"
_FIELDS = {
    *METADATA_FIELDS,
    *GRAPH_FIELDS,
    "schema_id",
    "creator_binding",
    "lifecycle_status",
    "origin_profile",
    "origin_intent_ref",
    "document_ref",
}
_OPEN = b"<!-- aware.goal.intent.document.v1:start -->\n```json\n"
_CLOSE = b"\n```\n<!-- aware.goal.intent.document.v1:end -->\n"


class GoalPlanningDocumentError(ValueError):
    """Structural contradiction, not an evaluation of issuance authority."""


def _reference(value: object, domain: str) -> str:
    if (
        type(value) is not str
        or re.fullmatch(re.escape(domain) + r":sha256:[0-9a-f]{64}", value) is None
    ):
        raise GoalPlanningDocumentError("planning_document_reference")
    return value


def _creator(raw: object, owner: object) -> dict[str, object]:
    creator = _object(raw, {"kind", "execution_id", "evidence_ref"})
    if creator["kind"] != "provider_execution_correlation":
        raise GoalPlanningDocumentError("planning_document_creator_kind")
    if _token(creator["execution_id"]) != owner:
        raise GoalPlanningDocumentError("planning_document_creator_owner")
    # This local initial-authoring profile points to its original Workspace
    # enrollment. A self-consistent reference is NOT verification of enrollment.
    _ = _reference(creator["evidence_ref"], "workspace-initial-enrollment")
    return creator


def validate_planning_goal_creator(
    request: PlanningGoalCreationRequestV2, creator_binding: object
) -> dict[str, object]:
    """Pure consistency only; providers independently authenticate these facts."""
    if type(request) is not PlanningGoalCreationRequestV2:
        raise GoalPlanningDocumentError("planning_request_type")
    return _creator(creator_binding, request.to_wire()["owner_ref"])


def _validate(raw: object) -> dict[str, object]:
    body = _object(raw, _FIELDS)
    if body["schema_id"] != DOCUMENT_SCHEMA:
        raise GoalPlanningDocumentError("planning_document_schema")
    validate_planning_metadata(body)
    validate_undecomposed_graph(body)
    _ = _creator(body["creator_binding"], body["owner_ref"])
    if (
        body["lifecycle_status"] != "proposed"
        or body["origin_profile"] != ORIGIN_PROFILE
    ):
        raise GoalPlanningDocumentError("planning_document_initial_state")
    _ = _reference(body["origin_intent_ref"], "goal-planning-creation-intent")
    expected = (
        DOCUMENT_DOMAIN
        + ":"
        + fingerprint(
            {key: value for key, value in body.items() if key != "document_ref"}
        )
    )
    if type(body["document_ref"]) is not str or body["document_ref"] != expected:
        raise GoalPlanningDocumentError("planning_document_digest")
    return body


@dataclass(frozen=True, slots=True)
class GoalPlanningIntentDocumentV1:
    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not GoalPlanningIntentDocumentV1:
            raise GoalPlanningDocumentError("planning_document_type")
        return _validate(_parse(self.canonical_body))

    @property
    def document_ref(self) -> str:
        return _reference(self.to_wire()["document_ref"], DOCUMENT_DOMAIN)

    @property
    def planning_status(self) -> str:
        _ = self.to_wire()
        return "not_yet_decomposed"


def make_goal_planning_intent_document(
    request: PlanningGoalCreationRequestV2,
    *,
    creator_binding: object,
    origin_intent_ref: str,
) -> GoalPlanningIntentDocumentV1:
    """Join claims only; the original provider still owns their authentication."""
    if type(request) is not PlanningGoalCreationRequestV2:
        raise GoalPlanningDocumentError("planning_request_type")
    source = request.to_wire()
    body = {
        "schema_id": DOCUMENT_SCHEMA,
        **{key: source[key] for key in METADATA_FIELDS | GRAPH_FIELDS},
        "creator_binding": creator_binding,
        "lifecycle_status": "proposed",
        "origin_profile": ORIGIN_PROFILE,
        "origin_intent_ref": origin_intent_ref,
    }
    body["document_ref"] = DOCUMENT_DOMAIN + ":" + fingerprint(body)
    return GoalPlanningIntentDocumentV1(_json(_validate(body)))


def decode_goal_planning_intent_document(
    payload: bytes,
) -> GoalPlanningIntentDocumentV1:
    if type(payload) is not bytes:
        raise GoalPlanningDocumentError("planning_document_bytes")
    try:
        return GoalPlanningIntentDocumentV1(
            _json(_validate(_parse(payload.decode("utf-8"))))
        )
    except UnicodeError as exc:
        raise GoalPlanningDocumentError("planning_document_encoding") from exc


def encode_goal_planning_intent_document(
    document: GoalPlanningIntentDocumentV1,
) -> bytes:
    if type(document) is not GoalPlanningIntentDocumentV1:
        raise GoalPlanningDocumentError("planning_document_type")
    return _json(document.to_wire()).encode("utf-8")


def validate_goal_planning_intent_join(
    document: GoalPlanningIntentDocumentV1,
    request: PlanningGoalCreationRequestV2,
    *,
    creator_binding: object,
    origin_intent_ref: str,
) -> None:
    """Recompute a complete claim join; callers must separately verify authority."""
    expected = make_goal_planning_intent_document(
        request, creator_binding=creator_binding, origin_intent_ref=origin_intent_ref
    )
    if encode_goal_planning_intent_document(
        document
    ) != encode_goal_planning_intent_document(expected):
        raise GoalPlanningDocumentError("planning_document_source_mismatch")


def render_goal_planning_markdown(document: GoalPlanningIntentDocumentV1) -> bytes:
    body = document.to_wire()
    # JSON scalars keep multiline/marker-bearing authored text in one header
    # line. The complete header is a deterministic display, not another source.
    header = (
        "# Goal intent\n\n"
        + "".join(
            "- " + label + ": " + _json(body[key]) + "\n"
            for label, key in (
                ("Tag", "goal_tag"),
                ("Title", "title"),
                ("Intent", "intent"),
                ("Owner correlation", "owner_ref"),
                ("Priority", "priority"),
                ("Definition of done reference", "definition_of_done_ref"),
                ("Locks reference", "locks_ref"),
            )
        )
        + "- Status: Proposed\n- Planning: not yet decomposed\n\n"
    )
    return (
        header.encode("utf-8")
        + _OPEN
        + encode_goal_planning_intent_document(document)
        + _CLOSE
    )


def extract_goal_planning_markdown(candidate: bytes) -> GoalPlanningIntentDocumentV1:
    if type(candidate) is not bytes:
        raise GoalPlanningDocumentError("planning_carrier_bytes")
    start = candidate.rfind(_OPEN)
    if start < 0 or not candidate.endswith(_CLOSE):
        raise GoalPlanningDocumentError("planning_carrier_terminal_frame")
    end = len(candidate) - len(_CLOSE)
    if end < start + len(_OPEN):
        raise GoalPlanningDocumentError("planning_carrier_terminal_frame")
    document = decode_goal_planning_intent_document(candidate[start + len(_OPEN) : end])
    if render_goal_planning_markdown(document) != candidate:
        raise GoalPlanningDocumentError("planning_carrier_noncanonical")
    return document
