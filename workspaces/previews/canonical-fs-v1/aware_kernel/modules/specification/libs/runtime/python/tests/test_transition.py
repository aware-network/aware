from __future__ import annotations

from dataclasses import fields, replace

import pytest

from aware_specification_runtime import (
    SpecificationContractError,
    SpecificationDefinition,
    SpecificationMovement,
    SpecificationMovementKind,
    SpecificationPhaseDefinition,
    SpecificationPhaseGateDefinition,
    SpecificationSnapshot,
    derive_specification_transition,
)

RESOLUTION = "sha256:895aff740618ae1e1dd842902fd96298c800a1654a283f73c20e191b46e57b31"


def snapshot(title: str) -> SpecificationSnapshot:
    phase = SpecificationPhaseDefinition(
        "phase",
        title,
        0,
        SpecificationPhaseGateDefinition(
            "gate", "Accepted", "aware.gate.v1", "aware.proof.gate.v1"
        ),
    )
    return SpecificationSnapshot(
        (SpecificationDefinition("spec", "Spec", 1, RESOLUTION, phases=(phase,)),)
    )


def test_genesis_and_successor_movements_are_deterministic() -> None:
    first = snapshot("First")
    genesis = derive_specification_transition(None, first)
    assert genesis.predecessor_snapshot_digest is None
    assert all(
        value.kind is SpecificationMovementKind.ADDED for value in genesis.movements
    )

    second = snapshot("Second")
    successor = derive_specification_transition(first, second)
    assert successor.predecessor_snapshot_digest == first.snapshot_digest
    assert successor.result_snapshot_digest == second.snapshot_digest
    assert {value.kind for value in successor.movements} == {
        SpecificationMovementKind.CHANGED
    }
    assert successor == derive_specification_transition(first, second)


def test_restamped_transition_rejects() -> None:
    value = derive_specification_transition(None, snapshot("First"))
    object.__setattr__(value, "transition_digest", "sha256:" + "9" * 64)
    try:
        value.__post_init__()
    except ValueError:
        pass
    else:
        raise AssertionError("restamped transition accepted")


def test_movement_digest_shape_is_exact() -> None:
    value_digest = "sha256:" + "1" * 64
    with pytest.raises(SpecificationContractError, match="added movement shape"):
        SpecificationMovement(
            "specification:spec",
            SpecificationMovementKind.ADDED,
            value_digest,
            value_digest,
        )
    with pytest.raises(SpecificationContractError, match="changed movement shape"):
        SpecificationMovement(
            "specification:spec",
            SpecificationMovementKind.CHANGED,
            value_digest,
            value_digest,
        )


def test_promise_only_successor_changes_exact_gate_closure() -> None:
    first = snapshot("First")
    phase = first.definitions[0].phases[0]
    changed_gate = SpecificationPhaseGateDefinition(
        phase.gate.gate_key,
        "A renewed acceptance promise",
        phase.gate.gate_contract,
        phase.gate.evidence_schema_ref,
    )
    second = SpecificationSnapshot(
        (
            SpecificationDefinition(
                "spec",
                "Spec",
                1,
                RESOLUTION,
                phases=(
                    SpecificationPhaseDefinition(
                        phase.phase_key,
                        phase.title,
                        phase.ordinal,
                        changed_gate,
                    ),
                ),
            ),
        )
    )
    transition = derive_specification_transition(first, second)
    assert transition == derive_specification_transition(first, second)
    assert {movement.coordinate for movement in transition.movements} == {
        "specification:spec",
        "specification:spec/phase:phase",
        "specification:spec/phase:phase/gate:gate",
    }


@pytest.mark.parametrize(
    "coordinate",
    (
        "not-a-coordinate",
        "specification:spec/invariant:value/extra",
        "specification:spec/phase:phase/invariant:value",
        "specification:spec/phase:phase/gate:Gate",
        "specification:spec/phase:phase/dependency:bad_key",
        "specification:foreign/phase:phase/gate:gate ",
        "specification:spéc/phase:phase",
    ),
)
def test_movement_coordinate_union_is_exact(coordinate: str) -> None:
    with pytest.raises(SpecificationContractError):
        SpecificationMovement(
            coordinate,
            SpecificationMovementKind.ADDED,
            None,
            "sha256:" + "1" * 64,
        )


def _assert_contextual_transition(
    predecessor: SpecificationSnapshot | None,
    result: SpecificationSnapshot,
    supplied: object,
) -> None:
    expected = derive_specification_transition(predecessor, result)
    if type(supplied) is not type(expected) or supplied != expected:
        raise SpecificationContractError(
            "supplied transition does not match fresh contextual derivation"
        )


def test_supplied_transition_must_match_fresh_contextual_derivation() -> None:
    first = snapshot("First")
    second = snapshot("Second")
    expected = derive_specification_transition(first, second)
    _assert_contextual_transition(first, second, expected)

    first_movement = expected.movements[0]
    valid_foreign_coordinate = "specification:foreign"
    poisons = (
        replace(
            expected,
            movements=(
                replace(first_movement, coordinate=valid_foreign_coordinate),
                *expected.movements[1:],
            ),
        ),
        replace(expected, movements=expected.movements[1:]),
        replace(
            expected,
            movements=(
                replace(
                    first_movement,
                    coordinate="specification:spec/invariant:foreign",
                ),
                *expected.movements[1:],
            ),
        ),
        replace(
            expected,
            movements=(
                replace(first_movement, result_digest="sha256:" + "2" * 64),
                *expected.movements[1:],
            ),
        ),
        replace(
            expected,
            movements=(
                *expected.movements,
                SpecificationMovement(
                    "specification:zz",
                    SpecificationMovementKind.ADDED,
                    None,
                    "sha256:" + "1" * 64,
                ),
            ),
        ),
    )
    for poison in poisons:
        with pytest.raises(
            SpecificationContractError, match="fresh contextual derivation"
        ):
            _assert_contextual_transition(first, second, poison)

    with pytest.raises(SpecificationContractError, match="unique and sorted"):
        replace(expected, movements=tuple(reversed(expected.movements)))

    with pytest.raises(SpecificationContractError, match="member coordinate"):
        replace(first_movement, coordinate="specification:spec/unknown:value")


def test_transition_values_object_new_and_foreign_behavior_laws() -> None:
    transition = derive_specification_transition(snapshot("First"), snapshot("Second"))
    for value in (transition.movements[0], transition):
        clone = object.__new__(type(value))
        for field_definition in fields(value):
            object.__setattr__(
                clone, field_definition.name, getattr(value, field_definition.name)
            )
        type(value).__post_init__(clone)
        assert clone == value

        incomplete = object.__new__(type(value))
        with pytest.raises((AttributeError, SpecificationContractError)):
            type(value).__post_init__(incomplete)

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
