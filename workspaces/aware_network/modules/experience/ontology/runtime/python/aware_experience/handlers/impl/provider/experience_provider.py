from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.provider.experience_provider import ExperienceProvider
from aware_experience_ontology.provider.experience_provider_action_binding import ExperienceProviderActionBinding

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def bind_action(
    experience_provider: ExperienceProvider,
    binding_key: str,
    experience_invocation_action_config_id: UUID,
    provider_action_ref: str | None = None,
    required_contract_scope: str = "operation",
    selection_policy: str = "contract_required",
    status: str = "active",
    description: str | None = None,
) -> ExperienceProviderActionBinding:
    """
    Bind one Experience action config to this provider slot.

    Contract:
    - Experience owns the public provider/action contract.
    - Provider-owned fulfillment binds concrete operations to this binding later.
    """

    # --- AWARE: LOGIC START bind_action
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END bind_action


async def build_via_projection_experience(
    projection_experience_id: UUID,
    provider_key: str,
    provider_kind: str = "provider",
    selection_policy: str = "contract_required",
    status: str = "active",
    title: str | None = None,
    description: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> ExperienceProvider:
    """
    Create one public provider slot under a ProjectionExperience.

    Contract:
    - Parent ProjectionExperience scope is propagated by constructor lowering.
    - Stable identity is `(projection_experience_id, provider_key)`.
    - The provider slot is Experience-owned public contract, not a concrete
      implementation object.
    """

    # --- AWARE: LOGIC START build_via_projection_experience
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_projection_experience
