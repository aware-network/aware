RoleConfig policy CORE:

- `RoleConfig` is the commit-backed policy root.
- Function allowlist policy is canonical on `RoleConfigClassConfigFunctionConfig.function_config_id`.
- Prefer program-owned installation (`identity:RoleConfigToolPolicies_v1`) over ad-hoc runtime mutation.

Profile-first reproducibility:

- Seed policy symbols must be declared in `configs/seeds/aware_kernel.seed.profile.toml`.
- Kernel program must consume profile symbols (no hardcoded policy names in program source).

Reference assets only:

- `docs/rules/SOFTWARE/assets/minimal-references/4-policy.md`
- `configs/seeds/aware_kernel.seed.aware`
- `configs/seeds/aware_kernel.seed.profile.toml`
