from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Environment Ontology
from aware_environment_ontology.environment.environment_session_config import EnvironmentSessionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_environment_session_config_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_environment_config(
    environment_config_id: UUID,
    key: str,
    identity_session_config_id: UUID,
    default_profile_config_id: UUID | None = None,
    default_process_config_id: UUID | None = None,
    default_thread_config_id: UUID | None = None,
    title: str | None = None,
    description: str | None = None,
    purpose: str | None = None,
    status: str = "active",
    source_kind: str | None = None,
    source_ref: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentSessionConfig:
    """
    Construct one EnvironmentSessionConfig under an EnvironmentConfig.

    Contract:
    - Stable identity is EnvironmentConfig path + `key`.
    - `identity_session_config_id` resolves the Identity SessionConfig
      portal. It is required and must not be inferred from keys.
    - Optional default profile/process/thread refs are bootstrap defaults
      and must not define runtime session containment.
    - This object never owns actor membership.
    """

    # --- AWARE: LOGIC START build_via_environment_config
    environment_session_config_id = stable_environment_session_config_id(
        environment_config_id=environment_config_id,
        key=key,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(
        EnvironmentSessionConfig,
        environment_session_config_id,
    )
    if existing is not None:
        if existing.environment_config_id != environment_config_id or existing.key != key:
            raise RuntimeError(
                "EnvironmentSessionConfig.build_via_environment_config mismatch "
                f"for existing environment_session_config_id={environment_session_config_id}"
            )
        return existing

    return EnvironmentSessionConfig(
        id=environment_session_config_id,
        environment_config_id=environment_config_id,
        key=key,
        identity_session_config_id=identity_session_config_id,
        default_profile_config_id=default_profile_config_id,
        default_process_config_id=default_process_config_id,
        default_thread_config_id=default_thread_config_id,
        title=title,
        description=description,
        purpose=purpose,
        status=status,
        source_kind=source_kind,
        source_ref=source_ref,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END build_via_environment_config
