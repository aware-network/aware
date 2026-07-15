from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Environment Ontology
from aware_environment_ontology.environment.environment import Environment
from aware_environment_ontology.environment.environment_ontology import EnvironmentOntology
from aware_environment_ontology.environment.environment_profile import EnvironmentProfile
from aware_environment_ontology.environment.environment_session import EnvironmentSession

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Storage Ontology
from aware_storage_ontology.blob.storage_blob import StorageBlob

# Environment Ontology
from aware_environment_ontology.stable_ids import (
    stable_environment_config_id,
    stable_environment_id,
)

# --- AWARE: USER_IMPORTS END


async def build(key: str, title: str, description: str | None = None) -> Environment:
    """
    Create a runtime Environment territory.

    Contract:
    - Environment creation does not install an Experience profile.
    - Process, Thread, layout, and branch pointers are explicit follow-up mutations.
    """

    # --- AWARE: LOGIC START build
    return Environment(
        id=stable_environment_id(key=key),
        config_id=stable_environment_config_id(handle=key),
        key=key,
        title=title,
        description=description,
        profiles=[],
        sessions=[],
        ontologies=[],
    )
    # --- AWARE: LOGIC END build


async def apply_profile(
    environment: Environment,
    profile_config_id: UUID,
    title: str | None = None,
    description: str | None = None,
    status: str = "active",
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentProfile:
    """
    Apply one EnvironmentProfileConfig under this Environment.

    Contract:
    - Mutates only Environment-owned applied profile membership.
    - ProcessConfig and ThreadConfig remain under EnvironmentProfileConfig.
    - EnvironmentSessionConfig remains under EnvironmentConfig.
    - Does not install or inspect any Experience.
    """

    # --- AWARE: LOGIC START apply_profile
    if environment.id is None:
        raise RuntimeError("Environment.apply_profile requires Environment.id")

    created = await EnvironmentProfile.build_via_environment(
        environment_id=environment.id,
        profile_config_id=profile_config_id,
        title=title,
        description=description,
        status=status,
        metadata_json=metadata_json,
    )
    for existing in environment.profiles:
        if existing.id == created.id:
            return existing
    environment.profiles.append(created)
    return created
    # --- AWARE: LOGIC END apply_profile


async def start_session(
    environment: Environment,
    identity_session_id: UUID,
    session_config_id: UUID | None = None,
    key: str | None = None,
    title: str | None = None,
    description: str | None = None,
    purpose: str | None = None,
    status: str = "active",
    source_kind: str | None = None,
    source_ref: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentSession:
    """
    Start or attach one runtime EnvironmentSession under this Environment.

    Contract:
    - Stable identity is Environment path + Identity Session.
    - `session_config_id` is optional non-key provenance/defaults.
    - Actor membership, ActorRole evidence, and provider sessions live on
      the linked Identity Session.
    - Process/Thread/Layout selection is EnvironmentSession-owned through
      navigation contexts and session-thread pins.
    """

    # --- AWARE: LOGIC START start_session
    if environment.id is None:
        raise RuntimeError("Environment.start_session requires Environment.id")

    created = await EnvironmentSession.build_via_environment(
        environment_id=environment.id,
        identity_session_id=identity_session_id,
        session_config_id=session_config_id,
        key=key,
        title=title,
        description=description,
        purpose=purpose,
        status=status,
        source_kind=source_kind,
        source_ref=source_ref,
        metadata_json=metadata_json,
    )
    for existing in environment.sessions:
        if existing.id == created.id:
            return existing
    environment.sessions.append(created)
    return created
    # --- AWARE: LOGIC END start_session


async def attach_ontology(
    environment: Environment,
    ontology_id: UUID,
    role: str = "runtime",
    status: str = "active",
    title: str | None = None,
    description: str | None = None,
) -> EnvironmentOntology:
    """
    Attach one Ontology authority to this runtime Environment.

    Contract:
    - Mutates only Environment-owned ontology membership.
    - The target Ontology owns OIGI inventory discovery.
    - Environment does not duplicate ObjectInstanceGraph membership or
      commit pins.
    """

    # --- AWARE: LOGIC START attach_ontology
    if environment.id is None:
        raise RuntimeError("Environment.attach_ontology requires Environment.id")

    created = await EnvironmentOntology.build_via_environment(
        environment_id=environment.id,
        ontology_id=ontology_id,
        role=role,
        status=status,
        title=title,
        description=description,
    )
    for existing in environment.ontologies:
        if existing.id == created.id:
            return existing
    environment.ontologies.append(created)
    return created
    # --- AWARE: LOGIC END attach_ontology


async def update_picture(
    environment: Environment,
    image_id: UUID | None = None,
    image_sha: str | None = None,
    image_mime_type: str | None = None,
    image_size_bytes: int | None = None,
) -> None:
    """
    Updates (or clears) the environment territory image override.

    Contract:
    - Raw bytes are uploaded out-of-band via HTTP file operations.
    - Commits must reference commit-backed StorageBlob metadata only.
    - When setting a picture, image_sha/image_mime_type/image_size_bytes must be provided together.

    Parameters:
        image_id: Optional uploaded blob id to assert against image_sha-derived stable id.
        image_sha: SHA-256 hex digest of uploaded bytes.
        image_mime_type: MIME type of uploaded bytes.
        image_size_bytes: Size of uploaded bytes.
    Returns: None.
    """

    # --- AWARE: LOGIC START update_picture
    has_any_meta = any(
        (
            image_sha is not None,
            image_mime_type is not None,
            image_size_bytes is not None,
        )
    )

    # Clear picture.
    if image_id is None and not has_any_meta:
        environment.image_id = None
        environment.image = None
        return

    if not has_any_meta:
        raise ValueError("image_sha, image_mime_type, and image_size_bytes are required when setting a picture")
    if image_sha is None or image_mime_type is None or image_size_bytes is None:
        raise ValueError("image_sha, image_mime_type, and image_size_bytes must be set together")

    blob = await StorageBlob.create(
        sha=image_sha,
        mime_type=image_mime_type,
        size_bytes=image_size_bytes,
    )
    if image_id is not None and image_id != blob.id:
        raise ValueError(
            "image_id does not match StorageBlob.id derived from image_sha " f"(image_id={image_id} blob_id={blob.id})"
        )

    environment.image = blob
    environment.image_id = blob.id
    # --- AWARE: LOGIC END update_picture
