from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_storage_ontology.blob.storage_blob import StorageBlob


class IdentityProfile(ORMModel):
    # Relationships
    image: StorageBlob | None = Field(default=None, exclude=True)

    # Attributes
    public_handle: str
    display_name: str
    full_name: str
    country_code: str
    language_code: str
    bio: str | None = Field(default=None)

    # Foreign Keys
    image_id: UUID | None = Field(default=None, description="Foreign key for IdentityProfile.image")

    @classmethod
    async def create(
        cls,
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

        payload = {
            "public_handle": public_handle,
            "display_name": display_name,
            "full_name": full_name,
            "country_code": country_code,
            "language_code": language_code,
            "bio": bio,
            "image_id": image_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, IdentityProfile):
            return value
        return IdentityProfile.validate_invocation_value(value)

    async def update_bio(self, bio: str) -> None:
        """
        Updates the bio of the identity.
        Parameters: bio: The new bio of the identity.
        Returns: None.
        """

        payload = {"bio": bio}
        await invoke_instance(orm_model=self, function_name="update_bio", payload=payload)
        return None

    async def update_country(self, country_code: str) -> None:
        """
        Updates the country code of the identity profile.
        Parameters: country_code: ISO 3166-1 alpha-2 country code.
        Returns: None.
        """

        payload = {"country_code": country_code}
        await invoke_instance(orm_model=self, function_name="update_country", payload=payload)
        return None

    async def update_language(self, language_code: str) -> None:
        """
        Updates the language code of the identity profile.
        Parameters: language_code: ISO 639-1 language code.
        Returns: None.
        """

        payload = {"language_code": language_code}
        await invoke_instance(orm_model=self, function_name="update_language", payload=payload)
        return None

    async def update_picture(
        self,
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

        payload = {
            "image_id": image_id,
            "image_sha": image_sha,
            "image_mime_type": image_mime_type,
            "image_size_bytes": image_size_bytes,
        }
        await invoke_instance(orm_model=self, function_name="update_picture", payload=payload)
        return None


class IdentityProfileCreateInput(BaseModel):
    public_handle: str
    display_name: str
    full_name: str
    country_code: str
    language_code: str
    bio: str | None = Field(default=None)
    image_id: UUID | None = Field(default=None)


class IdentityProfileCreateOutput(BaseModel):
    value: IdentityProfile


class IdentityProfileUpdateBioInput(BaseModel):
    bio: str


class IdentityProfileUpdateBioOutput(BaseModel):
    pass


class IdentityProfileUpdateCountryInput(BaseModel):
    country_code: str


class IdentityProfileUpdateCountryOutput(BaseModel):
    pass


class IdentityProfileUpdateLanguageInput(BaseModel):
    language_code: str


class IdentityProfileUpdateLanguageOutput(BaseModel):
    pass


class IdentityProfileUpdatePictureInput(BaseModel):
    image_id: UUID | None = Field(default=None)
    image_sha: str | None = Field(default=None)
    image_mime_type: str | None = Field(default=None)
    image_size_bytes: int | None = Field(default=None)


class IdentityProfileUpdatePictureOutput(BaseModel):
    pass


FUNCTIONS = {
    "IdentityProfile": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Creates a new identity profile.\n\nParameters: \n    public_handle: The public handle of the identity profile.\n    display_name: The display name of the identity profile.\n    full_name: The full name of the identity profile.\n    country_code: The country code of the identity profile.\n    language_code: The language code of the identity profile.\n    bio: The bio of the identity profile, by default NULL.\n    image_id: The ID of the image to set as the profile image, by default NULL.\n\nReturns: The new identity profile.",
                "is_constructor": True,
            },
            "input": IdentityProfileCreateInput,
            "output": IdentityProfileCreateOutput,
        },
        "update_bio": {
            "canonical": {
                "name": "update_bio",
                "description": "Updates the bio of the identity.\nParameters: bio: The new bio of the identity.\nReturns: None.",
                "is_constructor": False,
            },
            "input": IdentityProfileUpdateBioInput,
            "output": IdentityProfileUpdateBioOutput,
        },
        "update_country": {
            "canonical": {
                "name": "update_country",
                "description": "Updates the country code of the identity profile.\nParameters: country_code: ISO 3166-1 alpha-2 country code.\nReturns: None.",
                "is_constructor": False,
            },
            "input": IdentityProfileUpdateCountryInput,
            "output": IdentityProfileUpdateCountryOutput,
        },
        "update_language": {
            "canonical": {
                "name": "update_language",
                "description": "Updates the language code of the identity profile.\nParameters: language_code: ISO 639-1 language code.\nReturns: None.",
                "is_constructor": False,
            },
            "input": IdentityProfileUpdateLanguageInput,
            "output": IdentityProfileUpdateLanguageOutput,
        },
        "update_picture": {
            "canonical": {
                "name": "update_picture",
                "description": "Updates (or clears) the profile picture.\n\nContract:\n- Raw bytes are uploaded out-of-band via HTTP file operations.\n- Commits must reference commit-backed StorageBlob metadata only.\n- When setting a picture, image_sha/image_mime_type/image_size_bytes must be provided together.\n\nParameters:\n    image_id: Optional uploaded blob id to assert against image_sha-derived stable id.\n    image_sha: SHA-256 hex digest of uploaded bytes.\n    image_mime_type: MIME type of uploaded bytes.\n    image_size_bytes: Size of uploaded bytes.\nReturns: None.",
                "is_constructor": False,
            },
            "input": IdentityProfileUpdatePictureInput,
            "output": IdentityProfileUpdatePictureOutput,
        },
    },
}

__all__ = [
    "IdentityProfile",
    "IdentityProfileCreateInput",
    "IdentityProfileCreateOutput",
    "IdentityProfileUpdateBioInput",
    "IdentityProfileUpdateBioOutput",
    "IdentityProfileUpdateCountryInput",
    "IdentityProfileUpdateCountryOutput",
    "IdentityProfileUpdateLanguageInput",
    "IdentityProfileUpdateLanguageOutput",
    "IdentityProfileUpdatePictureInput",
    "IdentityProfileUpdatePictureOutput",
    "FUNCTIONS",
]
