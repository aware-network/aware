# Issue: Integrate exact a14 whole-envelope tree without selection

- Slug: canonical-a14-public-integration-v0
- Tag: fb/2026-10-19/canonical-a14-public-integration-v0
- Status: In Progress
- Owner: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Priority: P1
- Goal: TBD
- Captured: 2026-10-19
- Recorder: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Source: Customer-directed work through aware issue open

## Ownership Scope
- `README.md`
- `docs/alignment/CURRENT.md`
- `docs/issues/2026/10/19/fb-2026-10-19-canonical-a14-public-integration-v0.md`
- `protocols/WORKFLOW.md`
- `protocols/install.py`
- `protocols/workspace/README.md`
- `protocols/workspace/RESOURCE-RELEASES.md`
- `protocols/workspace/REVIEWED-SETUP.md`
- `releases/README.md`
- `releases/canonical-a14-fs-v1/CONTENT-AUDIT.json`
- `releases/canonical-a14-fs-v1/DELIVERY-MAP.json`
- `releases/canonical-a14-fs-v1/LAYOUT-REVIEW.json`
- `releases/canonical-a14-fs-v1/LICENSE`
- `releases/canonical-a14-fs-v1/LOCAL-INTEGRATION.md`
- `releases/canonical-a14-fs-v1/NOTICE`
- `releases/canonical-a14-fs-v1/NOTICE-BINDINGS.json`
- `releases/canonical-a14-fs-v1/README.md`
- `releases/canonical-a14-fs-v1/REVIEW-STATUS.md`
- `releases/canonical-a14-fs-v1/SOURCE-INDEX.json`
- `releases/canonical-a14-fs-v1/SOURCE-MAP.json`
- `releases/canonical-a14-fs-v1/archive_verifier.py`
- `releases/canonical-a14-fs-v1/canonical-a14-source-notice-review-v1.tar.gz`
- `releases/canonical-a14-fs-v1/source-bindings/original-metadata/aware-workspace-fs-adapter/pyproject.toml`
- `releases/canonical-a14-fs-v1/source-bindings/original-metadata/aware-workspace-runtime/pyproject.toml`
- `releases/canonical-a14-fs-v1/source-bindings/original-metadata/aware-workspace-sdk/pyproject.toml`
- `releases/canonical-a14-fs-v1/source-bindings/workspace-metadata-overlays.json`
- `releases/canonical-a14-fs-v1/source-history/CONTRIBUTING.md`
- `releases/canonical-a14-fs-v1/source-history/LICENSE`
- `releases/canonical-a14-fs-v1/source-history/NOTICE`
- `releases/canonical-a14-fs-v1/source-history/README.md`
- `releases/canonical-a14-fs-v1/source-history/SECURITY.md`
- `releases/canonical-a14-fs-v1/source-history/THIRD_PARTY_NOTICES.md`
- `releases/canonical-a14-fs-v1/source-history/docs/legal/ARTIFACT_PROVENANCE.toml`
- `releases/canonical-a14-fs-v1/source-history/docs/legal/GENERATED_OUTPUT_POLICY.md`
- `releases/canonical-a14-fs-v1/source-history/docs/legal/OPEN_SOURCE_POLICY.md`
- `releases/canonical-a14-fs-v1/test_local_integration.py`
- `workspaces/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/create_first_initialization.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/initialization.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/main.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/workspace_review.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/pyproject.toml`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_composition.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_create_first_initialization.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_initialization.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_installed_create_first.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_workspace_release_summary.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_workspace_setup.py`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/aware_protocol_fs_adapter/manifest.py`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/aware_protocol_fs_adapter/native_goal_resolver.py`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/aware_protocol_fs_adapter/project_bootstrap.py`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/aware_protocol_fs_adapter/project_resolver.py`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/pyproject.toml`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/tests/test_planning_bootstrap.py`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/tests/test_planning_profile.py`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/tests/test_project_bootstrap.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/declaration_scope_admission.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/dependency_resolution.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_cli_selected_host.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/initial_authoring.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/initial_authoring_selection.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/initial_goal_intent.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/initial_goal_publication.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/initial_goal_source.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/initial_membership.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/local_service.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_publication.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/product_supplier_fixture.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_dependency_inventory_checkpoint.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_dependency_resolution.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_dependency_scope_admission.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_product_performance.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_local_service.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_original_input_commitment.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_product_inventory_validation_window.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_public_attention_supplier.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_public_meta_supplier.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_selected_source_validation_window.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/git_identity.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/git_writer.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/initial_authoring.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/initial_authoring_selection.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/initial_goal_intent.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/initial_goal_publication.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/initial_goal_source.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/initial_membership.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/initial_membership_projection.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_publication.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/tests/test_initial_git_identity.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/initial_authoring/authority.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/initial_authoring/goal_intent.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/initial_authoring/goal_publication.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/initial_authoring/goal_source.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/initial_authoring/membership.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/initial_authoring/values.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_publication/authority.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_initial_authoring.py`




## Problem
1. Accepted a14 layout is not integrated against freshly observed public23d5b8ea; no baseline movement is present.





## Goal
1. Project the reviewed 97-path delta preserving whole-envelope carriage, explicit metadata overlays/preimages, useful-task branches, contributor governance and predecessor selection.





## Acceptance Checklist
- [ ] Exact 101-path scope, all1818 accepted postimages/modes, overlay provenance and original receipts; no reconciliation debt.
- [ ] Retained exact-candidate 42-package installation with source hiding, supported help and safe refusals; no new environment or customer workflow replay.
- [ ] Independent review before closeout; instructions remain draft and successor unselected; no push or unassisted-onboarding claim.





## Updates (append-only)
- Ensured through `issue_sdk.ensure_issue_snapshot`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Applied `issue_sdk.start_issue_progress`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Thirty original/receiving controls and eight public integration checks passed. All1818 accepted postimages/Git modes and exact97-path layout+four integration records verified. Complete envelope/source/notices and three metadata overlays/preimages remain; predecessor selection/contributor a6/operational blocks unchanged. Retained consumer read-only16commands verify42 versions,dependencies,13help entrances,missing identity refusal without effects and155 original module hashes. No new install, owner workflow replay, selection,freeze,activation,GC or push. Independent review before closeout; whole-envelope delivery and capability limits remain mandatory. (outcome: qualified_pending_independent_review) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Local implementation67fe9d1dbfeb contains exact101-path admitted delta. Original dry-run/apply share original Issue guardabd3bbe3... and actual target paths; CAS/index completed without debt. Thirty controls and eight integration tests pass. Retained16read-only commands verify42versions/dependencies/13help/missing identity refusal and155 original module hashes. Current handoff updates only this Issue and LOCAL-INTEGRATION.md; no re-projection or owner workflow replay. Request independent review; keep both Issues InProgress. No selection,freeze,new install,activation,GC or push; whole-envelope and capability limits unchanged. (outcome: handoff_pending_independent_review) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
