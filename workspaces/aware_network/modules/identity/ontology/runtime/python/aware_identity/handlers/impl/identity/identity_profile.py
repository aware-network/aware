from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.identity.identity_profile import IdentityProfile

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
import re

from aware_identity_ontology.stable_ids import stable_identity_profile_id
from aware_storage_ontology.blob.storage_blob import StorageBlob

# --- AWARE: USER_IMPORTS END


async def create(
    public_handle: str,
    display_name: str,
    full_name: str,
    country_code: str,
    language_code: str,
    bio: str | None = None,
    image_id: UUID | None = None,
) -> IdentityProfile:
    """
    Creates a new identity profile.

    Parameters:
        public_handle: The public handle of the identity profile.
        display_name: The display name of the identity profile.
        full_name: The full name of the identity profile.
        country_code: The country code of the identity profile.
        language_code: The language code of the identity profile.
        bio: The bio of the identity profile, by default NULL.
        image_id: The ID of the image to set as the profile image, by default NULL.

    Returns: The new identity profile.
    """

    # --- AWARE: LOGIC START create
    profile_id = stable_identity_profile_id(public_handle=public_handle)
    return IdentityProfile(
        id=profile_id,
        public_handle=public_handle,
        display_name=display_name,
        full_name=full_name,
        country_code=country_code,
        language_code=language_code,
        bio=bio,
        image_id=image_id,
    )
    # --- AWARE: LOGIC END create


async def update_bio(identity_profile: IdentityProfile, bio: str) -> None:
    """
    Updates the bio of the identity.
    Parameters: bio: The new bio of the identity.
    Returns: None.
    """

    # --- AWARE: LOGIC START update_bio
    identity_profile.bio = bio
    # --- AWARE: LOGIC END update_bio


async def update_country(identity_profile: IdentityProfile, country_code: str) -> None:
    """
    Updates the country code of the identity profile.
    Parameters: country_code: ISO 3166-1 alpha-2 country code.
    Returns: None.
    """

    # --- AWARE: LOGIC START update_country
    normalized = (country_code or "").strip().upper()
    if not re.fullmatch(r"[A-Z]{2}", normalized):
        raise ValueError("country_code must be an ISO 3166-1 alpha-2 code (2 letters)")
    identity_profile.country_code = normalized
    # --- AWARE: LOGIC END update_country


async def update_language(identity_profile: IdentityProfile, language_code: str) -> None:
    """
    Updates the language code of the identity profile.
    Parameters: language_code: ISO 639-1 language code.
    Returns: None.
    """

    # --- AWARE: LOGIC START update_language
    normalized = (language_code or "").strip().lower()
    if not re.fullmatch(r"[a-z]{2}", normalized):
        raise ValueError("language_code must be an ISO 639-1 code (2 letters)")
    identity_profile.language_code = normalized
    # --- AWARE: LOGIC END update_language


async def update_picture(
    identity_profile: IdentityProfile,
    image_id: UUID | None = None,
    image_sha: str | None = None,
    image_mime_type: str | None = None,
    image_size_bytes: int | None = None,
) -> None:
    """
    Updates (or clears) the profile picture.

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
        identity_profile.image_id = None
        identity_profile.image = None
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

    identity_profile.image = blob
    identity_profile.image_id = blob.id
    # --- AWARE: LOGIC END update_picture
