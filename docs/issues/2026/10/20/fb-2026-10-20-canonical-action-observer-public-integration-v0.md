# Issue: Integrate exact historical-action-observer whole-envelope tree without selection

- Slug: canonical-action-observer-public-integration-v0
- Tag: fb/2026-10-20/canonical-action-observer-public-integration-v0
- Status: In Progress
- Owner: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Priority: P1
- Goal: TBD
- Captured: 2026-10-20
- Recorder: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Source: Customer-directed work through aware issue open

## Ownership Scope
- `README.md`
- `docs/alignment/CURRENT.md`
- `docs/issues/2026/10/20/fb-2026-10-20-canonical-action-observer-public-integration-v0.md`
- `protocols/WORKFLOW.md`
- `protocols/install.py`
- `protocols/workspace/ACTION-OBSERVATION.md`
- `protocols/workspace/README.md`
- `releases/README.md`
- `releases/canonical-action-observer-fs-v1/CONTENT-AUDIT.json`
- `releases/canonical-action-observer-fs-v1/DELIVERY-MAP.json`
- `releases/canonical-action-observer-fs-v1/LAYOUT-REVIEW.json`
- `releases/canonical-action-observer-fs-v1/LICENSE`
- `releases/canonical-action-observer-fs-v1/LOCAL-INTEGRATION.md`
- `releases/canonical-action-observer-fs-v1/NOTICE`
- `releases/canonical-action-observer-fs-v1/NOTICE-BINDINGS.json`
- `releases/canonical-action-observer-fs-v1/README.md`
- `releases/canonical-action-observer-fs-v1/REVIEW-STATUS.md`
- `releases/canonical-action-observer-fs-v1/SOURCE-INDEX.json`
- `releases/canonical-action-observer-fs-v1/SOURCE-MAP.json`
- `releases/canonical-action-observer-fs-v1/SUPPLEMENTAL-SOURCE-MAP.json`
- `releases/canonical-action-observer-fs-v1/archive_verifier.py`
- `releases/canonical-action-observer-fs-v1/canonical-action-observer-source-notice-review-v1.tar.gz`
- `releases/canonical-action-observer-fs-v1/source-bindings/observer-overlays.json`
- `releases/canonical-action-observer-fs-v1/source-bindings/preimages/workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/architecture_setup_review.py`
- `releases/canonical-action-observer-fs-v1/source-bindings/preimages/workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/pyproject.toml`
- `releases/canonical-action-observer-fs-v1/source-bindings/preimages/workspaces/aware_workspace/modules/workspace/sdks/workspace/aware/architecture_setup_review_ports.aware`
- `releases/canonical-action-observer-fs-v1/source-bindings/preimages/workspaces/aware_workspace/modules/workspace/sdks/workspace/aware/architecture_setup_review_values.aware`
- `releases/canonical-action-observer-fs-v1/source-bindings/preimages/workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/pyproject.toml`
- `releases/canonical-action-observer-fs-v1/source-bindings/preimages/workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/README.md`
- `releases/canonical-action-observer-fs-v1/source-bindings/preimages/workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_review.py`
- `releases/canonical-action-observer-fs-v1/source-bindings/preimages/workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_review_codec.py`
- `releases/canonical-action-observer-fs-v1/source-bindings/preimages/workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_review_values.py`
- `releases/canonical-action-observer-fs-v1/source-bindings/preimages/workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/pyproject.toml`
- `releases/canonical-action-observer-fs-v1/source-bindings/preimages/workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_architecture_setup_review_codec.py`
- `releases/canonical-action-observer-fs-v1/source-history/CONTRIBUTING.md`
- `releases/canonical-action-observer-fs-v1/source-history/LICENSE`
- `releases/canonical-action-observer-fs-v1/source-history/NOTICE`
- `releases/canonical-action-observer-fs-v1/source-history/README.md`
- `releases/canonical-action-observer-fs-v1/source-history/SECURITY.md`
- `releases/canonical-action-observer-fs-v1/source-history/THIRD_PARTY_NOTICES.md`
- `releases/canonical-action-observer-fs-v1/source-history/docs/legal/ARTIFACT_PROVENANCE.toml`
- `releases/canonical-action-observer-fs-v1/source-history/docs/legal/GENERATED_OUTPUT_POLICY.md`
- `releases/canonical-action-observer-fs-v1/source-history/docs/legal/OPEN_SOURCE_POLICY.md`
- `releases/canonical-action-observer-fs-v1/test_local_integration.py`
- `workspaces/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/create_first_initialization.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/initialization.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/workspace_review.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/pyproject.toml`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_action_observer.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_composition.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_configuration_continuation.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_initialization.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_installed_create_first.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_workspace_setup.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/README.md`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/confined_mutation.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/cooperative_source.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/staging_plan.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/staging_worker_canary.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/terminal_codec.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/docs/BOUNDED_STREAM_WRITER.md`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/docs/CANARY_CLOSURE_SETUP_HANDOFF.md`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/docs/DEDICATED_WORKER_CANARY.md`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/docs/STAGING_CREATION_BACKENDS.md`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/docs/STAGING_CREATION_CUSTODY.md`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/docs/STAGING_PLAN.md`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/docs/STREAMED_POSTIMAGE.md`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/pyproject.toml`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/tests/test_confined_postimage.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/tests/test_confined_stream_writer.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/tests/test_cooperative_source.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/tests/test_private_directory.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/tests/test_staging_plan.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/tests/test_staging_worker_canary.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/tests/test_terminal_codec.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/architecture_setup_review.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/aware/architecture_setup_review_ports.aware`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/aware/architecture_setup_review_values.aware`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/README.md`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_review.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_review_codec.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_review_values.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_action_admission_observation.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_architecture_setup_review_codec.py`




## Problem
1. Accepted observer layout is not integrated against freshly observed publicdbdc57d05230; no baseline movement is present.





## Goal
1. Project the reviewed 84-path delta preserving complete carriage, twelve overlays/preimages, supplemental authored declarations, useful/adoption branches, contributor governance and predecessor selection.





## Acceptance Checklist
- [ ] Exact 88-path scope, all1935 accepted postimages/modes, original guards and receipts; no reconciliation debt.
- [ ] Retained exact-candidate 42-package installation with source hiding, supported help and safe refusals; no new environment or customer workflow replay.
- [ ] Independent review before closeout; instructions remain draft and successor unselected; no push or unassisted-onboarding claim.





## Updates (append-only)
- Ensured through `issue_sdk.ensure_issue_snapshot`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Applied `issue_sdk.start_issue_progress`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- 30 pre-effect guards and eight integration checks pass. All1935 accepted postimages/Git modes and exact88-path scope verify; complete envelope/source/notice carriage, twelve overlays and two supplemental declarations preserved. Retained installation only: 42 packages, dependency check,13 help entrances, missing-identity effect-none refusal and156 original module hashes. Three initial exact-tree checks failed due six generated Python caches from the first reviewer run; exact caches quarantined and failures retained, final unchanged eight-case replay passes with bytecode writes disabled. No product/test assertion changes, reprojection, new installation, customer replay, selection, GC disposal or push. Instructions draft/unselected; independent review required before closeout. (outcome: Bounded integration verification passed with retained reviewer-cache qualifications.) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Original implementation git:833e1a1fa11ccde9ecdce5e1ce78660c41f99bba applies exact88 paths; CAS/index applied without debt. Complete1935 accepted postimages/Git modes, whole envelope, overlay/preimage/supplemental mappings, predecessor selection and contributor governance preserved. Final8 integration checks and30 guards pass; initial cache-related review failures and six quarantined generated cache files retained. Two-path Issue/note handoff follows with fresh observed guard. Independent review before closeout; no selection, freeze, new installation, customer replay, GC disposal or push. (outcome: Bounded local integration applied; independent review pending.) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
