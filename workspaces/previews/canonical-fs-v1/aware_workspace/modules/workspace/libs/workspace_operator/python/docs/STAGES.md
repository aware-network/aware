# Workspace Bootstrap Stages

Status: Stage-by-stage behavior and ownership.

## Stage 1: Resolve Workspace Root

- create repo root when missing
- enforce repo-root path safety

Implementation:
- `pipeline/utils.py::resolve_repo_root`

## Stage 2: Module Preflight

- resolve explicit/discovered module ids
- discover known package names from `aware.toml`
- validate module manifests and workflow preflight
- collect missing dependency closure

Implementation:
- `pipeline/stages/preflight.py`

## Stage 3: Scaffold Environment

- write `aware.environment.toml` (default on)

Implementation:
- `pipeline/stages/scaffold.py::ensure_environment_file`

## Stage 4: Scaffold Agent Rails

- export skills pack
- write `AGENTS.md`

Implementation:
- `pipeline/stages/scaffold.py::ensure_agent_files`

## Stage 5: Scaffold Collaboration Rails

- write `docs/issues/PROTOCOL.md`
- write `docs/feed/PROTOCOL.md`
- write `docs/feed/FEED.md`
- write daily feed log

Implementation:
- `pipeline/stages/scaffold.py::ensure_collaboration_scaffold`

## Stage 6: Scaffold Proof Rails

- write module proof scaffold tests for discovered modules

Implementation:
- `pipeline/stages/scaffold.py::ensure_proof_tests`

## Stage 7: Scaffold Workspace Parity Rails

- write root `pyproject.toml`
- write workspace manifests
- write CI workflow scaffold

Implementation:
- `pipeline/stages/scaffold.py::ensure_workspace_scaffold`

## Stage 8: Scaffold Delivery Contracts

- write `configs/contracts/environment_experience.toml`
- write `configs/contracts/agent_delivery.toml`
- write `configs/contracts/evidence_policy.toml`
- write `configs/contracts/quality_gates.toml`

Implementation:
- `pipeline/stages/scaffold.py::ensure_delivery_contracts`

## Stage 9: Scaffold Grammar Docs Bundle

- write bundled Aware grammar references to `docs/aware/grammar/*.md`
- keep external `.aware` authoring unblocked without monorepo source access

Implementation:
- `pipeline/stages/scaffold.py::ensure_grammar_docs_bundle`

## Stage 10: Scaffold Software Rules Bundle

- compose software-rule docs from template + profile contracts
- source of truth: revision-owned `aware_workspace_operator/assets/software`
- resolve profile `asset://` references against package `assets/software/assets/**`
- canonical rendered stage sequence: `0-config, 1-runtime, 2-representation, 3-programs, 4-policy, 5-reactivity`
- write composed output to `docs/rules/SOFTWARE/*.md`
- copy stage assets to `docs/rules/SOFTWARE/assets/**`
- keep mental-model routing explicit for external agents

Implementation:
- `pipeline/stages/scaffold.py::ensure_software_rules_bundle`
- `prompt_composition.py`

## Stage 11: Scaffold Seed Bundle

- write bundled seed artifacts to `configs/seeds/*`
- includes `aware_kernel.seed.aware`, `aware_kernel.seed.profile.toml`, `aware.programs.toml`
- keeps external workspace instantiation rails self-contained

Implementation:
- `pipeline/stages/scaffold.py::ensure_seed_bundle`

## Stage 12: Build Report

- compute status (`ok`/`failed`)
- emit `next_required_actions` using two-loop ordering
  - Workspace Config Loop first
  - Workspace Instantiation Loop second
- render human summary when non-JSON mode is used

Implementation:
- `pipeline/stages/reporting.py`

## Post-bootstrap Quality Command

- plan/run lint+type gates through one command:
  - `aware-cli workspace quality-gates --path <target>`
- language resolution is plugin-backed with fallback defaults (Python/Dart)

Implementation:
- `quality.py`

## Canonical Commit Command

- stage+commit only explicit scoped paths with one command:
  - `aware-cli commit --issue <issue.md> --path <path> --message <subject>`
- validates owner identity + issue metadata + ownership scope before git mutation
- fails closed when pre-staged/staged files escape ownership/requested path scope
- emits deterministic commit evidence payload

Implementation:
- `commit.py`
