# Goal: Synthetic reader demo

This is test input, not customer authority or an approval.

- Slug: `reader-demo`
- Tag: `goal/2026-10-05/reader-demo`
- Status: `Active`
- Priority: `P2`
- Owner: `demo-fixture`

## Lane Map

| Lane | Role | Owner | Status | Current Issue | Since | Last Receipt | Scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `demo` | Sample | `demo-fixture` | Ready | `TBD:read` | Pending | Pending | Read-only |

## Forward Plan By Lane

| Lane | Next Issue | Gate |
| --- | --- | --- |
| `demo` | `TBD:read` | Observe the fixture without changing it. |

## Lane Sequences

### `demo`

| Step | Key | Time | Tick | Issue | Gate | Status | Owner | Receipt |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `read` | Pending | `[ ]` | `TBD:read` | Observe the fixture without changing it. | Planned | `demo-fixture` | Pending |

## Integrated Updates (append-only)

<!-- aware.goal.lane-phase.document.v1:start -->
```json
{"authority_profile":"native_phase_definition_v1","compatibility_profile":"markdown_legacy_v1","compatibility_projection_byte_count":910,"compatibility_projection_sha256":"sha256:19d3f85a504014c8153b4691ff2a7ea07b8c929336f3551d4ef96449c675e4d3","definitions":[{"coordinate":{"goal_tag":"goal/2026-10-05/reader-demo","lane_key":"demo","phase_key":"read"},"definition_ref":"goal-phase-definition:sha256:84fc49dff0eacf9f7e6d2ea12ae9a29c8a7b44b0f8d66580a4c879f48a99e006","gate":{"evidence_schema_ref":"example:read-evidence","gate_contract_ref":"example:read-contract","gate_digest":"sha256:51c7cd765c4c895a257d8b28e34f82033cdd5c1ab5049f7efd7dcb3b8ef2557c","gate_key":"read","invariant_refs":[],"promise":"Observe the fixture without changing it.","semantic_revision":1},"intent":"Demonstrate read-only observations.","ordinal":1,"title":"Read"}],"document_ref":"goal-phase-document:sha256:254a18fd844c21db99bcc7edd2d044db8ab5b6db302bcaaf7f2d7e663f0d55d0","execution_authority":{"authority_ref":"goal-phase-execution-authority:sha256:29bf2f0d4af1e22d1d0de450db0288881b52880279d47aac79bb3c4263638c35","coordinator_acceptance_ref":"goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:3333333333333333333333333333333333333333333333333333333333333333","legacy_execution_disposition":"retired","parity_ref":"goal-phase-native-compatibility-parity:sha256:1111111111111111111111111111111111111111111111111111111111111111","proposal_aggregate_ref":"goal-phase-native-operational-bootstrap-proposal:sha256:2222222222222222222222222222222222222222222222222222222222222222","schema_id":"aware.goal.phase-execution-authority.v1","source_execution_authority_profile":"hybrid_legacy_row_phase_native_v1","target_execution_authority_profile":"phase_native_operational_v1"},"goal_tag":"goal/2026-10-05/reader-demo","operational_bundle":{"dependencies":[],"phases":[{"coordinate":{"goal_tag":"goal/2026-10-05/reader-demo","lane_key":"demo","phase_key":"read"},"gate":{"evidence_schema_ref":"example:read-evidence","gate_contract_ref":"example:read-contract","gate_digest":"sha256:51c7cd765c4c895a257d8b28e34f82033cdd5c1ab5049f7efd7dcb3b8ef2557c","gate_key":"read","invariant_refs":[],"promise":"Observe the fixture without changing it.","semantic_revision":1},"gate_observations":[],"intent":"Demonstrate read-only observations.","last_receipt_ref":null,"ordinal":1,"pursuit_directive":null,"state":"active","title":"Read","work_associations":[]}],"schema_id":"aware.goal.lane-phase.bundle.v1"},"schema_id":"aware.goal.lane-phase.document.v2","source_refs":["repository-path:protocols/examples/read-only/goals/2026/10/05/goal-2026-10-05-reader-demo.md"],"unresolved_dependencies":[]}
```
<!-- aware.goal.lane-phase.document.v1:end -->
