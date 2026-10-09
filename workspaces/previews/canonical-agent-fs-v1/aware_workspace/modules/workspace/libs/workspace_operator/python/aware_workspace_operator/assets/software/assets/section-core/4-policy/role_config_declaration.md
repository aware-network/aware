RoleConfig declaration CORE flow:

1. Declare policy topology in `.aware` (`RoleConfig`, class policy, function policy).
2. Install policy through a deterministic `.aware program` (`identity:RoleConfigToolPolicies_v1`).
3. Drive policy values from seed profile symbols (`seed.conversation_role_config_*`).
4. Validate idempotent install and commit truth.

Reference assets only:

- `docs/rules/SOFTWARE/assets/minimal-references/4-policy.md`
- `configs/seeds/aware.programs.toml`
- `docs/rules/SOFTWARE/assets/minimal-references/end-to-end-checklist.md`
