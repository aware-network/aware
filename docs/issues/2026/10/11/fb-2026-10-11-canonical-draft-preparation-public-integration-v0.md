# Issue: Integrate exact draft-preparation whole-envelope tree without selection

- Slug: canonical-draft-preparation-public-integration-v0
- Tag: fb/2026-10-11/canonical-draft-preparation-public-integration-v0
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
- `docs/issues/2026/10/11/fb-2026-10-11-canonical-draft-preparation-public-integration-v0.md`
- `protocols/WORKFLOW.md`
- `protocols/install.py`
- `protocols/issues/FIRST-ISSUE.md`
- `releases/README.md`
- `releases/canonical-draft-preparation-fs-v1/CONTENT-AUDIT.json`
- `releases/canonical-draft-preparation-fs-v1/DELIVERY-MAP.json`
- `releases/canonical-draft-preparation-fs-v1/LAYOUT-REVIEW.json`
- `releases/canonical-draft-preparation-fs-v1/LICENSE`
- `releases/canonical-draft-preparation-fs-v1/LOCAL-INTEGRATION.md`
- `releases/canonical-draft-preparation-fs-v1/NOTICE`
- `releases/canonical-draft-preparation-fs-v1/NOTICE-BINDINGS.json`
- `releases/canonical-draft-preparation-fs-v1/README.md`
- `releases/canonical-draft-preparation-fs-v1/REVIEW-STATUS.md`
- `releases/canonical-draft-preparation-fs-v1/SOURCE-INDEX.json`
- `releases/canonical-draft-preparation-fs-v1/SOURCE-MAP.json`
- `releases/canonical-draft-preparation-fs-v1/archive_verifier.py`
- `releases/canonical-draft-preparation-fs-v1/canonical-draft-preparation-source-notice-review-v1.tar.gz`
- `releases/canonical-draft-preparation-fs-v1/source-history/CONTRIBUTING.md`
- `releases/canonical-draft-preparation-fs-v1/source-history/LICENSE`
- `releases/canonical-draft-preparation-fs-v1/source-history/NOTICE`
- `releases/canonical-draft-preparation-fs-v1/source-history/README.md`
- `releases/canonical-draft-preparation-fs-v1/source-history/SECURITY.md`
- `releases/canonical-draft-preparation-fs-v1/source-history/THIRD_PARTY_NOTICES.md`
- `releases/canonical-draft-preparation-fs-v1/source-history/docs/legal/ARTIFACT_PROVENANCE.toml`
- `releases/canonical-draft-preparation-fs-v1/source-history/docs/legal/GENERATED_OUTPUT_POLICY.md`
- `releases/canonical-draft-preparation-fs-v1/source-history/docs/legal/OPEN_SOURCE_POLICY.md`
- `releases/canonical-draft-preparation-fs-v1/test_local_integration.py`
- `workspaces/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/draft_preparation.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/main.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/pyproject.toml`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_composition.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_draft_preparation.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_initialization.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/aware_issue_fs_adapter/provider.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/tests/test_provider.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/aware_issue_sdk/operation_codec.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/tests/test_operation_codec.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/README.md`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/aware_specification_cli/draft_commands.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/pyproject.toml`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/tests/test_draft_commands.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/tests/test_read_commands.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/README.md`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/aware_specification_fs_sdk_adapter/__init__.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/aware_specification_fs_sdk_adapter/input_observation.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/pyproject.toml`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/tests/test_input_observation.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/tests/test_issue_storage_successor.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/tests/test_package_catalog.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/README.md`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/aware_specification_sdk/__init__.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/aware_specification_sdk/input_observation.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/aware_specification_sdk/wire.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/pyproject.toml`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/tests/test_authored_closure.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/tests/test_draft_evidence.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/tests/test_input_observation.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/tests/test_operation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_delta_capture.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_delta_capture_client.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_delta_retention.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_repository_delta_capture.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_delta_capture.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_delta_retention.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/README.md`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_delta_capture.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_delta_retention.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/qualify_repository_delta_capture_install.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_repository_delta_capture_client.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_repository_delta_capture_packaging.py`




## Problem
1. Accepted draft-preparation layout is not yet integrated against the exact incoming public revision.





## Goal
1. Project the reviewed 74-path delta with complete source/notice carriage, preserving contributor governance and predecessor selection.





## Acceptance Checklist
- [ ] Exact 78-path scope, accepted layout bytes and executable modes, original receipts and actual commit delta; no reconciliation debt.
- [ ] Fresh offline hidden-checkout 40-package installation with supported help, missing-identity and reuse refusals.
- [ ] Independent review before closeout; instructions remain draft and successor unselected; no push or unassisted-onboarding claim.





## Updates (append-only)
- Ensured through `issue_sdk.ensure_issue_snapshot`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Applied `issue_sdk.start_issue_progress`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Exact accepted 74-path layout projection plus four review/Issue files verified. 28 owner/projection guards and eight integration checks passed, zero skipped, including fresh offline checkout-hidden forty-package installation and prep help/missing-harness/reuse refusals. Complete sources/notices, predecessor selection and contributor a6 preserved. Next original exact-scope repository dry-run/apply; independent review before closeout. No selection, instruction freeze, full domain proof or push. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Implementation 7b3f82dc39047a9957e3f110d71a4685c549b888 changes exact 78 admitted paths. Original CAS/index receipt applied; no reconciliation debt. 28 guards and eight integration cases passed with fresh offline hidden-checkout forty-package installation. Complete artifacts, predecessor selection and contributor governance unchanged. Two-path evidence handoff only; independent integration review pending. No domain-matrix replay, selection, freeze or push. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
