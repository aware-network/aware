Actor subscription declaration CORE flow:

1. Install reactivity config rails.
2. Seed domain lane/class instance (runtime auto-ensures scope from policy).
3. Prefer combined identity rail (`identity:EnsureActorActReactBindingFromBranch_v1`) for ACT + REACT in one deterministic apply.
4. For conversation-first composition, prefer `conversation_default:EnsureConversationActorActReactBinding_v1`.
5. Use split subscription-only rails (`identity:EnsureActorSubscriptionBinding_v1`, `identity:EnsureActorSubscriptionBindingFromBranch_v1`, `conversation_default:EnsureConversationActorSubscriptionBinding_v1`) only when role and subscription are intentionally managed in separate steps.
6. Validate idempotent subscription materialization and runtime scope evidence.

Reference assets only:

- `docs/rules/SOFTWARE/assets/minimal-references/5-reactivity.md`
