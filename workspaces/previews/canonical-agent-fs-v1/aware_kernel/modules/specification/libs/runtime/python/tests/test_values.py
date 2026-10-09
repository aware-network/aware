from __future__ import annotations

from dataclasses import fields, replace

import pytest

from aware_specification_runtime import (
    SpecificationContractError,
    SpecificationDefinition,
    SpecificationInvariantDefinition,
    SpecificationIterationPlan,
    SpecificationPhaseAcceptance,
    SpecificationPhaseDefinition,
    SpecificationPhaseDependency,
    SpecificationPhaseGateDefinition,
    SpecificationSnapshot,
    invariant_ref,
    phase_ref,
)

RESOLUTION = "sha256:895aff740618ae1e1dd842902fd96298c800a1654a283f73c20e191b46e57b31"


def specification_fixture(*, title: str = "Recovery") -> SpecificationDefinition:
    invariant = SpecificationInvariantDefinition("safe", "No unsafe transition")
    gate = SpecificationPhaseGateDefinition(
        "artifact-accepted",
        "Deterministic artifact is independently accepted",
        "aware.specification.gate.evidence-accepted.v1",
        "proof.artifact-acceptance-v1",
        (invariant_ref("recovery", "safe"),),
    )
    phase = SpecificationPhaseDefinition(
        "artifact",
        "Deterministic artifact",
        2,
        gate,
        iterations=(
            SpecificationIterationPlan(
                "artifact-r1", "Artifact R1", "Build deterministic recovery artifact"
            ),
        ),
    )
    return SpecificationDefinition(
        "recovery", title, 1, RESOLUTION, (invariant,), (phase,)
    )


def test_definition_snapshot_and_refs_are_stable() -> None:
    definition = specification_fixture()
    snapshot = SpecificationSnapshot((definition,))

    assert phase_ref("recovery", "artifact") == "specification:recovery/phase:artifact"
    assert snapshot.snapshot_digest.startswith("sha256:")
    assert definition.phases[0].gate.gate_digest.startswith("sha256:")


def test_ordinal_does_not_create_a_dependency() -> None:
    definition = specification_fixture()
    assert definition.phases[0].ordinal == 2
    assert definition.phases[0].dependencies == ()


def test_unknown_invariant_and_unsorted_closures_reject() -> None:
    definition = specification_fixture()
    bad_gate = replace(
        definition.phases[0].gate,
        invariant_refs=(invariant_ref("foreign", "unknown"),),
    )
    with pytest.raises(SpecificationContractError, match="unknown invariant"):
        replace(
            definition,
            phases=(replace(definition.phases[0], gate=bad_gate),),
        )

    with pytest.raises(SpecificationContractError, match="unique and sorted"):
        SpecificationDefinition(
            "recovery",
            "Recovery",
            1,
            RESOLUTION,
            (
                SpecificationInvariantDefinition("z", "Z"),
                SpecificationInvariantDefinition("a", "A"),
            ),
        )


def test_missing_target_stale_gate_self_edge_and_cycle_reject() -> None:
    base = specification_fixture()
    gate = base.phases[0].gate
    missing = SpecificationPhaseDependency(
        "missing", "specification:foreign/phase:x", gate.gate_digest
    )
    with pytest.raises(SpecificationContractError, match="target is unavailable"):
        SpecificationSnapshot(
            (replace(base, phases=(replace(base.phases[0], dependencies=(missing,)),)),)
        )

    self_edge = SpecificationPhaseDependency(
        "self", phase_ref("recovery", "artifact"), gate.gate_digest
    )
    with pytest.raises(SpecificationContractError, match="depend on itself"):
        SpecificationSnapshot(
            (
                replace(
                    base, phases=(replace(base.phases[0], dependencies=(self_edge,)),)
                ),
            )
        )

    gate_a = SpecificationPhaseGateDefinition(
        "a", "A accepted", "aware.gate.v1", "proof.a"
    )
    gate_b = SpecificationPhaseGateDefinition(
        "b", "B accepted", "aware.gate.v1", "proof.b"
    )
    phase_a = SpecificationPhaseDefinition(
        "a",
        "A",
        0,
        gate_a,
        (
            SpecificationPhaseDependency(
                "needs-b", phase_ref("cycle", "b"), gate_b.gate_digest
            ),
        ),
    )
    phase_b = SpecificationPhaseDefinition(
        "b",
        "B",
        1,
        gate_b,
        (
            SpecificationPhaseDependency(
                "needs-a", phase_ref("cycle", "a"), gate_a.gate_digest
            ),
        ),
    )
    with pytest.raises(SpecificationContractError, match="cycle"):
        SpecificationSnapshot(
            (
                SpecificationDefinition(
                    "cycle", "Cycle", 1, RESOLUTION, phases=(phase_a, phase_b)
                ),
            )
        )


def test_foreign_nested_value_rejects() -> None:
    class ForeignGate(SpecificationPhaseGateDefinition):
        pass

    with pytest.raises(SpecificationContractError, match="gate type must be exact"):
        ForeignGate("gate", "Gate", "aware.gate.v1", "proof.gate")


def test_foreign_gate_rejects_before_foreign_behavior() -> None:
    calls: list[str] = []

    class ForeignGate(SpecificationPhaseGateDefinition):
        def __getattribute__(self, name: str) -> object:
            calls.append(name)
            return super().__getattribute__(name)

    foreign = object.__new__(ForeignGate)
    with pytest.raises(SpecificationContractError, match="phase gate must be exact"):
        SpecificationPhaseDefinition("phase", "Phase", 0, foreign)
    assert calls == []


def test_incomplete_object_new_gate_rejects() -> None:
    incomplete = object.__new__(SpecificationPhaseGateDefinition)
    with pytest.raises((AttributeError, SpecificationContractError)):
        incomplete.__post_init__()


@pytest.mark.parametrize(
    "value",
    (
        " recovery",
        "Recovery",
        "recovery_rail",
        "recovery..rail",
        "récovery",
        "r" * 193,
    ),
)
def test_specification_key_grammar_rejects(value: str) -> None:
    with pytest.raises(SpecificationContractError, match="key"):
        SpecificationDefinition(value, "Recovery", 1, RESOLUTION)


@pytest.mark.parametrize(
    "value", (" phase", "Phase", "phase_one", "phase--one", "pháse", "p" * 97)
)
def test_member_key_grammar_rejects(value: str) -> None:
    with pytest.raises(SpecificationContractError, match="key"):
        SpecificationPhaseDefinition(
            value,
            "Phase",
            0,
            SpecificationPhaseGateDefinition(
                "gate", "Accepted", "aware.gate.v1", "aware.proof.v1"
            ),
        )


@pytest.mark.parametrize(
    "contract,evidence",
    (
        ("aware:gate", "aware.proof.v1"),
        ("Aware.gate", "aware.proof.v1"),
        ("aware.gate.v1 ", "aware.proof.v1"),
        ("aware.gate.v1", "aware/proof/v1"),
        ("aware.gate.v1", "aware_proof_v1"),
    ),
)
def test_gate_semantic_refs_reject(contract: str, evidence: str) -> None:
    with pytest.raises(SpecificationContractError):
        SpecificationPhaseGateDefinition("gate", "Accepted", contract, evidence)


def test_duplicate_required_phase_target_rejects() -> None:
    gate = SpecificationPhaseGateDefinition(
        "gate", "Accepted", "aware.gate.v1", "aware.proof.v1"
    )
    target = phase_ref("recovery", "target")
    with pytest.raises(SpecificationContractError, match="targets must be unique"):
        SpecificationPhaseDefinition(
            "owner",
            "Owner",
            0,
            gate,
            dependencies=(
                SpecificationPhaseDependency("first", target, gate.gate_digest),
                SpecificationPhaseDependency("second", target, gate.gate_digest),
            ),
        )


def test_gate_promise_changes_gate_digest() -> None:
    first = SpecificationPhaseGateDefinition(
        "gate", "First promise", "aware.gate.v1", "aware.proof.v1"
    )
    second = SpecificationPhaseGateDefinition(
        "gate", "Second promise", "aware.gate.v1", "aware.proof.v1"
    )
    assert first.gate_digest != second.gate_digest


@pytest.mark.parametrize(
    "value",
    (
        "sha256:" + "A" * 64,
        "sha256:" + "a" * 63,
        "sha256:" + "a" * 65,
        "sha256:" + "a" * 64 + " ",
        "digest:" + "a" * 64,
    ),
)
def test_required_gate_digest_must_be_exact_lowercase_sha256(value: str) -> None:
    with pytest.raises(SpecificationContractError):
        SpecificationPhaseDependency(
            "requires-target", phase_ref("spec", "target"), value
        )


@pytest.mark.parametrize(
    "value",
    (
        "specification:spec/invariant:bad_ref",
        "specification:spec/phase:wrong-kind",
        "specification:Spec/invariant:value",
        " specification:spec/invariant:value",
    ),
)
def test_invariant_ref_shape_is_exact(value: str) -> None:
    with pytest.raises(SpecificationContractError):
        SpecificationPhaseGateDefinition(
            "gate",
            "Accepted",
            "aware.gate.v1",
            "aware.proof.v1",
            (value,),
        )


@pytest.mark.parametrize(
    "value",
    (
        "not-a-phase-ref",
        "specification:spec/invariant:value",
        " specification:spec/phase:value",
        "specification:spéc/phase:value",
        "specification:spec/phase:Value",
        "specification:spec/phase:value/iteration:one",
    ),
)
def test_dependency_and_acceptance_phase_refs_are_exact(value: str) -> None:
    with pytest.raises(SpecificationContractError):
        SpecificationPhaseDependency("requires-value", value, "sha256:" + "1" * 64)
    with pytest.raises(SpecificationContractError):
        SpecificationPhaseAcceptance(
            "acceptance:value",
            value,
            "sha256:" + "1" * 64,
            "sha256:" + "2" * 64,
            ("proof:value",),
            "authority:reviewer",
            "revision:1",
            "2026-09-05T00:00:00Z",
        )


def _portable_values() -> tuple[object, ...]:
    definition = specification_fixture()
    snapshot = SpecificationSnapshot((definition,))
    target = phase_ref("recovery", "artifact")
    acceptance = SpecificationPhaseAcceptance(
        "acceptance:artifact",
        target,
        definition.phases[0].gate.gate_digest,
        "sha256:" + "2" * 64,
        ("proof:value",),
        "authority:reviewer",
        "revision:1",
        "2026-09-05T00:00:00Z",
    )
    return (
        definition.invariants[0],
        definition.phases[0].gate,
        SpecificationPhaseDependency(
            "requires-foreign", phase_ref("foreign", "phase"), "sha256:" + "1" * 64
        ),
        definition.phases[0].iterations[0],
        definition.phases[0],
        definition,
        snapshot,
        acceptance,
    )


def test_complete_object_new_reconstruction_is_lawful() -> None:
    for value in _portable_values():
        clone = object.__new__(type(value))
        for field_definition in fields(value):
            object.__setattr__(
                clone, field_definition.name, getattr(value, field_definition.name)
            )
        type(value).__post_init__(clone)
        assert clone == value


def test_incomplete_object_new_roots_reject() -> None:
    for value in _portable_values():
        incomplete = object.__new__(type(value))
        with pytest.raises((AttributeError, SpecificationContractError)):
            type(value).__post_init__(incomplete)


def test_foreign_portable_roots_reject_before_foreign_behavior() -> None:
    for value in _portable_values():
        calls: list[str] = []

        def observed_getattribute(
            self: object, name: str, _calls: list[str] = calls
        ) -> object:
            _calls.append(name)
            return super(type(self), self).__getattribute__(name)

        foreign_type = type(
            f"Foreign{type(value).__name__}",
            (type(value),),
            {"__getattribute__": observed_getattribute},
        )
        foreign = object.__new__(foreign_type)
        with pytest.raises(SpecificationContractError, match="type must be exact"):
            type(value).__post_init__(foreign)
        assert calls == []
