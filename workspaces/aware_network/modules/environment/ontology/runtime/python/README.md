# Aware Environment Runtime

Runtime handlers and helpers for the Environment module.

## Ownership

Environment runtime owns Environment/Process/Thread semantics and the OS lane
topology model:

- Environment ladder construction and evolution.
- Environment readiness orchestration: `ensure_ready` phase ordering,
  idempotency, readiness receipts, and modular readiness step scheduling.
- Process/thread creation.
- `Thread.attach_lane` and related domain-lane-to-thread attachment policy.
- The target Meta-fanout reaction that keeps Environment lane topology aligned
  after domain commits.

Meta owns graph commit authority and emits commit fanout. Environment service
and Environment SDK/API provide the subscription and host boundary. They do not
own the Environment lane topology model.

## Target Reaction Rail

The next migration target for Environment lane propagation is:

```text
MetaCommitEventEnvelope
-> Environment SDK/API commit-event subscription source
-> aware_environment runtime lane-topology reaction
-> generated API call for Thread.attach_lane
-> Meta commit
```

The reaction package should consume typed generated DTOs and typed ports. It
must not import `FunctionCallInvoker`, `FSLaneCommitter`, local Meta runtime
helpers, or local commit-store internals for service reaction work.

The subscription event must preserve Meta commit identity and orchestration
context. A lane-head receipt alone is not sufficient unless Environment SDK/API
enriches it with that context.

## Environment Readiness

`ensure_ready` is the canonical Environment admission operation. The external
caller contract remains generated Environment API/SDK, but the semantic owner is
the Environment runtime. Environment service should host the endpoint, validate
host/package/infrastructure requirements, and delegate readiness planning to
Environment services over typed ports.

Meta owns graph commit authority. Any Environment genesis or readiness graph
write must go through generated Meta API/SDK, not local Meta runtime imports or
local commit-store mutation. The target architecture and first implementation
slice are documented in [ensure_ready.md](../docs/ensure_ready.md).

## Compatibility Debt

Current inline compatibility behavior still exists in
`libs/runtime/aware_runtime/function_call/environment_lane.py`. Environment
service keeps a compatibility import surface for host wiring, but pure attach
planning, skip rules, idempotency, and topology update semantics now live under
`aware_environment.reactions.environment_lane`.
