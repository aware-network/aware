from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol, cast

from .contracts import (
    AchieveGoalIntent,
    ActivateGoalIntent,
    ActorEvidence,
    AppendGoalLaneIssueIntent,
    AppendGoalUpdateIntent,
    BlockGoalIntent,
    EnsureGoalIntent,
    EnsureGoalLaneIntent,
    GoalIntent,
    GoalLaneIssueTick,
    GoalLaneStatus,
    IntentContext,
    LinkGoalLaneIssueIntent,
    ParkGoalIntent,
    ResumeGoalIntent,
    SupersedeGoalIntent,
    SyncGoalLaneIssueIntent,
)
from .identity import fingerprint, required_token
from .observation import (
    GoalObservation,
    GoalObservationQuery,
    ObservationDepth,
    ObservationOutcome,
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
BOOTSTRAP_PLAN_SCHEMA = "aware.goal.operational_bootstrap_plan.v1"


@dataclass(frozen=True, slots=True)
class CommittedGoalBootstrapSource:
    repository_revision: str
    goal_path: str
    goal_sha256: str
    publication_receipt_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "repository_revision",
            required_token(self.repository_revision, "repository_revision"),
        )
        object.__setattr__(
            self, "goal_path", required_token(self.goal_path, "goal_path")
        )
        object.__setattr__(
            self,
            "publication_receipt_ref",
            required_token(self.publication_receipt_ref, "publication_receipt_ref"),
        )
        if type(self.goal_sha256) is not str or not _SHA256.fullmatch(self.goal_sha256):
            raise ValueError("goal_sha256 must be 64 lowercase hexadecimal characters")

    def to_wire(self) -> dict[str, object]:
        return {
            "repository_revision": self.repository_revision,
            "goal_path": self.goal_path,
            "goal_sha256": self.goal_sha256,
            "publication_receipt_ref": self.publication_receipt_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalBootstrapSourceVerification:
    source: CommittedGoalBootstrapSource
    verification_receipt_ref: str

    def __post_init__(self) -> None:
        if type(self.source) is not CommittedGoalBootstrapSource:
            raise TypeError("source must be CommittedGoalBootstrapSource")
        object.__setattr__(
            self,
            "verification_receipt_ref",
            required_token(self.verification_receipt_ref, "verification_receipt_ref"),
        )


class GoalBootstrapSourceVerifier(Protocol):
    def verify(
        self,
        source: CommittedGoalBootstrapSource,
    ) -> GoalBootstrapSourceVerification: ...


@dataclass(frozen=True, slots=True)
class GoalOperationalBootstrapPlan:
    source: CommittedGoalBootstrapSource
    authority_ref: str
    actor_evidence: ActorEvidence
    intents: tuple[GoalIntent, ...]
    terminal_query: GoalObservationQuery

    def __post_init__(self) -> None:
        if type(self.source) is not CommittedGoalBootstrapSource:
            raise TypeError("source must be CommittedGoalBootstrapSource")
        object.__setattr__(
            self,
            "authority_ref",
            required_token(self.authority_ref, "authority_ref"),
        )
        if type(self.actor_evidence) is not ActorEvidence:
            raise TypeError("actor_evidence must be ActorEvidence")
        if not self.actor_evidence.accepted:
            raise ValueError("bootstrap requires accepted actor evidence")
        if not self.intents:
            raise ValueError("bootstrap requires at least one Goal intent")
        intent_ids: list[str] = []
        for intent in self.intents:
            context = intent.context
            if context.expected_authority_generation != 0:
                raise ValueError("bootstrap intents require authority generation zero")
            if context.actor_evidence != self.actor_evidence:
                raise ValueError("bootstrap intent actor evidence differs from plan")
            intent_ids.append(context.client_intent_id)
        if len(intent_ids) != len(set(intent_ids)):
            raise ValueError("bootstrap client intent ids must be unique")
        if type(self.terminal_query) is not GoalObservationQuery:
            raise TypeError("terminal_query must be GoalObservationQuery")

    @property
    def plan_digest(self) -> str:
        return fingerprint(
            {
                "source": self.source.to_wire(),
                "authority_ref": self.authority_ref,
                "actor_evidence": self.actor_evidence.to_wire(),
                "intents": [intent.to_wire() for intent in self.intents],
                "terminal_query": {
                    "depth": self.terminal_query.depth.value,
                    "goal_ref": self.terminal_query.goal_ref,
                    "goal_tag": self.terminal_query.goal_tag,
                    "lane_ref": self.terminal_query.lane_ref,
                    "lane_key": self.terminal_query.lane_key,
                    "row_ref": self.terminal_query.row_ref,
                    "row_key": self.terminal_query.row_key,
                },
            }
        )


def encode_goal_operational_bootstrap_plan(
    plan: GoalOperationalBootstrapPlan,
) -> str:
    """Encode one exact, portable bootstrap plan for a separate host process."""
    payload = _plan_wire(plan)
    envelope = {
        "schema": BOOTSTRAP_PLAN_SCHEMA,
        "plan_digest": plan.plan_digest,
        "plan": payload,
    }
    return json.dumps(envelope, sort_keys=True, separators=(",", ":"))


def decode_goal_operational_bootstrap_plan(
    encoded: str,
) -> GoalOperationalBootstrapPlan:
    """Strictly reconstruct a plan and reject loss, extension, or tampering."""
    try:
        value = cast(object, json.loads(encoded))
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError("bootstrap plan must be canonical JSON") from error
    envelope = _object(value, {"schema", "plan_digest", "plan"}, "envelope")
    if envelope["schema"] != BOOTSTRAP_PLAN_SCHEMA:
        raise ValueError("unsupported bootstrap plan schema")
    expected_digest = _text(envelope["plan_digest"], "plan_digest")
    plan_wire = _object(
        envelope["plan"],
        {"source", "authority_ref", "actor_evidence", "intents", "terminal_query"},
        "plan",
    )
    source_wire = _object(
        plan_wire["source"],
        {"repository_revision", "goal_path", "goal_sha256", "publication_receipt_ref"},
        "source",
    )
    actor = _actor(plan_wire["actor_evidence"])
    intents_wire = plan_wire["intents"]
    if type(intents_wire) is not list:
        raise TypeError("intents must be list")
    intent_values = cast(list[object], intents_wire)
    query_wire = _object(
        plan_wire["terminal_query"],
        {"depth", "goal_ref", "goal_tag", "lane_ref", "lane_key", "row_ref", "row_key"},
        "terminal_query",
    )
    plan = GoalOperationalBootstrapPlan(
        source=CommittedGoalBootstrapSource(
            repository_revision=_text(
                source_wire["repository_revision"], "repository_revision"
            ),
            goal_path=_text(source_wire["goal_path"], "goal_path"),
            goal_sha256=_text(source_wire["goal_sha256"], "goal_sha256"),
            publication_receipt_ref=_text(
                source_wire["publication_receipt_ref"], "publication_receipt_ref"
            ),
        ),
        authority_ref=_text(plan_wire["authority_ref"], "authority_ref"),
        actor_evidence=actor,
        intents=tuple(_intent(item, actor) for item in intent_values),
        terminal_query=GoalObservationQuery(
            ObservationDepth(_text(query_wire["depth"], "depth")),
            goal_ref=_optional_text(query_wire["goal_ref"], "goal_ref"),
            goal_tag=_optional_text(query_wire["goal_tag"], "goal_tag"),
            lane_ref=_optional_text(query_wire["lane_ref"], "lane_ref"),
            lane_key=_optional_text(query_wire["lane_key"], "lane_key"),
            row_ref=_optional_text(query_wire["row_ref"], "row_ref"),
            row_key=_optional_text(query_wire["row_key"], "row_key"),
        ),
    )
    if plan.plan_digest != expected_digest:
        raise ValueError("bootstrap plan digest mismatch")
    if encode_goal_operational_bootstrap_plan(plan) != encoded:
        raise ValueError("bootstrap plan JSON is not canonical")
    return plan


def _plan_wire(plan: GoalOperationalBootstrapPlan) -> dict[str, object]:
    query = plan.terminal_query
    return {
        "source": plan.source.to_wire(),
        "authority_ref": plan.authority_ref,
        "actor_evidence": plan.actor_evidence.to_wire(),
        "intents": [intent.to_wire() for intent in plan.intents],
        "terminal_query": {
            "depth": query.depth.value,
            "goal_ref": query.goal_ref,
            "goal_tag": query.goal_tag,
            "lane_ref": query.lane_ref,
            "lane_key": query.lane_key,
            "row_ref": query.row_ref,
            "row_key": query.row_key,
        },
    }


def _object(value: object, fields: set[str], name: str) -> dict[str, object]:
    if type(value) is not dict:
        raise TypeError(f"{name} must be object")
    result = cast(dict[str, object], value)
    if set(result) != fields:
        raise ValueError(f"{name} fields must be exact")
    return result


def _text(value: object, name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be text")
    return value


def _optional_text(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _text(value, name)


def _integer(value: object, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be integer")
    return value


def _actor(value: object) -> ActorEvidence:
    wire = _object(value, {"actor_ref", "evidence_ref", "accepted"}, "actor_evidence")
    if type(wire["accepted"]) is not bool:
        raise TypeError("accepted must be bool")
    return ActorEvidence(
        _text(wire["actor_ref"], "actor_ref"),
        _text(wire["evidence_ref"], "evidence_ref"),
        wire["accepted"],
    )


def _context(value: object, actor: ActorEvidence) -> IntentContext:
    wire = _object(
        value,
        {"client_intent_id", "expected_authority_generation", "actor_evidence"},
        "intent context",
    )
    context_actor = _actor(wire["actor_evidence"])
    if context_actor != actor:
        raise ValueError("intent actor evidence differs from plan")
    return IntentContext(
        _text(wire["client_intent_id"], "client_intent_id"),
        _integer(
            wire["expected_authority_generation"], "expected_authority_generation"
        ),
        context_actor,
    )


def _intent(value: object, actor: ActorEvidence) -> GoalIntent:
    if type(value) is not dict:
        raise TypeError("intent must be object")
    intent_object = cast(dict[str, object], value)
    kind = _text(intent_object.get("kind"), "kind")
    common = {"kind", "context"}
    context = _context(intent_object.get("context"), actor)
    if kind == "ensure_goal":
        wire = _object(
            intent_object,
            common
            | {
                "tag",
                "title",
                "priority_level",
                "definition_of_done_ref",
                "locks_ref",
                "evidence_ref",
            },
            "ensure_goal",
        )
        return EnsureGoalIntent(
            context,
            _text(wire["tag"], "tag"),
            _text(wire["title"], "title"),
            _text(wire["priority_level"], "priority_level"),
            _optional_text(wire["definition_of_done_ref"], "definition_of_done_ref"),
            _optional_text(wire["locks_ref"], "locks_ref"),
            _optional_text(wire["evidence_ref"], "evidence_ref"),
        )
    lifecycle = {
        "activate_goal": ActivateGoalIntent,
        "block_goal": BlockGoalIntent,
        "resume_goal": ResumeGoalIntent,
        "park_goal": ParkGoalIntent,
        "achieve_goal": AchieveGoalIntent,
        "supersede_goal": SupersedeGoalIntent,
    }.get(kind)
    if lifecycle is not None:
        wire = _object(
            intent_object,
            common | {"goal_ref", "expected_goal_revision", "evidence_ref", "reason"},
            kind,
        )
        return lifecycle(
            context,
            _text(wire["goal_ref"], "goal_ref"),
            _integer(wire["expected_goal_revision"], "expected_goal_revision"),
            _optional_text(wire["evidence_ref"], "evidence_ref"),
            _optional_text(wire["reason"], "reason"),
        )
    if kind == "ensure_goal_lane":
        wire = _object(
            intent_object,
            common
            | {
                "goal_ref",
                "expected_goal_revision",
                "lane_key",
                "status",
                "role_key",
                "role_label",
                "owner_execution_id",
                "scope",
            },
            kind,
        )
        return EnsureGoalLaneIntent(
            context,
            _text(wire["goal_ref"], "goal_ref"),
            _integer(wire["expected_goal_revision"], "expected_goal_revision"),
            _text(wire["lane_key"], "lane_key"),
            GoalLaneStatus(_text(wire["status"], "status")),
            _optional_text(wire["role_key"], "role_key"),
            _optional_text(wire["role_label"], "role_label"),
            _optional_text(wire["owner_execution_id"], "owner_execution_id"),
            _optional_text(wire["scope"], "scope"),
        )
    if kind == "append_goal_lane_issue":
        wire = _object(
            intent_object,
            common
            | {
                "goal_ref",
                "lane_ref",
                "expected_lane_revision",
                "expected_head_row_ref",
                "row_key",
                "gate",
                "prerequisite_refs",
                "planned_issue_tag",
                "owner_execution_id",
            },
            kind,
        )
        prerequisites = wire["prerequisite_refs"]
        if type(prerequisites) is not list or any(
            type(item) is not str for item in cast(list[object], prerequisites)
        ):
            raise TypeError("prerequisite_refs must be list of text")
        prerequisite_refs = cast(list[str], prerequisites)
        return AppendGoalLaneIssueIntent(
            context,
            _text(wire["goal_ref"], "goal_ref"),
            _text(wire["lane_ref"], "lane_ref"),
            _integer(wire["expected_lane_revision"], "expected_lane_revision"),
            _optional_text(wire["expected_head_row_ref"], "expected_head_row_ref"),
            _text(wire["row_key"], "row_key"),
            _text(wire["gate"], "gate"),
            tuple(prerequisite_refs),
            _optional_text(wire["planned_issue_tag"], "planned_issue_tag"),
            _optional_text(wire["owner_execution_id"], "owner_execution_id"),
        )
    if kind == "link_goal_lane_issue":
        wire = _object(
            intent_object,
            common
            | {
                "goal_ref",
                "lane_ref",
                "row_ref",
                "expected_lane_revision",
                "expected_row_revision",
                "issue_ref",
                "issue_authority_receipt_ref",
            },
            kind,
        )
        return LinkGoalLaneIssueIntent(
            context,
            _text(wire["goal_ref"], "goal_ref"),
            _text(wire["lane_ref"], "lane_ref"),
            _text(wire["row_ref"], "row_ref"),
            _integer(wire["expected_lane_revision"], "expected_lane_revision"),
            _integer(wire["expected_row_revision"], "expected_row_revision"),
            _text(wire["issue_ref"], "issue_ref"),
            _text(wire["issue_authority_receipt_ref"], "issue_authority_receipt_ref"),
        )
    if kind == "sync_goal_lane_issue":
        wire = _object(
            intent_object,
            common
            | {
                "goal_ref",
                "lane_ref",
                "row_ref",
                "expected_lane_revision",
                "expected_row_revision",
                "issue_ref",
                "issue_observation_ref",
                "status_snapshot",
                "tick",
                "owner_execution_id",
                "receipt_ref",
            },
            kind,
        )
        return SyncGoalLaneIssueIntent(
            context,
            _text(wire["goal_ref"], "goal_ref"),
            _text(wire["lane_ref"], "lane_ref"),
            _text(wire["row_ref"], "row_ref"),
            _integer(wire["expected_lane_revision"], "expected_lane_revision"),
            _integer(wire["expected_row_revision"], "expected_row_revision"),
            _text(wire["issue_ref"], "issue_ref"),
            _text(wire["issue_observation_ref"], "issue_observation_ref"),
            _text(wire["status_snapshot"], "status_snapshot"),
            GoalLaneIssueTick(_text(wire["tick"], "tick")),
            _optional_text(wire["owner_execution_id"], "owner_execution_id"),
            _optional_text(wire["receipt_ref"], "receipt_ref"),
        )
    if kind == "append_goal_update":
        wire = _object(
            intent_object,
            common
            | {
                "goal_ref",
                "expected_update_head_key",
                "update_key",
                "kind_token",
                "message",
                "recorded_at",
                "lane_ref",
                "row_ref",
                "receipt_ref",
            },
            kind,
        )
        return AppendGoalUpdateIntent(
            context,
            _text(wire["goal_ref"], "goal_ref"),
            _optional_text(
                wire["expected_update_head_key"], "expected_update_head_key"
            ),
            _text(wire["update_key"], "update_key"),
            _text(wire["kind_token"], "kind_token"),
            _text(wire["message"], "message"),
            _optional_text(wire["recorded_at"], "recorded_at"),
            _optional_text(wire["lane_ref"], "lane_ref"),
            _optional_text(wire["row_ref"], "row_ref"),
            _optional_text(wire["receipt_ref"], "receipt_ref"),
        )
    raise ValueError(f"unsupported bootstrap intent kind: {kind}")


@dataclass(frozen=True, slots=True)
class GoalOperationalBootstrapReceipt:
    receipt_ref: str
    plan_digest: str
    source: CommittedGoalBootstrapSource
    source_verification_receipt_ref: str
    authority_ref: str
    database_path: str
    intent_receipt_refs: tuple[str, ...]
    terminal_observation: GoalObservation

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "receipt_ref", required_token(self.receipt_ref, "receipt_ref")
        )
        object.__setattr__(
            self, "plan_digest", required_token(self.plan_digest, "plan_digest")
        )
        object.__setattr__(
            self,
            "source_verification_receipt_ref",
            required_token(
                self.source_verification_receipt_ref,
                "source_verification_receipt_ref",
            ),
        )
        object.__setattr__(
            self,
            "authority_ref",
            required_token(self.authority_ref, "authority_ref"),
        )
        object.__setattr__(
            self,
            "database_path",
            required_token(self.database_path, "database_path"),
        )
        if type(self.source) is not CommittedGoalBootstrapSource:
            raise TypeError("source must be CommittedGoalBootstrapSource")
        if not self.intent_receipt_refs:
            raise ValueError("bootstrap receipt requires intent receipts")
        for receipt_ref in self.intent_receipt_refs:
            _ = required_token(receipt_ref, "intent_receipt_ref")
        if self.terminal_observation.outcome is not ObservationOutcome.FOUND:
            raise ValueError("bootstrap receipt requires a found terminal observation")
