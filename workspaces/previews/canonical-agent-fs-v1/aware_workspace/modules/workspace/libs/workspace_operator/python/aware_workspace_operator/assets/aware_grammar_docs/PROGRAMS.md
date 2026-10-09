# Programs (Deterministic Invocation Plans)

`program` is a first-class top-level `.aware` declaration intended to model **deterministic instance evolution** as a
canonical plan that can later be executed as commit-backed `FunctionCall` steps.

This exists to prevent multiple ad-hoc “seeding/config instantiation” rails (Python/TOML/Markdown/YAML) from diverging.

## v0 Scope (What Exists Today)

v0 is intentionally small:

- Statement grammar: `let` bindings + `call` invocations only.
- No control flow (`if/else`), no loops, no IO, no randomness.
- Parses into an AST and compiles into a canonical IR (`InvocationPlan`) with deterministic validation.

Execution (turning an `InvocationPlan` into commit-backed `FunctionCall`s) intentionally lives outside the grammar package.

However, there is now a first executor wired for kernel seeding (MVP, kernel-specific):

- Program SSOT: `configs/seeds/aware_kernel.seed.aware`
- Runner: `services/node/aware_node_service/kernel_ops/seed_program_apply.py`
- Proof/parity: `services/node/tests/test_kernel_seed_stages.py`

And an env-experience executor for installing commit-backed config lanes (aware-api-only, DEV-first):

- Example program: `modules/conversation/programs/reactivity/conversation_reactivity_policies_v1.aware`
- Runner: `libs/environment-experience/aware_environment_experience/program_apply.py`
- CLI: `aware-environment-experience apply|provision --install-program <path>`
- Proof/idempotency: `services/node/tests/test_env_experience_program_reactivity_policies.py`

The kernel seed executor interprets reserved directive calls as context steps:

- `call plan.actor(...)`
- `call plan.lane(...)`
- `call plan.object(...)`
- `call plan.apply_program_ref(...)` (nested composition; symbol-forwarded)

`plan.lane` supports fail-closed and idempotency helpers:

- `skip_if_head=true`: skip all subsequent calls in the lane if the lane already has a head commit.
- `require_head=true`: fail if the lane has no head commit (use for compiler-owned lanes you must not create at runtime).

`plan.apply_program_ref` v0 runtime semantics:
- requires `program_ref="<module_id>:<program_name>"`
- optional `symbols={...}` map forwards explicit symbols to the nested program
- optional `validate_only=true|false` overrides nested validation mode
- cycle detection is fail-closed (A -> B -> A raises)

And evaluates a small registry of deterministic pure helper calls inside `let` expressions.

Stable IDs inside programs must be resolved from canonical sources (no re-authored UUIDv5 math per executor):

- Generic helpers (intrinsic): `stable.ns_url`, `stable.uuid5` (implemented in the Experience-owned program surface `aware_experience.program.language.stdlib`).
- Meta / OCG plane stable ids: `meta.stable_*` (canonical implementation: `aware_meta.graph.config.stable_ids`).
- Module-owned stable ids (recommended): `<module_id>.stable_*` resolved dynamically from compiler-emitted stable-id libraries:
  - `aware_<module_id>_ontology.stable_ids.<fn>`
  - fallback: `aware_<module_id>.stable_ids.<fn>` (compat only)

## Program Assets (Where They Live)

This repo treats `.aware program` files as **canonical SSOT artifacts**, but they have different ownership scopes:

- **Aware product / operator-owned programs**:
  - Kernel seed and future ops/migrations: `configs/seeds/**/*.aware`
  - Reserved (rare): environment-wide rollups: `configs/programs/`
- **Module-owned programs** (recommended for domain/policy/config lanes):
  - `modules/**/programs/**/*.aware` (peer to `structure/`, `runtime/`, `representation/`)

Direction:
- Prefer **one program per file**.
- Declare refs via `aware.programs.toml`:
  - module-owned: `modules/<module>/programs/aware.programs.toml`
  - operator-owned: `configs/seeds/aware.programs.toml`
- Runtime/API executors resolve `program_ref` using manifest-embedded `program_registry` when present; directory scans are compatibility fallback for legacy manifests.
- Runtime can be forced fail-closed (no legacy fallback) with:
  - `AWARE_RUNTIME_REQUIRE_PROGRAM_REGISTRY=1`

### Program Registry Contract (v0)

`aware.programs.toml` uses:

```toml
aware = 1

[[programs]]
ref = "conversation_default:ConversationReactivityPolicies_v1"
path = "reactivity/conversation_reactivity_policies_v1.aware"
name = "ConversationReactivityPolicies_v1"
dependencies = ["conversation-ontology", "reactivity-ontology", "meta-ontology"]
required_symbols = []
optional_symbols = ["plan.environment_id", "plan.process_id", "plan.thread_id"]
```

Validation rules:
- one declaration per program file for ref-based resolution
- `ref` format: `<module_id>:<program_name>`
- `name` must equal `<program_name>` from `ref`
- `path` is root-relative to the containing `programs/` directory and must point to `.aware`
- symbol contract fields are optional, but when present must be namespaced (`plan.*`, `boot.*`, etc).

## Canonical Example: Ensure Boot Interface Graph (AX==UX)

Problem: Interface (Dart) currently contains an explicit, capability-driven bootstrap routine that ensures the OS
navigation substrate exists from the first frame:

- `Interface` (device identity, lane-rooted)
- at least one `Window`
- the primary `FocusScope`
- `ThreadFocusScope` so the Thread exposes discoverable FocusScopes
- window viewport binding (`WindowFocusScope`) so a Window follows a FocusScope

This must not exist as duplicated step lists in Dart + Python + CLI + native agents.

Direction:
- define **one** `.aware program` that ensures this graph idempotently
- both Dart and Python session layers execute it by canonical ids
- stable ids used by the program must be compiler-owned (see `fb/2026-02-10/compiler-owned-stable-ids-codegen`)

Sketch (v0, executor-directed lane switching):

```aware
program EnsureBootInterfaceGraph_v0 {
    // Provided by the session layer (device installation id / agent interface id).
    let interface_id = plan.interface_id

    // Executor-resolved from the current API context.
    let environment_id = plan.environment_id
    let thread_id = plan.thread_id

    // Stable id derivations (do not guess UUIDs).
    let window_id = interface.stable_window_id(interface_id=interface_id, window_key="execution")
    let focus_scope_id = interface.stable_thread_device_focus_scope_id(
        window_id=window_id,
        thread_id=thread_id
    )
    let boot_branch_id = history.stable_branch_id(environment_id=environment_id, thread_id=thread_id)

    // Canonical v0 selection (Identity gate).
    let opgi_id = meta.stable_object_projection_graph_identity_id(opg_identity_key="aware_identity:identity")
    let view_id = meta.stable_object_projection_graph_view_id(
        object_projection_graph_identity_id=opgi_id,
        view_key="onboarding.welcome"
    )
    let focus_id = attention.stable_focus_id(object_projection_graph_identity_id=opgi_id)

    // Ensure Interface object in the `Interface` projection.
    call plan.lane(branch_id=interface_id, opg="Interface")
    call interface.Interface.create(os="macos", version="0.0.0")  // id is ctx.branch_id

    // Ensure Window object in the `Window` projection.
    call plan.lane(branch_id=window_id, opg="Window")
    call window.Window.build(window_id=window_id)
    call window.Window.set_active_focus_scope(
        focus_scope_id=focus_scope_id,
        title="Primary",
        description=null
    )

    // Ensure FocusScope object in the `FocusScope` projection.
    call plan.lane(branch_id=focus_scope_id, opg="FocusScope")
    call focus.FocusScope.build(title="Primary", description=null)

    // Ensure selection exists and is set commit-backed.
    call plan.lane(branch_id=opgi_id, opg="ObjectProjectionGraphIdentity", require_head=true)
    call plan.lane(branch_id=focus_id, opg="Focus")
    call focus.Focus.build(
        projection_hash=null,
        object_projection_graph_identity_id=opgi_id,
        description="Identity gate (boot)",
        is_active=true
    )
    call plan.lane(branch_id=focus_scope_id, opg="FocusScope")
    call plan.object(object_id=focus_scope_id)
    call focus.FocusScope.set_focus(focus_id=focus_id, rationale="boot")
    call focus.FocusScope.set_view(view_id=view_id, rationale="boot")

    // Register the FocusScope under the current OS Thread (discoverability only).
    // Note: Thread territory is OS-owned and committed in the `environment` lane.
    call plan.lane(branch_id=boot_branch_id, opg="Environment")
    call plan.object(object_id=thread_id)
    call thread.Thread.add_focus_scope(focus_scope_id=focus_scope_id)

    // Link Interface -> Window (commit only in the `Interface` projection).
    call plan.lane(branch_id=interface_id, opg="Interface")
    call interface.Interface.attach_window(window_id=window_id)
}
```

Notes:
- `plan.*` directives are executor-owned today. Long-term this should become first-class program syntax.
- The program must call **idempotent** functions only (or the owning ontology must introduce `ensure_*` functions).
- The program must fail-closed if required capabilities/function ids are missing.
- v0 programs cannot build interpolated strings; stable ids must come from module-owned stable-id libraries (`<module_id>.stable_*`) or meta stable-id delegates (`meta.stable_*`).

## Syntax (v0)

```aware
program ReactivitySeed {
    let schema = {"name": "conversation.created", "version": 1}

    call event.EventConfig.create(
        name="conversation.created",
        description="Conversation creation domain event.",
        event_schema=schema
    )
}
```

Notes:
- `;` is optional after `let` and `call` statements.
- `//` line comments are allowed anywhere a statement can appear.

## Expressions (v0)

Allowed expression forms:

- Calls: `some.Qualified.name(...)`
- Symbol references: `some.Qualified.name` or `human`
- Literals:
  - strings: `"..."` or `'...'`
  - numbers: `123` or `1.5`
  - booleans: `true` / `false`
  - null: `null`
  - raw blocks: `"""..."""` and `$$...$$` (treated as strings)
- Strict JSON:
  - objects: `{"key": "value", "n": 1}`
  - arrays: `[1, 2, 3]`

## Compilation: `program` -> `InvocationPlan`

Parsing produces `ProgramDeclaration` / `ProgramLet` / `ProgramCall` / `ProgramRef`.

Compilation produces a canonical IR:

- `InvocationPlan(name, steps=...)`
  - `PlanLet(name, value=...)`
  - `PlanInvoke(call=PlanCall(target, args=...))`

Key v0 compilation/validation rules:

- `let` names must be unique.
- Call args:
  - positional args cannot appear after keyword args
  - duplicate keyword names are rejected
- References are classified deterministically:
  - if a ref matches a prior `let`, it becomes a `PlanLocalRef`
  - otherwise it becomes a `PlanSymbolRef` (to be resolved by the executor)
- JSON objects are canonicalized by sorting keys recursively (arrays keep order).

API surface:
- `aware_experience.program.language.parse_program_declarations(source: str) -> tuple[ProgramDeclaration, ...]`
- `aware_experience.program.language.compile_invocation_plans(source: str) -> tuple[InvocationPlan, ...]`

## Quick Dry-Compile

```bash
UV_CACHE_DIR=$PWD/.uv-cache uv run --project languages/aware/grammar/grammar python - <<'PY'
from pathlib import Path
from aware_experience.program.language import compile_invocation_plans

src = Path("languages/aware/grammar/grammar/tests/samples/reactivity_seed_program.aware").read_text()
print(compile_invocation_plans(src)[0])
PY
```

## Next Stages (Planned)

- General-purpose executor: resolve `PlanSymbolRef` (FunctionConfig, enums, OPG selectors, etc) and emit deterministic commit-backed `FunctionCall`s.
- Make execution context steps explicit and non-hacky:
  - promote `plan.*` directives to first-class statement grammar (instead of reserved call targets), or
  - formalize a small `context` statement surface while keeping determinism and no-control-flow constraints.
- Keep the language mutation-boundary-aligned: state changes only via commits.
