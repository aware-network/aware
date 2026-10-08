# Workspace Software Narrative (Interface-Node Power)

The revision-owned `aware_workspace_operator/assets/software` bundle is the
documentation spine that external workspaces inherit through Workspace bootstrap.

The narrative here must remain executable:
operators should read this and know **what can run**, **who can run it**, and
**what truth proves action happened**.

The primary proposition is: every module declared through `.aware` becomes a
reproducible software surface for both human and agent workflows, with
`@interface/app` as the human-visible proof node.

`aware init` seeds this flow from the Workspace operator package, so all generated
workspaces inherit the same contract text and runtime order.

## Core Position

- `@interface/app` is the operator power node for software usage and visibility.
- Reactive TUI and pane mounting are the first proof that a contract is live.
- `docs/rules/SOFTWARE` is the generated output contract, not raw implementation
  details.
- Runtime truth is the only authority for progress (`accepted -> running -> feedback* -> terminal`).

## Operator Flow (single paragraph)

Start with `aware-dev conversation bootstrap` to establish the current
service-backed headless Conversation context, then use
`aware-dev conversation add-message` and `aware-dev conversation tail` to act
and observe. The future full reactive Dev room enters through the authored Dev
Experience; it must preserve capability-first controls so humans see
`capability -> role -> grant -> act` first, then execute committed conversation messages as
`function_call -> commit -> condition -> event -> actor_subscription -> action -> feedback* -> terminal -> commit`,
and surfaces all outcomes as `pane refresh` evidence in `@interface/app`.

## End-to-End Flow (AI-native, role-gated)

The full loop is deterministic and must hold for every module:

1. Message / consent input
2. Commit creation (`conversation`, identity, or policy change)
3. Event materialization from committed truth
4. Condition + actor-role + actor-subscription gate
5. Action execution with feedback*
6. Terminal status (`succeeded|failed|skipped|dead_letter`)
7. Commit(s) and pane refresh as visible end state

Where possible, this same chain should be rendered by both local TUI and Interface.

## Interface-First Documentation Rules

- Generated docs must use these terms consistently:
  - `message` (user action)
  - `commit` (proof of mutation)
  - `event` (trigger)
  - `subscription` (who wakes)
  - `action` (function call)
  - `feedback` (runtime stage signal)
  - `receipt` (evidence)
  - `terminal` (completion)
  - `pane refresh` (human-visible UI update)
- Any module onboarding should explain these gates in one paragraph before
  implementation details.
- Never present actions before capabilities; users must read capability first.

## Composition Map (Workspace operator package assets)

- `templates/<template_id>/*.md` define narrative shape.
- `profiles/<profile_id>.toml` define naming and token resolution.
- `assets/section-core/<stage>/*.md` keep stage-level truth blocks.
- `assets/minimal-references/*.md` store canonical references.

Generated files in `docs/rules/SOFTWARE/*` should reflect this same contract
without adding implementation-only detail.

## SOFTWARE Stages ↔ Runtime/Interface Responsibilities

- `0-config` → ontology, projection, and policy shape in `.aware` + TOMLs.
- `1-runtime` → handler `impl` logic and proof gates.
- `2-representation` → pane definitions and deterministic focus routes.
- `3-programs` → deterministic invocation and policy/bootstrap plans.
- `5-reactivity` → condition/event/action/subscription activation and attribution.

For this phase, all stages must agree on the same operator-facing contract:
human sees why an actor can run, what is allowed, and why the pane changed.

## Runtime and CLI Contract Anchors

- Current headless entry is the `aware-dev conversation` command family over
  Dev and Conversation API/service/SDK boundaries.
- The actor-facing entry is the authored Dev Experience through Interface; the
  retired root local-runtime launcher is not a compatibility authority.
- Turn lifecycle rendering must stay mailbox-driven:
  `accepted -> running -> feedback* -> terminal`.
- Completion is observed from runtime state/stream, not from prompt timeout alone.

## External Work Reuse

When `aware init` / workspace bootstrap copies these docs into a new workspace,
the same sequence should be reusable:

- one trusted operator node (`@interface/app`),
- one execution contract (runtime + mailbox),
- one visible proof surface (pane refresh from commits/events/actions),
- one human-first workflow (capabilities before execution).
