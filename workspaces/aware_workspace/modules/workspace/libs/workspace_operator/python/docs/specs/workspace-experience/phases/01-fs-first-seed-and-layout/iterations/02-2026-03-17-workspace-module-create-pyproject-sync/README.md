# Iteration 02 — Workspace Module Create Pyproject Sync

State: `In Progress`
Owner: `codex-019cd2a5-c937-72a2-8675-8042b4bfdfaf`
Approval: `User-directed in-thread on 2026-03-17`

Phase: `libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/README.md`
Issue: `docs/issues/2026/03/17/fb-2026-03-17-workspace-module-create-pyproject-sync-v0.md`
LOCK: This iteration may implement the first workspace-owned module-create transaction and root `pyproject.toml` sync. It must not widen into ontology/generated-package registration, placeholder-root creation, or non-Python root descriptor adapters.

## Goal

Ship the first real code cut where module creation flows through workspace-operator as a workspace-owned transaction over package truth and updates the workspace root `pyproject.toml` with no manual edits.

## Scope In

- `docs/issues/2026/03/17/fb-2026-03-17-workspace-module-create-pyproject-sync-v0.md`
- `docs/issues/2026/03/17/issues-2026-03-17.md`
- `docs/feed/2026/03/17.md`
- `libs/workspace-operator/docs/specs/workspace-operator/PHASES.md`
- `libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/README.md`
- `libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/iterations/02-2026-03-17-workspace-module-create-pyproject-sync/README.md`
- `languages/aware/grammar/grammar/aware_grammar/module/scaffold.py`
- `libs/environment-artifacts/aware_environment_artifacts/pipeline/modules/scaffold.py`
- `libs/environment-artifacts/tests/test_module_scaffold.py`
- `libs/workspace-operator/aware_workspace_operator/__init__.py`
- `libs/workspace-operator/aware_workspace_operator/bootstrap.py`
- `libs/workspace-operator/aware_workspace_operator/models.py`
- `libs/workspace-operator/aware_workspace_operator/module_create.py`
- `libs/workspace-operator/aware_workspace_operator/pipeline/executor.py`
- `libs/workspace-operator/aware_workspace_operator/pipeline/stages/scaffold.py`
- `libs/workspace-operator/aware_workspace_operator/renderers.py`
- `libs/workspace-operator/tests/test_module_create.py`
- `tools/cli/aware_cli/py.typed`
- `tools/cli/aware_cli/commands/module.py`
- `tools/cli/pyproject.toml`
- `tools/cli/tests/test_module_command.py`

## Scope Out

- `environments/robotics/workspace/**`
- placeholder-root directory creation
- ontology/generated-package root descriptor sync
- additional root descriptor adapters beyond `pyproject.toml`

## Expected Deltas

- structured package registrations added to grammar-owned scaffold results
- workspace-operator module-create entrypoint and typed result
- deterministic root `pyproject.toml` sync for scaffolded Python packages
- CLI delegation into workspace-operator
- focused proofs on scaffold contract and CLI behavior
- no module-path scraping or manual root descriptor edits

## Patch Order (declarative)

1. Extend grammar scaffold result with structured package registration truth.
2. Add the workspace-operator module-create transaction and root `pyproject.toml` adapter.
3. Switch CLI module create to delegate into workspace-operator.
4. Add focused tests for scaffold registrations, workspace pyproject sync, and CLI output.
5. Run focused proofs and sync issue/day/feed receipts.

## Proofs (commands)

1. `uv run pytest -q libs/environment-artifacts/tests/test_module_scaffold.py libs/workspace-operator/tests/test_module_create.py tools/cli/tests/test_module_command.py`
2. `uv run flake8 languages/aware/grammar/grammar/aware_grammar/module/scaffold.py libs/environment-artifacts/aware_environment_artifacts/pipeline/modules/scaffold.py libs/environment-artifacts/tests/test_module_scaffold.py libs/workspace-operator/aware_workspace_operator/__init__.py libs/workspace-operator/aware_workspace_operator/bootstrap.py libs/workspace-operator/aware_workspace_operator/models.py libs/workspace-operator/aware_workspace_operator/module_create.py libs/workspace-operator/aware_workspace_operator/renderers.py libs/workspace-operator/tests/test_module_create.py tools/cli/aware_cli/commands/module.py tools/cli/tests/test_module_command.py`
3. `uv run mypy --follow-imports=silent languages/aware/grammar/grammar/aware_grammar/module/scaffold.py libs/environment-artifacts/aware_environment_artifacts/pipeline/modules/scaffold.py libs/environment-artifacts/tests/test_module_scaffold.py libs/workspace-operator/aware_workspace_operator/__init__.py libs/workspace-operator/aware_workspace_operator/bootstrap.py libs/workspace-operator/aware_workspace_operator/models.py libs/workspace-operator/aware_workspace_operator/module_create.py libs/workspace-operator/aware_workspace_operator/renderers.py libs/workspace-operator/tests/test_module_create.py tools/cli/aware_cli/commands/module.py tools/cli/tests/test_module_command.py`
4. `uv run basedpyright --level warning languages/aware/grammar/grammar/aware_grammar/module/scaffold.py libs/environment-artifacts/aware_environment_artifacts/pipeline/modules/scaffold.py libs/environment-artifacts/tests/test_module_scaffold.py libs/workspace-operator/aware_workspace_operator/__init__.py libs/workspace-operator/aware_workspace_operator/bootstrap.py libs/workspace-operator/aware_workspace_operator/models.py libs/workspace-operator/aware_workspace_operator/module_create.py libs/workspace-operator/aware_workspace_operator/renderers.py libs/workspace-operator/tests/test_module_create.py tools/cli/aware_cli/commands/module.py tools/cli/tests/test_module_command.py`

## Proof Receipts

- `uv run pytest -q libs/environment-artifacts/tests/test_module_scaffold.py libs/workspace-operator/tests/test_module_create.py tools/cli/tests/test_module_command.py` -> `13 passed`
- `uv run flake8 languages/aware/grammar/grammar/aware_grammar/module/scaffold.py libs/environment-artifacts/aware_environment_artifacts/pipeline/modules/scaffold.py libs/environment-artifacts/tests/test_module_scaffold.py libs/workspace-operator/aware_workspace_operator/__init__.py libs/workspace-operator/aware_workspace_operator/bootstrap.py libs/workspace-operator/aware_workspace_operator/models.py libs/workspace-operator/aware_workspace_operator/module_create.py libs/workspace-operator/aware_workspace_operator/renderers.py libs/workspace-operator/tests/test_module_create.py tools/cli/aware_cli/commands/module.py tools/cli/tests/test_module_command.py` -> clean
- `uv run mypy --follow-imports=silent languages/aware/grammar/grammar/aware_grammar/module/scaffold.py libs/environment-artifacts/aware_environment_artifacts/pipeline/modules/scaffold.py libs/environment-artifacts/tests/test_module_scaffold.py libs/workspace-operator/aware_workspace_operator/__init__.py libs/workspace-operator/aware_workspace_operator/bootstrap.py libs/workspace-operator/aware_workspace_operator/models.py libs/workspace-operator/aware_workspace_operator/module_create.py libs/workspace-operator/aware_workspace_operator/renderers.py libs/workspace-operator/tests/test_module_create.py tools/cli/aware_cli/commands/module.py tools/cli/tests/test_module_command.py` -> `Success: no issues found in 11 source files`
- `uv run basedpyright --level warning languages/aware/grammar/grammar/aware_grammar/module/scaffold.py libs/environment-artifacts/aware_environment_artifacts/pipeline/modules/scaffold.py libs/environment-artifacts/tests/test_module_scaffold.py libs/workspace-operator/aware_workspace_operator/__init__.py libs/workspace-operator/aware_workspace_operator/bootstrap.py libs/workspace-operator/aware_workspace_operator/models.py libs/workspace-operator/aware_workspace_operator/module_create.py libs/workspace-operator/aware_workspace_operator/renderers.py libs/workspace-operator/tests/test_module_create.py tools/cli/aware_cli/commands/module.py tools/cli/tests/test_module_command.py` -> `0 errors, 0 warnings, 0 notes`

## Exit Checks

- [x] Grammar scaffold returns structured package registrations for the packages it writes today.
- [x] Workspace-experience owns root `pyproject.toml` sync.
- [x] CLI module create is transport-only.
- [x] Workspace-experience applies root descriptor mutation from package registrations rather than inferred module paths.
- [x] Focused proofs are green.

## Roadblock Rules

Mark `Roadblock` and stop if:

- the cut requires ontology/generated-package registration in the same loop
- root `pyproject.toml` sync cannot be implemented without broad manual-edit preservation work
- the bridge requires moving business logic back into CLI

## Sign-Off

- Start: `2026-03-17T11:52:00Z`
- End: `2026-03-17T12:32:00Z`
- Proofs: `pytest + flake8 + mypy + basedpyright --level warning`
- Commit: `TBD`
- Handoff: `Commit the owned slice, then take the next Phase 01 proof: real workspace-root placeholder materialization and root-descriptor evolution against environments/robotics/workspace/.`
