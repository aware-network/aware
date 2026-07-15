from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Skill Ontology
from aware_skill_ontology.skill.skill_config_api_endpoint import SkillConfigApiEndpoint

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_meta.runtime.handler_context import current_handler_session
from aware_skill_ontology.stable_ids import stable_skill_config_api_endpoint_id

# --- AWARE: USER_IMPORTS END


async def build_via_skill_config_api(
    skill_config_api_id: UUID, api_endpoint_id: UUID, capability_name: str, name: str, description: str | None = None
) -> SkillConfigApiEndpoint:
    """
    Create one Skill-owned API endpoint requirement.

    Contract:
    - This object is Skill-owned endpoint requirement truth.
    - `capability_name` and `name` preserve Skill-owned selection identity.
    - It targets API-owned `ApiCapabilityEndpoint` invocation truth.
    - Projection routes the target through API's `Api` projection.
    """

    # --- AWARE: LOGIC START build_via_skill_config_api
    skill_config_api_endpoint_id = stable_skill_config_api_endpoint_id(
        skill_config_api_id=skill_config_api_id,
        api_endpoint_id=api_endpoint_id,
        capability_name=capability_name,
        name=name,
    )
    session = current_handler_session()
    existing = session.imap_get(SkillConfigApiEndpoint, skill_config_api_endpoint_id)
    if existing is not None:
        if (
            existing.skill_config_api_id != skill_config_api_id
            or existing.api_endpoint_id != api_endpoint_id
            or existing.capability_name != capability_name
            or existing.name != name
        ):
            raise RuntimeError(
                "SkillConfigApiEndpoint.build_via_skill_config_api payload mismatch for existing endpoint: "
                + f"skill_config_api_endpoint_id={skill_config_api_endpoint_id}"
            )
        return existing

    return SkillConfigApiEndpoint(
        id=skill_config_api_endpoint_id,
        skill_config_api_id=skill_config_api_id,
        api_endpoint_id=api_endpoint_id,
        api_endpoint=session.imap_get(ApiCapabilityEndpoint, api_endpoint_id),
        capability_name=capability_name,
        name=name,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_skill_config_api
