"""Read-only, Phase-scoped Workflow projection of verified O7/H4 facts.

The qualified entrance is sealed by the local committed-source provider.  A
missing H4 observation is represented separately and never creates a qualified
Ontology root.  No clock, Issue time, ordinal, or schedule is consulted here.
"""

from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Literal, cast

from .identity import fingerprint
from .phase_contracts import (
    GoalLanePhase,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
)
from .phase_codec import encode_goal_phase_bundle
from .phase_temporal_occurrence import (
    GoalLanePhaseTemporalLedgerV1,
    GoalLanePhaseTemporalObservationV1,
    GoalPhaseTemporalObservationAuthorityKind,
    GoalPhaseTemporalObservationAuthorityV1,
    GoalPhaseTemporalPublicationReceiptV1,
    decode_goal_phase_temporal_observation,
    goal_phase_temporal_phase_binding_digest,
)

_RESULT_SCHEMA = "aware.goal.phase-temporal-projection-result.v1"
_REGISTRY_LIMIT = 128
_REGISTRY: OrderedDict[object, str] = OrderedDict()


class GoalPhaseTemporalProjectionError(ValueError):
    """The supplied source or temporal join is not qualified."""


@dataclass(frozen=True, slots=True)
class GoalPhaseTemporalNotSuppliedV1:
    coordinate: GoalPhaseCoordinate
    reason: Literal[
        "no_temporal_authority",
        "no_h4_observation",
        "legacy_h4_source_evidence_absent",
    ]

    def __post_init__(self) -> None:
        if type(self.coordinate) is not GoalPhaseCoordinate or self.reason not in (
            "no_temporal_authority",
            "no_h4_observation",
            "legacy_h4_source_evidence_absent",
        ):
            raise GoalPhaseTemporalProjectionError("invalid not_supplied result")

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": _RESULT_SCHEMA,
            "kind": "not_supplied",
            "coordinate": _coordinate(self.coordinate),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True, init=False)
class VerifiedGoalPhaseTemporalWorkflowSourceV1:
    """Provider-sealed complete source; plain callers cannot construct it."""

    phase: GoalLanePhase
    ledger: GoalLanePhaseTemporalLedgerV1
    publication_receipt: GoalPhaseTemporalPublicationReceiptV1
    authority: GoalPhaseTemporalObservationAuthorityV1
    observation: GoalLanePhaseTemporalObservationV1
    goal_source_revision: str
    goal_source_path: str
    goal_source_sha256: str
    source_verification_receipt_ref: str
    source_envelope_digest: str
    h4_payload_digest: str
    committed_blob_oid: str
    verification_ref: str
    verifier_token: object = field(repr=False)


def _coordinate(value: GoalPhaseCoordinate) -> dict[str, str]:
    return {
        "goal_tag": value.goal_tag,
        "lane_key": value.lane_key,
        "phase_key": value.phase_key,
    }


def goal_phase_temporal_projection_ref(
    *,
    coordinate: GoalPhaseCoordinate,
    source_envelope_digest: str,
    h4_payload_digest: str,
    observation_ref: str,
    snapshot_receipt_ref: str,
) -> str:
    """Identify one Phase and one exact admitted H4 snapshot projection."""

    if type(coordinate) is not GoalPhaseCoordinate or any(
        type(value) is not str or not value
        for value in (
            source_envelope_digest,
            h4_payload_digest,
            observation_ref,
            snapshot_receipt_ref,
        )
    ):
        raise GoalPhaseTemporalProjectionError("projection identity inputs differ")
    return "goal-phase-temporal-projection:" + fingerprint(
        {
            "schema_id": "aware.goal.phase-temporal-qualified-identity.v1",
            "coordinate": _coordinate(coordinate),
            "source_envelope_digest": source_envelope_digest,
            "h4_payload_digest": h4_payload_digest,
            "observation_ref": observation_ref,
            "snapshot_receipt_ref": snapshot_receipt_ref,
        }
    )


def _source_body(value: VerifiedGoalPhaseTemporalWorkflowSourceV1) -> dict[str, object]:
    return {
        "phase_bundle_json": encode_goal_phase_bundle(
            GoalPhaseContractBundleV1((value.phase,), ())
        ).decode("utf-8"),
        "ledger": value.ledger.to_wire(),
        "publication_receipt": value.publication_receipt.to_wire(),
        "authority": value.authority.to_wire(),
        "observation": value.observation.to_wire(),
        "goal_source_revision": value.goal_source_revision,
        "goal_source_path": value.goal_source_path,
        "goal_source_sha256": value.goal_source_sha256,
        "source_verification_receipt_ref": value.source_verification_receipt_ref,
        "source_envelope_digest": value.source_envelope_digest,
        "h4_payload_digest": value.h4_payload_digest,
        "committed_blob_oid": value.committed_blob_oid,
    }


def _seal_goal_phase_temporal_workflow_source(  # pyright: ignore[reportUnusedFunction]
    *,
    phase: GoalLanePhase,
    ledger: GoalLanePhaseTemporalLedgerV1,
    publication_receipt: GoalPhaseTemporalPublicationReceiptV1,
    authority: GoalPhaseTemporalObservationAuthorityV1,
    observation: GoalLanePhaseTemporalObservationV1,
    goal_source_revision: str,
    goal_source_path: str,
    goal_source_sha256: str,
    source_verification_receipt_ref: str,
    source_envelope_digest: str,
    h4_payload_digest: str,
    committed_blob_oid: str,
) -> VerifiedGoalPhaseTemporalWorkflowSourceV1:
    """Private provider entrance; not an authority resolver or caller API."""

    value = object.__new__(VerifiedGoalPhaseTemporalWorkflowSourceV1)
    object.__setattr__(value, "phase", phase)
    object.__setattr__(value, "ledger", ledger)
    object.__setattr__(value, "publication_receipt", publication_receipt)
    object.__setattr__(value, "authority", authority)
    object.__setattr__(value, "observation", observation)
    object.__setattr__(value, "goal_source_revision", goal_source_revision)
    object.__setattr__(value, "goal_source_path", goal_source_path)
    object.__setattr__(value, "goal_source_sha256", goal_source_sha256)
    object.__setattr__(
        value, "source_verification_receipt_ref", source_verification_receipt_ref
    )
    object.__setattr__(value, "source_envelope_digest", source_envelope_digest)
    object.__setattr__(value, "h4_payload_digest", h4_payload_digest)
    object.__setattr__(value, "committed_blob_oid", committed_blob_oid)
    body = _source_body(value)
    reference = "goal-phase-temporal-workflow-source:" + fingerprint(body)
    token = object()
    object.__setattr__(value, "verification_ref", reference)
    object.__setattr__(value, "verifier_token", token)
    _REGISTRY[token] = fingerprint(body)
    while len(_REGISTRY) > _REGISTRY_LIMIT:
        _ = _REGISTRY.popitem(last=False)
    return value


def _require_verified(value: VerifiedGoalPhaseTemporalWorkflowSourceV1) -> None:
    if type(value) is not VerifiedGoalPhaseTemporalWorkflowSourceV1:
        raise GoalPhaseTemporalProjectionError("source is not provider-sealed")
    try:
        body = _source_body(value)
        token = value.verifier_token
    except (AttributeError, TypeError) as error:
        raise GoalPhaseTemporalProjectionError("source is not provider-sealed") from error
    if (
        _REGISTRY.get(token) != fingerprint(body)
        or value.verification_ref
        != "goal-phase-temporal-workflow-source:" + fingerprint(body)
    ):
        raise GoalPhaseTemporalProjectionError("source was forged or mutated")


@dataclass(frozen=True, slots=True)
class GoalPhaseTemporalQualifiedResultV1:
    coordinate: GoalPhaseCoordinate
    root: dict[str, object]

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": _RESULT_SCHEMA,
            "kind": "qualified",
            "coordinate": _coordinate(self.coordinate),
            "root": self.root,
        }


def _exact_tree(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        lhs, rhs = cast(dict[str, object], left), cast(dict[str, object], right)
        return set(lhs) == set(rhs) and all(
            _exact_tree(lhs[key], rhs[key]) for key in lhs
        )
    if type(left) is list:
        lhs, rhs = cast(list[object], left), cast(list[object], right)
        return len(lhs) == len(rhs) and all(
            _exact_tree(first, second) for first, second in zip(lhs, rhs, strict=True)
        )
    return left == right


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise GoalPhaseTemporalProjectionError("duplicate projection JSON field")
        result[key] = value
    return result


def decode_goal_phase_temporal_projection_result(
    payload: bytes,
    *,
    source: VerifiedGoalPhaseTemporalWorkflowSourceV1 | None = None,
) -> GoalPhaseTemporalNotSuppliedV1 | GoalPhaseTemporalQualifiedResultV1:
    """Decode only a canonical result, independently recomputing qualified facts."""

    if type(payload) is not bytes:
        raise GoalPhaseTemporalProjectionError("projection payload must be bytes")
    try:
        raw: object = cast(
            object, json.loads(payload, object_pairs_hook=_unique_json_object)
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoalPhaseTemporalProjectionError("projection JSON is invalid") from error
    if type(raw) is not dict:
        raise GoalPhaseTemporalProjectionError("projection must be an object")
    fields = cast(dict[str, object], raw)
    if fields.get("schema_id") != _RESULT_SCHEMA:
        raise GoalPhaseTemporalProjectionError("projection schema differs")
    if fields.get("kind") == "not_supplied":
        if set(fields) != {"schema_id", "kind", "coordinate", "reason"}:
            raise GoalPhaseTemporalProjectionError("not_supplied fields differ")
        coordinate = fields["coordinate"]
        if type(coordinate) is not dict or set(cast(dict[str, object], coordinate)) != {
            "goal_tag", "lane_key", "phase_key"
        }:
            raise GoalPhaseTemporalProjectionError("coordinate is invalid")
        values = cast(dict[str, object], coordinate)
        if any(type(value) is not str for value in values.values()):
            raise GoalPhaseTemporalProjectionError("coordinate fields must be text")
        reason = fields["reason"]
        if reason not in (
            "no_temporal_authority",
            "no_h4_observation",
            "legacy_h4_source_evidence_absent",
        ) or type(reason) is not str:
            raise GoalPhaseTemporalProjectionError("not_supplied reason differs")
        result = GoalPhaseTemporalNotSuppliedV1(
            GoalPhaseCoordinate(
                cast(str, values["goal_tag"]),
                cast(str, values["lane_key"]),
                cast(str, values["phase_key"]),
            ),
            cast(
                Literal[
                    "no_temporal_authority",
                    "no_h4_observation",
                    "legacy_h4_source_evidence_absent",
                ],
                reason,
            ),
        )
    elif fields.get("kind") == "qualified":
        if source is None or set(fields) != {
            "schema_id", "kind", "coordinate", "root"
        }:
            raise GoalPhaseTemporalProjectionError(
                "qualified result requires exact verified source"
            )
        result = project_goal_phase_temporal_workflow(source)
    else:
        raise GoalPhaseTemporalProjectionError("projection variant differs")
    if not _exact_tree(fields, result.to_wire()):
        raise GoalPhaseTemporalProjectionError("projection differs from authority")
    return result


def project_goal_phase_temporal_workflow(
    source: VerifiedGoalPhaseTemporalWorkflowSourceV1,
) -> GoalPhaseTemporalQualifiedResultV1:
    """Carry only O7-evaluated selector facts and exact H4 snapshot evidence."""

    _require_verified(source)
    phase, ledger = source.phase, source.ledger
    authority, observation = source.authority, source.observation
    receipt = source.publication_receipt
    binding = goal_phase_temporal_phase_binding_digest(phase)
    if (
        authority.authority_kind is not GoalPhaseTemporalObservationAuthorityKind.H4
        or
        ledger.coordinate != phase.coordinate
        or authority.coordinate != phase.coordinate
        or observation.coordinate != phase.coordinate
        or ledger.current_phase_binding_digest != binding
        or observation.phase_binding_digest != binding
        or authority.phase_binding_digest != binding
        or observation.ledger_digest != ledger.ledger_digest
        or authority.ledger_digest != ledger.ledger_digest
        or observation.observation_authority_ref != authority.authority_ref
        or observation.snapshot_at != authority.snapshot_at
        or observation.currentness != authority.currentness
        or observation.currentness_ref != authority.currentness_receipt_ref
    ):
        raise GoalPhaseTemporalProjectionError("O7/H4 Phase binding differs")
    canonical = decode_goal_phase_temporal_observation(
        json.dumps(observation.to_wire(), sort_keys=True, separators=(",", ":")).encode(),
        phase=phase,
        ledger=ledger,
        authority=authority,
        publication_receipt=receipt,
    )
    if canonical != observation:
        raise GoalPhaseTemporalProjectionError("O7 selected facts differ")
    coordinate = phase.coordinate
    root: dict[str, object] = {
        "projection_ref": goal_phase_temporal_projection_ref(
            coordinate=coordinate,
            source_envelope_digest=source.source_envelope_digest,
            h4_payload_digest=source.h4_payload_digest,
            observation_ref=observation.observation_ref,
            snapshot_receipt_ref=authority.snapshot_receipt_ref,
        ),
        **_coordinate(coordinate),
        "phase_binding_digest": binding,
        "o7_ledger_digest": ledger.ledger_digest,
        "o7_ledger_revision": ledger.coverage_through.ledger_revision,
        "o7_origin_ref": ledger.origin.origin_ref,
        "o7_source_revision_ref": observation.source_revision_ref,
        "o7_publication_receipt_ref": receipt.receipt_ref,
        "h4_goal_source_revision": source.goal_source_revision,
        "h4_goal_source_path": source.goal_source_path,
        "h4_goal_source_sha256": source.goal_source_sha256,
        "h4_source_verification_receipt_ref": source.source_verification_receipt_ref,
        "h4_source_envelope_digest": source.source_envelope_digest,
        "h4_payload_digest": source.h4_payload_digest,
        "h4_observation_authority_ref": authority.authority_ref,
        "h4_observation_ref": observation.observation_ref,
        "h4_snapshot_receipt_ref": authority.snapshot_receipt_ref,
        "h4_currentness_receipt_ref": authority.currentness_receipt_ref,
        "snapshot_at": observation.snapshot_at,
        "currentness": observation.currentness.value,
        "committed_source_verification_ref": source.verification_ref,
        "coverage": {
            "kind": ledger.history_coverage.value,
            "through_phase_binding_digest": ledger.coverage_through.phase_binding_digest,
            "through_ledger_revision": ledger.coverage_through.ledger_revision,
            "through_publication_binding_ref": ledger.coverage_through.publication_binding_ref,
            "gaps": [item.to_wire() for item in ledger.gaps],
        },
        "facts": [
            {
                "selector_kind": fact.selector.kind.value,
                "selector_slot_ref": fact.selector.transition_slot_ref,
                "selector_target_state": (
                    None if fact.selector.target_state is None else fact.selector.target_state.value
                ),
                "availability": fact.availability.value,
                "transition_slot_ref": (
                    None if fact.occurrence is None else fact.occurrence.transition_slot_ref
                ),
                "occurrence_ref": (
                    None if fact.occurrence is None else fact.occurrence.occurrence_ref
                ),
                "from_state": (
                    None if fact.occurrence is None else fact.occurrence.from_state.value
                ),
                "to_state": (
                    None if fact.occurrence is None else fact.occurrence.to_state.value
                ),
                "effective_at": (
                    None if fact.occurrence is None else fact.occurrence.effective_at
                ),
                "recorded_at": (
                    None if fact.occurrence is None else fact.occurrence.recorded_at
                ),
                "proof_refs": list(fact.proof_refs),
            }
            for fact in observation.facts
        ],
    }
    return GoalPhaseTemporalQualifiedResultV1(coordinate, root)
