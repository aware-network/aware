# Aware Goal Operational Runtime

Workflow-owned, materialization-independent Goal operation authority. It
defines immutable Goal, GoalLane, GoalLaneIssue, and GoalUpdate values;
revision-bound deterministic transitions; strict serialization; lane-local
expected-head conflict behavior; and explicit Issue link/synchronization
receipts. Its dependency-free host adds bounded admission, cancellation,
generation-CAS persistence, restart-safe idempotency, a retained event journal,
typed replay, exact bounded observation, and explicit local-to-canonical
reconciliation.

`GoalOperationalAuthority` is the provider-neutral consumer surface. The
destructive `run_goal_operational_authority_conformance(...)` proof accepts one
already-admitted, isolated authority and verifies applied receipts, exact
idempotency, lane-head conflict behavior, Issue link/synchronization,
observation, ordered replay, durable readback, and the absence of implicit Goal
achievement. The neutral host is the first passing implementation. A canonical
adapter must pass the same proof before it can claim semantic parity.

The package has no runtime dependencies. It does not parse Markdown, access a
filesystem projection, host a service, import generated Goal/Issue DTOs, invoke
Ontology or Meta, compose Development WorkContext, call Workspace, or dispatch
an Agent. Durable providers are injected through the neutral generation-CAS
port; the in-memory atomic provider is the conformance reference.

## Goal pursuit receipts and currentness

`issue_goal_pursuit_receipt(...)` and
`verify_goal_pursuit_currentness(...)` own the deterministic
`aware.goal.pursuit.receipt.v0` and
`aware.goal.pursuit.currentness.v0` semantics over a structural
`GoalDirectionSnapshot`. A caller must first resolve the exact Goal, lane, row,
Issue observation, pursuit directive, and source digest. The runtime neither
selects nor reads that source.

The compatibility Markdown adapter supplies one such structural snapshot. A
future canonical Goal API provider can supply the same surface from operational
and Ontology authority without copying receipt or currentness logic. Receipt
issuance rejects non-ready lanes, wrong rows, source-digest mismatch, and a
completion gate that differs from the selected row. Currentness compares one
retained receipt with one fresh supplied observation and returns only `current`
or typed `stale` reasons.

These receipts remain read-only and non-authorizing. They do not open or choose
an Issue, establish a WorkContext, dispatch an Agent, grant mutation, evaluate
a dependency, or qualify evidence. Goal mutation continues to return the
separate `GoalOperationReceipt`; dependency evaluation and intake retain their
separate explicit contracts below.

## GoalDependency operational observations

`GoalDependency` declarations and dependency satisfaction remain separate.
`evaluate_goal_dependency(...)` consumes only explicit dependent/prerequisite
source observations and qualified gate evidence. A satisfied observation binds
the exact dependency definition digest, both endpoint source revisions, the
prerequisite gate digest, evidence kind, evidence receipt, qualification
receipt, and evaluator. A later definition, source, or gate change reports the
old evidence as `stale`.

`requires_completion` accepts only qualified completion evidence;
`requires_acceptance` accepts only qualified acceptance evidence. Issue closure,
lane sequence, row status, blocker prose, and declaration evidence refs are not
inputs and cannot satisfy a dependency.

`summarize_goal_dependency_gate(...)` evaluates multiple declarations
conjunctively and reports `clear`, `blocked`, `stale`, or `unresolved`. Even
`clear` is read-only, non-authorizing evidence: it cannot pursue a Goal, admit
an Issue or WorkContext, dispatch an Agent, or mutate source. Markdown parsing,
SDK/view projection, persistence, and landscape rendering remain separate
consumer integrations.

### Observation intake

`compose_goal_dependency_observation_intake(...)` keeps observation absence
separate from evaluator satisfaction. Its `not_evaluated` availability means
no operational observation was supplied; it must not be translated to
`pending`. When an observation is present, the intake validates its exact
declaration digest, coordinates, relation, source/gate bindings, evidence
shape, evaluator reference, deterministic observation reference, schema, and
non-authorizing effect profile.

`decode_goal_dependency_observation(...)` rejects unknown fields and preserves
the evaluator wire payload without deriving satisfaction from Markdown row
presence. `decode_goal_dependency_gate_observation(...)` accepts already typed
observations and requires the gate payload to equal their canonical
conjunctive summary. These checks establish contract integrity, not evaluator
trust or work authority; consumers must retain the provenance of the supplied
evaluator and evidence receipts independently.
