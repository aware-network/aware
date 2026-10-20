# aware-goal-sdk 0.3

This is the neutral, provider-injected Goal SDK for Phase/Gate transport,
read-only direction and eligibility requests, authored Markdown source, and
dependency View contracts. Its base dependency is
`aware-goal-operational-runtime`. The wheel does not contain generated Goal
API/DTO clients, Service adapters, Experience View code, or ontology/ORM
implementations.

## What this wheel exposes

- `GoalPhaseOperationClient.observe_eligibility(...)` transports a read-only
  Phase eligibility request to an explicitly supplied provider. The neutral
  runtime makes the eligibility decision; this SDK validates the request and
  result wire contract without independently evaluating Gates.
- `GoalPhaseDirectionClient.observe_phase_direction(...)` and
  `verify_phase_direction_currentness(...)` transport provider-qualified
  direction and currentness results. A Phase direction receipt's
  whole-document currentness must not be presented as semantic-scope
  currentness for an unchanged Phase after an unrelated Goal edit.
- Markdown source and Phase projection modules parse or carry authored
  structure and identity. Parsing a Goal document does not admit operational
  lifecycle facts, satisfy dependencies, select an Issue, or authorize work.
- `compose_goal_dependency_view(...)` and `decode_goal_dependency_view(...)`
  carry exact declarations and optional supplied observations. Presentation
  summaries are not additional dependency, Gate, or currentness authority.

Use the package's exported `GoalPhaseOperationClient`,
`GoalPhaseDirectionClient`, Phase Markdown, and dependency View contracts, or
their corresponding `aware_goal_sdk` modules. Construct operation clients
with a provider admitted for the selected target. The SDK does not discover a
provider from availability or fall back from one authority to another.

## Authority boundary

Goal direction and eligibility are read-only and non-authorizing. They do not
approve a Phase, admit Agent pursuit, dispatch, open or close an Issue, or
mutate a Workspace. Committed-source qualification belongs to the selected
provider; the Phase/Gate decision belongs to neutral Goal runtime. Issue and
WorkContext authority remains separate from Goal direction.

Do not derive current Goal status, lane state, Phase progress, or time from
`docs/goals/LATEST.md`, path dates, table order, or a rendered View. Use the
admitted Goal source and its qualified operational observations. Missing
observations remain unevaluated; the SDK must not invent satisfaction or
currentness.

## Legacy Service and Home View callers

The old `GoalSdkClient`, generated Goal API/DTO operations, Home View
rendering, and legacy Goal–Lane–Issue adapters are **not exported by 0.3**.
Callers that intentionally retain those contracts must install
`aware-goal-service-view-compat` and import
`aware_goal_service_view_compat` explicitly. Its separately packaged README
labels the legacy behavior and migration boundary. No extra or conditional
import makes those adapters part of this neutral wheel.
