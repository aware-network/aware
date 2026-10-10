# Workspace Operator Functionality

## Opinionated Defaults

`workspace bootstrap` defaults are intentionally on:

- environment file
- AGENTS + skills
- Aware grammar docs bundle (`docs/aware/grammar/*.md`)
- software rules bundle (`docs/rules/SOFTWARE/*.md`, composed from package assets)
- seed bundle (`configs/seeds/*`)
- collaboration scaffold
- workspace scaffold (pyproject/manifests/CI)
- delivery contracts

Proof tests are generated for discovered modules only.

## Bootstrap Profiles

- `remote-managed` (default): external-first bootstrap; preflight stays decoupled from strict local compiler dependency/workflow checks.
- `full-local`: enables strict local compiler preflight (dependency closure + workflow compile checks).

## Explicit Module Creation

Bootstrap never guesses starter modules.

After Human-Agent agreement, module creation is explicit:

```bash
aware-cli module create <module_id> --repo-root <repo_root>
```

## Two-loop Delivery Contract

Workspace Config Loop first:

1. capture intent/agreement
2. review bundled Aware grammar docs (`docs/aware/grammar/README.md`)
3. review software rules mental-model bundle (`docs/rules/SOFTWARE/index.md`)
4. module create
5. config -> runtime -> representation -> programs -> policy -> reactivity
6. compile pass
7. quality gates pass (`aware-cli workspace quality-gates`)
8. module proof pass
9. pane registrar pass
10. IPC e2e pass

Workspace Instantiation Loop second:

1. connect compiler authority (remote-managed or full-local)
2. apply environment-level experience topology
3. apply seed experience (`configs/seeds/aware_kernel.seed.aware` + `configs/seeds/aware_kernel.seed.profile.toml`)
4. validate instantiation outcomes
5. evidence logged

## Typed Contract Surface

Primary typed request/report models:

- `WorkspaceBootstrapOptions`
- `WorkspaceBootstrapReport`
- `WorkspaceBootstrapOutcome`
- `WorkspaceCommitOptions`
- `WorkspaceCommitReport`
- `WorkspaceCommitOutcome`
- `WorkspaceQualityOptions`
- `WorkspaceQualityReport`
- `WorkspaceQualityOutcome`

Nested statuses are also typed (`EnvironmentFileStatus`, `AgentFilesStatus`, `WorkspaceScaffoldStatus`, etc.).

All model surfaces are Pydantic with `extra = "forbid"`.

## Canonical Commit Rail

`aware-cli commit` runs through `aware-workspace-operator` and enforces:

1. stable owner execution identity (`<provider>-<provider_session_id>`)
2. issue metadata requirements (`Tag`, `Owner`, `Status: In Progress`, `Ownership Scope`)
3. explicit scoped paths only (`--path` repeatable)
4. fail-closed checks for pre-staged/staged files outside issue scope
5. deterministic commit metadata/evidence (`Issue-Tag`, `Issue-Path`, `Owner`, `Owned-Paths`)

Software prompt composition is typed and deterministic:

- template/provider source: `aware_workspace_operator/assets/software`
- profile source: package `assets/software/profiles/*.toml`
- section-core assets source: package `assets/software/assets/section-core/**`
- compose engine: `prompt_composition.py`
- stage assets source: package `assets/software/assets/**` (exported to `docs/rules/SOFTWARE/assets/**`)
- profile replacements can use `asset://<relative-path>` to keep templates thin and move CORE text to modular assets.

## Bridge Backbone (Remote-Collaboration Ready)

`aware-workspace-operator` also defines decoupled bridge ports:

- `WorkspaceDeltaPort`
- `CompilerSessionPort`
- `UpgradePort`
- `EvidencePort`

Canonical cycle:

1. normalize `CodePackageDelta`
2. call compiler session (`open` -> `apply`)
3. apply upgrade/preflight when OCG delta is present
4. append evidence events
