from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Skill Ontology
from aware_skill_ontology.skill.skill_run_enums import SkillRunStatus
from aware_skill_ontology.skill.skill_run_step import SkillRunStep

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_api_ontology.api.api_call import ApiCall
from aware_meta.runtime.handler_context import current_handler_session
from aware_skill_ontology.skill.skill_config_api_endpoint import SkillConfigApiEndpoint
from aware_skill_ontology.skill.skill_config_step import SkillConfigStep
from aware_skill_ontology.skill.skill_run import SkillRun
from aware_skill_ontology.stable_ids import stable_skill_run_step_id

# --- AWARE: USER_IMPORTS END


async def build_via_skill_run(
    skill_run_id: UUID,
    skill_config_step_id: UUID,
    api_call_id: UUID | None = None,
    status: SkillRunStatus = SkillRunStatus.queued,
    started_at_utc: datetime | None = None,
    finished_at_utc: datetime | None = None,
    error: str | None = None,
) -> SkillRunStep:
    """
    Create one Skill-owned step execution receipt.

    Contract:
    - This object reports Skill orchestration state only.
    - The referenced `SkillConfigStep` owns authored instruction and ordering.
    - The referenced `ApiCall`, when present, owns request and response payload truth.
    """

    # --- AWARE: LOGIC START build_via_skill_run
    if status in {SkillRunStatus.succeeded, SkillRunStatus.failed} and api_call_id is None:
        raise RuntimeError("SkillRunStep.build_via_skill_run requires api_call_id for terminal invoked step status")

    skill_run_step_id = stable_skill_run_step_id(
        skill_run_id=skill_run_id,
        skill_config_step_id=skill_config_step_id,
    )
    session = current_handler_session()
    existing = session.imap_get(SkillRunStep, skill_run_step_id)
    if existing is not None:
        if (
            existing.skill_run_id != skill_run_id
            or existing.skill_config_step_id != skill_config_step_id
            or existing.api_call_id != api_call_id
        ):
            raise RuntimeError(
                "SkillRunStep.build_via_skill_run payload mismatch for existing step: "
                + f"skill_run_step_id={skill_run_step_id}"
            )
        return existing

    skill_run = session.imap_get(SkillRun, skill_run_id)
    skill_config_step = session.imap_get(SkillConfigStep, skill_config_step_id)
    if (
        skill_run is not None
        and skill_config_step is not None
        and skill_config_step.skill_config_id != skill_run.skill_config_id
    ):
        raise RuntimeError(
            "SkillRunStep.build_via_skill_run skill_config_step does not belong to the run parent SkillConfig: "
            + f"skill_run_id={skill_run_id} skill_config_step_id={skill_config_step_id}"
        )

    api_call = session.imap_get(ApiCall, api_call_id) if api_call_id is not None else None
    if api_call is not None and skill_config_step is not None:
        endpoint_requirement = (
            session.imap_get(
                SkillConfigApiEndpoint,
                skill_config_step.skill_config_api_endpoint_id,
            )
            if skill_config_step.skill_config_api_endpoint_id is not None
            else None
        )
        if (
            endpoint_requirement is not None
            and api_call.api_capability_endpoint_id != endpoint_requirement.api_endpoint_id
        ):
            raise RuntimeError(
                "SkillRunStep.build_via_skill_run api_call endpoint does not match SkillConfigStep endpoint: "
                + f"api_call_id={api_call_id} skill_config_step_id={skill_config_step_id}"
            )

    return SkillRunStep(
        id=skill_run_step_id,
        skill_run_id=skill_run_id,
        skill_config_step=skill_config_step,
        skill_config_step_id=skill_config_step_id,
        api_call=api_call,
        api_call_id=api_call_id,
        status=status,
        started_at_utc=started_at_utc,
        finished_at_utc=finished_at_utc,
        error=error,
    )
    # --- AWARE: LOGIC END build_via_skill_run
