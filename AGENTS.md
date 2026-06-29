# Aware CANONICAL ERA.

This file is the operational contract for all agents in this workspace.
Goal: alignment first, issue-driven execution, canonical engineering only.

## 0) Non-negotiable collaboration rules (read first)

### A) Identify yourself first

- In the first task update of a new thread, publish your stable provider-backed execution id.
- Use the same id in issue update bullets and FEED pulse logs.
- Valid identity format for active work is a stable `<provider>-<provider_session_id>`.
- Alias identities (example: model aliases) are invalid for ownership/recorder fields.
- If identity is not a stable provider-backed execution id: no move, no claim, no implementation.

#### Codex identity bootstrap (explicit)

- Resolve your session id directly from env:
  - `echo "$CODEX_THREAD_ID"`
- Emit canonical ownership id:
  - `echo "codex-$CODEX_THREAD_ID"`
- Strict fail-fast check (preferred in scripts):
  - `: "${CODEX_THREAD_ID:?CODEX_THREAD_ID is not set}"; echo "codex-$CODEX_THREAD_ID"`
- If `CODEX_THREAD_ID` is missing: set issue `Status: Blocked`, keep `Owner: Unassigned`, and do not implement until identity is valid.

#### Provider identity standard (canonical)

- Active owner/recorder identity is an execution identity, not a vendor label or model-family label.
- Canonical format:
  - `<provider>-<provider_session_id>`
- `provider` must be lowercase snake_case and name the harness/session owner.
- `provider_session_id` must be the provider-native stable session/thread identifier for the active run.
- Do not rewrite provider-backed ids into aliases; keep raw, stable session-backed ids only.
- Future canonical actor ids such as `apt_id` / `aware_id` are additive and separate; they do not replace execution identity in issue/feed/spec ownership fields.

| Provider key | Meaning | Stable session source | Canonical execution id |
| --- | --- | --- | --- |
| `codex` | Codex harness | `CODEX_THREAD_ID` | `codex-$CODEX_THREAD_ID` |
| `claude_code` | Claude Code harness | Provider-native stable session/thread id supplied by the harness | `claude_code-<provider_session_id>` |
| `<provider>` | Any other approved agent harness | Provider-native stable session/thread id supplied by that harness | `<provider>-<provider_session_id>` |

- Preferred provider keys:
  - `codex`
  - `claude_code`
- Do not use ambiguous provider keys such as:
  - `claude`
  - `anthropic`
  - `openai`
  - model-family labels (`gpt5`, `sonnet`, etc.)

### B) Work via issue first (before coding)

- Every task must map to one issue file:
  - `docs/issues/YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md`
- If the issue does not exist, create it first using:
  - `docs/issues/PROTOCOL.md`
- Claim before code:
  - set `Owner`
  - set `Status: In Progress`
  - append one dated bullet in `Updates`
- For local markdown-backed issues, the issue file is the agent-facing issue
  authority. `.aware/workflow_issue/state.json` is only a local cache for CLI
  enforcement and must not be edited or treated as SSOT.

### C) FEED is the live team snapshot

- Use agent feed under `docs/feed/` for shared coordination.
- Global snapshot:
  - `docs/feed/FEED.md`
- Daily append-only log:
  - `docs/feed/YYYY/MM/DD.md`
- Ownership split:
  - Working agents append scoped operational truth to `docs/feed/YYYY/MM/DD.md`.
  - Maintainer (or designated scribe) owns `docs/feed/FEED.md` refresh and global pulse truth.
- On maintainer ping, refresh FEED as a point-in-time pulse with:
  - `Shipping now (P0 / In Progress)`
  - `Needs owner now (P0 / Open)`
  - `Recently closed (today)`
  - `Alignment checks`
  - `Pulse log (append-only)`
- Per-issue files are SSOT for local markdown-backed issues. FEED is the
  coordination snapshot.

### D) Git governance (critical)

- Luis is the global Git coordinator (release integration + override authority).
- Agent mutation rail is canonical:
  - `aware-cli commit` only.
  - Required before mutation:
    - stable owner identity `<provider>-<provider_session_id>`
    - issue `Status: In Progress`
    - canonical issue ownership scope bound
    - explicit owned `--path` entries only
    - run `--dry-run` preflight first
  - Commit preflight refreshes the local issue-state cache from the current
    issue authority before enforcing owner/status/scope. Agents should not run
    manual `issue sync` as a normal commit prerequisite; use it only as recovery
    if the authority projection is unavailable or malformed.
  - `Closed` issues are immutable on the normal rail. Canonical ordering is:
    - implementation commit(s) while the issue remains `In Progress`
    - final receipt/closeout commit that records implementation evidence and flips the issue doc to `Closed`
    - no more commits on that issue unless Luis explicitly approves an override or the lane is intentionally reopened
- Agents must not run raw Git mutation commands:
  - `git add`
  - `git commit`
  - `git restore`
  - `git checkout`
  - `git reset`
  - `git rebase`
  - `git cherry-pick`
  - `git merge`
  - `git stash`
  - `git clean`
  - `git revert`
- Read-only Git inspection is discouraged and allowed only when Luis explicitly requests it, or when needed to resolve a blocking alignment conflict.
- Never stage, commit, or rewrite history through raw Git mutation commands.

#### FAST-EYES override rule

- FAST-EYES is override-only and must be explicitly approved by Luis.
- Override operation is one-shot and still canonical (`aware-cli commit` only).
- Raw `git add`/`git commit` are not allowed for FAST-EYES.
- Every override must append approval + commit evidence in:
  - issue `Updates`
  - `docs/feed/YYYY/MM/DD.md`

### E) Parallel safety

- One active owner per issue.
- `Updates` sections are append-only; do not rewrite prior bullets.
- If overlap/conflict is detected, log it in the issue and in FEED `Alignment checks` before continuing.
- If owner identity is invalid/unmapped, set `Status: Blocked` and `Owner: Unassigned` until remapped to a stable provider-backed execution id.

### F) Alignment protocol is mandatory

- Use `docs/alignment/PROTOCOL.md` for shared semantic coordinates before broad direction or invariant work.
- Alignment coordinates must be issue-derived, actor-scoped, and receipt-backed.
- `AGENTS.md` is the bootstrap contract; do not use it as the weekly invariant ledger.
- Treat `docs/alignment/CURRENT.md` as mutable private current truth and `docs/alignment/daily/YYYY/MM/DD.md` as the receipt aggregation track.
- Public-safe alignment lives in `docs/alignment/PUBLIC.md`; do not publish private issue/feed refs into the public facade.
- If current direction is unclear, read today's issue index, the current week's issue headings, `docs/alignment/CURRENT.md`, and the relevant issue files before claiming implementation.

## 1) Read once (SSOT map)

- [Architecture Overview](./docs/architecture/overview.md)
- [Aware TOML Hierarchy](./docs/architecture/aware-toml-hierarchy.md)
- [Compiler Ledger](./docs/architecture/compiler-ledger.md)
- [Kernel env: aware.environment.toml -> runtime manifest](./docs/architecture/kernel-environment-from-aware-environment-toml.md)
- [Agent Canonical Rules](./docs/architecture/agent-canonical-rules.md)
- [Interface Network Canonical Milestones](./docs/architecture/interface-network-canonical-milestones.md)
- [Issues Protocol](./docs/issues/PROTOCOL.md)
- [Agent Feed Protocol](./docs/feed/PROTOCOL.md)
- [Goals Protocol](./docs/goals/PROTOCOL.md)
- [Alignment Protocol](./docs/alignment/PROTOCOL.md)
- [Current Alignment](./docs/alignment/CURRENT.md)
- [Specs Protocol (SPEC/PHASES/ITERATIONS)](./docs/specs/PROTOCOL.md)
- [Live Feed](./docs/feed/FEED.md)
- [Active Goals (Latest)](./docs/goals/LATEST.md)

Canonical source remains `.aware` plus the minimal TOML SSOT files. Product
and workspace package materialization runs through Workspace materialize:

```bash
uv run aware-cli workspace materialize --workspace-toml workspaces/<workspace>/aware.workspace.toml --package <package_name> --plan
```

Use the equivalent `aware-dev materialize` / Workspace SDK or Workspace service
facade only when the issue or spec names that facade and it records the same
Workspace materialize receipt. `libs/environment-artifacts` and compile-pack
paths are deprecation/bridge targets, not product-lane materialization rails.

## 2) Canonical development loop (the only path)

1. Structure SSOT: edit `.aware` sources and minimal TOMLs.
2. Materialize workspace/package changes through Workspace materialize:
   plan first with `uv run aware-cli workspace materialize --workspace-toml workspaces/<workspace>/aware.workspace.toml --package <package_name> --plan`, then execute the issue-scoped materialization when generated artifacts are explicitly in scope.
3. Runtime: implement handlers only inside allowed `impl` sections.
4. Tests: update/add module proof tests.
5. Representation: align panes with declared projection views.
6. Human validation: verify behavior in Interface runtime.

For DTO/API/package/module product work, select the owning semantic package with
`--package` and record the Workspace materialize receipt in the issue. Do not
use `aware-cli compile package`, `aware-cli compile api`, or direct
environment-artifacts commands as product-lane proof. `aware-cli compile module`
is a narrow compiler-maintenance exception only when no Workspace materialize
rail exists, and the issue must state why.

## 3) What you may edit vs generated read-only

### Editable (SSOT)

- `.aware` ontology sources:
  - `modules/**/structure/**/aware/**/*.aware`
- `.aware program` assets (deterministic invocation plans):
  - `configs/seeds/**/*.aware` (kernel seed + future ops/migrations)
  - `modules/**/programs/**/*.aware` (module-owned programs; peer to structure/runtime/representation)
  - `configs/seeds/aware.programs.toml` (operator-owned program registry contract)
  - `modules/**/programs/aware.programs.toml` (module-owned program registry contract)
- TOML SSOT:
  - `modules/**/structure/**/aware.toml`
  - `modules/**/structure/**/stable_ids.toml`
  - `modules/**/aware.module.toml`
  - `modules/**/structure/aware.workflows.toml`
  - `aware.environment.toml`
- Documentation:
  - `docs/**`
- Runtime implementation:
  - `modules/**/runtime/**/handlers/impl/**`

### Read-only (generated)

- Generated/materialized artifacts:
  - `modules/**/structure/**/.aware/**`
  - `modules/**/structure/**/{python,dart,sql,sqlite}/**`
- Runtime caches/state:
  - `.aware/**`
  - `_aware/**`

Do not edit generated artifacts manually.

## 4) Materialize and lock discipline

### Normal workspace/package loop

```bash
uv run aware-cli workspace materialize --workspace-toml workspaces/<workspace>/aware.workspace.toml --package <package_name> --plan
```

If the plan is accepted and generated/materialized artifacts are in scope, run
the same bounded package selection through the issue-approved execution mode,
for example:

```bash
uv run aware-cli workspace materialize --workspace-toml workspaces/<workspace>/aware.workspace.toml --package <package_name> --execute-heavy-semantic-materialization --json
```

Record the Workspace materialize receipt path/status in the issue. If Workspace
materialize is blocked, record the blocked receipt or blocker and stop; do not
fall back to retired compile rails.

### Retired and bridge-only rails

- `aware-cli compile package` is retired/bridge-only and is not validation for active workspace/package product work.
- `aware-cli compile api`, direct `libs/environment-artifacts`, and compile-pack commands are bridge/deprecation paths unless an explicit compiler-bridge issue owns them.
- Generated/materialized artifacts must come from Workspace materialize or an issue-named canonical generator, never from manual edits.

### Narrow compiler maintenance exception

Use module compile only for isolated compiler/module maintenance when the issue
states why Workspace materialize is not the applicable rail:

```bash
aware-cli compile module <module_id>
```

Intentional lock/ledger advance remains explicit:

```bash
aware-cli compile --update-lock --update-ledger module <module_id>
```

Environment compile is rare and only for locking a composed kernel version, not
for package product materialization:

```bash
aware-cli compile environment <environment_handle>
```

Do not hand-edit lock/ledger outputs.

## 5) Runtime mutation boundary and handler rules

- Generated ontology/runtime materialization is read-only.
- Implement logic only in handler `impl` files.
- Edit only inside explicit user sections:
  - `# --- AWARE: USER_IMPORTS START/END`
  - `# --- AWARE: LOGIC START <fn> / END <fn>`
- Mutation boundary is enforced:
  - A handler may mutate only the invoked instance.
  - Cross-object changes require invoking that target object's public method.

Reference:
- Meta runtime handler execution and service/module public invocation facades
  own the current mutation boundary. Do not add new `aware_runtime` imports.

## 6) Projection and representation invariants

- Projection views are declared in `.aware` and are canonical for `FocusScope.view_id`.
- Do not invent view keys at runtime.
- Keep representation changes aligned with projection/view declarations.

References:
- `languages/aware/grammar/docs/PROJECTION_VIEWS.md`
- `apps/interface_flutter/aware_pane_runtime/docs/projection-views.md`

## 7) Tests are required

- Add/update tests for behavior changes.
- Module proof contract must hold.

References:
- Existing module proof tests under the owning module/workspace runtime tests.
- Meta runtime proof helpers in `aware_meta.runtime.testing`.

## 8) Troubleshooting quick checks

- Missing runtime manifest during environment compile:
  - materialize the owning workspace package first, or document a narrow module compile exception in the issue.
- `Cross-object mutation detected`:
  - fix handler to obey mutation boundary.
- Projection view not appearing:
  - verify view declaration in `.aware`, run Workspace materialize for the owning package, confirm deterministic default view configuration.
