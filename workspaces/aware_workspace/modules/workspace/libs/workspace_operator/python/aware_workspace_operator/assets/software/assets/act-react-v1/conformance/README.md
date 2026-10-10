# ACT-REACT Conformance Runner (Scaffold)

This folder provides a minimal cross-runtime scaffold for validating the
`ACT-REACT Protocol v1` checklist (`AR-01..AR-10`).

## Files

- `runner.py`: validates a conformance report and enforces required checklist ids.
- `../act-react.v1.schema.json`: machine-readable Program IR schema.

## Report contract

Runtimes should emit a JSON report shaped as:

```json
{
  "protocol_version": "act-react.v1",
  "runtime_id": "my-runtime@1.2.3",
  "results": [
    { "id": "AR-01", "status": "pass", "details": "..." },
    { "id": "AR-02", "status": "pass", "details": "..." }
  ]
}
```

Required result ids:

- `AR-01`
- `AR-02`
- `AR-03`
- `AR-04`
- `AR-05`
- `AR-06`
- `AR-07`
- `AR-08`
- `AR-09`
- `AR-10`

Frozen UX handshake (must be explicit in runtime/docs):

- Step A: capability resolve (from `ActorRole`).
- Step B: AI proposes `program_ref` + required inputs.
- Step C: human accepts/rejects.
- Step D: submit and observe (`submit_program_turn` + `get_turn_execution`).

Allowed statuses:

- `pass`
- `fail`
- `skip`

Minimum evidence notes:

- `AR-04`: `expect` and `intent` remain contract-only.
- `AR-05`: each IR step has unique `step_id`; order is deterministic.
- Runtime remains owner of actual event/action outcomes and receipts.

## Usage

```bash
python docs/rules/SOFTWARE/assets/act-react-v1/conformance/runner.py \
  --report /path/to/act-react-conformance-report.json
```

Optional:

- `--allow-skip`: treat `skip` as non-failing for incremental adoption.
- `--program-ir`: validate Program IR structural invariants (`step_id` and purity boundary).

Exit codes:

- `0`: valid report and all required checks pass (or skip when allowed), plus valid Program IR if `--program-ir` is provided.
- `1`: invalid report shape, missing ids, duplicate ids, unknown ids, or failing checks.
