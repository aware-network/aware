ActorSubscription CORE:

- Identity module owns activation bindings.
- Runtime owns event scope materialization (`EventConfigConditionConfigScope`) from
  class-instance create + reactivity policy registry.
- Default to integrated program rails:
  - `identity:EnsureActorActReactBindingFromBranch_v1`
  - `conversation_default:EnsureConversationActorActReactBinding_v1`
- Keep split actor-intent rails when ACT and REACT rollout must be separated:
  - `identity:EnsureActorSubscriptionBinding_v1`
  - `identity:EnsureActorSubscriptionBindingFromBranch_v1`
  - `conversation_default:EnsureConversationActorSubscriptionBinding_v1`
- Keep explicit scope programs only as fallback overrides:
  - `identity:EnsureEventScopeBindingFromBranch_v1`
  - `conversation_default:EnsureConversationEventScopeBinding_v1`
- Scope contracts remain graph-identity first (`OIGI` required, `OIGB` optional).

Reference assets only:

- `docs/rules/SOFTWARE/assets/minimal-references/5-reactivity.md`
