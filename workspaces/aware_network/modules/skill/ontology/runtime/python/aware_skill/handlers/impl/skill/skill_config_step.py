from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Skill Ontology
from aware_skill_ontology.skill.skill_config_step import SkillConfigStep
from aware_skill_ontology.skill.skill_config_step_target import SkillConfigStepTarget

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_skill_ontology.skill.skill_config_api_endpoint import SkillConfigApiEndpoint
from aware_skill_ontology.skill.skill_config_target import SkillConfigTarget
from aware_skill_ontology.stable_ids import stable_skill_config_step_id

# --- AWARE: USER_IMPORTS END


async def add_target(
    skill_config_step: SkillConfigStep, skill_config_target_id: UUID, description: str | None = None
) -> SkillConfigStepTarget:
    """
    Bind one Experience-owned authored Skill target to this step.

    Contract:
    - A step may bind zero, one, or many SkillConfigTarget rows.
    - Each target resolves through Experience-owned graph identity truth.
    - The step API endpoint requirement remains on `SkillConfigApiEndpoint`.
    """

    # --- AWARE: LOGIC START add_target
    skill_config_target_id = (
        skill_config_target_id if isinstance(skill_config_target_id, UUID) else UUID(str(skill_config_target_id))
    )
    if skill_config_step.id is None:
        raise RuntimeError("SkillConfigStep.add_target requires SkillConfigStep.id")

    session = current_handler_session()
    if session.imap_get(SkillConfigTarget, skill_config_target_id) is None:
        raise RuntimeError(
            "SkillConfigStep.add_target requires existing SkillConfigTarget: "
            + f"skill_config_target_id={skill_config_target_id}"
        )

    created = await SkillConfigStepTarget.build_via_skill_config_step(
        skill_config_step_id=skill_config_step.id,
        skill_config_target_id=skill_config_target_id,
        description=description,
    )
    for existing in skill_config_step.targets:
        if existing.id == created.id:
            return existing
    skill_config_step.targets.append(created)
    return created
    # --- AWARE: LOGIC END add_target


async def build_via_skill_config(
    skill_config_id: UUID, position: int, skill_config_api_endpoint_id: UUID, instruction: str
) -> SkillConfigStep:
    """
    Create one ordered step in a Skill orchestration plan.

    Contract:
    - A step binds to Skill-owned `SkillConfigApiEndpoint` requirement truth.
    - API-owned endpoint invocation details remain downstream runtime/service concerns.
    """

    # --- AWARE: LOGIC START build_via_skill_config
    skill_config_id = skill_config_id if isinstance(skill_config_id, UUID) else UUID(str(skill_config_id))
    skill_config_api_endpoint_id = (
        skill_config_api_endpoint_id
        if isinstance(skill_config_api_endpoint_id, UUID)
        else UUID(str(skill_config_api_endpoint_id))
    )
    normalized_instruction = (instruction or "").strip()
    if not normalized_instruction:
        raise RuntimeError("SkillConfigStep.build_via_skill_config requires non-empty instruction")

    skill_config_step_id = stable_skill_config_step_id(
        skill_config_id=skill_config_id,
        position=position,
    )
    session = current_handler_session()
    existing = session.imap_get(SkillConfigStep, skill_config_step_id)
    if existing is not None:
        if (
            existing.skill_config_id != skill_config_id
            or existing.position != position
            or existing.skill_config_api_endpoint_id != skill_config_api_endpoint_id
        ):
            raise RuntimeError(
                "SkillConfigStep.build_via_skill_config payload mismatch for existing step: "
                + f"skill_config_step_id={skill_config_step_id}"
            )
        return existing

    skill_config_api_endpoint = session.imap_get(
        SkillConfigApiEndpoint,
        skill_config_api_endpoint_id,
    )
    if skill_config_api_endpoint is None:
        raise RuntimeError(
            "SkillConfigStep.build_via_skill_config requires existing SkillConfigApiEndpoint: "
            + f"skill_config_api_endpoint_id={skill_config_api_endpoint_id}"
        )

    return SkillConfigStep(
        id=skill_config_step_id,
        skill_config_id=skill_config_id,
        skill_config_api_endpoint=skill_config_api_endpoint,
        skill_config_api_endpoint_id=skill_config_api_endpoint_id,
        position=position,
        instruction=normalized_instruction,
    )
    # --- AWARE: LOGIC END build_via_skill_config
