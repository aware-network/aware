"""Detached data types for the accepted facade v1 wire; none is authority."""

from typing import Literal, TypeAlias, TypedDict

JsonValue: TypeAlias = (
    None | bool | int | str | list["JsonValue"] | dict[str, "JsonValue"]
)
Record: TypeAlias = dict[str, JsonValue]
Command: TypeAlias = Literal[
    "facts.read", "view.read", "owner.verify", "owner.command_verify",
    "operation.activate", "object.acquire", "object.invoke", "object.construct",
    "operation.complete", "operation.abort", "operation.inspect", "command.inspect",
]

REQUEST_CONTRACT = "aware.ontology.facade-request.v1"
RESULT_CONTRACT = "aware.ontology.facade-result.v1"
REJECTION_CONTRACT = "aware.ontology.facade-rejection.v1"
INTENT_CONTRACT = "aware.ontology.facade-command-intent.v1"
PREIMAGE_CONTRACT = "aware.ontology.facade-outcome-preimage.v1"
OBSERVATION_CONTRACT = "aware.ontology.facade-outcome-observation.v1"
ASSOCIATION_CONTRACT = "aware.ontology.facade-replay-association.v1"
PREFIX_CONTRACT = "aware.ontology.facade-command-prefix.v1"
# Explicit operation successor; predecessor constants remain historical v1.
OPERATION_REQUEST_CONTRACT = "aware.ontology.facade-request.v4"
OPERATION_RESULT_CONTRACT = "aware.ontology.facade-result.v4"
OPERATION_INTENT_CONTRACT = "aware.ontology.facade-command-intent.v2"
OPERATION_PREIMAGE_CONTRACT = "aware.ontology.facade-outcome-preimage.v2"
OPERATION_OBSERVATION_CONTRACT = "aware.ontology.facade-outcome-observation.v2"
OPERATION_ASSOCIATION_CONTRACT = "aware.ontology.facade-replay-association.v2"
FACTS_CONTRACT = "aware.ontology.facade-facts.v2"
BUNDLE_CONTRACT = "aware.ontology.facade-bundle.v2"
PREPARATION_BASE_CONTRACT = "aware.ontology.facade-preparation-base.v1"
MAX_MESSAGE_BYTES = 65_536
MAX_BODY_BYTES = 16_384
MAX_REF_BYTES = 512
MAX_DEPTH = 32
MAX_ENTRIES = 4_096
MAX_COUNTER = 9_007_199_254_740_991
MAX_COMMANDS = 64
MAX_ACTIONS = 16
MAX_OBJECTS = 32
MAX_WITNESSES = 16
MAX_DELIVERY_MS = 30_000
MAX_CHALLENGE_MS = 5_000

COMMANDS: tuple[str, ...] = (
    "facts.read", "view.read", "owner.verify", "owner.command_verify",
    "operation.activate", "object.acquire", "object.invoke", "object.construct",
    "operation.complete", "operation.abort", "operation.inspect", "command.inspect",
)
ACTIVE_COMMANDS = frozenset(COMMANDS[4:10])
REFUSAL_CODES = frozenset((
    "malformed", "unsupported_contract", "unsupported_profile", "unsupported_authority",
    "limit_exceeded", "capacity_unavailable", "unauthorized", "owner_unavailable",
    "owner_state_conflict", "claim_unavailable", "fence_unavailable", "facts_expired",
    "issuer_changed", "source_stale", "target_unresolved", "target_ambiguous",
    "binding_mismatch", "argument_invalid", "result_invalid", "command_conflict",
    "command_gap", "command_in_progress", "session_expired", "scope_closed",
    "cross_branch_unavailable", "deadline_elapsed", "cancelled", "inspection_unavailable",
    "outcome_unavailable", "indeterminate_contact",
))
FAILURE_STAGES = frozenset((
    "decode", "selection", "preparation", "owner_verification", "contact", "execution",
    "completion", "settlement", "inspection",
))
CONTACT_STATES = frozenset(("not_started", "possible", "observed"))
COMMAND_PHASES = frozenset((
    "reserved", "contact_claimed", "verified", "refused_before_contact", "uncertain",
))
ABORT_REASONS = frozenset((
    "application_error", "caller_cancelled", "deadline_elapsed", "explicit_abort",
))
WITNESS_FIELDS: dict[str, tuple[str, ...]] = {
    "facts_issuance": ("facts",),
    "view_observation": ("view",),
    "owner_preparation": ("preparation_record",),
    "owner_reread": ("preparation_reread", "head_reread"),
    "owner_head": ("owner_head",),
    "owner_contact_claim": ("contact_claim", "initial_contact_claim"),
    "provider_fence": (),
    "command_outcome": (),
    "operation_completion": ("receipt", "abort_evidence"),
    "historical_recovery": ("recovery_evidence",),
    "service_settlement": (),
}


class Body(TypedDict):
    contract_ref: str
    body_hex: str
    body_hash: str


class Origin(TypedDict):
    owner_ref: str
    owner_generation: str
    journal_namespace_ref: str
    invocation_ref: str
    attempt_ref: str
    principal_ref: str
    entry_kind: Literal["view", "raw", "client"]


class OperationKey(TypedDict):
    ontology_ref: str
    branch_ref: str
    actor_ref: str
    projection_ref: str
    operation_ref: str
    idempotency_key: str
    object_abi_digest: str
    provider_ref: str
    provider_generation: str
    expected_revision_ref: str | None
    base_operational_digest: str


class Delivery(TypedDict):
    delivery_ref: str
    recipient_incarnation: str
    timeout_ms: int


class Request(TypedDict):
    contract: Literal["aware.ontology.facade-request.v1", "aware.ontology.facade-request.v4"]
    kind: Command
    origin: Origin
    operation: OperationKey | None
    ordinal: int | None
    payload: Record
    result_budget_bytes: int
    intent_digest: str
    delivery: Delivery


class Witness(TypedDict):
    role: str
    issuer_ref: str
    issuer_generation: str
    body: Body | None
    value_field: str | None


class Result(TypedDict):
    contract: Literal["aware.ontology.facade-result.v1", "aware.ontology.facade-result.v4"]
    kind: Command
    origin: Origin
    operation: OperationKey | None
    ordinal: int | None
    intent_digest: str
    delivery_ref: str
    responder_incarnation: str
    outcome: Record
    witnesses: list[Witness]
    result_digest: str
