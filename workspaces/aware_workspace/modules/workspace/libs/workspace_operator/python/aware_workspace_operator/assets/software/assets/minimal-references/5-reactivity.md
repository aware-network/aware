# Stage 5 - Reactivity (Config + Activation)

Goal: model deterministic ACT-REACT contracts from reactivity config to actor activation binding.

Minimal references:

- `docs/aware/grammar/PROGRAMS.md`
- `configs/seeds/aware.programs.toml`
- `configs/seeds/aware_kernel.seed.aware`
- `configs/seeds/aware_kernel.seed.profile.toml`
- `docs/rules/SOFTWARE/5-reactivity.md`
- `docs/rules/SOFTWARE/assets/minimal-references/3-programs.md`
- `docs/rules/SOFTWARE/assets/minimal-references/end-to-end-checklist.md`

Rules:

- Keep condition/event/action identities deterministic.
- Prefer program-owned rails for policy install and activation binding.
- Default activation path is integrated ACT-REACT binding (`Ensure*ActReactBinding*` refs).
- Runtime auto-ensures event scopes from class-instance creation + policy registry.
- Use explicit scope rails only for fallback/override operations.
- Use subscription-only binding programs when ACT and REACT rollout must be split.
- ActorSubscription is identity-owned activation contract (OIGI required, OIGB optional).
- Agent execution consumes canonical subscription/event/action bindings.

Done criteria:

- Reactivity config compiles.
- Reactivity policy install path passes.
- Subscription binding programs materialize idempotently.
- Agent ACT-REACT execution contracts resolve canonical ids.
