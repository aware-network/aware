from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Skill Ontology
from aware_skill_ontology.skill.skill_run_enums import SkillRunStatus
from aware_skill_ontology.skill.skill_run import SkillRun
from aware_skill_ontology.skill.skill_run_step import SkillRunStep

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_skill_ontology.skill.skill_config import SkillConfig
from aware_skill_ontology.skill.skill_config_step import SkillConfigStep
from aware_skill_ontology.stable_ids import stable_skill_run_id

# --- AWARE: USER_IMPORTS END


async def create_step(
    skill_run: SkillRun,
    skill_config_step_id: UUID,
    api_call_id: UUID | None = None,
    status: SkillRunStatus = SkillRunStatus.queued,
    started_at_utc: datetime | None = None,
    finished_at_utc: datetime | None = None,
    error: str | None = None,
) -> SkillRunStep:
    """
    Attach one execution receipt for an authored SkillConfigStep.

    Contract:
    - `skill_config_step_id` is the authored step identity and supplies ordering.
    - `api_call_id` is optional while queued/running/skipped, but terminal invoked steps
      must attach API-owned call truth at the service/runtime layer.
    """

    # --- AWARE: LOGIC START create_step
    if skill_run.id is None:
        raise RuntimeError("SkillRun.create_step requires SkillRun.id")
    if status in {SkillRunStatus.succeeded, SkillRunStatus.failed} and api_call_id is None:
        raise RuntimeError("SkillRun.create_step requires api_call_id for terminal invoked step status")

    session = current_handler_session()
    skill_config_step = session.imap_get(SkillConfigStep, skill_config_step_id)
    if skill_config_step is not None and skill_config_step.skill_config_id != skill_run.skill_config_id:
        raise RuntimeError(
            "SkillRun.create_step skill_config_step does not belong to the run parent SkillConfig: "
            + f"skill_run_id={skill_run.id} skill_config_step_id={skill_config_step_id}"
        )

    created = await SkillRunStep.build_via_skill_run(
        skill_run_id=skill_run.id,
        skill_config_step_id=skill_config_step_id,
        api_call_id=api_call_id,
        status=status,
        started_at_utc=started_at_utc,
        finished_at_utc=finished_at_utc,
        error=error,
    )
    for existing in skill_run.steps:
        if existing.id == created.id:
            return existing
    skill_run.steps.append(created)
    return created
    # --- AWARE: LOGIC END create_step


async def build_via_skill_config(
    skill_config_id: UUID,
    run_key: str,
    status: SkillRunStatus = SkillRunStatus.queued,
    started_at_utc: datetime | None = None,
    finished_at_utc: datetime | None = None,
    error: str | None = None,
) -> SkillRun:
    """
    Create one Skill-owned orchestration run receipt.

    Contract:
    - `SkillRun` records boundary status only.
    - Input/output payloads remain API-owned through `SkillRunStep.api_call`.
    - The parent `SkillConfig` is the canonical owner through `SkillConfig.runs`.
    """

    # --- AWARE: LOGIC START build_via_skill_config
    normalized_run_key = (run_key or "").strip()
    if not normalized_run_key:
        raise RuntimeError("SkillRun.build_via_skill_config requires non-empty run_key")

    skill_run_id = stable_skill_run_id(
        skill_config_id=skill_config_id,
        run_key=normalized_run_key,
    )
    session = current_handler_session()
    existing = session.imap_get(SkillRun, skill_run_id)
    if existing is not None:
        if existing.skill_config_id != skill_config_id or (existing.run_key or "").strip() != normalized_run_key:
            raise RuntimeError(
                "SkillRun.build_via_skill_config payload mismatch for existing run: " + f"skill_run_id={skill_run_id}"
            )
        return existing

    _ = session.imap_get(SkillConfig, skill_config_id)
    return SkillRun(
        id=skill_run_id,
        skill_config_id=skill_config_id,
        run_key=normalized_run_key,
        status=status,
        started_at_utc=started_at_utc,
        finished_at_utc=finished_at_utc,
        error=error,
    )
    # --- AWARE: LOGIC END build_via_skill_config
