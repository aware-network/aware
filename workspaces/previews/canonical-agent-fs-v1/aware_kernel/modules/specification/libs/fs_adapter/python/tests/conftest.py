from __future__ import annotations

import os
from pathlib import Path

import pytest
from aware_specification_runtime import SpecificationPhaseGateDefinition


def repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repository root unavailable")


@pytest.fixture
def schema_bytes() -> bytes:
    return (
        repository_root() / "docs/specs/schemas/aware-spec-v1.schema.json"
    ).read_bytes()


@pytest.fixture
def canonical_tree(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "source"
    spec_root = "specs/example"
    target = root / spec_root
    invariant_path = "invariants/00-stable-meaning/README.md"
    phase_a_path = "phases/00-foundation/README.md"
    phase_b_path = "phases/01-consumer/README.md"
    iteration_path = "phases/00-foundation/iterations/00-2026-09-06-proof/README.md"
    for relative in (invariant_path, phase_a_path, phase_b_path, iteration_path):
        (target / relative).parent.mkdir(parents=True, exist_ok=True)

    invariant_ref = "specification:example.spec/invariant:stable-meaning"
    phase_a_ref = "specification:example.spec/phase:foundation"
    phase_b_ref = "specification:example.spec/phase:consumer"
    gate_a = SpecificationPhaseGateDefinition(
        "foundation-ready",
        "The foundation is accepted.",
        "aware.specification.gate.evidence-accepted.v1",
        "aware.example.foundation-proof.v1",
        (invariant_ref,),
    )
    manifest = f'''aware = 1

[specification]
profile = "specification_fs_v1"
key = "example.spec"
semantic_version = 1
entrypoint = "SPEC.md"
invariant_index = "invariants/README.md"
phase_index = "PHASES.md"

[[invariants]]
key = "stable-meaning"
semantic_revision = 1
entrypoint = "{invariant_path}"

[[phases]]
key = "consumer"
ordinal = 1
entrypoint = "{phase_b_path}"
gate_key = "consumer-ready"
gate_contract = "aware.specification.gate.evidence-accepted.v1"
evidence_schema_ref = "aware.example.consumer-proof.v1"
invariant_refs = ["{invariant_ref}"]

[[phases]]
key = "foundation"
ordinal = 0
entrypoint = "{phase_a_path}"
gate_key = "foundation-ready"
gate_contract = "aware.specification.gate.evidence-accepted.v1"
evidence_schema_ref = "aware.example.foundation-proof.v1"
invariant_refs = ["{invariant_ref}"]

[[phase_dependencies]]
key = "requires-foundation"
owner_phase_ref = "{phase_b_ref}"
kind = "requires"
required_phase_ref = "{phase_a_ref}"
required_gate_digest = "{gate_a.gate_digest}"
rationale = "The consumer requires the foundation."

[[iterations]]
key = "proof"
phase_ref = "{phase_a_ref}"
plan_revision = 1
entrypoint = "{iteration_path}"
'''
    sources = {
        "aware.spec.toml": manifest,
        "SPEC.md": """# Example Specification — SPEC

Status: `in_progress`
Owner: `fixture`

## Goal

Provide exact filesystem parity.
""",
        "invariants/README.md": f"""# Example Specification — Invariants

## Members

| Invariant Ref | Path |
| --- | --- |
| `{invariant_ref}` | `{invariant_path}` |
""",
        invariant_path: """# Invariant 00 — Stable Meaning

Status: `declared`
Owner: `fixture`
Spec: `SPEC.md`

## Statement

Meaning remains exact.
""",
        "PHASES.md": f"""# Example Specification — PHASES

Status: `in_progress`
Owner: `fixture`

## Members

| Phase Ref | Path |
| --- | --- |
| `{phase_b_ref}` | `{phase_b_path}` |
| `{phase_a_ref}` | `{phase_a_path}` |
""",
        phase_b_path: f"""# Phase 01 — Consumer

State: `planned`
Owner: `fixture`

## Gate

The consumer is accepted.

## Goal

Consume the foundation.

## Advances

- `{invariant_ref}`

## Dependencies

| Dependency Key | Kind | Required Phase Ref | Required Gate Digest | Rationale |
| --- | --- | --- | --- | --- |
| `requires-foundation` | `requires` | `{phase_a_ref}` | `{gate_a.gate_digest}` | The consumer requires the foundation. |

## Iterations

No iterations.
""",
        phase_a_path: f"""# Phase 00 — Foundation

State: `in_progress`
Owner: `fixture`

## Gate

The foundation is accepted.

## Goal

Establish the foundation.

## Advances

- `{invariant_ref}`

## Dependencies

| Dependency Key | Kind | Required Phase Ref | Required Gate Digest | Rationale |
| --- | --- | --- | --- | --- |

## Iterations

- `{iteration_path}`
""",
        iteration_path: f"""# Iteration 00 — Proof

State: `planned`
Owner: `fixture`
Approval: `approved`

Phase: `{phase_a_path}`
Invariants: `{invariant_path}`
Issue: `docs/issues/example.md`
LOCK: Prove exact parity.

## Goal

Prove the filesystem adapter.
""",
    }
    for relative, body in sources.items():
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8", newline="")
    return root, spec_root


@pytest.fixture
def source_fd(canonical_tree: tuple[Path, str]):
    root, _ = canonical_tree
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        yield fd
    finally:
        os.close(fd)
