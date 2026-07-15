from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Skill Ontology
from aware_skill_ontology.skill.skill_run_enums import SkillRunStatus
from aware_skill_ontology.skill.skill_config import SkillConfig
from aware_skill_ontology.skill.skill_config_api import SkillConfigApi
from aware_skill_ontology.skill.skill_config_experience import SkillConfigExperience
from aware_skill_ontology.skill.skill_config_step import SkillConfigStep
from aware_skill_ontology.skill.skill_run import SkillRun

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_skill_ontology.stable_ids import stable_skill_config_id

# --- AWARE: USER_IMPORTS END


async def build(name: str, description: str | None = None) -> SkillConfig:
    """
    Create one canonical reusable Skill definition.

    Contract:
    - `SkillConfig` is the semantic orchestration root.
    - `SkillConfigApi` groups API-scoped endpoint requirements for this Skill.
    - `SkillConfigApiEndpoint` binds to API-owned endpoint invocation truth through the Api projection.
    - Runtime execution/service overlays are later layers, not owned by this config.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("SkillConfig.build requires non-empty name")

    skill_config_id = stable_skill_config_id(name=normalized_name)
    session = current_handler_session()
    existing = session.imap_get(SkillConfig, skill_config_id)
    if existing is not None:
        if (existing.name or "").strip() != normalized_name:
            raise RuntimeError(
                "SkillConfig.build payload mismatch for existing skill_config: " + f"skill_config_id={skill_config_id}"
            )
        return existing

    return SkillConfig(
        id=skill_config_id,
        name=normalized_name,
        description=description,
    )
    # --- AWARE: LOGIC END build


async def add_api(skill_config: SkillConfig, api_id: UUID, description: str | None = None) -> SkillConfigApi:
    """
    Add one API grouping available to this Skill.
    """

    # --- AWARE: LOGIC START add_api
    if skill_config.id is None:
        raise RuntimeError("SkillConfig.add_api requires SkillConfig.id")

    created = await SkillConfigApi.build_via_skill_config(
        skill_config_id=skill_config.id,
        api_id=api_id,
        description=description,
    )
    for existing in skill_config.apis:
        if existing.id == created.id:
            return existing
    skill_config.apis.append(created)
    return created
    # --- AWARE: LOGIC END add_api


async def add_step(
    skill_config: SkillConfig, position: int, skill_config_api_endpoint_id: UUID, instruction: str
) -> SkillConfigStep:
    """
    Add one ordered orchestration step bound to one Skill-owned API endpoint requirement.
    """

    # --- AWARE: LOGIC START add_step
    if skill_config.id is None:
        raise RuntimeError("SkillConfig.add_step requires SkillConfig.id")
    normalized_instruction = (instruction or "").strip()
    if not normalized_instruction:
        raise RuntimeError("SkillConfig.add_step requires non-empty instruction")

    created = await SkillConfigStep.build_via_skill_config(
        skill_config_id=skill_config.id,
        position=position,
        skill_config_api_endpoint_id=skill_config_api_endpoint_id,
        instruction=normalized_instruction,
    )
    for existing in skill_config.steps:
        if existing.id == created.id:
            return existing
    skill_config.steps.append(created)
    return created
    # --- AWARE: LOGIC END add_step


async def add_experience(
    skill_config: SkillConfig, projection_experience_id: UUID, description: str | None = None
) -> SkillConfigExperience:
    """
    Add one Experience graph namespace this SkillConfig may target.

    Contract:
    - Skill targets remain authored Skill-owned truth.
    - Experience owns graph identity/profile resolution.
    """

    # --- AWARE: LOGIC START add_experience
    if skill_config.id is None:
        raise RuntimeError("SkillConfig.add_experience requires SkillConfig.id")

    created = await SkillConfigExperience.build_via_skill_config(
        skill_config_id=skill_config.id,
        projection_experience_id=projection_experience_id,
        description=description,
    )
    for existing in skill_config.experiences:
        if existing.id == created.id:
            return existing
    skill_config.experiences.append(created)
    return created
    # --- AWARE: LOGIC END add_experience


async def create_run(
    skill_config: SkillConfig,
    run_key: str,
    status: SkillRunStatus = SkillRunStatus.queued,
    started_at_utc: datetime | None = None,
    finished_at_utc: datetime | None = None,
    error: str | None = None,
) -> SkillRun:
    """
    Create one canonical execution receipt for this SkillConfig.

    Contract:
    - `SkillRun` is Skill-owned orchestration status truth.
    - Request/response payload truth remains owned by API through `ApiCall`.
    - Run steps are tracked as `SkillRunStep` receipts keyed to authored `SkillConfigStep` truth.
    """

    # --- AWARE: LOGIC START create_run
    if skill_config.id is None:
        raise RuntimeError("SkillConfig.create_run requires SkillConfig.id")
    normalized_run_key = (run_key or "").strip()
    if not normalized_run_key:
        raise RuntimeError("SkillConfig.create_run requires non-empty run_key")

    created = await SkillRun.build_via_skill_config(
        skill_config_id=skill_config.id,
        run_key=normalized_run_key,
        status=status,
        started_at_utc=started_at_utc,
        finished_at_utc=finished_at_utc,
        error=error,
    )
    for existing in skill_config.runs:
        if existing.id == created.id:
            return existing
    skill_config.runs.append(created)
    return created
    # --- AWARE: LOGIC END create_run
