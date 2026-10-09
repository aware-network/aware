from __future__ import annotations

import pytest

from aware_specification_runtime import (
    SpecificationContractError,
    SpecificationDefinition,
    SpecificationPhaseAcceptance,
    SpecificationPhaseDefinition,
    SpecificationPhaseDependency,
    SpecificationPhaseGateDefinition,
    SpecificationPhaseReadiness,
    SpecificationReadinessStatus,
    SpecificationSnapshot,
    evaluate_specification_readiness,
    invariant_closure_digest,
    phase_ref,
)

RESOLUTION = "sha256:895aff740618ae1e1dd842902fd96298c800a1654a283f73c20e191b46e57b31"


def chain_fixture() -> tuple[SpecificationSnapshot, str, str]:
    base_gate = SpecificationPhaseGateDefinition(
        "artifact", "Artifact accepted", "aware.gate.v1", "aware.proof.artifact"
    )
    live_gate = SpecificationPhaseGateDefinition(
        "live", "Live recovery accepted", "aware.gate.v1", "aware.proof.live"
    )
    base_ref = phase_ref("recovery", "artifact")
    base = SpecificationPhaseDefinition("artifact", "Artifact", 2, base_gate)
    live = SpecificationPhaseDefinition(
        "live",
        "Live recovery",
        4,
        live_gate,
        (
            SpecificationPhaseDependency(
                "requires-artifact", base_ref, base_gate.gate_digest
            ),
        ),
    )
    snapshot = SpecificationSnapshot(
        (
            SpecificationDefinition(
                "recovery", "Recovery", 1, RESOLUTION, phases=(base, live)
            ),
        )
    )
    return snapshot, base_ref, phase_ref("recovery", "live")


def acceptance(
    snapshot: SpecificationSnapshot, target: str
) -> SpecificationPhaseAcceptance:
    phase = next(
        phase
        for definition in snapshot.definitions
        for phase in definition.phases
        if phase_ref(definition.key, phase.phase_key) == target
    )
    return SpecificationPhaseAcceptance(
        f"acceptance:{phase.phase_key}",
        target,
        phase.gate.gate_digest,
        invariant_closure_digest(snapshot, target),
        ("proof:receipt",),
        "authority:reviewer",
        "revision:1",
        "2026-09-05T00:00:00Z",
    )


def test_dependency_is_held_then_ready_from_exact_acceptance() -> None:
    snapshot, base_ref, live_ref = chain_fixture()
    held = {
        value.phase_ref: value
        for value in evaluate_specification_readiness(snapshot, ())
    }
    assert held[base_ref].status is SpecificationReadinessStatus.READY
    assert held[live_ref].status is SpecificationReadinessStatus.HELD
    assert held[live_ref].blocker_refs == (base_ref,)

    ready = {
        value.phase_ref: value
        for value in evaluate_specification_readiness(
            snapshot, (acceptance(snapshot, base_ref),)
        )
    }
    assert ready[live_ref].status is SpecificationReadinessStatus.READY


def test_duplicate_selected_acceptance_is_conflicting() -> None:
    snapshot, base_ref, live_ref = chain_fixture()
    first = acceptance(snapshot, base_ref)
    second = SpecificationPhaseAcceptance(
        "acceptance:artifact-2",
        first.phase_ref,
        first.gate_digest,
        first.invariant_closure_digest,
        ("proof:receipt-2",),
        first.authority_ref,
        "revision:2",
        "2026-09-05T00:01:00Z",
    )
    result = {
        value.phase_ref: value
        for value in evaluate_specification_readiness(snapshot, (first, second))
    }
    assert result[live_ref].status is SpecificationReadinessStatus.CONFLICTING


def test_acceptance_for_predecessor_promise_cannot_satisfy_renewed_gate() -> None:
    snapshot, base_ref, live_ref = chain_fixture()
    stale = SpecificationPhaseAcceptance(
        "acceptance:stale-artifact",
        base_ref,
        "sha256:" + "1" * 64,
        invariant_closure_digest(snapshot, base_ref),
        ("proof:receipt",),
        "authority:reviewer",
        "revision:old-promise",
        "2026-09-05T00:00:00Z",
    )
    result = {
        value.phase_ref: value
        for value in evaluate_specification_readiness(snapshot, (stale,))
    }
    assert result[live_ref].status is SpecificationReadinessStatus.HELD
    assert result[live_ref].blocker_refs == (base_ref,)


@pytest.mark.parametrize(
    "value",
    (
        "not-a-phase-ref",
        "specification:recovery/invariant:safe",
        " specification:recovery/phase:artifact",
        "specification:récovery/phase:artifact",
        "specification:recovery/phase:Artifact",
    ),
)
def test_readiness_phase_ref_must_be_canonical(value: str) -> None:
    with pytest.raises(SpecificationContractError):
        SpecificationPhaseReadiness(
            value,
            SpecificationReadinessStatus.HELD,
            (),
        )


@pytest.mark.parametrize(
    "value",
    (
        "bad",
        "specification:recovery/invariant:safe",
        "specification:recovery/phase:artifact ",
        "specification:recovery/phase:artífact",
        "specification:recovery/phase:artifact/iteration:one",
    ),
)
def test_readiness_blocker_ref_must_be_canonical(value: str) -> None:
    with pytest.raises(SpecificationContractError):
        SpecificationPhaseReadiness(
            phase_ref("recovery", "live"),
            SpecificationReadinessStatus.HELD,
            (value,),
        )
