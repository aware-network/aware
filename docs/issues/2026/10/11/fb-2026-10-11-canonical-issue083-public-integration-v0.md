# Issue: Integrate exact Issue083 whole-envelope tree without selection

- Slug: canonical-issue083-public-integration-v0
- Tag: fb/2026-10-11/canonical-issue083-public-integration-v0
- Status: In Progress
- Owner: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Priority: P1
- Goal: TBD
- Captured: 2026-10-11
- Recorder: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Source: Customer-directed work through aware issue open

## Ownership Scope
- `README.md`
- `docs/alignment/CURRENT.md`
- `docs/issues/2026/10/11/fb-2026-10-11-canonical-issue083-public-integration-v0.md`
- `protocols/WORKFLOW.md`
- `protocols/install.py`
- `protocols/issues/FIRST-ISSUE.md`
- `protocols/repository/README.md`
- `releases/README.md`
- `releases/canonical-issue083-fs-v1/CONTENT-AUDIT.json`
- `releases/canonical-issue083-fs-v1/DELIVERY-MAP.json`
- `releases/canonical-issue083-fs-v1/LAYOUT-REVIEW.json`
- `releases/canonical-issue083-fs-v1/LICENSE`
- `releases/canonical-issue083-fs-v1/LOCAL-INTEGRATION.md`
- `releases/canonical-issue083-fs-v1/NOTICE`
- `releases/canonical-issue083-fs-v1/NOTICE-BINDINGS.json`
- `releases/canonical-issue083-fs-v1/README.md`
- `releases/canonical-issue083-fs-v1/REVIEW-STATUS.md`
- `releases/canonical-issue083-fs-v1/SOURCE-INDEX.json`
- `releases/canonical-issue083-fs-v1/SOURCE-MAP.json`
- `releases/canonical-issue083-fs-v1/archive_verifier.py`
- `releases/canonical-issue083-fs-v1/canonical-issue083-source-notice-review-v1.tar.gz`
- `releases/canonical-issue083-fs-v1/source-history/CONTRIBUTING.md`
- `releases/canonical-issue083-fs-v1/source-history/LICENSE`
- `releases/canonical-issue083-fs-v1/source-history/NOTICE`
- `releases/canonical-issue083-fs-v1/source-history/README.md`
- `releases/canonical-issue083-fs-v1/source-history/SECURITY.md`
- `releases/canonical-issue083-fs-v1/source-history/THIRD_PARTY_NOTICES.md`
- `releases/canonical-issue083-fs-v1/source-history/docs/legal/ARTIFACT_PROVENANCE.toml`
- `releases/canonical-issue083-fs-v1/source-history/docs/legal/GENERATED_OUTPUT_POLICY.md`
- `releases/canonical-issue083-fs-v1/source-history/docs/legal/OPEN_SOURCE_POLICY.md`
- `releases/canonical-issue083-fs-v1/test_local_integration.py`
- `workspaces/README.md`
- `workspaces/aware_coordination/modules/workflow/libs/issue_operational_runtime/aware_issue_operational_runtime/source_projection.py`
- `workspaces/aware_coordination/modules/workflow/libs/issue_operational_runtime/pyproject.toml`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/cli/python/README.md`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/cli/python/aware_issue_cli/main.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/cli/python/pyproject.toml`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/cli/python/tests/test_publication_guidance.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/cli/python/tests/test_reference_onboarding.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/cli/python/tests/test_registrars.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/README.md`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/aware_issue_fs_adapter/provider.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/aware_issue_fs_adapter/source_projection.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/pyproject.toml`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/tests/test_reference_diagnostics.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/aware_issue_sdk/source_projection.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_command/materialize_command.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/change_evidence_codec.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_command_composition.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/observation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/package_occurrence_lineage.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_mutation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_source_projection.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/semantic_materialization_publication.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_command_scoped_observation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_live_profile_selection.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_materialize_command.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_package_occurrence_transitions.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_repository_mutation_terminal_evidence.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_source_projection.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_source_projection.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_source_projection_codec.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_source_projection_values.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/fixtures/workspace_source_projection_signatures.pyi`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/fixtures/workspace_source_projection_values.aware`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_issue_source_projection_composition.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_workspace_source_projection_authored_qualification.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_workspace_source_projection_production_codec.py`



## Problem
1. Accepted Issue083 layout is not yet integrated against the exact incoming public revision.




## Goal
1. Project the reviewed 68-path delta with complete source/notice carriage, preserving contributor governance and predecessor selection.




## Acceptance Checklist
- [ ] Exact 72-path scope, accepted layout bytes and executable modes, original receipts and actual commit delta; no reconciliation debt.
- [ ] Fresh offline hidden-checkout 40-package installation with supported help, missing-identity and reuse refusals.
- [ ] Independent review before closeout; instructions remain draft and successor unselected; no push or unassisted-onboarding claim.




## Updates (append-only)
- Ensured through `issue_sdk.ensure_issue_snapshot`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Applied `issue_sdk.start_issue_progress`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Exact reviewed 68-path projection plus four governance records is present. 28 projection/authority checks and eight integrated-tree checks pass, including fresh offline checkout-hidden installation of forty packages. Whole-envelope sources/notices/audit and contributor a6/predecessor selection preserved. No selection, instruction freeze, unassisted-onboarding acceptance or push. Local publication receipts follow; independent review remains pending. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
