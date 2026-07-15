from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.environment.environment_experience_program import EnvironmentExperienceProgram
from aware_experience_ontology.environment.environment_experience_program_apply import EnvironmentExperienceProgramApply
from aware_experience_ontology.environment.environment_experience_thread_config import EnvironmentExperienceThreadConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_environment_experience_thread_config_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def add_program(
    environment_experience_thread_config: EnvironmentExperienceThreadConfig, program_config_id: UUID
) -> EnvironmentExperienceProgram:
    """
    Attach one ProgramConfig association edge under this thread config bridge.
    """

    # --- AWARE: LOGIC START add_program
    thread_bridge_id = environment_experience_thread_config.id
    if thread_bridge_id is None:
        raise RuntimeError(
            "EnvironmentExperienceThreadConfig.add_program requires EnvironmentExperienceThreadConfig.id"
        )

    created = await EnvironmentExperienceProgram.build_via_environment_experience_thread_config(
        environment_experience_thread_config_id=thread_bridge_id,
        program_config_id=program_config_id,
    )
    for existing in environment_experience_thread_config.programs:
        if existing.id == created.id:
            if existing.program_config_id != program_config_id:
                raise RuntimeError(
                    "EnvironmentExperienceThreadConfig.add_program payload mismatch "
                    f"for existing program: environment_experience_program_id={existing.id}"
                )
            return existing
    environment_experience_thread_config.programs.append(created)
    return created
    # --- AWARE: LOGIC END add_program


async def add_program_apply(
    environment_experience_thread_config: EnvironmentExperienceThreadConfig,
    program_config_id: UUID,
    key: str,
    phase: str = "bootstrap",
    position: int | None = None,
    message: str | None = None,
    symbols: JsonObject = JsonObject(),
) -> EnvironmentExperienceProgramApply:
    """
    Attach one thread-scoped seed/apply declaration.

    Contract:
    - `program_config_id` should already be installed in `programs`.
    - Represents config-only apply intent; it does not execute the program.
    - Experience runtime later maps this declaration to `run_program`.
    """

    # --- AWARE: LOGIC START add_program_apply
    thread_bridge_id = environment_experience_thread_config.id
    if thread_bridge_id is None:
        raise RuntimeError(
            "EnvironmentExperienceThreadConfig.add_program_apply requires EnvironmentExperienceThreadConfig.id"
        )
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("EnvironmentExperienceThreadConfig.add_program_apply requires non-empty key")

    created = await EnvironmentExperienceProgramApply.build_via_environment_experience_thread_config(
        environment_experience_thread_config_id=thread_bridge_id,
        program_config_id=program_config_id,
        key=normalized_key,
        phase=phase,
        position=position,
        message=message,
        symbols=symbols,
    )
    for existing in environment_experience_thread_config.program_applies:
        if existing.id == created.id:
            if existing.program_config_id != program_config_id or existing.key != normalized_key:
                raise RuntimeError(
                    "EnvironmentExperienceThreadConfig.add_program_apply payload mismatch "
                    f"for existing apply: environment_experience_program_apply_id={existing.id}"
                )
            return existing
    environment_experience_thread_config.program_applies.append(created)
    return created
    # --- AWARE: LOGIC END add_program_apply


async def build_via_environment_experience_process_config(
    environment_experience_process_config_id: UUID,
    thread_config_id: UUID,
    key: str,
    title: str | None = None,
    description: str | None = None,
    position: int | None = None,
    narrative: str | None = None,
    intent: str | None = None,
) -> EnvironmentExperienceThreadConfig:
    """
    Construct one Experience thread config bridge.

    Contract:
    - Identity is derived from parent process bridge plus `(thread_config_id, key)`.
    - `thread_config_id` references Environment ThreadConfig topology truth.
    """

    # --- AWARE: LOGIC START build_via_environment_experience_process_config
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("EnvironmentExperienceThreadConfig.build requires non-empty key")
    if position is not None and position < 0:
        raise RuntimeError("EnvironmentExperienceThreadConfig.build requires position >= 0")

    thread_bridge_id = stable_environment_experience_thread_config_id(
        environment_experience_process_config_id=environment_experience_process_config_id,
        thread_config_id=thread_config_id,
        key=normalized_key,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentExperienceThreadConfig, thread_bridge_id)
    if existing is not None:
        if (
            existing.environment_experience_process_config_id != environment_experience_process_config_id
            or existing.thread_config_id != thread_config_id
            or existing.key != normalized_key
            or existing.title != title
            or existing.description != description
            or existing.position != position
            or existing.narrative != narrative
            or existing.intent != intent
        ):
            raise RuntimeError(
                "EnvironmentExperienceThreadConfig.build payload mismatch "
                f"for existing bridge: environment_experience_thread_config_id={thread_bridge_id}"
            )
        return existing

    return EnvironmentExperienceThreadConfig(
        id=thread_bridge_id,
        environment_experience_process_config_id=environment_experience_process_config_id,
        thread_config_id=thread_config_id,
        key=normalized_key,
        title=title,
        description=description,
        position=position,
        narrative=narrative,
        intent=intent,
    )
    # --- AWARE: LOGIC END build_via_environment_experience_process_config
