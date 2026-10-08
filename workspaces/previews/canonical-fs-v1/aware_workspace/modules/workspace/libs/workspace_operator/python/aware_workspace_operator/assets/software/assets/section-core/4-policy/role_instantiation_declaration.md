Role instantiation CORE flow:

1. Materialize identity branch and target lane branch id.
2. Apply `identity:EnsureActorRoleBindingFromBranch_v1` with explicit binding symbols.
3. For conversation-first bootstrap, prefer `conversation_default:EnsureConversationActorRoleBinding_v1` to compose lane creation + binding in one deterministic apply.
4. Resolve ActorRole -> Role -> RoleConfig function allowlist from materialized commits.
5. Verify idempotency and fail-closed behavior.

Reference assets only:

- `docs/rules/SOFTWARE/assets/minimal-references/4-policy.md`
- `docs/rules/SOFTWARE/assets/minimal-references/end-to-end-checklist.md`
