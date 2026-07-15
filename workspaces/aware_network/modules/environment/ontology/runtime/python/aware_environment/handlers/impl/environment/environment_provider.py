from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Environment Ontology
from aware_environment_ontology.environment.environment_provider import EnvironmentProvider
from aware_environment_ontology.environment.environment_provider_grant import EnvironmentProviderGrant

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def grant_scope(
    environment_provider: EnvironmentProvider,
    grant_key: str,
    scope_kind: str = "profile",
    process_config_id: UUID | None = None,
    thread_config_id: UUID | None = None,
    object_projection_graph_id: UUID | None = None,
    action_scope: str | None = None,
    status: str = "active",
    description: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentProviderGrant:
    """
    Grant this provider slot a scoped Environment capability.

    Contract:
    - Grants are provider-neutral and Experience-free.
    - Experience resolves these grants before issuing graph gateway context.
    """

    # --- AWARE: LOGIC START grant_scope
    if environment_provider.id is None:
        raise RuntimeError("EnvironmentProvider.grant_scope requires EnvironmentProvider.id")

    created = await EnvironmentProviderGrant.build_via_environment_provider(
        environment_provider_id=environment_provider.id,
        grant_key=grant_key,
        scope_kind=scope_kind,
        process_config_id=process_config_id,
        thread_config_id=thread_config_id,
        object_projection_graph_id=object_projection_graph_id,
        action_scope=action_scope,
        status=status,
        description=description,
        metadata_json=metadata_json,
    )
    for existing in environment_provider.grants:
        if existing.id == created.id:
            return existing
    environment_provider.grants.append(created)
    return created
    # --- AWARE: LOGIC END grant_scope


async def build_via_environment_profile_config(
    environment_profile_config_id: UUID,
    provider_key: str,
    provider_kind: str = "provider",
    contract_ref: str | None = None,
    selection_policy: str = "contract_required",
    status: str = "active",
    title: str | None = None,
    description: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentProvider:
    """
    Create one provider-neutral slot under an EnvironmentProfileConfig.

    Contract:
    - Parent EnvironmentProfileConfig scope is propagated by constructor lowering.
    - Stable identity is `(environment_profile_config_id, provider_key)`.
    """

    # --- AWARE: LOGIC START build_via_environment_profile_config
    return EnvironmentProvider(
        environment_profile_config_id=environment_profile_config_id,
        provider_key=provider_key,
        provider_kind=provider_kind,
        contract_ref=contract_ref,
        selection_policy=selection_policy,
        status=status,
        title=title,
        description=description,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END build_via_environment_profile_config
