# Iteration 01 — Module Registration Bridge Direction Lock

State: `In Progress`
Owner: `codex-019cd2a5-c937-72a2-8675-8042b4bfdfaf`
Approval: `User-directed in-thread on 2026-03-17`

Phase: `libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/README.md`
Issue: `docs/issues/2026/03/17/fb-2026-03-17-workspace-operator-module-registration-bridge-v0.md`
LOCK: This iteration may freeze the module-create orchestration and root descriptor evolution boundary in docs only. It must not change CLI or runtime code in the same loop.

## Goal

Lock the canonical module-create flow so workspace-operator owns the full workspace FS evolution transaction while aware-grammar stays the lower-level module scaffold engine that can speak in package terms within a module.

## Scope In

- `docs/issues/2026/03/17/fb-2026-03-17-workspace-operator-module-registration-bridge-v0.md`
- `docs/issues/2026/03/17/issues-2026-03-17.md`
- `docs/feed/2026/03/17.md`
- `libs/workspace-operator/docs/specs/workspace-operator/SPEC.md`
- `libs/workspace-operator/docs/specs/workspace-operator/PHASES.md`
- `libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/README.md`
- `libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/iterations/01-2026-03-17-module-registration-bridge-direction-lock/README.md`

## Scope Out

- `tools/cli/aware_cli/**` code changes
- `libs/workspace-operator/aware_workspace_operator/**` code changes
- `languages/aware/grammar/grammar/aware_grammar/module/scaffold.py` code changes
- robotics workspace mutation

## Expected Deltas

- freeze `aware-cli -> workspace-operator -> aware-grammar` as the canonical module-create flow
- freeze workspace-operator ownership of root descriptor evolution
- freeze structured package registration as the bridge contract
- align the contract to package-first semantics from `docs/conversations/2026-03-17-CODE-OWNER-2.md`
- make module create explicitly workspace-owned over package truth, not CLI-owned over module-path guesses

## Patch Order (declarative)

1. Open a dedicated docs-only issue for the bridge direction lock.
2. Update the spec with the module bootstrap and root descriptor evolution boundary.
3. Update the phase ledger and Phase 01 README.
4. Record the iteration artifact and sync issue/day/feed receipts.
5. Run docs proofs and capture receipts.

## Proofs (commands)

1. `rg -n "Module Bootstrap And Root Descriptor Evolution|aware-cli|workspace-operator|aware-grammar|Structured package registration contract|Root descriptor adapters" libs/workspace-operator/docs/specs/workspace-operator/SPEC.md`
2. `rg -n "module-create orchestration boundary|root descriptor evolution|structured package registration" libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/README.md libs/workspace-operator/docs/specs/workspace-operator/PHASES.md`
3. `rg -n "aware_environment_artifacts.pipeline.modules.scaffold|aware_code.module_manifest.scaffold|render_workspace_pyproject" tools/cli/aware_cli/commands/module.py libs/environment-artifacts/aware_environment_artifacts/pipeline/modules/scaffold.py workspaces/aware_kernel/modules/code/ontology/runtime/python/aware_code/module_manifest/scaffold.py libs/workspace-operator/aware_workspace_operator/renderers.py`

## Proof Receipts

- `rg -n "Module Bootstrap And Root Descriptor Evolution|aware-cli|workspace-operator|aware-grammar|Structured package registration contract|Root descriptor adapters" libs/workspace-operator/docs/specs/workspace-operator/SPEC.md` -> hit the new orchestration boundary, structured package registration, and root descriptor adapter sections.
- `rg -n "module-create orchestration boundary|root descriptor evolution|structured package registration" libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/README.md libs/workspace-operator/docs/specs/workspace-operator/PHASES.md` -> hit the Phase 01 gate and roadmap anchors for the new bridge direction.
- `rg -n "aware_environment_artifacts\\.pipeline\\.modules\\.scaffold|aware_grammar\\.module\\.scaffold|render_workspace_pyproject" tools/cli/aware_cli/commands/module.py libs/environment-artifacts/aware_environment_artifacts/pipeline/modules/scaffold.py languages/aware/grammar/grammar/aware_grammar/module/scaffold.py libs/workspace-operator/aware_workspace_operator/renderers.py` -> confirmed current repo truth: CLI still imports the env-artifacts shim, that shim re-exports grammar-owned scaffold helpers, and workspace-operator already owns the root `pyproject.toml` renderer.

## Exit Checks

- [x] The spec states that CLI is transport-only.
- [x] The spec states that workspace-operator owns root descriptor evolution.
- [x] The spec states that grammar owns lower-level module scaffold only.
- [x] The spec aligns the bridge to package-first semantics.
- [x] The spec states that module create is a workspace-owned transaction over package registrations.
- [x] Day/index/feed receipts are synced after proofs.

## Roadblock Rules

Mark `Roadblock` and stop if:

- the docs would force immediate code changes in the same loop
- the package-first direction conflicts with the existing workspace-operator owner direction
- the contract would move business logic back into CLI

## Sign-Off

- Start: `2026-03-17T11:34:00Z`
- End: `TBD`
- Proofs: `TBD`
- Commit: `TBD`
- Handoff: `Next loop should implement the typed workspace-operator module-create rail where grammar emits package registrations and workspace-operator applies them to root pyproject truth.`
