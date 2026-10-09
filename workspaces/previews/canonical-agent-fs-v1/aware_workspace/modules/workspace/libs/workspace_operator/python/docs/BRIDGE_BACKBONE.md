# Workspace Bridge Backbone

Status: canonical interface layer for remote collaborative workspace execution.

## Intent

`aware-workspace-operator` orchestrates a bridge loop but should not own compiler/runtime internals.
It does this via typed ports that can be backed by local or remote adapters.

## Ports

### `WorkspaceDeltaPort`

Purpose: normalize/validate/prepare `CodePackageDelta` payloads before compiler submission.

Contract:
- input: code package delta payload
- output: code package delta payload (possibly normalized)
- must be deterministic and side-effect free

### `CompilerSessionPort`

Purpose: manage compiler session lifecycle and delta operations.

Required operations:
- `open_session`
- `apply_code_package_delta`
- `get_object_config_graph_delta`
- `close_session`

Remote adapter target: `CompilerServiceOperation`.
Reference implementation: `bridge/adapters/compiler_service_remote.py`.
Backend operation support: `services/environment/.../compiler_service.py` supports
`operation=apply_upgrade` with structured `upgrade_result` response payloads.

### `UpgradePort`

Purpose: apply OCG delta upgrade flow and return lane/preflight outcome.

Contract:
- input: compiler apply result
- output includes:
  - lane head before/after
  - lane head advanced flag
  - preflight status + relationship + integrity
Remote adapter target: service-operation request payloads carrying `upgrade_result`.
Reference implementation: `bridge/adapters/upgrade_service_remote.py`.

### `EvidencePort`

Purpose: append-only event logging for reproducibility and future performance optimization.

Events include:
- step
- status
- timestamp
- structured details

## Orchestrator Flow

1. normalize code package delta (`WorkspaceDeltaPort`)
2. open compiler session (`CompilerSessionPort`)
3. apply code package delta (`CompilerSessionPort`)
4. if OCG delta present: run upgrade (`UpgradePort`)
5. emit evidence for each step (`EvidencePort`)
6. close session (policy-driven)

## Error Policy

- Fail closed on malformed deltas or ambiguous session state.
- Record failure event before returning.
- Never emit "green" result without explicit preflight/evidence status.

## Release Policy

The port contracts are stable independent of package-release status.
External installation gates must not alter bridge behavior.
