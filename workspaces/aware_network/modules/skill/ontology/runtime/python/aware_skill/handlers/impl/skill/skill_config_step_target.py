from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Skill Ontology
from aware_skill_ontology.skill.skill_config_step_target import SkillConfigStepTarget

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_skill_ontology.skill.skill_config_experience import SkillConfigExperience
from aware_skill_ontology.skill.skill_config_step import SkillConfigStep
from aware_skill_ontology.skill.skill_config_target import SkillConfigTarget
from aware_skill_ontology.stable_ids import stable_skill_config_step_target_id

# --- AWARE: USER_IMPORTS END


async def build_via_skill_config_step(
    skill_config_step_id: UUID, skill_config_target_id: UUID, description: str | None = None
) -> SkillConfigStepTarget:
    """
    Create one Skill-owned binding between a Skill step and an Experience target.

    Contract:
    - `skill_config_target` is Skill/Experience-owned semantic target selection.
    - The parent `SkillConfigStep` owns API endpoint intent through `SkillConfigApiEndpoint`.
    - API calls remain payload truth; Service remains downstream fulfillment truth.
    """

    # --- AWARE: LOGIC START build_via_skill_config_step
    skill_config_step_target_id = stable_skill_config_step_target_id(
        skill_config_step_id=skill_config_step_id,
        skill_config_target_id=skill_config_target_id,
    )
    session = current_handler_session()
    existing = session.imap_get(SkillConfigStepTarget, skill_config_step_target_id)
    if existing is not None:
        if (
            existing.skill_config_step_id != skill_config_step_id
            or existing.skill_config_target_id != skill_config_target_id
        ):
            raise RuntimeError(
                "SkillConfigStepTarget.build_via_skill_config_step payload mismatch for existing step target: "
                + f"skill_config_step_target_id={skill_config_step_target_id}"
            )
        return existing

    skill_config_step = session.imap_get(SkillConfigStep, skill_config_step_id)
    if skill_config_step is None:
        raise RuntimeError(
            "SkillConfigStepTarget.build_via_skill_config_step requires existing SkillConfigStep: "
            + f"skill_config_step_id={skill_config_step_id}"
        )
    skill_config_target = session.imap_get(SkillConfigTarget, skill_config_target_id)
    if skill_config_target is None:
        raise RuntimeError(
            "SkillConfigStepTarget.build_via_skill_config_step requires existing SkillConfigTarget: "
            + f"skill_config_target_id={skill_config_target_id}"
        )

    skill_config_experience = session.imap_get(
        SkillConfigExperience,
        skill_config_target.skill_config_experience_id,
    )
    if skill_config_experience is None:
        raise RuntimeError(
            "SkillConfigStepTarget.build_via_skill_config_step requires target SkillConfigExperience: "
            + f"skill_config_experience_id={skill_config_target.skill_config_experience_id}"
        )
    if skill_config_experience.skill_config_id != skill_config_step.skill_config_id:
        raise RuntimeError(
            "SkillConfigStepTarget.build_via_skill_config_step requires step and target to belong to "
            + "the same SkillConfig"
        )

    return SkillConfigStepTarget(
        id=skill_config_step_target_id,
        skill_config_step_id=skill_config_step_id,
        skill_config_target_id=skill_config_target_id,
        skill_config_target=skill_config_target,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_skill_config_step
