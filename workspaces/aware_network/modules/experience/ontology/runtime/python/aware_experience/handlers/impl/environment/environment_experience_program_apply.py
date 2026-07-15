from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.environment.environment_experience_program_apply import EnvironmentExperienceProgramApply

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import (
    stable_environment_experience_program_apply_id,
)

from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_environment_experience_thread_config(
    environment_experience_thread_config_id: UUID,
    program_config_id: UUID,
    key: str,
    phase: str = "bootstrap",
    position: int | None = None,
    message: str | None = None,
    symbols: JsonObject = JsonObject(),
) -> EnvironmentExperienceProgramApply:
    """
    Construct the canonical EnvironmentExperienceProgramApply declaration.

    Contract:
    - Identity is derived from `(environment_experience_thread_config_id, key)`.
    - `program_config_id` should reference one installed thread config program.
    - This class is configuration-only; actual execution happens later via
      Experience-owned `run_program`.
    """

    # --- AWARE: LOGIC START build_via_environment_experience_thread_config
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("EnvironmentExperienceProgramApply.build requires non-empty key")
    normalized_phase = (phase or "").strip() or "bootstrap"
    normalized_message = (message or "").strip() or None
    if position is not None and position < 0:
        raise RuntimeError("EnvironmentExperienceProgramApply.build requires position >= 0")

    apply_id = stable_environment_experience_program_apply_id(
        environment_experience_thread_config_id=environment_experience_thread_config_id,
        key=normalized_key,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentExperienceProgramApply, apply_id)
    if existing is not None:
        if (
            existing.environment_experience_thread_config_id != environment_experience_thread_config_id
            or existing.program_config_id != program_config_id
            or (existing.key or "").strip() != normalized_key
            or (existing.phase or "").strip() != normalized_phase
            or existing.position != position
            or existing.message != normalized_message
            or dict(existing.symbols or {}) != dict(symbols or {})
        ):
            raise RuntimeError(
                "EnvironmentExperienceProgramApply.build payload mismatch for existing apply declaration: "
                f"environment_experience_program_apply_id={apply_id}"
            )
        return existing

    return EnvironmentExperienceProgramApply(
        id=apply_id,
        environment_experience_thread_config_id=environment_experience_thread_config_id,
        program_config_id=program_config_id,
        key=normalized_key,
        phase=normalized_phase,
        position=position,
        message=normalized_message,
        symbols=JsonObject(symbols or {}),
    )
    # --- AWARE: LOGIC END build_via_environment_experience_thread_config
