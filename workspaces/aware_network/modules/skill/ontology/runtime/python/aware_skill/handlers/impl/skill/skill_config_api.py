from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Skill Ontology
from aware_skill_ontology.skill.skill_config_api import SkillConfigApi
from aware_skill_ontology.skill.skill_config_api_endpoint import SkillConfigApiEndpoint

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_api_ontology.api.api import Api
from aware_meta.runtime.handler_context import current_handler_session
from aware_skill_ontology.stable_ids import stable_skill_config_api_id

# --- AWARE: USER_IMPORTS END


async def add_api_endpoint(
    skill_config_api: SkillConfigApi,
    api_endpoint_id: UUID,
    capability_name: str,
    name: str,
    description: str | None = None,
) -> SkillConfigApiEndpoint:
    """
    Add one Skill-owned API endpoint requirement under this API grouping.
    """

    # --- AWARE: LOGIC START add_api_endpoint
    if skill_config_api.id is None:
        raise RuntimeError("SkillConfigApi.add_api_endpoint requires SkillConfigApi.id")

    created = await SkillConfigApiEndpoint.build_via_skill_config_api(
        skill_config_api_id=skill_config_api.id,
        api_endpoint_id=api_endpoint_id,
        capability_name=capability_name,
        name=name,
        description=description,
    )
    for existing in skill_config_api.api_endpoints:
        if existing.id == created.id:
            return existing
    skill_config_api.api_endpoints.append(created)
    return created
    # --- AWARE: LOGIC END add_api_endpoint


async def build_via_skill_config(skill_config_id: UUID, api_id: UUID, description: str | None = None) -> SkillConfigApi:
    """
    Create one Skill-level API grouping.
    """

    # --- AWARE: LOGIC START build_via_skill_config
    skill_config_api_id = stable_skill_config_api_id(
        skill_config_id=skill_config_id,
        api_id=api_id,
    )
    session = current_handler_session()
    existing = session.imap_get(SkillConfigApi, skill_config_api_id)
    if existing is not None:
        if existing.skill_config_id != skill_config_id or existing.api_id != api_id:
            raise RuntimeError(
                "SkillConfigApi.build_via_skill_config payload mismatch for existing bridge: "
                + f"skill_config_api_id={skill_config_api_id}"
            )
        return existing

    return SkillConfigApi(
        id=skill_config_api_id,
        skill_config_id=skill_config_id,
        api_id=api_id,
        api=session.imap_get(Api, api_id),
        description=description,
    )
    # --- AWARE: LOGIC END build_via_skill_config
