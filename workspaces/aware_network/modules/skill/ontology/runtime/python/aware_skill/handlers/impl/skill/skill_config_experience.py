from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Skill Ontology
from aware_skill_ontology.skill.skill_config_experience import SkillConfigExperience
from aware_skill_ontology.skill.skill_config_target import SkillConfigTarget

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience_ontology.projection.projection_experience import ProjectionExperience
from aware_meta.runtime.handler_context import current_handler_session
from aware_skill_ontology.stable_ids import stable_skill_config_experience_id

# --- AWARE: USER_IMPORTS END


async def add_target(
    skill_config_experience: SkillConfigExperience,
    projection_experience_graph_identity_id: UUID,
    name: str,
    description: str | None = None,
) -> SkillConfigTarget:
    """
    Add one reusable Skill target bound to an Experience graph identity.
    """

    # --- AWARE: LOGIC START add_target
    if skill_config_experience.id is None:
        raise RuntimeError("SkillConfigExperience.add_target requires SkillConfigExperience.id")
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("SkillConfigExperience.add_target requires non-empty name")

    created = await SkillConfigTarget.build_via_skill_config_experience(
        skill_config_experience_id=skill_config_experience.id,
        projection_experience_graph_identity_id=projection_experience_graph_identity_id,
        name=normalized_name,
        description=description,
    )
    for existing in skill_config_experience.targets:
        if existing.id == created.id:
            return existing
    skill_config_experience.targets.append(created)
    return created
    # --- AWARE: LOGIC END add_target


async def build_via_skill_config(
    skill_config_id: UUID, projection_experience_id: UUID, description: str | None = None
) -> SkillConfigExperience:
    """
    Create one Skill-owned bridge to an Experience projection namespace.

    Contract:
    - Skill owns that this SkillConfig may use the Experience namespace.
    - Experience owns graph identity/profile resolution under that namespace.
    """

    # --- AWARE: LOGIC START build_via_skill_config
    skill_config_experience_id = stable_skill_config_experience_id(
        skill_config_id=skill_config_id,
        projection_experience_id=projection_experience_id,
    )
    session = current_handler_session()
    existing = session.imap_get(SkillConfigExperience, skill_config_experience_id)
    if existing is not None:
        if existing.skill_config_id != skill_config_id or existing.projection_experience_id != projection_experience_id:
            raise RuntimeError(
                "SkillConfigExperience.build_via_skill_config payload mismatch for existing bridge: "
                + f"skill_config_experience_id={skill_config_experience_id}"
            )
        return existing

    return SkillConfigExperience(
        id=skill_config_experience_id,
        skill_config_id=skill_config_id,
        projection_experience_id=projection_experience_id,
        projection_experience=session.imap_get(ProjectionExperience, projection_experience_id),
        description=description,
    )
    # --- AWARE: LOGIC END build_via_skill_config
