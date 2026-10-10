Role instantiation CORE:

- `Role` binds policy scope to graph identity plane (`OIGI` required, `OIGB` optional).
- `ActorRole` is the explicit assignment edge (Actor -> Role).
- Use program-owned binding (`identity:EnsureActorRoleBindingFromBranch_v1`) once target lane branch is known.
- For conversation-first bootstrap, use composition rail `conversation_default:EnsureConversationActorRoleBinding_v1`.

Scope and determinism:

- Binding symbols are explicit (`actor_id`, `actor_identity_branch_id`, `role_config_name`, `object_instance_graph_domain_branch_id`).
- Keep binding in the actor identity branch for deterministic replay.

Reference assets only:

- `docs/rules/SOFTWARE/assets/minimal-references/4-policy.md`
- `docs/rules/SOFTWARE/assets/minimal-references/end-to-end-checklist.md`
