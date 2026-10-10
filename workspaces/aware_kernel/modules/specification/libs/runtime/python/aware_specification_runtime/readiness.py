"""Pure Specification phase dependency readiness evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .values import (
    SpecificationContractError,
    SpecificationPhaseAcceptance,
    SpecificationSnapshot,
    invariant_closure_digest,
    phase_ref,
    token,
)


class SpecificationReadinessStatus(StrEnum):
    READY = "ready"
    HELD = "held"
    UNAVAILABLE = "unavailable"
    CONFLICTING = "conflicting"


@dataclass(frozen=True, slots=True)
class SpecificationPhaseReadiness:
    phase_ref: str
    status: SpecificationReadinessStatus
    blocker_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self) is not SpecificationPhaseReadiness:
            raise SpecificationContractError("readiness type must be exact")
        token(self.phase_ref, "phase_ref")
        if type(self.status) is not SpecificationReadinessStatus:
            raise SpecificationContractError("readiness status must be exact")
        if type(self.blocker_refs) is not tuple or any(
            type(value) is not str for value in self.blocker_refs
        ):
            raise SpecificationContractError("blocker_refs must be exact")
        normalized = tuple(token(value, "blocker_ref") for value in self.blocker_refs)
        if normalized != tuple(sorted(set(normalized))):
            raise SpecificationContractError("blocker_refs must be unique and sorted")


def evaluate_specification_readiness(
    snapshot: SpecificationSnapshot,
    acceptances: tuple[SpecificationPhaseAcceptance, ...],
) -> tuple[SpecificationPhaseReadiness, ...]:
    if type(snapshot) is not SpecificationSnapshot:
        raise SpecificationContractError("snapshot type must be exact")
    snapshot.__post_init__()
    if type(acceptances) is not tuple or any(
        type(value) is not SpecificationPhaseAcceptance for value in acceptances
    ):
        raise SpecificationContractError("acceptances must be an exact tuple")
    index = {
        phase_ref(definition.key, phase.phase_key): (definition, phase)
        for definition in snapshot.definitions
        for phase in definition.phases
    }
    selected: dict[str, list[SpecificationPhaseAcceptance]] = {}
    for acceptance in acceptances:
        acceptance.__post_init__()
        if acceptance.phase_ref not in index:
            raise SpecificationContractError("acceptance phase is unavailable")
        selected.setdefault(acceptance.phase_ref, []).append(acceptance)

    results: list[SpecificationPhaseReadiness] = []
    for current_ref, (_, phase) in sorted(index.items()):
        blockers: list[str] = []
        conflict = False
        unavailable = False
        for dependency in phase.dependencies:
            target = index.get(dependency.required_phase_ref)
            if target is None:
                unavailable = True
                blockers.append(dependency.required_phase_ref)
                continue
            observations = selected.get(dependency.required_phase_ref, [])
            if len(observations) > 1:
                conflict = True
                blockers.append(dependency.required_phase_ref)
                continue
            if not observations:
                blockers.append(dependency.required_phase_ref)
                continue
            _, target_phase = target
            observation = observations[0]
            expected_invariants = invariant_closure_digest(
                snapshot, dependency.required_phase_ref
            )
            if (
                observation.gate_digest != target_phase.gate.gate_digest
                or observation.invariant_closure_digest != expected_invariants
                or observation.gate_digest != dependency.required_gate_digest
            ):
                blockers.append(dependency.required_phase_ref)
        status = (
            SpecificationReadinessStatus.CONFLICTING
            if conflict
            else SpecificationReadinessStatus.UNAVAILABLE
            if unavailable
            else SpecificationReadinessStatus.HELD
            if blockers
            else SpecificationReadinessStatus.READY
        )
        results.append(
            SpecificationPhaseReadiness(
                phase_ref=current_ref,
                status=status,
                blocker_refs=tuple(sorted(set(blockers))),
            )
        )
    return tuple(results)
