from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Environment Ontology
from aware_environment_ontology.environment.environment_config import EnvironmentConfig
from aware_environment_ontology.environment.environment_config_ontology_config import EnvironmentConfigOntologyConfig
from aware_environment_ontology.environment.environment_profile_config import EnvironmentProfileConfig
from aware_environment_ontology.environment.environment_session_config import EnvironmentSessionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_environment_ontology.stable_ids import (
    stable_environment_config_id,
)

# --- AWARE: USER_IMPORTS END


async def build(
    handle: str,
    title: str,
    canonical_language: CodeLanguage,
    languages: list[CodeLanguage],
    description: str | None = None,
    is_kernel: bool = False,
) -> EnvironmentConfig:
    """
    Build one EnvironmentConfig for a deterministic module/environment handle.

    Contract:
    - `handle` is the identity key used by compiler-owned stable IDs.
    - EnvironmentConfig does not own repository, ownership, or raw Meta OCG
      composition truth.
    - OCG resolution is reachable only through attached OntologyConfig roots.
    """

    # --- AWARE: LOGIC START build
    return EnvironmentConfig(
        id=stable_environment_config_id(handle=handle),
        handle=handle,
        title=title,
        canonical_language=canonical_language,
        languages=list(languages),
        description=description,
        is_kernel=is_kernel,
        ontology_configs=[],
        profile_configs=[],
        session_configs=[],
    )
    # --- AWARE: LOGIC END build


async def attach_ontology_config(
    environment_config: EnvironmentConfig,
    name: str,
    fqn_prefix: str,
    ontology_config_object_instance_graph_commit_id: UUID | None = None,
) -> EnvironmentConfigOntologyConfig:
    """
    Attach one ontology config requirement to this environment config.

    Contract:
    - Parent `EnvironmentConfig` scope is injected by propagation.
    - Target OntologyConfig identity is resolved from `(name, fqn_prefix)`.
    - The optional OIG commit pin is exact OntologyConfig replay truth.
    - EnvironmentConfig never resolves ObjectConfigGraph directly; it goes
      through `OntologyConfig.object_config_graph`.
    """

    # --- AWARE: LOGIC START attach_ontology_config
    created = await EnvironmentConfigOntologyConfig.build_via_environment_config(
        environment_config_id=environment_config.id,
        name=name,
        fqn_prefix=fqn_prefix,
        ontology_config_object_instance_graph_commit_id=(ontology_config_object_instance_graph_commit_id),
    )
    for existing in environment_config.ontology_configs:
        if existing.id == created.id:
            return existing
    environment_config.ontology_configs.append(created)
    return created
    # --- AWARE: LOGIC END attach_ontology_config


async def add_profile_config(
    environment_config: EnvironmentConfig,
    key: str,
    title: str | None = None,
    description: str | None = None,
    narrative: str | None = None,
) -> EnvironmentProfileConfig:
    """
    Declare one Environment-level profile config.

    Contract:
    - EnvironmentConfig owns reusable profile topology for this
      Environment composition.
    - Stable identity is EnvironmentConfig path + `key`.
    - EnvironmentProfileConfig remains topology/config truth only; runtime
      EnvironmentProfile instances are Environment-owned.
    """

    # --- AWARE: LOGIC START add_profile_config
    if environment_config.id is None:
        raise RuntimeError("EnvironmentConfig.add_profile_config requires EnvironmentConfig.id")

    created = await EnvironmentProfileConfig.build_via_environment_config(
        environment_config_id=environment_config.id,
        key=key,
        title=title,
        description=description,
        narrative=narrative,
    )
    for existing in environment_config.profile_configs:
        if existing.id == created.id:
            return existing
    environment_config.profile_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_profile_config


async def add_session_config(
    environment_config: EnvironmentConfig,
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
    Declare one Environment-level session config.

    Contract:
    - EnvironmentConfig owns reusable session defaults for this Environment
      composition.
    - Identity owns reusable SessionConfig policy and concrete membership.
    - Optional default profile/process/thread config portals are bootstrap
      defaults only; runtime session/thread resolution remains
      EnvironmentSession-owned.
    """

    # --- AWARE: LOGIC START add_session_config
    if environment_config.id is None:
        raise RuntimeError("EnvironmentConfig.add_session_config requires EnvironmentConfig.id")

    created = await EnvironmentSessionConfig.build_via_environment_config(
        environment_config_id=environment_config.id,
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
    for existing in environment_config.session_configs:
        if existing.id == created.id:
            return existing
    environment_config.session_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_session_config
