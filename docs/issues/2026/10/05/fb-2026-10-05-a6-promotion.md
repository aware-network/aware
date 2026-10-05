# Issue: Promote accepted a6 selection and align public consumer experience

- Slug: a6-promotion
- Tag: fb/2026-10-05/a6-promotion
- Status: In Progress
- Owner: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Priority: P1
- Goal: TBD
- Captured: 2026-10-05
- Recorder: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Source: Customer-directed work through aware issue open

## Ownership Scope
- `.aware/agent-bootstrap.json`
- `.aware/agent-protocol.md`
- `AGENTS.md`
- `README.md`
- `aware.protocol.toml`
- `docs/agents/README.md`
- `docs/agents/operational-work.md`
- `docs/agents/repository-change.md`
- `docs/agents/verification-and-handoff.md`
- `docs/alignment/CURRENT.md`
- `docs/alignment/PROTOCOL.md`
- `docs/alignment/README.md`
- `docs/issues/2026/10/05/fb-2026-10-05-a6-promotion.md`
- `docs/issues/PROTOCOL.md`
- `protocols/agent/AGENTS.md`
- `protocols/agent/LAUNCH.md`
- `protocols/agent/README.md`
- `protocols/agent/VERIFICATION.md`
- `protocols/agent/quickstart.md`
- `protocols/agent/release-a5.json`
- `protocols/agent/release.json`
- `protocols/agent/test_a5_bundle.py`
- `protocols/agent/test_a6_bundle.py`
- `protocols/contracts/README.md`
- `protocols/publication/A6-PROMOTION.md`
- `protocols/publication/README.md.in`
- `protocols/publication/receipt.json`
- `protocols/publication/test_a6_promotion.py`
- `protocols/publication/test_feedback_a6.py`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/AGENTS.md.in`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/contract.json`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/agents/README.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/agents/operational-work.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/agents/repository-change.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/agents/verification-and-handoff.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/alignment/CURRENT.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/alignment/PROTOCOL.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/alignment/README.md`
- `workspaces/aware_coordination/modules/workflow/clients/agent/python/aware_agent_cli/templates/agent-fs-v1/docs/issues/PROTOCOL.md`



## Problem
1. Accepted a6 candidate e02a06544e88 is not selected; public instructions/bootstrap still describe a5 and contain the fixed label defect.




## Goal
1. Select exact reviewed a6 manifest; preserve historical a5; deliberately render contract 1.2.1 and align consumer docs/verification/context. Prepare local publication checkpoint; no push, rebuild or SPEC.




## Acceptance Checklist
- [ ] Selected release exactly equals accepted a6; old artifacts and contracts remain immutable; no wheel/runtime/source changes.
- [ ] Root, modular docs, setup provenance, installed contract and consumer instructions agree; customer upgrades remain explicit.
- [ ] Focused promotion and installed-path checks pass; retain evidence and separate local preparation from authorized remote delivery.




## Updates (append-only)
- Ensured through `issue_sdk.ensure_issue_snapshot`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Applied `issue_sdk.start_issue_progress`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Local a6 promotion selects exact accepted archive c3d6e593fd5894a927d338da5347a32e9c9eda3aec0aadcf9a662d51e348b804 and manifest 1f33866867c3385d817776b9afa179751ab669ca280ddab76e8d2080f7b0a08b. Historical a5 manifest retained byte-identically. Scoped renderer explicitly migrates root/modular bootstrap to 1.2.1; current alignment is an approved post-render authored amendment. README-only exporter verifies 105 unchanged outputs. No archive, wheel, neutral workspace source or versioned contract changed. 70 promotion checks zero skips (plus three subtests); historical suite 18 checks includes eight repeated current-selection baselines. Retained offline checkout-hidden env replay 224 tests zero skips, not fresh install/independent review. Receipts and exact limitations in protocols/publication/A6-PROMOTION.md. First README refresh used nonexistent original-name coordinate and failed before writes; corrected to existing public filename. Original candidate JUnit retained unchanged and replay result saved separately. Remote main still 8ecf22d67b834ece5aa845171c70344b2069411e. Prepared for bounded review and explicit non-force push authorization to aware-network/aware/main; no push, rebuild, registry release or SPEC work. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
