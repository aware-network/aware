# Stage 4 - Policy (RoleConfig -> FunctionConfig -> ActorRole)

Goal: resolve deterministic capabilities from commit-backed ActorRole policy rails.

Minimal references:

- `docs/aware/grammar/PROGRAMS.md`
- `configs/seeds/README.md`
- `configs/seeds/aware.programs.toml`
- `configs/seeds/aware_kernel.seed.aware`
- `configs/seeds/aware_kernel.seed.profile.toml`
- `docs/rules/SOFTWARE/4-policy.md`
- `docs/rules/SOFTWARE/assets/minimal-references/3-programs.md`
- `docs/rules/SOFTWARE/assets/minimal-references/end-to-end-checklist.md`

Rules:

- RoleConfig is policy root.
- Function-level policy is canonical via `RoleConfigClassConfigFunctionConfig.function_config_id`.
- Role instances bind actor/runtime scope via OIG identity/branch.
- Seed policy declarations are profile-driven (`seed.conversation_role_config_*`).

Done criteria:

- Policy program installs deterministically from profile symbols.
- Role/actor binding proofs pass idempotently.
- Agent/runtime function allowlist resolves from materialized commits.
