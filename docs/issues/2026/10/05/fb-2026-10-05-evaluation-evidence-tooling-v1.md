# Issue: Harden external evaluation capture, freeze and metadata export

- Slug: evaluation-evidence-tooling-v1
- Tag: fb/2026-10-05/evaluation-evidence-tooling-v1
- Status: In Progress
- Owner: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Priority: P1
- Goal: TBD
- Captured: 2026-10-05
- Recorder: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Source: Customer-directed work through aware issue open

## Ownership Scope
- `docs/issues/2026/10/05/fb-2026-10-05-evaluation-evidence-tooling-v1.md`
- `protocols/evaluations/README.md`
- `protocols/evaluations/admissions/a6-evidence-tooling-20261005.md`
- `protocols/evaluations/tooling/README.md`
- `protocols/evaluations/tooling/evidence.py`
- `protocols/evaluations/tooling/test_evidence.py`




## Problem
1. Pinned external a6 evaluation 9bdc8a38655a11a78920b75091b1f8918c45838c identifies evaluator evidence gaps, not a reported product regression: early command capture, self-inclusive freeze inventory, null refusal logging and unsafe inline-payload export.





## Goal
1. Provide optional standard-library producer/evaluator tooling outside the consumer runtime: journal starts before effects, deterministic separate freeze, null-safe receipt projection and metadata-only allowlisted export.





## Acceptance Checklist
- [ ] Synthetic tests cover early capture, partial failure without automatic replay, self-excluding deterministic freeze and input preservation.
- [ ] Export omits inline code, patches, raw streams and private paths while retaining evidence digests and explicit interpreter provenance; no sanitization-completeness claim.
- [ ] Keep a6 payload, v2 schemas, external frozen evaluation and SPEC/Workflow paths unchanged; publish a scoped source checkpoint for independent review, not release promotion or remote push.





## Updates (append-only)
- Ensured through `issue_sdk.ensure_issue_snapshot`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Applied `issue_sdk.start_issue_progress`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Implemented optional standard-library Linux evaluator tooling and docs only. Pinned external evidence 9bdc8a38655a11a78920b75091b1f8918c45838c validates 23 artifacts/145 interactions/18 findings; customer operations not independently replayed. 42 new synthetic helper tests + 70 adjacent checks (16 validator, 35 publication/layout, 19 bundle including historical base) passed, zero skips. Standalone /usr/bin/python3.12 CLI replay captured actual interpreter, ran 42 cases, produced byte-identical separate snapshots and metadata-only export. Private proof /tmp/aware-evidence-tooling-proof.62Bx6a retained; no raw evidence transferred. Null-safe receipt projection and duplicate capture-ID refusal retain unknown effects without automatic operation replay; exporter omits inline code, patches, arbitrary attachments and raw streams. Ruff and scoped diff checks pass. Selected a6 manifest/archive pins unchanged, v2 unchanged, no SPEC/Workflow paths or consumer runtime edits. This execution retains explicitly approved installed a5 governance command; no CLI substitution, build, promotion, transfer or push. Exact evidence, hashes and limitations in protocols/evaluations/admissions/a6-evidence-tooling-20261005.md. Source checkpoint remains In Progress for independent review. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Source checkpoint applied through selected installed aware dry-run then identical apply: git:d296cc4be9a0c060a95b25a0757e2af72fe571fa, operator aware_workspace_operator.run_workspace_commit.v1, transaction isolated_index_atomic_ref_v1, reference cas_applied, shared-index projection applied and reconciliation not pending for that operation. Commit check passed and working tree/index clean after apply. All six changed paths are exact Issue scope. Handoff: independently review optional capture/freeze/receipt/export source, docs and 42 synthetic tests plus retained 70 adjacent checks; do not infer 224 installed replay or customer acceptance. Issue stays In Progress for independent review. a6/runtime/Schema-v2/SPEC unchanged; no remote push, promotion, artifact rebuild, evaluation transfer or release. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
