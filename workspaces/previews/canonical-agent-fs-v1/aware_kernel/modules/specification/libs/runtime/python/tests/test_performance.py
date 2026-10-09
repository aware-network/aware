from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from statistics import median
from time import perf_counter

from aware_specification_runtime import (
    SpecificationDefinition,
    SpecificationPhaseDefinition,
    SpecificationPhaseGateDefinition,
    SpecificationSnapshot,
    decode_specification_snapshot,
    derive_specification_transition,
    encode_specification_snapshot,
)

RESOLUTION = "sha256:895aff740618ae1e1dd842902fd96298c800a1654a283f73c20e191b46e57b31"


def fixture(count: int = 100) -> SpecificationSnapshot:
    definitions = []
    for index in range(count):
        key = f"spec-{index:03d}"
        phase = SpecificationPhaseDefinition(
            "phase",
            "Phase",
            index,
            SpecificationPhaseGateDefinition(
                "gate", "Gate accepted", "aware.gate.v1", "aware.proof.gate"
            ),
        )
        definitions.append(
            SpecificationDefinition(
                key, f"Spec {index}", 1, RESOLUTION, phases=(phase,)
            )
        )
    return SpecificationSnapshot(tuple(definitions))


def _measure(operation: Callable[[], object]) -> tuple[float, float]:
    for _ in range(5):
        operation()
    samples: list[float] = []
    for _ in range(30):
        start = perf_counter()
        operation()
        samples.append((perf_counter() - start) * 1000)
    ordered = sorted(samples)
    return median(samples), ordered[28]


def _promise_successor(snapshot: SpecificationSnapshot) -> SpecificationSnapshot:
    definition = snapshot.definitions[0]
    phase = definition.phases[0]
    next_gate = replace(phase.gate, promise="Renewed Gate promise")
    next_phase = replace(phase, gate=next_gate)
    next_definition = replace(definition, phases=(next_phase, *definition.phases[1:]))
    return SpecificationSnapshot((next_definition, *snapshot.definitions[1:]))


def _benchmark(
    count: int,
) -> tuple[int, tuple[float, float], tuple[float, float], tuple[float, float]]:
    snapshot = fixture(count)
    encoded = encode_specification_snapshot(snapshot)
    successor = _promise_successor(snapshot)
    encode_times = _measure(lambda: encode_specification_snapshot(snapshot))
    decode_times = _measure(lambda: decode_specification_snapshot(encoded))
    transition_times = _measure(
        lambda: derive_specification_transition(snapshot, successor)
    )
    return len(encoded), encode_times, decode_times, transition_times


def test_representative_and_doubled_snapshot_codec_are_bounded() -> None:
    representative = _benchmark(100)
    doubled = _benchmark(200)

    size, encode_times, decode_times, transition_times = representative
    assert size < 150_000
    assert encode_times[0] < 50.0
    assert encode_times[1] < 75.0
    assert decode_times[0] < 100.0
    assert decode_times[1] < 150.0
    assert transition_times[0] < 100.0
    assert transition_times[1] < 150.0

    for representative_times, doubled_times in zip(
        representative[1:], doubled[1:], strict=True
    ):
        assert doubled_times[0] <= representative_times[0] * 2.5
