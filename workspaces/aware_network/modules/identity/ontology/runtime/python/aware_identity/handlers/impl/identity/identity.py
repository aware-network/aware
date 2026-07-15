from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.credential.credential_profile_enums import (
    CredentialKind,
    CredentialProfileStatus,
    CredentialTargetKind,
)
from aware_identity_ontology.identity.identity_enums import IdentityType
from aware_identity_ontology.identity.identity_pattern_enums import IdentityPatternType
from aware_identity_ontology.actor.actor import Actor
from aware_identity_ontology.credential.credential_profile import CredentialProfile
from aware_identity_ontology.identity.create_profile_request import CreateProfileRequest
from aware_identity_ontology.identity.identity import Identity
from aware_identity_ontology.identity.identity_profile import IdentityProfile

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Identity Runtime
from aware_identity.auth.public_key.generator import canonicalize_ed25519_public_key
from aware_identity.context import current_actor_id
from aware_identity.helpers import (
    DEFAULT_ACTOR_KEY,
    normalize_actor_key,
    stable_actor_id_for_identity_key,
)
from aware_identity_ontology.stable_ids import (
    stable_actor_id,
    stable_credential_profile_id,
    stable_identity_id,
    stable_organization_id,
)

# Identity Ontology
from aware_identity_ontology.actor.actor_enums import ActorType
from aware_identity_ontology.human.human import Human

# Storage Ontology
from aware_storage_ontology.blob.storage_blob import StorageBlob


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


# --- AWARE: USER_IMPORTS END


async def signup(public_key: str, type: IdentityType = IdentityType.human) -> Identity:
    """
    Canonical identity signup (v0).

    This is the first end-to-end identity mutation:
    `.aware` → runtime handler → OIG delta → OIG commit → UI materialization.

    Notes:
    - Signup is a state mutation and must always be commit-backed (no transport-only identity creation).
    - The public key is the canonical identity anchor (human + AI).
    """

    # --- AWARE: LOGIC START signup
    if type not in (
        IdentityType.human,
        IdentityType.agent,
        IdentityType.organization,
        IdentityType.system,
    ):
        raise ValueError(
            "v1 identity.signup currently supports only type in " "{'human', 'agent', 'organization', 'system'}"
        )

    canonical_key, _key_bytes = canonicalize_ed25519_public_key(public_key)
    identity_id = stable_identity_id(public_key=canonical_key, type=type.value)

    expected_actor_id = stable_actor_id(identity_id=identity_id)
    actual_actor_id = current_actor_id()
    if actual_actor_id != expected_actor_id:
        raise ValueError(
            "forbidden: actor_id does not match public key (anti-claim): "
            f"actor_id={actual_actor_id} expected={expected_actor_id}"
        )

    identity = Identity(id=identity_id, public_key=canonical_key, type=type)
    if type == IdentityType.human:
        actor = await Actor.create_actor(type=ActorType.human, identity_id=identity.id)
        human = await Human.create_human(actor_id=actor.id)
        identity.human_id = human.id
        identity.human = human
    elif type == IdentityType.agent:
        # NOTE: Agent inversion is handled by AgentProcessThread.create_thread
        await Actor.create_actor(type=ActorType.agent_process_thread, identity_id=identity.id)
    elif type == IdentityType.organization:
        actor = await Actor.create_actor(type=ActorType.organization, identity_id=identity.id)
        # Identity→Organization is a portal edge. Do not construct Organization
        # objects in the identity lane; create them in the `organization` projection.
        identity.organization_id = stable_organization_id(actor_id=actor.id)
    elif type == IdentityType.system:
        await Actor.create_actor(type=ActorType.system, identity_id=identity.id)
    return identity
    # --- AWARE: LOGIC END signup


async def signup_via_profile(
    public_key: str, create_profile_request: CreateProfileRequest, type: IdentityType = IdentityType.human
) -> Identity:
    """
    Creates identity and profile in a single commit (canonical onboarding).

    Contract:
    - public_key is device-generated; runtime canonicalizes and derives stable ids.
    - idempotent by public key (stable Identity.id).
    - profile handle is unique (stable IdentityProfile.id).
    """

    # --- AWARE: LOGIC START signup_via_profile

    requested_identity_type = type if isinstance(type, IdentityType) else IdentityType(_enum_value(type))
    if requested_identity_type != create_profile_request.identity_type:
        raise ValueError(
            "identity.signup_via_profile type must match create_profile_request.identity_type: "
            f"type={requested_identity_type.value} "
            f"create_profile_request.identity_type={create_profile_request.identity_type.value}"
        )

    if requested_identity_type not in (
        IdentityType.human,
        IdentityType.agent,
        IdentityType.organization,
    ):
        raise ValueError(
            "v1 identity.signup_via_profile currently supports only type in {'human', 'agent', 'organization'}"
        )

    canonical_key, _key_bytes = canonicalize_ed25519_public_key(public_key)
    identity_id = stable_identity_id(
        public_key=canonical_key,
        type=requested_identity_type.value,
    )

    expected_actor_id = stable_actor_id(identity_id=identity_id)
    actual_actor_id = current_actor_id()
    if actual_actor_id != expected_actor_id:
        raise ValueError(
            "forbidden: actor_id does not match public key (anti-claim): "
            f"actor_id={actual_actor_id} expected={expected_actor_id}"
        )

    identity = await Identity.signup(public_key=canonical_key, type=requested_identity_type)

    resolved_image_id = create_profile_request.image_id
    has_any_image_meta = any(
        (
            create_profile_request.image_sha is not None,
            create_profile_request.image_mime_type is not None,
            create_profile_request.image_size_bytes is not None,
        )
    )
    if has_any_image_meta:
        if (
            create_profile_request.image_sha is None
            or create_profile_request.image_mime_type is None
            or create_profile_request.image_size_bytes is None
        ):
            raise ValueError("image_sha, image_mime_type, and image_size_bytes must be set together when provided")

        blob = await StorageBlob.create(
            sha=create_profile_request.image_sha,
            mime_type=create_profile_request.image_mime_type,
            size_bytes=create_profile_request.image_size_bytes,
        )
        if create_profile_request.image_id is not None and create_profile_request.image_id != blob.id:
            raise ValueError(
                "image_id does not match commit-backed StorageBlob.id derived from image_sha "
                f"(image_id={create_profile_request.image_id} blob_id={blob.id})"
            )
        resolved_image_id = blob.id

    await identity.create_profile(
        public_handle=create_profile_request.public_handle,
        display_name=create_profile_request.display_name,
        full_name=create_profile_request.full_name,
        country_code=create_profile_request.country_code,
        language_code=create_profile_request.language_code,
        bio=create_profile_request.bio,
        image_id=resolved_image_id,
    )
    return identity
    # --- AWARE: LOGIC END signup_via_profile


async def create_profile(
    identity: Identity,
    public_handle: str,
    display_name: str,
    full_name: str,
    country_code: str,
    language_code: str,
    bio: str | None = None,
    image_id: UUID | None = None,
) -> IdentityProfile:
    """
    Creates and links a profile to this Identity (v0).

    Runtime invariants:
    - Mutate-self-only: this handler may only mutate the Identity instance.
    - Profile creation must occur via the IdentityProfile constructor handler (propagation).
    """

    # --- AWARE: LOGIC START create_profile
    if identity.identity_profile_id is not None:
        raise ValueError(
            f"Identity already has a profile: identity_id={identity.id} profile_id={identity.identity_profile_id}"
        )

    profile = await IdentityProfile.create(
        public_handle=public_handle,
        display_name=display_name,
        full_name=full_name,
        country_code=country_code,
        language_code=language_code,
        bio=bio,
        image_id=image_id,
    )
    identity.identity_profile = profile
    identity.identity_profile_id = profile.id
    return profile
    # --- AWARE: LOGIC END create_profile


async def ensure_actor(identity: Identity, key: str = "default") -> Actor:
    """
    Ensure an Actor instance exists for this Identity.

    Contract:
    - `IdentityType.agent` may own multiple keyed actors (deterministic by key).
    - `IdentityType.human`/`organization`/`system` remain 1:1 and only allow `key=default`.
    - Returns existing actor when the deterministic id already exists.
    """

    # --- AWARE: LOGIC START ensure_actor
    key_norm = normalize_actor_key(key)
    identity_type = IdentityType(_enum_value(identity.type))

    if identity_type == IdentityType.human:
        actor_type = ActorType.human
    elif identity_type == IdentityType.agent:
        actor_type = ActorType.agent_process_thread
    elif identity_type == IdentityType.organization:
        actor_type = ActorType.organization
    elif identity_type == IdentityType.system:
        actor_type = ActorType.system
    else:
        raise ValueError(f"unreachable: unknown identity type: identity_id={identity.id} type={identity.type}")

    if identity_type != IdentityType.agent and key_norm != DEFAULT_ACTOR_KEY:
        raise ValueError(
            "Identity.ensure_actor only supports non-default keys for IdentityType.agent: "
            f"identity_id={identity.id} identity_type={identity_type.value} key={key_norm!r}"
        )

    actor_id = stable_actor_id_for_identity_key(identity_id=identity.id, key=key_norm)
    existing = Actor.by_id_cached(actor_id)
    if existing is not None:
        if existing.identity_id != identity.id:
            raise ValueError(
                "Identity.ensure_actor identity mismatch for deterministic actor id: "
                f"actor_id={actor_id} expected_identity_id={identity.id} got_identity_id={existing.identity_id}"
            )
        return existing

    return await Actor.create_actor(type=actor_type, identity_id=identity.id, key=key_norm)
    # --- AWARE: LOGIC END ensure_actor


async def create_credential_profile(
    identity: Identity,
    profile_key: str,
    target_kind: CredentialTargetKind = CredentialTargetKind.aware_api,
    credential_kind: CredentialKind = CredentialKind.api_key,
    status: CredentialProfileStatus = CredentialProfileStatus.planned,
    display_name: str | None = None,
    target_name: str | None = None,
    issuer: str | None = None,
    audience: str | None = None,
    external_subject: str | None = None,
    created_at_utc: str | None = None,
    updated_at_utc: str | None = None,
    expires_at_utc: str | None = None,
    revoked_at_utc: str | None = None,
    metadata: JsonObject | None = None,
) -> CredentialProfile:
    """
    Create one Identity-owned credential profile.

    Contract:
    - Parent Identity context is propagated by traversal.
    - Organizations use Identity.type=organization on this same rail.
    - Secret values are never stored on this object.
    - Secret material is resolved through profile-owned refs.
    """

    # --- AWARE: LOGIC START create_credential_profile
    if identity.id is None:
        raise ValueError("Identity.create_credential_profile requires a bound identity.id")

    credential_profile_id = stable_credential_profile_id(
        identity_id=identity.id,
        profile_key=profile_key,
        target_kind=_enum_value(target_kind),
    )

    for existing in identity.credential_profiles:
        if existing.id == credential_profile_id:
            return existing

    existing_profile = CredentialProfile.by_id_cached(credential_profile_id)
    if existing_profile is not None:
        if existing_profile.identity_id != identity.id:
            raise ValueError(
                "Identity.create_credential_profile resolved profile belongs to a different identity: "
                f"credential_profile_id={credential_profile_id} requested_identity_id={identity.id} "
                f"existing_identity_id={existing_profile.identity_id}"
            )
        identity.credential_profiles = [
            *identity.credential_profiles,
            existing_profile,
        ]
        return existing_profile

    profile = await CredentialProfile.create_via_identity(
        identity_id=identity.id,
        profile_key=profile_key,
        target_kind=target_kind,
        credential_kind=credential_kind,
        status=status,
        display_name=display_name,
        target_name=target_name,
        issuer=issuer,
        audience=audience,
        external_subject=external_subject,
        created_at_utc=created_at_utc,
        updated_at_utc=updated_at_utc,
        expires_at_utc=expires_at_utc,
        revoked_at_utc=revoked_at_utc,
        metadata=metadata,
    )
    if profile.id != credential_profile_id:
        raise RuntimeError(
            "Identity.create_credential_profile deterministic id mismatch after constructor resolution: "
            f"expected={credential_profile_id} got={profile.id} identity_id={identity.id}"
        )
    if profile.identity_id != identity.id:
        raise RuntimeError(
            "Identity.create_credential_profile constructor returned mismatched identity rail: "
            f"expected_identity_id={identity.id} got_identity_id={profile.identity_id} "
            f"credential_profile_id={profile.id}"
        )
    identity.credential_profiles = [*identity.credential_profiles, profile]
    return profile
    # --- AWARE: LOGIC END create_credential_profile


async def find_relevant_patterns(
    identity: Identity,
    category: str | None = None,
    pattern_type: IdentityPatternType | None = None,
    min_confidence: float | None = 0.0,
) -> None:
    """
    Experimentally finds relevant patterns for an identity.
    """

    # --- AWARE: LOGIC START find_relevant_patterns
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END find_relevant_patterns
