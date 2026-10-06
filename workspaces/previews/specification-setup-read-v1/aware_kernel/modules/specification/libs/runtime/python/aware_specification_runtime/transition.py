"""Deterministic Specification snapshot movements."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .values import (
    SpecificationContractError,
    SpecificationSnapshot,
    canonical_json_bytes,
    definition_to_wire,
    dependency_to_wire,
    digest,
    gate_to_wire,
    invariant_ref,
    invariant_to_wire,
    iteration_to_wire,
    phase_ref,
    phase_to_wire,
    sha256_ref,
    specification_ref,
    token,
)


class SpecificationMovementKind(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


@dataclass(frozen=True, slots=True)
class SpecificationMovement:
    coordinate: str
    kind: SpecificationMovementKind
    predecessor_digest: str | None
    result_digest: str | None

    def __post_init__(self) -> None:
        if type(self) is not SpecificationMovement:
            raise SpecificationContractError("movement type must be exact")
        token(self.coordinate, "coordinate")
        if type(self.kind) is not SpecificationMovementKind:
            raise SpecificationContractError("movement kind must be exact")
        old = (
            None
            if self.predecessor_digest is None
            else sha256_ref(self.predecessor_digest, "predecessor_digest")
        )
        new = (
            None
            if self.result_digest is None
            else sha256_ref(self.result_digest, "result_digest")
        )
        if self.kind is SpecificationMovementKind.ADDED and (
            old is not None or new is None
        ):
            raise SpecificationContractError("added movement shape is invalid")
        if self.kind is SpecificationMovementKind.REMOVED and (
            old is None or new is not None
        ):
            raise SpecificationContractError("removed movement shape is invalid")
        if self.kind is SpecificationMovementKind.CHANGED and (
            old is None or new is None or old == new
        ):
            raise SpecificationContractError("changed movement shape is invalid")


@dataclass(frozen=True, slots=True)
class SpecificationTransition:
    predecessor_snapshot_digest: str | None
    result_snapshot_digest: str
    movements: tuple[SpecificationMovement, ...]
    transition_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not SpecificationTransition:
            raise SpecificationContractError("transition type must be exact")
        if self.predecessor_snapshot_digest is not None:
            sha256_ref(self.predecessor_snapshot_digest, "predecessor_snapshot_digest")
        sha256_ref(self.result_snapshot_digest, "result_snapshot_digest")
        if type(self.movements) is not tuple or any(
            type(value) is not SpecificationMovement for value in self.movements
        ):
            raise SpecificationContractError("movements must be exact")
        for value in self.movements:
            value.__post_init__()
        if tuple(value.coordinate for value in self.movements) != tuple(
            sorted({value.coordinate for value in self.movements})
        ):
            raise SpecificationContractError("movements must be unique and sorted")
        expected = digest("aware.specification.transition.v1", transition_body(self))
        existing = getattr(self, "transition_digest", expected)
        if existing != expected:
            raise SpecificationContractError("transition_digest mismatch")
        object.__setattr__(self, "transition_digest", expected)


def _members(snapshot: SpecificationSnapshot) -> dict[str, str]:
    snapshot.__post_init__()
    result: dict[str, str] = {}

    def add(coordinate: str, body: object) -> None:
        result[coordinate] = digest(
            "aware.specification.member.v1", canonical_json_bytes(body).decode("utf-8")
        )

    for definition in snapshot.definitions:
        spec_ref = specification_ref(definition.key)
        add(spec_ref, definition_to_wire(definition))
        for invariant in definition.invariants:
            add(
                invariant_ref(definition.key, invariant.invariant_key),
                invariant_to_wire(invariant),
            )
        for phase in definition.phases:
            current_phase_ref = phase_ref(definition.key, phase.phase_key)
            add(current_phase_ref, phase_to_wire(phase))
            add(
                f"{current_phase_ref}/gate:{phase.gate.gate_key}",
                gate_to_wire(phase.gate),
            )
            for dependency in phase.dependencies:
                add(
                    f"{current_phase_ref}/dependency:{dependency.dependency_key}",
                    dependency_to_wire(dependency),
                )
            for iteration in phase.iterations:
                add(
                    f"{current_phase_ref}/iteration:{iteration.iteration_key}",
                    iteration_to_wire(iteration),
                )
    return result


def derive_specification_transition(
    predecessor: SpecificationSnapshot | None, result: SpecificationSnapshot
) -> SpecificationTransition:
    if predecessor is not None and type(predecessor) is not SpecificationSnapshot:
        raise SpecificationContractError("predecessor snapshot type must be exact")
    if type(result) is not SpecificationSnapshot:
        raise SpecificationContractError("result snapshot type must be exact")
    before = {} if predecessor is None else _members(predecessor)
    after = _members(result)
    movements: list[SpecificationMovement] = []
    for coordinate in sorted(set(before) | set(after)):
        old = before.get(coordinate)
        new = after.get(coordinate)
        if old == new:
            continue
        kind = (
            SpecificationMovementKind.ADDED
            if old is None
            else SpecificationMovementKind.REMOVED
            if new is None
            else SpecificationMovementKind.CHANGED
        )
        movements.append(SpecificationMovement(coordinate, kind, old, new))
    return SpecificationTransition(
        predecessor_snapshot_digest=None
        if predecessor is None
        else predecessor.snapshot_digest,
        result_snapshot_digest=result.snapshot_digest,
        movements=tuple(movements),
    )


def transition_body(value: SpecificationTransition) -> dict[str, object]:
    return {
        "predecessor_snapshot_digest": value.predecessor_snapshot_digest,
        "result_snapshot_digest": value.result_snapshot_digest,
        "movements": [
            {
                "coordinate": movement.coordinate,
                "kind": movement.kind.value,
                "predecessor_digest": movement.predecessor_digest,
                "result_digest": movement.result_digest,
            }
            for movement in value.movements
        ],
    }
