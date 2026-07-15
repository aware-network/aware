from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Skill Ontology
from aware_skill_ontology.skill.skill_config_target import SkillConfigTarget

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience_ontology.projection.projection_experience_graph import ProjectionExperienceGraph
from aware_experience_ontology.projection.projection_experience_graph_identity import (
    ProjectionExperienceGraphIdentity,
)
from aware_meta.runtime.handler_context import current_handler_session
from aware_skill_ontology.skill.skill_config_experience import SkillConfigExperience
from aware_skill_ontology.stable_ids import stable_skill_config_target_id

# --- AWARE: USER_IMPORTS END


async def build_via_skill_config_experience(
    skill_config_experience_id: UUID,
    projection_experience_graph_identity_id: UUID,
    name: str,
    description: str | None = None,
) -> SkillConfigTarget:
    """
    Create one Skill-owned target alias over an Experience graph identity.

    Contract:
    - `name` is the Skill-local alias used by authored steps.
    - `projection_experience_graph_identity` is Experience-owned semantic target truth.
    """

    # --- AWARE: LOGIC START build_via_skill_config_experience
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("SkillConfigTarget.build_via_skill_config_experience requires non-empty name")

    skill_config_target_id = stable_skill_config_target_id(
        skill_config_experience_id=skill_config_experience_id,
        projection_experience_graph_identity_id=projection_experience_graph_identity_id,
        name=normalized_name,
    )
    session = current_handler_session()
    existing = session.imap_get(SkillConfigTarget, skill_config_target_id)
    if existing is not None:
        if (
            existing.skill_config_experience_id != skill_config_experience_id
            or existing.projection_experience_graph_identity_id != projection_experience_graph_identity_id
            or (existing.name or "").strip() != normalized_name
        ):
            raise RuntimeError(
                "SkillConfigTarget.build_via_skill_config_experience payload mismatch for existing target: "
                + f"skill_config_target_id={skill_config_target_id}"
            )
        return existing

    skill_config_experience = session.imap_get(SkillConfigExperience, skill_config_experience_id)
    if skill_config_experience is None:
        raise RuntimeError(
            "SkillConfigTarget.build_via_skill_config_experience requires existing SkillConfigExperience: "
            + f"skill_config_experience_id={skill_config_experience_id}"
        )

    graph_identity = session.imap_get(ProjectionExperienceGraphIdentity, projection_experience_graph_identity_id)
    if graph_identity is not None:
        graph = session.imap_get(ProjectionExperienceGraph, graph_identity.projection_experience_graph_id)
        if graph is not None and graph.projection_experience_id != skill_config_experience.projection_experience_id:
            raise RuntimeError(
                "SkillConfigTarget.build_via_skill_config_experience graph identity belongs to a different "
                + "ProjectionExperience: "
                + f"skill_config_experience_id={skill_config_experience_id} "
                + f"projection_experience_graph_identity_id={projection_experience_graph_identity_id}"
            )

    return SkillConfigTarget(
        id=skill_config_target_id,
        skill_config_experience_id=skill_config_experience_id,
        projection_experience_graph_identity_id=projection_experience_graph_identity_id,
        projection_experience_graph_identity=graph_identity,
        name=normalized_name,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_skill_config_experience
