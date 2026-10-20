"""Detached generic Object observation records; no issuer or Object authority."""

from typing import Literal, TypedDict

from . import wire as _wire
from .wire import Body, Delivery, Record, Witness

JsonValue = _wire.JsonValue

PROFILE = "aware.ontology.object-observation.v1"
REQUEST_CONTRACT = "aware.ontology.facade-request.v3"
RESULT_CONTRACT = "aware.ontology.facade-result.v3"
REJECTION_CONTRACT = "aware.ontology.object-read-rejection.v1"
INTENT_CONTRACT = "aware.ontology.object-read-intent.v1"
RESULT_DIGEST_DOMAIN = "aware.ontology.object-read-result.v1"
PREIMAGE_CONTRACT = "aware.ontology.object-read-outcome-preimage.v1"
OUTCOME_OBSERVATION_CONTRACT = "aware.ontology.object-read-outcome-observation.v1"
ORIGIN_CONTRACT = "aware.ontology.object-read-origin.v1"
MODEL_CONTRACT = "aware.ontology.object-read-model-binding.v1"
BINDING_CONTRACT = "aware.ontology.object-read-provider-binding.v1"
ROOT_CONTRACT = "aware.ontology.object-read-typed-root.v1"
READING_CONTRACT = "aware.ontology.object-read-provider-reading.v1"
OBSERVATION_CONTRACT = "aware.ontology.object-read-observation.v1"
TARGET_CONTRACT = "aware.ontology.object-read-target.v1"
TARGET_KEY_DOMAIN = "aware.ontology.object-read-target-key.v1"
FOCUS_CONTRACT = "aware.ontology.object-read-focus-admission.v1"

# Explicit portal carriage. These do not widen any V1 entrance or issue a read.
PROFILE_V2 = "aware.ontology.object-observation.v2"
MODEL_V2_CONTRACT = "aware.ontology.object-read-model-binding.v2"
OBSERVATION_V2_CONTRACT = "aware.ontology.object-read-observation.v2"
INTENT_V2_CONTRACT = "aware.ontology.object-read-intent.v2"
RESULT_V2_DIGEST_DOMAIN = "aware.ontology.object-read-result.v2"
PREIMAGE_V2_CONTRACT = "aware.ontology.object-read-outcome-preimage.v2"
OUTCOME_OBSERVATION_V2_CONTRACT = "aware.ontology.object-read-outcome-observation.v2"
REJECTION_V2_CONTRACT = "aware.ontology.object-read-rejection.v2"

MAX_REQUEST_BYTES = 65_536
MAX_RESULT_BYTES = 2_097_152
MIN_RESULT_BUDGET_BYTES = 65_536
MAX_BODY_BYTES = 262_144
MAX_AGGREGATE_BODY_BYTES = 1_048_576
MAX_DEPTH = 32
MAX_ENTRIES = 32_768
MAX_REF_BYTES = 512
MAX_COUNTER = 9_007_199_254_740_991
MAX_DELIVERY_MS = 5_000
MAX_LIFETIME_MS = 30_000
REFUSED_CODES = frozenset((
    "malformed", "unsupported_contract", "unsupported_profile", "unsupported_authority",
    "limit_exceeded", "unauthorized", "issuer_changed", "source_stale",
    "target_ambiguous", "binding_mismatch", "result_invalid", "facts_expired",
))
UNAVAILABLE_CODES = frozenset((
    "capacity_unavailable", "owner_unavailable", "target_unresolved",
    "deadline_elapsed", "cancelled",
))
FAILURE_STAGES = frozenset(("decode", "selection", "owner_verification", "contact", "inspection"))
CONTACT_STATES = frozenset(("not_started", "possible", "observed"))


class ReadOrigin(TypedDict):
    owner_ref: str
    owner_generation: str
    request_ref: str
    principal_ref: str
    entry_kind: Literal["view", "raw", "client"]


class Scope(TypedDict):
    ontology_ref: str
    namespace_ref: str
    context_ref: str
    branch_ref: str
    object_ref: str
    root_type_ref: str
    observable_ref: str
    projection_ref: str
    model_digest: str


class Selection(Scope):
    expected_revision_ref: str | None


class ReadOriginBody(TypedDict):
    contract: str
    origin: ReadOrigin
    api_request: Body
    service_binding: Body
    caller_admission: Body
    experience_admission: Body | None
    read_admission_ref: str
    origin_digest: str


class ReadPayload(TypedDict):
    selection: Selection
    origin_body: Body


class Rejection(TypedDict):
    contract: Literal["aware.ontology.object-read-rejection.v1"]
    profile_ref: Literal["aware.ontology.object-observation.v1"]
    tag: Literal["refused", "unavailable"]
    code: str


class Request(TypedDict):
    contract: Literal["aware.ontology.facade-request.v3"]
    profile_ref: Literal["aware.ontology.object-observation.v1"]
    kind: Literal["view.read"]
    origin: ReadOrigin
    operation: None
    ordinal: None
    payload: ReadPayload
    result_budget_bytes: int
    intent_digest: str
    delivery: Delivery


class Result(TypedDict):
    contract: Literal["aware.ontology.facade-result.v3"]
    profile_ref: Literal["aware.ontology.object-observation.v1"]
    kind: Literal["view.read"]
    origin: ReadOrigin
    operation: None
    ordinal: None
    intent_digest: str
    delivery_ref: str
    responder_incarnation: str
    outcome: Record
    witnesses: list[Witness]
    result_digest: str


class ModelBinding(TypedDict):
    contract: str
    model_ref: str
    model_revision_ref: str
    root_type_ref: str
    projection_ref: str
    schema_bundle: Body
    schema_slice: Body
    topology: Body
    model_admission: Body
    model_digest: str


class ProviderBinding(TypedDict):
    contract: str
    scope: Scope
    owner_ref: str
    provider_ref: str
    provider_generation: str
    owner_profile_ref: str
    binding_revision_ref: str
    namespace_admission: Body
    binding_digest: str


class TypedRoot(TypedDict):
    contract: str
    object: Record


class ProviderReading(TypedDict):
    contract: str
    reading_ref: str
    scope: Scope
    provider_binding_digest: str
    provider_ref: str
    provider_generation: str
    revision_ref: str
    owner_reading: Body
    input_evidence: Body
    typed_state: Body
    reading_digest: str


class Target(TypedDict):
    contract: str
    target_ref: str
    target_kind: Literal["branch"]
    scope: Scope
    topology_digest: str
    reading_ref: str
    authority_grade: Literal["local_operational"]
    target_digest: str


class Observation(TypedDict):
    contract: str
    observation_ref: str
    host_incarnation: str
    scope: Scope
    provider_binding: Body
    model_binding: Body
    provider_reading: Body
    branch: Body
    view: Body
    target: Target
    lifetime_ms: int
    observation_digest: str


class FocusAdmission(TypedDict):
    contract: str
    observation_ref: str
    observation_digest: str
    target: Target
    issuer_ref: str
    issuer_generation: str
    actor_ref: str
    attention_session_ref: str
    binding_ref: str
    binding_revision: int
    section_ref: str
    mount_activation_epoch: int
    permission_evidence: Body
    remaining_lifetime_ms: int
    admission_digest: str


class OutcomeObservation(TypedDict):
    contract: str
    request_intent_digest: str
    outcome_hash: str
    issuer_ref: str
    issuer_generation: str
    verification_ref: str
    owner_observation_body: Body
    observation_digest: str


class ModelBindingV2(ModelBinding):
    topology_profile_ref: Literal["meta-inspect-forward-portals.v1"]


class ObservationV2(Observation):
    """Same fields, explicitly bound to ModelBinding V2 by its owning codec."""


class OutcomeObservationV2(OutcomeObservation):
    """Same fields under a distinct V2 contract/digest domain."""


class RequestV2(TypedDict):
    contract: Literal["aware.ontology.facade-request.v3"]
    profile_ref: Literal["aware.ontology.object-observation.v2"]
    kind: Literal["view.read"]
    origin: ReadOrigin
    operation: None
    ordinal: None
    payload: ReadPayload
    result_budget_bytes: int
    intent_digest: str
    delivery: Delivery


class ResultV2(TypedDict):
    contract: Literal["aware.ontology.facade-result.v3"]
    profile_ref: Literal["aware.ontology.object-observation.v2"]
    kind: Literal["view.read"]
    origin: ReadOrigin
    operation: None
    ordinal: None
    intent_digest: str
    delivery_ref: str
    responder_incarnation: str
    outcome: Record
    witnesses: list[Witness]
    result_digest: str


class RejectionV2(TypedDict):
    contract: Literal["aware.ontology.object-read-rejection.v2"]
    profile_ref: Literal["aware.ontology.object-observation.v2"]
    tag: Literal["refused", "unavailable"]
    code: str
