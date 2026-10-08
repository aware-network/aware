from __future__ import annotations

import json

import pytest

from aware_specification_runtime import (
    SpecificationContractError,
    SpecificationDefinition,
    SpecificationInvariantDefinition,
    SpecificationIterationPlan,
    SpecificationPhaseAcceptance,
    SpecificationPhaseDefinition,
    SpecificationPhaseGateDefinition,
    SpecificationSnapshot,
    decode_phase_acceptance,
    decode_specification_snapshot,
    encode_phase_acceptance,
    encode_specification_snapshot,
    invariant_closure_digest,
    invariant_ref,
    phase_ref,
)

RESOLUTION = "sha256:895aff740618ae1e1dd842902fd96298c800a1654a283f73c20e191b46e57b31"


def snapshot_fixture() -> SpecificationSnapshot:
    invariants = (
        SpecificationInvariantDefinition("first", "First invariant"),
        SpecificationInvariantDefinition("second", "Second invariant"),
    )
    gate = SpecificationPhaseGateDefinition(
        "ready",
        "Ready for use",
        "aware.specification.gate.evidence-accepted.v1",
        "aware.proof.ready.v1",
        tuple(invariant_ref("spec", value.invariant_key) for value in invariants),
    )
    phase = SpecificationPhaseDefinition(
        "ready",
        "Ready",
        0,
        gate,
        iterations=(SpecificationIterationPlan("first", "First", "First plan"),),
    )
    return SpecificationSnapshot(
        (SpecificationDefinition("spec", "Spec", 1, RESOLUTION, invariants, (phase,)),)
    )


def test_snapshot_and_acceptance_round_trip_exactly() -> None:
    snapshot = snapshot_fixture()
    phase = snapshot.definitions[0].phases[0]
    acceptance = SpecificationPhaseAcceptance(
        "acceptance:ready",
        phase_ref("spec", "ready"),
        phase.gate.gate_digest,
        invariant_closure_digest(snapshot, phase_ref("spec", "ready")),
        ("proof:receipt",),
        "authority:reviewer",
        "revision:1",
        "2026-09-05T00:00:00Z",
    )

    assert (
        decode_specification_snapshot(encode_specification_snapshot(snapshot))
        == snapshot
    )
    assert decode_phase_acceptance(encode_phase_acceptance(acceptance)) == acceptance


def test_noncanonical_unknown_and_boolean_integer_substitution_reject() -> None:
    body = encode_specification_snapshot(snapshot_fixture())
    root = json.loads(body)
    root["definitions"][0]["version_number"] = True
    poisoned = json.dumps(root, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(SpecificationContractError):
        decode_specification_snapshot(poisoned)

    with pytest.raises(SpecificationContractError, match="canonical"):
        decode_specification_snapshot(body + b"\n")

    root = json.loads(body)
    root["foreign"] = "value"
    with pytest.raises(SpecificationContractError, match="exact"):
        decode_specification_snapshot(
            json.dumps(root, sort_keys=True, separators=(",", ":")).encode()
        )

    with pytest.raises(SpecificationContractError, match="canonical"):
        decode_specification_snapshot(b'{"value":NaN}')


@pytest.mark.parametrize(
    "path,value",
    (
        (("definitions", 0, "version_number"), True),
        (("definitions", 0, "phases", 0, "ordinal"), False),
        (("definitions", 0, "invariants", 0, "semantic_revision"), True),
        (("definitions", 0, "phases", 0, "iterations", 0, "plan_revision"), True),
    ),
)
def test_decoded_boolean_integer_substitution_rejects(
    path: tuple[object, ...], value: object
) -> None:
    root: object = json.loads(encode_specification_snapshot(snapshot_fixture()))
    target = root
    for part in path[:-1]:
        target = target[part]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]
    poisoned = json.dumps(root, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(SpecificationContractError):
        decode_specification_snapshot(poisoned)


def test_coherent_digest_restamping_rejects() -> None:
    snapshot = snapshot_fixture()
    body = encode_specification_snapshot(snapshot)
    root = json.loads(body)
    root["snapshot_digest"] = "sha256:" + "9" * 64
    poisoned = json.dumps(root, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(SpecificationContractError, match="freshly derived"):
        decode_specification_snapshot(poisoned)


def test_missing_and_restamped_gate_promise_reject() -> None:
    body = encode_specification_snapshot(snapshot_fixture())
    root = json.loads(body)
    del root["definitions"][0]["phases"][0]["gate"]["promise"]
    with pytest.raises(SpecificationContractError, match="fields must be exact"):
        decode_specification_snapshot(
            json.dumps(root, sort_keys=True, separators=(",", ":")).encode()
        )

    root = json.loads(body)
    root["definitions"][0]["phases"][0]["gate"]["promise"] = "Substituted"
    with pytest.raises(SpecificationContractError, match="freshly derived"):
        decode_specification_snapshot(
            json.dumps(root, sort_keys=True, separators=(",", ":")).encode()
        )


def test_decoded_closure_missing_extra_reordered_and_substituted_reject() -> None:
    body = encode_specification_snapshot(snapshot_fixture())

    roots = []
    for mutation in ("missing", "extra", "reordered", "substituted"):
        root = json.loads(body)
        invariants = root["definitions"][0]["invariants"]
        if mutation == "missing":
            invariants.pop()
        elif mutation == "extra":
            invariants.append(dict(invariants[-1]))
        elif mutation == "reordered":
            invariants.reverse()
        else:
            invariants[0]["statement"] = "Foreign meaning"
        roots.append(root)

    for root in roots:
        with pytest.raises(SpecificationContractError):
            decode_specification_snapshot(
                json.dumps(root, sort_keys=True, separators=(",", ":")).encode()
            )


def test_decoded_acceptance_digest_and_phase_ref_substitution_reject() -> None:
    snapshot = snapshot_fixture()
    phase = snapshot.definitions[0].phases[0]
    acceptance = SpecificationPhaseAcceptance(
        "acceptance:ready",
        phase_ref("spec", "ready"),
        phase.gate.gate_digest,
        invariant_closure_digest(snapshot, phase_ref("spec", "ready")),
        ("proof:receipt",),
        "authority:reviewer",
        "revision:1",
        "2026-09-05T00:00:00Z",
    )
    body = encode_phase_acceptance(acceptance)
    for field, value in (
        ("acceptance_digest", "sha256:" + "9" * 64),
        ("phase_ref", "specification:spec/invariant:first"),
    ):
        root = json.loads(body)
        root[field] = value
        with pytest.raises(SpecificationContractError):
            decode_phase_acceptance(
                json.dumps(root, sort_keys=True, separators=(",", ":")).encode()
            )
