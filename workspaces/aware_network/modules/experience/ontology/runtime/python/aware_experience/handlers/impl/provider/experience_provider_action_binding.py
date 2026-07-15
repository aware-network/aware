from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.provider.experience_provider_action_binding import ExperienceProviderActionBinding

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_experience_provider(
    experience_provider_id: UUID,
    binding_key: str,
    experience_invocation_action_config_id: UUID,
    provider_action_ref: str | None = None,
    required_contract_scope: str = "operation",
    selection_policy: str = "contract_required",
    status: str = "active",
    description: str | None = None,
) -> ExperienceProviderActionBinding:
    """
    Create one provider action binding under an ExperienceProvider.

    Contract:
    - Parent ExperienceProvider scope is propagated by constructor lowering.
    - Stable identity is `(experience_provider_id, binding_key)`.
    - The bound action stays Experience-owned; provider-owned operations bind
      to this object in the fulfillment migration.
    """

    # --- AWARE: LOGIC START build_via_experience_provider
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_experience_provider
