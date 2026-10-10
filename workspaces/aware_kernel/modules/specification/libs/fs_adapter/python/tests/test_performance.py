from __future__ import annotations

import os
from pathlib import Path
from statistics import median
from time import perf_counter

from aware_specification_fs_adapter import (
    SpecificationFsSchemaResolutionContext,
    adapt_specification_fs_roots,
    close_specification_fs_adapter,
    consume_specification_fs_adaptation,
    inspect_specification_fs_profile,
    install_specification_fs_adapter,
    lower_specification_fs_closures,
)
from aware_specification_runtime import SpecificationPhaseGateDefinition

_ONE_MIB = 1_048_576


def _write_representative(
    base: Path,
    *,
    spec_root: str,
    package_key: str,
    external_dependency: tuple[str, str] | None = None,
) -> None:
    target = base / spec_root
    invariant_keys = tuple(f"invariant-{index:02d}" for index in range(16))
    phase_keys = tuple(f"phase-{index:02d}" for index in range(32))
    invariant_refs = tuple(
        f"specification:{package_key}/invariant:{key}" for key in invariant_keys
    )
    phase_refs = tuple(f"specification:{package_key}/phase:{key}" for key in phase_keys)
    gates = tuple(
        SpecificationPhaseGateDefinition(
            f"gate-{index:02d}",
            f"Phase {index:02d} is accepted.",
            "aware.specification.gate.evidence-accepted.v1",
            "aware.fixture.phase-proof.v1",
            invariant_refs,
        )
        for index in range(32)
    )
    sources: dict[str, str] = {
        "SPEC.md": f"""# {package_key} — SPEC

Status: `in_progress`
Owner: `fixture`

## Goal

Prove the representative filesystem workload.
"""
    }
    invariant_paths = tuple(
        f"invariants/{index:02d}-{key}/README.md"
        for index, key in enumerate(invariant_keys)
    )
    sources["invariants/README.md"] = (
        f"# {package_key} — Invariants\n\n## Members\n\n"
        "| Invariant Ref | Path |\n| --- | --- |\n"
        + "".join(
            f"| `{ref}` | `{path}` |\n"
            for ref, path in zip(invariant_refs, invariant_paths, strict=True)
        )
    )
    for index, path in enumerate(invariant_paths):
        sources[path] = f"""# Invariant {index:02d} — Invariant {index:02d}

Status: `declared`
Owner: `fixture`
Spec: `SPEC.md`

## Statement

Invariant {index:02d} remains exact.
"""
    phase_paths = tuple(
        f"phases/{index:02d}-{key}/README.md" for index, key in enumerate(phase_keys)
    )
    sources["PHASES.md"] = (
        f"# {package_key} — PHASES\n\nStatus: `in_progress`\nOwner: `fixture`\n\n"
        "## Members\n\n| Phase Ref | Path |\n| --- | --- |\n"
        + "".join(
            f"| `{ref}` | `{path}` |\n"
            for ref, path in zip(phase_refs, phase_paths, strict=True)
        )
    )
    dependencies: list[dict[str, str]] = []
    iterations: list[dict[str, object]] = []
    for index, (key, ref, path, gate) in enumerate(
        zip(phase_keys, phase_refs, phase_paths, gates, strict=True)
    ):
        del key
        owned_dependencies: list[dict[str, str]] = []
        if index:
            owned_dependencies.append(
                {
                    "key": "requires-previous",
                    "owner": ref,
                    "target": phase_refs[index - 1],
                    "digest": gates[index - 1].gate_digest,
                    "rationale": "The prior phase is required.",
                }
            )
        elif external_dependency is not None:
            owned_dependencies.append(
                {
                    "key": "requires-first-package",
                    "owner": ref,
                    "target": external_dependency[0],
                    "digest": external_dependency[1],
                    "rationale": "The first package is required.",
                }
            )
        dependencies.extend(owned_dependencies)
        owned_iterations: list[dict[str, object]] = []
        for suffix_index, suffix in enumerate(("a", "b")):
            iteration_path = (
                path.removesuffix("README.md")
                + f"iterations/{suffix_index:02d}-2026-09-06-proof-{suffix}/README.md"
            )
            iteration: dict[str, object] = {
                "key": f"proof-{suffix}",
                "phase": ref,
                "revision": 1,
                "path": iteration_path,
            }
            iterations.append(iteration)
            owned_iterations.append(iteration)
            sources[
                iteration_path
            ] = f"""# Iteration {suffix_index:02d} — Proof {suffix.upper()}

State: `planned`
Owner: `fixture`
Approval: `approved`

Phase: `{path}`
Invariants: `invariants/README.md`
Issue: `docs/issues/fixture.md`
LOCK: Prove the representative workload.

## Goal

Prove phase {index:02d} iteration {suffix.upper()}.
"""
        dependency_rows = "".join(
            f"| `{item['key']}` | `requires` | `{item['target']}` | `{item['digest']}` | {item['rationale']} |\n"
            for item in owned_dependencies
        )
        iteration_rows = "".join(f"- `{item['path']}`\n" for item in owned_iterations)
        sources[path] = f"""# Phase {index:02d} — Phase {index:02d}

State: `planned`
Owner: `fixture`

## Gate

{gate.promise}

## Goal

Advance phase {index:02d}.

## Advances

{"".join(f"- `{item}`\n" for item in invariant_refs)}
## Dependencies

| Dependency Key | Kind | Required Phase Ref | Required Gate Digest | Rationale |
| --- | --- | --- | --- | --- |
{dependency_rows}
## Iterations

{iteration_rows}"""

    manifest = f"""aware = 1

[specification]
profile = "specification_fs_v1"
key = "{package_key}"
semantic_version = 1
entrypoint = "SPEC.md"
invariant_index = "invariants/README.md"
phase_index = "PHASES.md"

"""
    manifest += "".join(
        f'''[[invariants]]
key = "{key}"
semantic_revision = 1
entrypoint = "{path}"

'''
        for key, path in zip(invariant_keys, invariant_paths, strict=True)
    )
    manifest += "".join(
        f'''[[phases]]
key = "{key}"
ordinal = {index}
entrypoint = "{path}"
gate_key = "gate-{index:02d}"
gate_contract = "aware.specification.gate.evidence-accepted.v1"
evidence_schema_ref = "aware.fixture.phase-proof.v1"
invariant_refs = [{", ".join(f'"{item}"' for item in invariant_refs)}]

'''
        for index, (key, path) in enumerate(zip(phase_keys, phase_paths, strict=True))
    )
    manifest += "".join(
        f'''[[phase_dependencies]]
key = "{item["key"]}"
owner_phase_ref = "{item["owner"]}"
kind = "requires"
required_phase_ref = "{item["target"]}"
required_gate_digest = "{item["digest"]}"
rationale = "{item["rationale"]}"

'''
        for item in dependencies
    )
    manifest += "".join(
        f'''[[iterations]]
key = "{item["key"]}"
phase_ref = "{item["phase"]}"
plan_revision = {item["revision"]}
entrypoint = "{item["path"]}"

'''
        for item in iterations
    )
    sources["aware.spec.toml"] = manifest.rstrip("\n") + "\n"
    current = sum(len(value.encode()) for value in sources.values())
    prefix = "\n## Fixture Padding\n\n"
    padding = _ONE_MIB - current - len(prefix.encode()) - 1
    assert padding > 0
    sources["SPEC.md"] += prefix + ("x" * padding) + "\n"
    assert sum(len(value.encode()) for value in sources.values()) == _ONE_MIB
    assert len(sources) == 116
    for relative, body in sources.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(body, encoding="utf-8", newline="")


def _p95(values: list[float]) -> float:
    return sorted(values)[28]


def test_representative_and_doubled_performance_gates(
    tmp_path: Path, schema_bytes: bytes
) -> None:
    base = tmp_path / "source"
    first = "specs/representative-a"
    second = "specs/representative-b"
    first_key = "fixture.representative-a"
    _write_representative(base, spec_root=first, package_key=first_key)
    final_first_gate = SpecificationPhaseGateDefinition(
        "gate-31",
        "Phase 31 is accepted.",
        "aware.specification.gate.evidence-accepted.v1",
        "aware.fixture.phase-proof.v1",
        tuple(
            f"specification:{first_key}/invariant:invariant-{index:02d}"
            for index in range(16)
        ),
    )
    _write_representative(
        base,
        spec_root=second,
        package_key="fixture.representative-b",
        external_dependency=(
            f"specification:{first_key}/phase:phase-31",
            final_first_gate.gate_digest,
        ),
    )
    fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    adapter = install_specification_fs_adapter(
        fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    os.close(fd)
    try:
        complete_medians: list[float] = []
        for roots, ceiling in (((first,), 0.75), ((first, second), 1.5)):
            seed = adapt_specification_fs_roots(adapter, roots)
            closures = seed.lowering.closures
            snapshot = seed.lowering.snapshot
            consume_specification_fs_adaptation(adapter, seed)
            assert len(closures) == 1 if len(roots) == 1 else len(closures) == 2
            assert sum(len(item.members) for item in closures) == 116 * len(roots)
            assert sum(item.total_size_bytes for item in closures) == _ONE_MIB * len(
                roots
            )
            assert len(snapshot.definitions) == len(roots)
            assert sum(
                len(item.invariants) for item in snapshot.definitions
            ) == 16 * len(roots)
            assert sum(len(item.phases) for item in snapshot.definitions) == 32 * len(
                roots
            )
            expected_edges = 31 if len(roots) == 1 else 63
            assert (
                sum(
                    len(phase.dependencies)
                    for item in snapshot.definitions
                    for phase in item.phases
                )
                == expected_edges
            )
            observation_samples: list[float] = []
            lowering_samples: list[float] = []
            for _ in range(5):
                for root in roots:
                    inspect_specification_fs_profile(adapter, root)
                lower_specification_fs_closures(
                    closures, SpecificationFsSchemaResolutionContext()
                )
            for _ in range(30):
                started = perf_counter()
                for root in roots:
                    inspect_specification_fs_profile(adapter, root)
                observation_samples.append(perf_counter() - started)
                started = perf_counter()
                lower_specification_fs_closures(
                    closures, SpecificationFsSchemaResolutionContext()
                )
                lowering_samples.append(perf_counter() - started)
            observation_ceiling = 0.4 if len(roots) == 1 else 0.8
            lowering_ceiling = 0.4 if len(roots) == 1 else 0.8
            assert median(observation_samples) < observation_ceiling
            assert _p95(observation_samples) < observation_ceiling
            assert median(lowering_samples) < lowering_ceiling
            assert _p95(lowering_samples) < lowering_ceiling
            for _ in range(5):
                value = adapt_specification_fs_roots(adapter, roots)
                consume_specification_fs_adaptation(adapter, value)
            samples: list[float] = []
            for _ in range(30):
                started = perf_counter()
                value = adapt_specification_fs_roots(adapter, roots)
                samples.append(perf_counter() - started)
                consume_specification_fs_adaptation(adapter, value)
            assert median(samples) < ceiling
            assert _p95(samples) < ceiling
            complete_medians.append(median(samples))
            print(
                {
                    "roots": len(roots),
                    "members": 116 * len(roots),
                    "source_bytes": _ONE_MIB * len(roots),
                    "dependencies": expected_edges,
                    "observe_median_ms": round(median(observation_samples) * 1000, 3),
                    "observe_p95_ms": round(_p95(observation_samples) * 1000, 3),
                    "lower_median_ms": round(median(lowering_samples) * 1000, 3),
                    "lower_p95_ms": round(_p95(lowering_samples) * 1000, 3),
                    "complete_median_ms": round(median(samples) * 1000, 3),
                    "complete_p95_ms": round(_p95(samples) * 1000, 3),
                }
            )
        assert complete_medians[1] <= complete_medians[0] * 2.5
    finally:
        close_specification_fs_adapter(adapter)
