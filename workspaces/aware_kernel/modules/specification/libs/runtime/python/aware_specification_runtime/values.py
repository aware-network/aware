"""Portable Specification definitions and acceptance evidence."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import cast

SPECIFICATION_SNAPSHOT_CONTRACT = "aware.specification.snapshot.v1"
PHASE_ACCEPTANCE_CONTRACT = "aware.specification.phase-acceptance.v1"


class SpecificationContractError(ValueError):
    """Raised when Specification meaning is malformed or inconsistent."""


class SpecificationPhaseDependencyKind(StrEnum):
    REQUIRES = "requires"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest(contract: str, payload: object) -> str:
    return f"sha256:{sha256(canonical_json_bytes({'contract': contract, 'payload': payload})).hexdigest()}"


def _normalized_text(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or unicodedata.normalize("NFC", value) != value
    ):
        raise SpecificationContractError(
            f"{field_name} must be normalized non-empty text"
        )
    return value


def token(value: object, field_name: str) -> str:
    result = _normalized_text(value, field_name)
    if field_name in {"phase_ref", "blocker_ref"}:
        return canonical_phase_ref(result, field_name)
    if field_name == "coordinate":
        return canonical_movement_coordinate(result, field_name)
    return result


def _key(
    value: object,
    field_name: str,
    *,
    separators: frozenset[str],
    maximum_bytes: int,
) -> str:
    result = _normalized_text(value, field_name)
    valid = "abcdefghijklmnopqrstuvwxyz"
    continuation = valid + "0123456789"
    if (
        result[0] not in valid
        or result[-1] in separators
        or any(
            character not in continuation and character not in separators
            for character in result
        )
        or any(
            character in separators and result[index - 1] in separators
            for index, character in enumerate(result)
            if index > 0
        )
        or len(result.encode("utf-8")) > maximum_bytes
    ):
        raise SpecificationContractError(f"{field_name} has invalid key syntax")
    return result


def specification_key(value: object, field_name: str = "specification_key") -> str:
    return _key(
        value,
        field_name,
        separators=frozenset({".", "-"}),
        maximum_bytes=192,
    )


def member_key(value: object, field_name: str) -> str:
    return _key(value, field_name, separators=frozenset({"-"}), maximum_bytes=96)


def semantic_ref(value: object, field_name: str) -> str:
    try:
        return _key(
            value,
            field_name,
            separators=frozenset({".", "-"}),
            maximum_bytes=2**31 - 1,
        )
    except SpecificationContractError as error:
        raise SpecificationContractError(
            f"{field_name} must be an exact semantic ref"
        ) from error


def canonical_invariant_ref(value: object, field_name: str) -> str:
    result = _normalized_text(value, field_name)
    prefix = "specification:"
    owner, separator, member = result.removeprefix(prefix).partition("/invariant:")
    if not result.startswith(prefix) or separator == "":
        raise SpecificationContractError(
            f"{field_name} must be a canonical invariant ref"
        )
    _ = specification_key(owner, field_name)
    _ = member_key(member, field_name)
    if result != f"{prefix}{owner}/invariant:{member}":
        raise SpecificationContractError(
            f"{field_name} must be a canonical invariant ref"
        )
    return result


def canonical_phase_ref(value: object, field_name: str) -> str:
    result = _normalized_text(value, field_name)
    prefix = "specification:"
    owner, separator, member = result.removeprefix(prefix).partition("/phase:")
    if not result.startswith(prefix) or separator == "":
        raise SpecificationContractError(f"{field_name} must be a canonical phase ref")
    _ = specification_key(owner, field_name)
    _ = member_key(member, field_name)
    if result != f"{prefix}{owner}/phase:{member}":
        raise SpecificationContractError(f"{field_name} must be a canonical phase ref")
    return result


def canonical_movement_coordinate(value: object, field_name: str) -> str:
    result = _normalized_text(value, field_name)
    prefix = "specification:"
    if not result.startswith(prefix):
        raise SpecificationContractError(
            f"{field_name} must be a canonical Specification member coordinate"
        )
    owner_and_path = result.removeprefix(prefix)
    owner, separator, path = owner_and_path.partition("/")
    _ = specification_key(owner, field_name)
    if separator == "":
        expected = f"{prefix}{owner}"
    elif path.startswith("invariant:") and "/" not in path:
        member = path.removeprefix("invariant:")
        _ = member_key(member, field_name)
        expected = f"{prefix}{owner}/invariant:{member}"
    elif path.startswith("phase:"):
        phase_body = path.removeprefix("phase:")
        phase, nested_separator, nested = phase_body.partition("/")
        _ = member_key(phase, field_name)
        expected = f"{prefix}{owner}/phase:{phase}"
        if nested_separator:
            nested_kind, colon, nested_member = nested.partition(":")
            if (
                colon == ""
                or nested_kind not in {"gate", "dependency", "iteration"}
                or "/" in nested_member
            ):
                raise SpecificationContractError(
                    f"{field_name} must be a canonical Specification member coordinate"
                )
            _ = member_key(nested_member, field_name)
            expected = f"{expected}/{nested_kind}:{nested_member}"
    else:
        raise SpecificationContractError(
            f"{field_name} must be a canonical Specification member coordinate"
        )
    if result != expected:
        raise SpecificationContractError(
            f"{field_name} must be a canonical Specification member coordinate"
        )
    return result


def optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return token(value, field_name)


def exact_int(value: object, field_name: str, *, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        raise SpecificationContractError(
            f"{field_name} must be an integer >= {minimum}"
        )
    return value


def sha256_ref(value: object, field_name: str) -> str:
    result = token(value, field_name)
    body = result.removeprefix("sha256:")
    if (
        not result.startswith("sha256:")
        or len(body) != 64
        or any(character not in "0123456789abcdef" for character in body)
    ):
        raise SpecificationContractError(
            f"{field_name} must be a lowercase SHA-256 ref"
        )
    return result


def utc_instant(value: object, field_name: str) -> str:
    result = token(value, field_name)
    if not result.endswith("Z"):
        raise SpecificationContractError(f"{field_name} must be canonical UTC")
    try:
        parsed = datetime.fromisoformat(result)
    except ValueError as error:
        raise SpecificationContractError(
            f"{field_name} must be canonical UTC"
        ) from error
    if parsed.astimezone(UTC).isoformat().replace("+00:00", "Z") != result:
        raise SpecificationContractError(f"{field_name} must be canonical UTC")
    return result


def exact_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise SpecificationContractError(f"{field_name} must be an exact tuple")
    return value


def specification_ref(value: str) -> str:
    return f"specification:{specification_key(value)}"


def invariant_ref(specification_key: str, invariant_key: str) -> str:
    return f"{specification_ref(specification_key)}/invariant:{member_key(invariant_key, 'invariant_key')}"


def phase_ref(specification_key: str, phase_key: str) -> str:
    return f"{specification_ref(specification_key)}/phase:{member_key(phase_key, 'phase_key')}"


@dataclass(frozen=True, slots=True)
class SpecificationInvariantDefinition:
    invariant_key: str
    statement: str
    semantic_revision: int = 1

    def __post_init__(self) -> None:
        if type(self) is not SpecificationInvariantDefinition:
            raise SpecificationContractError("invariant type must be exact")
        object.__setattr__(
            self, "invariant_key", member_key(self.invariant_key, "invariant_key")
        )
        object.__setattr__(self, "statement", token(self.statement, "statement"))
        exact_int(self.semantic_revision, "semantic_revision", minimum=1)


@dataclass(frozen=True, slots=True)
class SpecificationPhaseGateDefinition:
    gate_key: str
    promise: str
    gate_contract: str
    evidence_schema_ref: str
    invariant_refs: tuple[str, ...] = ()
    gate_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not SpecificationPhaseGateDefinition:
            raise SpecificationContractError("gate type must be exact")
        object.__setattr__(self, "gate_key", member_key(self.gate_key, "gate_key"))
        object.__setattr__(self, "promise", token(self.promise, "promise"))
        object.__setattr__(
            self,
            "gate_contract",
            semantic_ref(self.gate_contract, "gate_contract"),
        )
        object.__setattr__(
            self,
            "evidence_schema_ref",
            semantic_ref(self.evidence_schema_ref, "evidence_schema_ref"),
        )
        refs = exact_tuple(self.invariant_refs, "invariant_refs")
        normalized = tuple(
            canonical_invariant_ref(value, "invariant_ref") for value in refs
        )
        if normalized != tuple(sorted(set(normalized))):
            raise SpecificationContractError("invariant_refs must be unique and sorted")
        object.__setattr__(self, "invariant_refs", normalized)
        expected = digest("aware.specification.phase-gate.v1", self.semantic_body())
        existing = getattr(self, "gate_digest", expected)
        if existing != expected:
            raise SpecificationContractError("gate_digest does not match gate meaning")
        object.__setattr__(self, "gate_digest", expected)

    def semantic_body(self) -> dict[str, object]:
        return {
            "gate_key": self.gate_key,
            "promise": self.promise,
            "gate_contract": self.gate_contract,
            "evidence_schema_ref": self.evidence_schema_ref,
            "invariant_refs": list(self.invariant_refs),
        }


@dataclass(frozen=True, slots=True)
class SpecificationPhaseDependency:
    dependency_key: str
    required_phase_ref: str
    required_gate_digest: str
    kind: SpecificationPhaseDependencyKind = SpecificationPhaseDependencyKind.REQUIRES
    rationale: str | None = None

    def __post_init__(self) -> None:
        if type(self) is not SpecificationPhaseDependency:
            raise SpecificationContractError("dependency type must be exact")
        object.__setattr__(
            self,
            "dependency_key",
            member_key(self.dependency_key, "dependency_key"),
        )
        object.__setattr__(
            self,
            "required_phase_ref",
            canonical_phase_ref(self.required_phase_ref, "required_phase_ref"),
        )
        object.__setattr__(
            self,
            "required_gate_digest",
            sha256_ref(self.required_gate_digest, "required_gate_digest"),
        )
        if type(self.kind) is not SpecificationPhaseDependencyKind:
            raise SpecificationContractError("dependency kind must be exact")
        object.__setattr__(
            self, "rationale", optional_text(self.rationale, "rationale")
        )


@dataclass(frozen=True, slots=True)
class SpecificationIterationPlan:
    iteration_key: str
    title: str
    objective: str
    plan_revision: int = 1

    def __post_init__(self) -> None:
        if type(self) is not SpecificationIterationPlan:
            raise SpecificationContractError("iteration type must be exact")
        object.__setattr__(
            self, "iteration_key", member_key(self.iteration_key, "iteration_key")
        )
        object.__setattr__(self, "title", token(self.title, "title"))
        object.__setattr__(self, "objective", token(self.objective, "objective"))
        exact_int(self.plan_revision, "plan_revision", minimum=1)


@dataclass(frozen=True, slots=True)
class SpecificationPhaseDefinition:
    phase_key: str
    title: str
    ordinal: int
    gate: SpecificationPhaseGateDefinition
    dependencies: tuple[SpecificationPhaseDependency, ...] = ()
    iterations: tuple[SpecificationIterationPlan, ...] = ()
    description: str | None = None

    def __post_init__(self) -> None:
        if type(self) is not SpecificationPhaseDefinition:
            raise SpecificationContractError("phase type must be exact")
        object.__setattr__(self, "phase_key", member_key(self.phase_key, "phase_key"))
        object.__setattr__(self, "title", token(self.title, "title"))
        exact_int(self.ordinal, "ordinal", minimum=0)
        if type(self.gate) is not SpecificationPhaseGateDefinition:
            raise SpecificationContractError("phase gate must be exact")
        self.gate.__post_init__()
        dependencies = cast(
            tuple[SpecificationPhaseDependency, ...],
            exact_tuple(self.dependencies, "dependencies"),
        )
        if any(
            type(value) is not SpecificationPhaseDependency for value in dependencies
        ):
            raise SpecificationContractError("phase dependencies must be exact")
        for value in dependencies:
            value.__post_init__()
        if tuple(value.dependency_key for value in dependencies) != tuple(
            sorted({value.dependency_key for value in dependencies})
        ):
            raise SpecificationContractError("dependencies must be unique and sorted")
        if len({value.required_phase_ref for value in dependencies}) != len(
            dependencies
        ):
            raise SpecificationContractError(
                "dependency required phase targets must be unique"
            )
        iterations = cast(
            tuple[SpecificationIterationPlan, ...],
            exact_tuple(self.iterations, "iterations"),
        )
        if any(type(value) is not SpecificationIterationPlan for value in iterations):
            raise SpecificationContractError("phase iterations must be exact")
        for value in iterations:
            value.__post_init__()
        if tuple(value.iteration_key for value in iterations) != tuple(
            sorted({value.iteration_key for value in iterations})
        ):
            raise SpecificationContractError("iterations must be unique and sorted")
        object.__setattr__(
            self, "description", optional_text(self.description, "description")
        )


@dataclass(frozen=True, slots=True)
class SpecificationDefinition:
    key: str
    title: str
    version_number: int
    semantic_resolution_digest: str
    invariants: tuple[SpecificationInvariantDefinition, ...] = ()
    phases: tuple[SpecificationPhaseDefinition, ...] = ()
    description: str | None = None

    def __post_init__(self) -> None:
        if type(self) is not SpecificationDefinition:
            raise SpecificationContractError("specification type must be exact")
        object.__setattr__(self, "key", specification_key(self.key, "key"))
        object.__setattr__(self, "title", token(self.title, "title"))
        exact_int(self.version_number, "version_number", minimum=1)
        object.__setattr__(
            self,
            "semantic_resolution_digest",
            sha256_ref(self.semantic_resolution_digest, "semantic_resolution_digest"),
        )
        invariants = cast(
            tuple[SpecificationInvariantDefinition, ...],
            exact_tuple(self.invariants, "invariants"),
        )
        if any(
            type(value) is not SpecificationInvariantDefinition for value in invariants
        ):
            raise SpecificationContractError("invariants must be exact")
        for value in invariants:
            value.__post_init__()
        if tuple(value.invariant_key for value in invariants) != tuple(
            sorted({value.invariant_key for value in invariants})
        ):
            raise SpecificationContractError("invariants must be unique and sorted")
        valid_invariant_refs = {
            invariant_ref(self.key, value.invariant_key) for value in invariants
        }
        phases = cast(
            tuple[SpecificationPhaseDefinition, ...],
            exact_tuple(self.phases, "phases"),
        )
        if any(type(value) is not SpecificationPhaseDefinition for value in phases):
            raise SpecificationContractError("phases must be exact")
        for value in phases:
            value.__post_init__()
            if not set(value.gate.invariant_refs) <= valid_invariant_refs:
                raise SpecificationContractError("gate references an unknown invariant")
        if tuple(value.phase_key for value in phases) != tuple(
            sorted({value.phase_key for value in phases})
        ):
            raise SpecificationContractError("phases must be unique and sorted")
        object.__setattr__(
            self, "description", optional_text(self.description, "description")
        )


def _phase_index(
    definitions: tuple[SpecificationDefinition, ...],
) -> dict[str, SpecificationPhaseDefinition]:
    result: dict[str, SpecificationPhaseDefinition] = {}
    for definition in definitions:
        for phase in definition.phases:
            result[phase_ref(definition.key, phase.phase_key)] = phase
    return result


def _assert_acyclic(index: dict[str, SpecificationPhaseDefinition]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(current: str) -> None:
        if current in visiting:
            raise SpecificationContractError("phase dependency graph contains a cycle")
        if current in visited:
            return
        visiting.add(current)
        for dependency in index[current].dependencies:
            visit(dependency.required_phase_ref)
        visiting.remove(current)
        visited.add(current)

    for current in sorted(index):
        visit(current)


@dataclass(frozen=True, slots=True)
class SpecificationSnapshot:
    definitions: tuple[SpecificationDefinition, ...]
    snapshot_digest: str = field(init=False)
    contract: str = SPECIFICATION_SNAPSHOT_CONTRACT

    def __post_init__(self) -> None:
        if type(self) is not SpecificationSnapshot:
            raise SpecificationContractError("snapshot type must be exact")
        if self.contract != SPECIFICATION_SNAPSHOT_CONTRACT:
            raise SpecificationContractError("snapshot contract is unsupported")
        definitions = cast(
            tuple[SpecificationDefinition, ...],
            exact_tuple(self.definitions, "definitions"),
        )
        if any(type(value) is not SpecificationDefinition for value in definitions):
            raise SpecificationContractError("snapshot definitions must be exact")
        for value in definitions:
            value.__post_init__()
        if tuple(value.key for value in definitions) != tuple(
            sorted({value.key for value in definitions})
        ):
            raise SpecificationContractError("definitions must be unique and sorted")
        index = _phase_index(definitions)
        for owner_ref, phase in index.items():
            for dependency in phase.dependencies:
                target = index.get(dependency.required_phase_ref)
                if target is None:
                    raise SpecificationContractError("dependency target is unavailable")
                if owner_ref == dependency.required_phase_ref:
                    raise SpecificationContractError("phase cannot depend on itself")
                if target.gate.gate_digest != dependency.required_gate_digest:
                    raise SpecificationContractError("dependency gate digest is stale")
        _assert_acyclic(index)
        expected = digest(SPECIFICATION_SNAPSHOT_CONTRACT, snapshot_semantic_body(self))
        existing = getattr(self, "snapshot_digest", expected)
        if existing != expected:
            raise SpecificationContractError("snapshot_digest does not match snapshot")
        object.__setattr__(self, "snapshot_digest", expected)


def invariant_closure_digest(
    snapshot: SpecificationSnapshot, target_phase_ref: str
) -> str:
    snapshot.__post_init__()
    for definition in snapshot.definitions:
        for phase in definition.phases:
            if phase_ref(definition.key, phase.phase_key) == target_phase_ref:
                values = {
                    invariant_ref(definition.key, item.invariant_key): item
                    for item in definition.invariants
                }
                body = [
                    {
                        "invariant_ref": ref,
                        "statement": values[ref].statement,
                        "semantic_revision": values[ref].semantic_revision,
                    }
                    for ref in phase.gate.invariant_refs
                ]
                return digest("aware.specification.invariant-closure.v1", body)
    raise SpecificationContractError("phase_ref is not in snapshot")


@dataclass(frozen=True, slots=True)
class SpecificationPhaseAcceptance:
    acceptance_ref: str
    phase_ref: str
    gate_digest: str
    invariant_closure_digest: str
    evidence_refs: tuple[str, ...]
    authority_ref: str
    authority_revision_ref: str
    observed_at: str
    acceptance_digest: str = field(init=False)
    contract: str = PHASE_ACCEPTANCE_CONTRACT

    def __post_init__(self) -> None:
        if type(self) is not SpecificationPhaseAcceptance:
            raise SpecificationContractError("acceptance type must be exact")
        if self.contract != PHASE_ACCEPTANCE_CONTRACT:
            raise SpecificationContractError("acceptance contract is unsupported")
        for name in (
            "acceptance_ref",
            "authority_ref",
            "authority_revision_ref",
        ):
            object.__setattr__(self, name, token(getattr(self, name), name))
        object.__setattr__(
            self, "phase_ref", canonical_phase_ref(self.phase_ref, "phase_ref")
        )
        object.__setattr__(
            self, "gate_digest", sha256_ref(self.gate_digest, "gate_digest")
        )
        object.__setattr__(
            self,
            "invariant_closure_digest",
            sha256_ref(self.invariant_closure_digest, "invariant_closure_digest"),
        )
        evidence = exact_tuple(self.evidence_refs, "evidence_refs")
        normalized = tuple(token(value, "evidence_ref") for value in evidence)
        if not normalized or normalized != tuple(sorted(set(normalized))):
            raise SpecificationContractError(
                "evidence_refs must be nonempty, unique, and sorted"
            )
        object.__setattr__(self, "evidence_refs", normalized)
        object.__setattr__(
            self, "observed_at", utc_instant(self.observed_at, "observed_at")
        )
        expected = digest(PHASE_ACCEPTANCE_CONTRACT, acceptance_semantic_body(self))
        existing = getattr(self, "acceptance_digest", expected)
        if existing != expected:
            raise SpecificationContractError(
                "acceptance_digest does not match acceptance"
            )
        object.__setattr__(self, "acceptance_digest", expected)


def invariant_to_wire(value: SpecificationInvariantDefinition) -> dict[str, object]:
    value.__post_init__()
    return {
        "invariant_key": value.invariant_key,
        "statement": value.statement,
        "semantic_revision": value.semantic_revision,
    }


def gate_to_wire(value: SpecificationPhaseGateDefinition) -> dict[str, object]:
    value.__post_init__()
    return {**value.semantic_body(), "gate_digest": value.gate_digest}


def dependency_to_wire(value: SpecificationPhaseDependency) -> dict[str, object]:
    value.__post_init__()
    return {
        "dependency_key": value.dependency_key,
        "required_phase_ref": value.required_phase_ref,
        "required_gate_digest": value.required_gate_digest,
        "kind": value.kind.value,
        "rationale": value.rationale,
    }


def iteration_to_wire(value: SpecificationIterationPlan) -> dict[str, object]:
    value.__post_init__()
    return {
        "iteration_key": value.iteration_key,
        "title": value.title,
        "objective": value.objective,
        "plan_revision": value.plan_revision,
    }


def phase_to_wire(value: SpecificationPhaseDefinition) -> dict[str, object]:
    value.__post_init__()
    return {
        "phase_key": value.phase_key,
        "title": value.title,
        "ordinal": value.ordinal,
        "description": value.description,
        "gate": gate_to_wire(value.gate),
        "dependencies": [dependency_to_wire(item) for item in value.dependencies],
        "iterations": [iteration_to_wire(item) for item in value.iterations],
    }


def definition_to_wire(value: SpecificationDefinition) -> dict[str, object]:
    value.__post_init__()
    return {
        "key": value.key,
        "title": value.title,
        "version_number": value.version_number,
        "description": value.description,
        "semantic_resolution_digest": value.semantic_resolution_digest,
        "invariants": [invariant_to_wire(item) for item in value.invariants],
        "phases": [phase_to_wire(item) for item in value.phases],
    }


def snapshot_semantic_body(value: SpecificationSnapshot) -> dict[str, object]:
    return {
        "contract": value.contract,
        "definitions": [definition_to_wire(item) for item in value.definitions],
    }


def snapshot_to_wire(value: SpecificationSnapshot) -> dict[str, object]:
    value.__post_init__()
    return {**snapshot_semantic_body(value), "snapshot_digest": value.snapshot_digest}


def acceptance_semantic_body(value: SpecificationPhaseAcceptance) -> dict[str, object]:
    return {
        "contract": value.contract,
        "acceptance_ref": value.acceptance_ref,
        "phase_ref": value.phase_ref,
        "gate_digest": value.gate_digest,
        "invariant_closure_digest": value.invariant_closure_digest,
        "evidence_refs": list(value.evidence_refs),
        "authority_ref": value.authority_ref,
        "authority_revision_ref": value.authority_revision_ref,
        "observed_at": value.observed_at,
    }


def acceptance_to_wire(value: SpecificationPhaseAcceptance) -> dict[str, object]:
    value.__post_init__()
    return {
        **acceptance_semantic_body(value),
        "acceptance_digest": value.acceptance_digest,
    }
