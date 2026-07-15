from __future__ import annotations

"""Runtime identity stable-id surface.

Policy:
- Ontology entity stable-id formulas are compiler-owned and imported from
  `aware_identity_ontology.stable_ids`.
- Runtime-only helpers in this module are allowed only for Identity-owned
  non-ontology rails.
"""

from aware_identity_ontology.stable_ids import (
    NS_IDENTITY,
    stable_actor_id,
    stable_actor_role_id,
    stable_actor_subscription_event_id,
    stable_actor_subscription_id,
    stable_auth_token_id,
    stable_auth_token_registry_id,
    stable_human_id,
    stable_identity_connection_id,
    stable_identity_id,
    stable_identity_profile_id,
    stable_organization_id,
    stable_organization_member_id,
    stable_role_config_class_config_function_config_id,
    stable_role_config_class_config_id,
    stable_role_config_id,
    stable_role_id,
)


__all__ = [
    "NS_IDENTITY",
    "stable_actor_id",
    "stable_actor_role_id",
    "stable_actor_subscription_id",
    "stable_actor_subscription_event_id",
    "stable_auth_token_id",
    "stable_auth_token_registry_id",
    "stable_human_id",
    "stable_identity_connection_id",
    "stable_identity_id",
    "stable_identity_profile_id",
    "stable_organization_id",
    "stable_organization_member_id",
    "stable_role_config_id",
    "stable_role_config_class_config_id",
    "stable_role_config_class_config_function_config_id",
    "stable_role_id",
]
