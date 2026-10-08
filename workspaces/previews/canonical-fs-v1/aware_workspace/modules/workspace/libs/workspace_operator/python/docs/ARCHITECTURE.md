# Workspace Operator Architecture

Status: Canonical reference for workspace bootstrap pipeline design.

## Purpose

`aware-workspace-operator` is the owner of workspace compilation rails:

- prepare an empty repository root for Aware development,
- emit deterministic scaffolds/contracts/docs,
- report strict next actions for Human-Agent execution.
- enforce typed bootstrap profiles (`remote-managed` default, `full-local` opt-in).
- run deterministic lint/type quality gates through one workspace-level entrypoint.
- run deterministic local commit rail checks (`aware-cli commit`) with ownership-safe git boundaries.

This package is intentionally separate from CLI transport and compile/materialization internals.

## Boundaries

Owned by `aware-workspace-operator`:

- workspace bootstrap orchestration
- AGENTS/contract/docs scaffold generation
- grammar-docs bundle generation for external `.aware` authoring
- seed-bundle generation for external environment instantiation (`configs/seeds/*`)
- staged report + `next_required_actions`
- quality-gate planning/execution (`workspace quality-gates`)
- canonical local commit flow (`commit`) with issue/ownership enforcement
- bridge orchestration ports for remote collaboration (`CodePackageDelta -> OCGDelta -> upgrade`)

Not owned here:

- ontology compile/materialization semantics (`aware-environment-artifacts`)
- module scaffold semantics (`aware-environment-artifacts.pipeline.modules.scaffold`)
- command parsing/terminal UX (`aware-cli` transport layer)

## High-level Components

- `aware_workspace_operator/models.py`
  - Pydantic request/report/status models
- `aware_workspace_operator/renderers.py`
  - deterministic text renderers for AGENTS/contracts/manifests/CI
- `aware_workspace_operator/pipeline/executor.py`
  - central staged execution
- `aware_workspace_operator/pipeline/stages/preflight.py`
  - module discovery + dependency/workflow preflight
- `aware_workspace_operator/pipeline/stages/scaffold.py`
  - file/materialization scaffold stages
- `aware_workspace_operator/pipeline/stages/reporting.py`
  - final report assembly + human-readable summary
- `aware_workspace_operator/bootstrap.py`
  - backward-compatible facade
- `aware_workspace_operator/quality.py`
  - plugin-backed language gate planner/executor with typed report output
- `aware_workspace_operator/commit.py`
  - canonical local git rail with strict ownership + deterministic evidence contract
- `aware_workspace_operator/bridge/interfaces.py`
  - decoupled backend contracts (`WorkspaceDeltaPort`, `CompilerSessionPort`, `UpgradePort`, `EvidencePort`)
- `aware_workspace_operator/bridge/adapters/compiler_service_remote.py`
  - remote adapter over `CompilerServiceOperation`
- `aware_workspace_operator/bridge/orchestrator.py`
  - canonical bridge-cycle orchestration

## External Command Path

`aware-cli workspace bootstrap`, `aware-cli workspace quality-gates`, and `aware-cli commit` should remain thin adapters:

1. parse args
2. build typed workspace options
3. call `aware_workspace_operator` runner (`run_workspace_bootstrap(...)` / `run_workspace_quality_gates(...)` / `run_workspace_commit(...)`)
4. print JSON/human summary

No business logic should live in CLI command modules.
