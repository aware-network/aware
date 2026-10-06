"""Strict contextual codecs for portable Specification values."""

from __future__ import annotations

import json
from typing import cast

from .values import (
    PHASE_ACCEPTANCE_CONTRACT,
    SPECIFICATION_SNAPSHOT_CONTRACT,
    SpecificationContractError,
    SpecificationDefinition,
    SpecificationInvariantDefinition,
    SpecificationIterationPlan,
    SpecificationPhaseAcceptance,
    SpecificationPhaseDefinition,
    SpecificationPhaseDependency,
    SpecificationPhaseDependencyKind,
    SpecificationPhaseGateDefinition,
    SpecificationSnapshot,
    acceptance_to_wire,
    canonical_json_bytes,
    snapshot_to_wire,
)

type JsonObject = dict[str, object]


def _object(value: object, keys: frozenset[str], field_name: str) -> JsonObject:
    if type(value) is not dict or frozenset(value) != keys:
        raise SpecificationContractError(f"{field_name} fields must be exact")
    return cast(JsonObject, value)


def _list(value: object, field_name: str) -> list[object]:
    if type(value) is not list:
        raise SpecificationContractError(f"{field_name} must be a list")
    return value


def _decode_canonical(body: bytes) -> JsonObject:
    if type(body) is not bytes:
        raise SpecificationContractError("body must be exact bytes")
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise SpecificationContractError("body must be canonical JSON") from error
    try:
        canonical = canonical_json_bytes(value)
    except (TypeError, ValueError) as error:
        raise SpecificationContractError("body must be canonical JSON") from error
    if canonical != body or type(value) is not dict:
        raise SpecificationContractError("body must be canonical JSON object bytes")
    return cast(JsonObject, value)


def _text(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise SpecificationContractError(f"{field_name} must be text")
    return value


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _text(value, field_name)


def _integer(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise SpecificationContractError(f"{field_name} must be an integer")
    return value


def _text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    items = _list(value, field_name)
    if any(type(item) is not str for item in items):
        raise SpecificationContractError(f"{field_name} members must be text")
    return tuple(cast(str, item) for item in items)


def _invariant(value: object) -> SpecificationInvariantDefinition:
    body = _object(
        value,
        frozenset({"invariant_key", "statement", "semantic_revision"}),
        "invariant",
    )
    return SpecificationInvariantDefinition(
        invariant_key=_text(body["invariant_key"], "invariant_key"),
        statement=_text(body["statement"], "statement"),
        semantic_revision=_integer(body["semantic_revision"], "semantic_revision"),
    )


def _gate(value: object) -> SpecificationPhaseGateDefinition:
    body = _object(
        value,
        frozenset(
            {
                "gate_key",
                "promise",
                "gate_contract",
                "evidence_schema_ref",
                "invariant_refs",
                "gate_digest",
            }
        ),
        "gate",
    )
    gate = SpecificationPhaseGateDefinition(
        gate_key=_text(body["gate_key"], "gate_key"),
        promise=_text(body["promise"], "promise"),
        gate_contract=_text(body["gate_contract"], "gate_contract"),
        evidence_schema_ref=_text(body["evidence_schema_ref"], "evidence_schema_ref"),
        invariant_refs=_text_tuple(body["invariant_refs"], "invariant_refs"),
    )
    if body["gate_digest"] != gate.gate_digest:
        raise SpecificationContractError("gate digest is not freshly derived")
    return gate


def _dependency(value: object) -> SpecificationPhaseDependency:
    body = _object(
        value,
        frozenset(
            {
                "dependency_key",
                "required_phase_ref",
                "required_gate_digest",
                "kind",
                "rationale",
            }
        ),
        "dependency",
    )
    try:
        kind = SpecificationPhaseDependencyKind(_text(body["kind"], "kind"))
    except (TypeError, ValueError) as error:
        raise SpecificationContractError("dependency kind is invalid") from error
    return SpecificationPhaseDependency(
        dependency_key=_text(body["dependency_key"], "dependency_key"),
        required_phase_ref=_text(body["required_phase_ref"], "required_phase_ref"),
        required_gate_digest=_text(
            body["required_gate_digest"], "required_gate_digest"
        ),
        kind=kind,
        rationale=_optional_text(body["rationale"], "rationale"),
    )


def _iteration(value: object) -> SpecificationIterationPlan:
    body = _object(
        value,
        frozenset({"iteration_key", "title", "objective", "plan_revision"}),
        "iteration",
    )
    return SpecificationIterationPlan(
        iteration_key=_text(body["iteration_key"], "iteration_key"),
        title=_text(body["title"], "title"),
        objective=_text(body["objective"], "objective"),
        plan_revision=_integer(body["plan_revision"], "plan_revision"),
    )


def _phase(value: object) -> SpecificationPhaseDefinition:
    body = _object(
        value,
        frozenset(
            {
                "phase_key",
                "title",
                "ordinal",
                "description",
                "gate",
                "dependencies",
                "iterations",
            }
        ),
        "phase",
    )
    return SpecificationPhaseDefinition(
        phase_key=_text(body["phase_key"], "phase_key"),
        title=_text(body["title"], "title"),
        ordinal=_integer(body["ordinal"], "ordinal"),
        description=_optional_text(body["description"], "description"),
        gate=_gate(body["gate"]),
        dependencies=tuple(
            _dependency(item) for item in _list(body["dependencies"], "dependencies")
        ),
        iterations=tuple(
            _iteration(item) for item in _list(body["iterations"], "iterations")
        ),
    )


def _definition(value: object) -> SpecificationDefinition:
    body = _object(
        value,
        frozenset(
            {
                "key",
                "title",
                "version_number",
                "description",
                "semantic_resolution_digest",
                "invariants",
                "phases",
            }
        ),
        "definition",
    )
    return SpecificationDefinition(
        key=_text(body["key"], "key"),
        title=_text(body["title"], "title"),
        version_number=_integer(body["version_number"], "version_number"),
        description=_optional_text(body["description"], "description"),
        semantic_resolution_digest=_text(
            body["semantic_resolution_digest"], "semantic_resolution_digest"
        ),
        invariants=tuple(
            _invariant(item) for item in _list(body["invariants"], "invariants")
        ),
        phases=tuple(_phase(item) for item in _list(body["phases"], "phases")),
    )


def encode_specification_snapshot(value: SpecificationSnapshot) -> bytes:
    if type(value) is not SpecificationSnapshot:
        raise SpecificationContractError("snapshot type must be exact")
    return canonical_json_bytes(snapshot_to_wire(value))


def decode_specification_snapshot(body: bytes) -> SpecificationSnapshot:
    root = _object(
        _decode_canonical(body),
        frozenset({"contract", "definitions", "snapshot_digest"}),
        "snapshot",
    )
    if root["contract"] != SPECIFICATION_SNAPSHOT_CONTRACT:
        raise SpecificationContractError("snapshot contract is unsupported")
    result = SpecificationSnapshot(
        definitions=tuple(
            _definition(item) for item in _list(root["definitions"], "definitions")
        )
    )
    if (
        root["snapshot_digest"] != result.snapshot_digest
        or encode_specification_snapshot(result) != body
    ):
        raise SpecificationContractError("snapshot is not freshly derived")
    return result


def encode_phase_acceptance(value: SpecificationPhaseAcceptance) -> bytes:
    if type(value) is not SpecificationPhaseAcceptance:
        raise SpecificationContractError("acceptance type must be exact")
    return canonical_json_bytes(acceptance_to_wire(value))


def decode_phase_acceptance(body: bytes) -> SpecificationPhaseAcceptance:
    root = _object(
        _decode_canonical(body),
        frozenset(
            {
                "contract",
                "acceptance_ref",
                "phase_ref",
                "gate_digest",
                "invariant_closure_digest",
                "evidence_refs",
                "authority_ref",
                "authority_revision_ref",
                "observed_at",
                "acceptance_digest",
            }
        ),
        "acceptance",
    )
    if root["contract"] != PHASE_ACCEPTANCE_CONTRACT:
        raise SpecificationContractError("acceptance contract is unsupported")
    result = SpecificationPhaseAcceptance(
        acceptance_ref=_text(root["acceptance_ref"], "acceptance_ref"),
        phase_ref=_text(root["phase_ref"], "phase_ref"),
        gate_digest=_text(root["gate_digest"], "gate_digest"),
        invariant_closure_digest=_text(
            root["invariant_closure_digest"], "invariant_closure_digest"
        ),
        evidence_refs=_text_tuple(root["evidence_refs"], "evidence_refs"),
        authority_ref=_text(root["authority_ref"], "authority_ref"),
        authority_revision_ref=_text(
            root["authority_revision_ref"], "authority_revision_ref"
        ),
        observed_at=_text(root["observed_at"], "observed_at"),
    )
    if (
        root["acceptance_digest"] != result.acceptance_digest
        or encode_phase_acceptance(result) != body
    ):
        raise SpecificationContractError("acceptance is not freshly derived")
    return result
