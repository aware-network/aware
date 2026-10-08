# Stage 3 - Programs (Deterministic Seed/Instantiation Rail)

Goal: define reproducible `.aware` program plans that materialize canonical objects through function calls and commits.

Minimal references:

- `docs/aware/grammar/PROGRAMS.md`
- `configs/seeds/README.md`
- `configs/seeds/aware.programs.toml`
- `configs/seeds/aware_kernel.seed.aware`
- `configs/seeds/aware_kernel.seed.profile.toml`
- `docs/rules/SOFTWARE/3-programs.md`
- `docs/rules/SOFTWARE/assets/minimal-references/end-to-end-checklist.md`

Rules:

- Programs are the canonical reproducible action rail (`func call -> commit`).
- Program inputs must be profile-driven symbols (no hardcoded environment values).
- Program replay must be idempotent and evidence-backed.

Done criteria:

- Program definitions compile.
- Profile symbol contract resolves deterministically.
- Program replay proof path passes with evidence logged.
