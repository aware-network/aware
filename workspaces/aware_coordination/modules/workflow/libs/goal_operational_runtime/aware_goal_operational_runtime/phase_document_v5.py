"""Structural V5 provenance reader. No authority verification or writer.

Preserved components are validated through the existing V2/V3/V4 codecs; their
internal reconstructed identities are never exposed as committed authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from .phase_acceptance_provenance import (
    OWNER_PROFILE, AcceptanceProvenanceError, decode_acceptance_provenance_v2,
    QUALIFICATION_SCHEMA, POLICY_SCHEMA,
    _digest, _json, _object, _parse,  # pyright: ignore[reportPrivateUsage]
)
from .phase_document import (
    GOAL_PHASE_EXECUTION_AUTHORITY_SCHEMA,
    decode_goal_phase_native_document, encode_goal_phase_native_document,
)

DOCUMENT_V5 = "aware.goal.lane-phase.document.v5"
PROVENANCE_PROFILE = "aware.goal.acceptance-provenance.v2"
_FIELDS = {
    "schema_id", "authority_profile", "compatibility_profile", "goal_tag",
    "compatibility_projection_sha256", "compatibility_projection_byte_count",
    "definitions", "operational_bundle", "unresolved_dependencies", "source_refs",
    "execution_authority", "native_lane_authorities", "operation_journal_profile",
    "acceptance_provenance_profile", "acceptance_qualifications",
    "acceptance_dependency_policies", "document_ref",
}


class GoalPhaseDocumentV5Error(ValueError):
    """Malformed or internally inconsistent structure; never a trust verdict."""


def _array(value: object) -> list[object]:
    if type(value) is not list:
        raise GoalPhaseDocumentV5Error("v5_array")
    return cast(list[object], value)


def _mapping(value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise GoalPhaseDocumentV5Error("v5_object")
    return cast(dict[str, object], value)


def _coordinate_key(value: object) -> tuple[str, str, str]:
    coordinate = _mapping(value)
    return (cast(str, coordinate["goal_tag"]), cast(str, coordinate["lane_key"]),
            cast(str, coordinate["phase_key"]))


def _validate_components(body: dict[str, object]) -> None:
    if _mapping(body["execution_authority"]).get("schema_id") != GOAL_PHASE_EXECUTION_AUTHORITY_SCHEMA:
        raise GoalPhaseDocumentV5Error("v5_genesis_provenance_unsupported")
    lanes = _array(body["native_lane_authorities"])
    profile = body["operation_journal_profile"]
    if profile not in ("none", "v1"):
        raise GoalPhaseDocumentV5Error("v5_journal_profile")
    if (profile == "v1") != ("phase_operation_journal" in body):
        raise GoalPhaseDocumentV5Error("v5_journal_presence")
    # Only an internal structural projection; never an old-reader handoff.
    component = {key: value for key, value in body.items() if key not in {
        "acceptance_provenance_profile", "acceptance_qualifications",
        "acceptance_dependency_policies", "document_ref",
    }}
    if lanes:
        component["schema_id"] = "aware.goal.lane-phase.document.v4"
    else:
        del component["native_lane_authorities"]
        del component["operation_journal_profile"]
        component["schema_id"] = ("aware.goal.lane-phase.document.v3" if profile == "v1"
                                  else "aware.goal.lane-phase.document.v2")
    component["document_ref"] = "goal-phase-document:" + _digest(component)
    decoded = decode_goal_phase_native_document(_json(component).encode())
    # Existing codecs already reject coercion/normalization; compare exact wire.
    if _parse(encode_goal_phase_native_document(decoded)) != component:
        raise GoalPhaseDocumentV5Error("v5_component_normalization")


def _validate_qualifications(body: dict[str, object]) -> None:
    definitions = {_coordinate_key(item["coordinate"]): item
                   for raw in _array(body["definitions"]) for item in [_mapping(raw)]}
    required: dict[tuple[tuple[str, str, str], str, str], dict[str, object]] = {}
    phases = _array(_mapping(body["operational_bundle"])["phases"])
    for raw in phases:
        phase = _mapping(raw)
        key = _coordinate_key(phase["coordinate"])
        if phase["state"] == "accepted":
            required[(key, "acceptance", cast(str, phase["last_receipt_ref"]))] = phase
        for item in _array(phase["gate_observations"]):
            observation = _mapping(item)
            if observation["outcome"] == "satisfied":
                required[(key, "gate_observation", cast(str, observation["observation_ref"]))] = observation
    supplied: dict[tuple[tuple[str, str, str], str, str], dict[str, object]] = {}
    ordered: list[tuple[tuple[str, str, str], str, str]] = []
    for raw in _array(body["acceptance_qualifications"]):
        record = decode_acceptance_provenance_v2(_json(raw)).to_wire()
        if record["schema_id"] != QUALIFICATION_SCHEMA:
            raise GoalPhaseDocumentV5Error("v5_qualification_schema")
        coordinate = _coordinate_key(record["coordinate"])
        key = (coordinate, cast(str, record["evidence_kind"]), cast(str, record["evidence_ref"]))
        if key in supplied or key not in required:
            raise GoalPhaseDocumentV5Error("v5_qualification_coverage")
        definition = definitions[coordinate]
        value = required[key]
        current_gate = _mapping(definition["gate"])["gate_digest"]
        evidence_gate = current_gate if record["evidence_kind"] == "acceptance" else value["gate_digest"]
        if record["gate_digest"] != evidence_gate:
            raise GoalPhaseDocumentV5Error("v5_qualification_target")
        if record["mode"] != "legacy_unqualified" and record["definition_ref"] != definition["definition_ref"]:
            raise GoalPhaseDocumentV5Error("v5_qualification_target")
        # Legacy preservation may retain the old definition identity without
        # promoting it. Original authority is a later provider-verifier input.
        if record["evidence_kind"] == "gate_observation":
            if record["mode"] == "owner_attested":
                if value["evaluator_ref"] != OWNER_PROFILE:
                    raise GoalPhaseDocumentV5Error("v5_owner_observation_profile")
            elif value["evaluator_ref"] == OWNER_PROFILE:
                raise GoalPhaseDocumentV5Error("v5_attestation_mode_stripped")
            epoch = _mapping(record["evidence_source_epoch"])
            if epoch["source_revision"] not in _array(value["source_revision_refs"]):
                raise GoalPhaseDocumentV5Error("v5_observation_epoch")
        supplied[key] = record
        ordered.append(key)
    if ordered != sorted(ordered) or set(supplied) != set(required):
        raise GoalPhaseDocumentV5Error("v5_qualification_coverage")
    # A claimed accepted Phase must not change the mode of its supporting
    # current-Gate satisfaction. This checks pairing, not acceptance issuance.
    for key, record in supplied.items():
        if key[1] != "acceptance":
            continue
        matches = [observation for obs_key, observation in supplied.items()
                   if obs_key[0] == key[0] and obs_key[1] == "gate_observation"
                   and all(observation[field] == record[field] for field in (
                       "mode", "profile", "decision_ref", "profile_authorization_ref", "gate_digest", "definition_ref",
                   ))]
        if not matches:
            raise GoalPhaseDocumentV5Error("v5_acceptance_mode_pair")


def _validate_policies(body: dict[str, object]) -> None:
    dependencies = _array(_mapping(body["operational_bundle"])["dependencies"])
    expected = {cast(str, declaration["dependency_key"]): declaration
                for raw in dependencies for declaration in [_mapping(raw)]
                if declaration["relation"] == "requires_acceptance"}
    keys: list[str] = []
    for raw in _array(body["acceptance_dependency_policies"]):
        record = decode_acceptance_provenance_v2(_json(raw)).to_wire()
        if record["schema_id"] != POLICY_SCHEMA:
            raise GoalPhaseDocumentV5Error("v5_policy_schema")
        declaration = _mapping(record["declaration"])
        key = cast(str, declaration["dependency_key"])
        if key not in expected or declaration != expected[key]:
            raise GoalPhaseDocumentV5Error("v5_policy_declaration")
        keys.append(key)
    if keys != sorted(set(keys)) or set(keys) != set(expected):
        raise GoalPhaseDocumentV5Error("v5_policy_coverage")


def _validate(raw: object) -> dict[str, object]:
    body = _mapping(raw)
    journal = body.get("operation_journal_profile") == "v1"
    _ = _object(body, _FIELDS | ({"phase_operation_journal"} if journal else set()))
    if body["schema_id"] != DOCUMENT_V5 or body["acceptance_provenance_profile"] != PROVENANCE_PROFILE:
        raise GoalPhaseDocumentV5Error("v5_profile")
    _validate_components(body)
    _validate_qualifications(body)
    _validate_policies(body)
    expected = "goal-phase-document:" + _digest({key: value for key, value in body.items() if key != "document_ref"})
    if body["document_ref"] != expected:
        raise GoalPhaseDocumentV5Error("v5_document_ref")
    return body


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeDocumentV5:
    """Detached canonical structure; not authenticated acceptance/source."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not GoalPhaseNativeDocumentV5 or type(self.canonical_body) is not str:
            raise GoalPhaseDocumentV5Error("v5_type")
        try:
            body = _validate(_parse(self.canonical_body))
        except (AcceptanceProvenanceError, TypeError, ValueError) as exc:
            raise GoalPhaseDocumentV5Error(str(exc)) from exc
        if self.canonical_body != _json(body):
            raise GoalPhaseDocumentV5Error("v5_canonical")
        return body

    @property
    def document_ref(self) -> str:
        return cast(str, self.to_wire()["document_ref"])


def decode_goal_phase_native_document_v5(payload: bytes) -> GoalPhaseNativeDocumentV5:
    if type(payload) is not bytes:
        raise GoalPhaseDocumentV5Error("v5_payload_type")
    try:
        body = _validate(_parse(payload))
    except (AcceptanceProvenanceError, TypeError, ValueError) as exc:
        raise GoalPhaseDocumentV5Error(str(exc)) from exc
    return GoalPhaseNativeDocumentV5(_json(body))


def encode_goal_phase_native_document_v5(value: GoalPhaseNativeDocumentV5) -> bytes:
    if type(value) is not GoalPhaseNativeDocumentV5:
        raise GoalPhaseDocumentV5Error("v5_type")
    return _json(value.to_wire()).encode()
