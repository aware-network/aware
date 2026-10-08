# Seeds (Aware‑specific SSOT)

This revision-owned package folder contains **Aware product seeding specs**
(not module ontology). Workspace bootstrap copies the bundle to
`configs/seeds/` in generated external workspaces.

Canonical direction:
- `.aware program` files are the long-term SSOT for deterministic instance seeding/config instantiation.
  - Kernel genesis seed source: `aware_kernel.seed.aware`
- Legacy TOML specs exist for compatibility with the current node boot entrypoint.
  - Kernel legacy spec source: `aware_kernel.seed.toml`

Rules:
- **Commit-only**: seeds are applied by calling canonical constructors/instance handlers that emit commits.
- **No secrets**: private keys are never committed here. Seed runners authenticate via `AWARE_KERNEL_SEED_KEYS_JSON` / `AWARE_KERNEL_SEED_KEYS_FILE`.
- **Idempotent**: specs must be safe to re-run (stable ids + presence checks).

Apply (dev/operator):
- TOML: pass this package's `aware_kernel.seed.toml`, or generated workspace `configs/seeds/aware_kernel.seed.toml`.
- Program: pass this package's `aware_kernel.seed.aware`, or generated workspace `configs/seeds/aware_kernel.seed.aware`.

See: `docs/architecture/kernel-seed-and-migrations.md`
