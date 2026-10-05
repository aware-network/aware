from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Protocol

from .host import GoalOperationalRuntimeHost
from .observation import (
    GoalObservation,
    GoalObservationQuery,
    ObservationDepth,
    ObservationOutcome,
)
from .persistence import (
    InMemoryGoalStateStore,
    decode_goal_operational_record,
    encode_goal_operational_record,
)

HANDOFF_SCHEMA_ID = "aware.goal.runtime_host_handoff.v1"


class GoalRuntimeHostHandoffAuthenticator(Protocol):
    @property
    def issuer_ref(self) -> str: ...

    def authenticate(self, payload: bytes) -> str: ...

    def verify(self, payload: bytes, authentication_ref: str) -> bool: ...


class HmacSha256GoalRuntimeHostHandoffAuthenticator:
    def __init__(self, *, issuer_ref: str, secret: bytes) -> None:
        self._issuer_ref = _required(issuer_ref, "issuer_ref")
        if not isinstance(secret, bytes) or len(secret) < 32:
            raise ValueError("handoff authentication secret must contain 32 bytes")
        self._secret = secret

    @property
    def issuer_ref(self) -> str:
        return self._issuer_ref

    def authenticate(self, payload: bytes) -> str:
        block_size = hashlib.sha256().block_size
        key = self._secret
        if len(key) > block_size:
            key = hashlib.sha256(key).digest()
        padded_key = key.ljust(block_size, b"\x00")
        inner_pad = bytes(value ^ 0x36 for value in padded_key)
        outer_pad = bytes(value ^ 0x5C for value in padded_key)
        inner_digest = hashlib.sha256(inner_pad + payload).digest()
        return "hmac-sha256:" + hashlib.sha256(
            outer_pad + inner_digest
        ).hexdigest()

    def verify(self, payload: bytes, authentication_ref: str) -> bool:
        expected = self.authenticate(payload).encode("ascii")
        try:
            candidate = authentication_ref.encode("ascii")
        except UnicodeEncodeError:
            return False
        if len(expected) != len(candidate):
            return False
        difference = 0
        for expected_byte, candidate_byte in zip(expected, candidate, strict=True):
            difference |= expected_byte ^ candidate_byte
        return difference == 0


@dataclass(frozen=True, slots=True)
class GoalRuntimeHostHandoff:
    schema_id: str
    provider_runtime_ref: str
    source_revision: str
    replay_context: str
    issuer_ref: str
    authority_ref: str
    currentness_receipt_ref: str
    query: dict[str, object]
    record_payload: str
    observation: dict[str, object]
    payload_digest: str
    authentication_ref: str

    def to_json(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RestoredGoalRuntimeHost:
    host: GoalOperationalRuntimeHost
    authority_ref: str
    query: GoalObservationQuery
    observation: GoalObservation
    handoff: GoalRuntimeHostHandoff


def issue_goal_runtime_host_handoff(
    *,
    host: GoalOperationalRuntimeHost,
    authority_ref: str,
    query: GoalObservationQuery,
    provider_runtime_ref: str,
    source_revision: str,
    currentness_receipt_ref: str,
    replay_context: str,
    authenticator: GoalRuntimeHostHandoffAuthenticator,
) -> GoalRuntimeHostHandoff:
    if type(host) is not GoalOperationalRuntimeHost:
        raise TypeError("host must be exact GoalOperationalRuntimeHost")
    authority_ref = _required(authority_ref, "authority_ref")
    if not isinstance(query, GoalObservationQuery):
        raise TypeError("query must be GoalObservationQuery")
    observation = host.observe(authority_ref, query)
    if (
        observation is None
        or observation.outcome is not ObservationOutcome.FOUND
        or observation.goal is None
        or observation.lane is None
        or observation.row is None
    ):
        raise ValueError("host handoff requires one exact found row observation")
    record = host.read(authority_ref)
    if record is None:
        raise ValueError("host authority is not admitted")
    provider_runtime_ref = _required(provider_runtime_ref, "provider_runtime_ref")
    source_revision = _required(source_revision, "source_revision")
    replay_context = _required(replay_context, "replay_context")
    issuer_ref = _required(authenticator.issuer_ref, "issuer_ref")
    currentness_receipt_ref = _required(
        currentness_receipt_ref, "currentness_receipt_ref"
    )
    query_wire = _query_wire(query)
    record_payload = encode_goal_operational_record(record)
    observation_wire = _observation_wire(observation)
    body: dict[str, object] = {
        "schema_id": HANDOFF_SCHEMA_ID,
        "provider_runtime_ref": provider_runtime_ref,
        "source_revision": source_revision,
        "replay_context": replay_context,
        "issuer_ref": issuer_ref,
        "authority_ref": authority_ref,
        "currentness_receipt_ref": currentness_receipt_ref,
        "query": query_wire,
        "record_payload": record_payload,
        "observation": observation_wire,
    }
    payload_digest = _digest(body)
    authenticated_payload = _canonical_bytes(
        {**body, "payload_digest": payload_digest}
    )
    return GoalRuntimeHostHandoff(
        schema_id=HANDOFF_SCHEMA_ID,
        provider_runtime_ref=provider_runtime_ref,
        source_revision=source_revision,
        replay_context=replay_context,
        issuer_ref=issuer_ref,
        authority_ref=authority_ref,
        currentness_receipt_ref=currentness_receipt_ref,
        query=query_wire,
        record_payload=record_payload,
        observation=observation_wire,
        payload_digest=payload_digest,
        authentication_ref=authenticator.authenticate(authenticated_payload),
    )


def encode_goal_runtime_host_handoff(handoff: GoalRuntimeHostHandoff) -> str:
    _validate_handoff_shape(handoff)
    return _canonical_bytes(handoff.to_json()).decode("utf-8")


def decode_goal_runtime_host_handoff(payload: str) -> GoalRuntimeHostHandoff:
    if not isinstance(payload, str) or not payload:
        raise ValueError("handoff payload must be non-empty JSON text")
    raw = json.loads(payload)
    if not isinstance(raw, dict):
        raise TypeError("handoff payload must decode to an object")
    expected = {
        "schema_id",
        "provider_runtime_ref",
        "source_revision",
        "replay_context",
        "issuer_ref",
        "authority_ref",
        "currentness_receipt_ref",
        "query",
        "record_payload",
        "observation",
        "payload_digest",
        "authentication_ref",
    }
    if set(raw) != expected:
        raise ValueError("handoff payload fields are not exact")
    if not isinstance(raw["query"], dict) or not isinstance(raw["observation"], dict):
        raise TypeError("handoff query and observation must be objects")
    handoff = GoalRuntimeHostHandoff(
        schema_id=_required(raw["schema_id"], "schema_id"),
        provider_runtime_ref=_required(
            raw["provider_runtime_ref"], "provider_runtime_ref"
        ),
        source_revision=_required(raw["source_revision"], "source_revision"),
        replay_context=_required(raw["replay_context"], "replay_context"),
        issuer_ref=_required(raw["issuer_ref"], "issuer_ref"),
        authority_ref=_required(raw["authority_ref"], "authority_ref"),
        currentness_receipt_ref=_required(
            raw["currentness_receipt_ref"], "currentness_receipt_ref"
        ),
        query={str(key): value for key, value in raw["query"].items()},
        record_payload=_required(raw["record_payload"], "record_payload"),
        observation={str(key): value for key, value in raw["observation"].items()},
        payload_digest=_required(raw["payload_digest"], "payload_digest"),
        authentication_ref=_required(
            raw["authentication_ref"], "authentication_ref"
        ),
    )
    _validate_handoff_shape(handoff)
    return handoff


def restore_goal_runtime_host_handoff(
    *,
    handoff: GoalRuntimeHostHandoff,
    authenticator: GoalRuntimeHostHandoffAuthenticator,
    expected_authority_ref: str,
    expected_provider_runtime_ref: str,
    expected_source_revision: str,
    expected_currentness_receipt_ref: str,
    expected_replay_context: str,
) -> RestoredGoalRuntimeHost:
    _validate_handoff_shape(handoff)
    if handoff.issuer_ref != authenticator.issuer_ref:
        raise ValueError("handoff issuer does not match authenticator")
    if handoff.authority_ref != _required(
        expected_authority_ref, "expected_authority_ref"
    ):
        raise ValueError("handoff authority does not match expected authority")
    if handoff.provider_runtime_ref != _required(
        expected_provider_runtime_ref, "expected_provider_runtime_ref"
    ):
        raise ValueError("handoff provider runtime is stale")
    if handoff.source_revision != _required(
        expected_source_revision, "expected_source_revision"
    ):
        raise ValueError("handoff source revision is stale")
    if handoff.currentness_receipt_ref != _required(
        expected_currentness_receipt_ref, "expected_currentness_receipt_ref"
    ):
        raise ValueError("handoff currentness receipt is stale")
    if handoff.replay_context != _required(
        expected_replay_context, "expected_replay_context"
    ):
        raise ValueError("handoff replay context is stale")
    body = _handoff_body(handoff)
    if _digest(body) != handoff.payload_digest:
        raise ValueError("handoff payload digest is invalid")
    authenticated_payload = _canonical_bytes(
        {**body, "payload_digest": handoff.payload_digest}
    )
    if not authenticator.verify(authenticated_payload, handoff.authentication_ref):
        raise ValueError("handoff authentication is invalid")
    record = decode_goal_operational_record(handoff.record_payload)
    if record.authority_ref != handoff.authority_ref:
        raise ValueError("handoff record authority does not match envelope")
    expected_store_generation = _integer(
        handoff.observation.get("store_generation"), "store_generation"
    )
    store = InMemoryGoalStateStore()
    created = store.create(handoff.authority_ref, handoff.record_payload)
    if not created.applied:
        raise AssertionError("fresh restoration store rejected authority")
    for generation in range(expected_store_generation):
        advanced = store.compare_and_set(
            handoff.authority_ref,
            expected_generation=generation,
            payload=handoff.record_payload,
        )
        if not advanced.applied:
            raise AssertionError("fresh restoration store generation conflict")
    host = GoalOperationalRuntimeHost(store)
    query = _query_from_wire(handoff.query)
    observation = host.observe(handoff.authority_ref, query)
    if observation is None or _observation_wire(observation) != handoff.observation:
        raise ValueError("restored host observation differs from handoff")
    return RestoredGoalRuntimeHost(
        host=host,
        authority_ref=handoff.authority_ref,
        query=query,
        observation=observation,
        handoff=handoff,
    )


def _handoff_body(handoff: GoalRuntimeHostHandoff) -> dict[str, object]:
    value = handoff.to_json()
    value.pop("payload_digest")
    value.pop("authentication_ref")
    return value


def _validate_handoff_shape(handoff: GoalRuntimeHostHandoff) -> None:
    if handoff.schema_id != HANDOFF_SCHEMA_ID:
        raise ValueError("unsupported Goal runtime host handoff schema")
    for field in (
        "provider_runtime_ref",
        "source_revision",
        "replay_context",
        "issuer_ref",
        "authority_ref",
        "currentness_receipt_ref",
        "record_payload",
        "payload_digest",
        "authentication_ref",
    ):
        _required(getattr(handoff, field), field)
    _query_from_wire(handoff.query)


def _query_wire(query: GoalObservationQuery) -> dict[str, object]:
    return {
        "depth": query.depth.value,
        "goal_ref": query.goal_ref,
        "goal_tag": query.goal_tag,
        "lane_ref": query.lane_ref,
        "lane_key": query.lane_key,
        "row_ref": query.row_ref,
        "row_key": query.row_key,
    }


def _query_from_wire(raw: dict[str, object]) -> GoalObservationQuery:
    expected = {
        "depth",
        "goal_ref",
        "goal_tag",
        "lane_ref",
        "lane_key",
        "row_ref",
        "row_key",
    }
    if set(raw) != expected:
        raise ValueError("handoff observation query fields are not exact")
    return GoalObservationQuery(
        depth=ObservationDepth(_required(raw["depth"], "depth")),
        goal_ref=_optional(raw["goal_ref"], "goal_ref"),
        goal_tag=_optional(raw["goal_tag"], "goal_tag"),
        lane_ref=_optional(raw["lane_ref"], "lane_ref"),
        lane_key=_optional(raw["lane_key"], "lane_key"),
        row_ref=_optional(raw["row_ref"], "row_ref"),
        row_key=_optional(raw["row_key"], "row_key"),
    )


def _observation_wire(observation: GoalObservation) -> dict[str, object]:
    return json.loads(_canonical_bytes(asdict(observation)))


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _required(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty normalized text")
    return value


def _optional(value: object, field: str) -> str | None:
    return None if value is None else _required(value, field)


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a nonnegative integer")
    return value
