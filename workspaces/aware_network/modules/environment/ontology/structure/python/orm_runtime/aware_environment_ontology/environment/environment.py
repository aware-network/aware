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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_environment_ontology.environment.environment_config import EnvironmentConfig
    from aware_environment_ontology.environment.environment_ontology import EnvironmentOntology
    from aware_environment_ontology.environment.environment_profile import EnvironmentProfile
    from aware_environment_ontology.environment.environment_session import EnvironmentSession
    from aware_storage_ontology.blob.storage_blob import StorageBlob


class Environment(ORMModel):
    # Relationships
    config: EnvironmentConfig | None = Field(
        default=None,
        exclude=True,
        description="Canonical composition truth bound to this runtime environment.\nContract:\n- Required runtime binder input.\n- Owned by Environment through `EnvironmentConfig`; `Environment` binds it.\n- Not part of `Environment` class-key identity in this cut.",
    )
    image: StorageBlob | None = Field(
        default=None,
        exclude=True,
        description="Optional territory image override for this environment.\nFallback guidance:\n- If unset, UI should resolve through the caller-selected Experience/profile\nsurface, not through Environment-owned profile selection.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )
    profiles: list[EnvironmentProfile] = Field(
        default_factory=list,
        exclude=True,
        description="Concrete Environment-applied profiles.\nContract:\n- Reusable OS topology lives in EnvironmentProfileConfig.\n- Applied profiles own runtime Process/Thread provenance.\n- Environment does not point at Experience profiles for canonical boot.",
    )
    sessions: list[EnvironmentSession] = Field(
        default_factory=list,
        description="Runtime Environment sessions.\nContract:\n- Environment owns concrete shared session wrappers.\n- Identity owns actor membership through the linked Identity Session.\n- Profiles remain Process/Thread provenance; sessions resolve threads\nthrough EnvironmentSessionThread pins and may cross applied profiles.",
    )
    ontologies: list[EnvironmentOntology] = Field(
        default_factory=list,
        description="Ontology authorities available to this runtime Environment.\nContract:\n- Environment selects Ontology instances through this portal only.\n- ObjectInstanceGraphIdentity inventory remains owned by Ontology.\n- Environment must not point directly at Meta ObjectInstanceGraph/OIGI\nmembership.",
    )

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)

    # Foreign Keys
    config_id: UUID = Field(description="Foreign key for Environment.config")
    image_id: UUID | None = Field(default=None, description="Foreign key for Environment.image")

    @classmethod
    async def build(cls, key: str, title: str, description: str | None = None) -> Environment:
        """
        Create a runtime Environment territory.

        Contract:
        - Environment creation does not install an Experience profile.
        - Process, Thread, layout, and branch pointers are explicit follow-up mutations.
        """

        payload = {"key": key, "title": title, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Environment):
            return value
        return Environment.validate_invocation_value(value)

    async def apply_profile(
        self,
        profile_config_id: UUID,
        title: str | None = None,
        description: str | None = None,
        status: str = "active",
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentProfile:
        """
        Apply one EnvironmentProfileConfig under this Environment.

        Contract:
        - Mutates only Environment-owned applied profile membership.
        - ProcessConfig and ThreadConfig remain under EnvironmentProfileConfig.
        - EnvironmentSessionConfig remains under EnvironmentConfig.
        - Does not install or inspect any Experience.
        """

        payload = {
            "profile_config_id": profile_config_id,
            "title": title,
            "description": description,
            "status": status,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="apply_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_profile import EnvironmentProfile

        if isinstance(value, EnvironmentProfile):
            return value
        return EnvironmentProfile.validate_invocation_value(value)

    async def start_session(
        self,
        identity_session_id: UUID,
        session_config_id: UUID | None = None,
        key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        status: str = "active",
        source_kind: str | None = None,
        source_ref: str | None = None,
        metadata_json: JsonObject | None = {},
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

        payload = {
            "identity_session_id": identity_session_id,
            "session_config_id": session_config_id,
            "key": key,
            "title": title,
            "description": description,
            "purpose": purpose,
            "status": status,
            "source_kind": source_kind,
            "source_ref": source_ref,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="start_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_session import EnvironmentSession

        if isinstance(value, EnvironmentSession):
            return value
        return EnvironmentSession.validate_invocation_value(value)

    async def attach_ontology(
        self,
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

        payload = {
            "ontology_id": ontology_id,
            "role": role,
            "status": status,
            "title": title,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_ontology", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_ontology import EnvironmentOntology

        if isinstance(value, EnvironmentOntology):
            return value
        return EnvironmentOntology.validate_invocation_value(value)

    async def update_picture(
        self,
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

        payload = {
            "image_id": image_id,
            "image_sha": image_sha,
            "image_mime_type": image_mime_type,
            "image_size_bytes": image_size_bytes,
        }
        await invoke_instance(orm_model=self, function_name="update_picture", payload=payload)
        return None


class EnvironmentBuildInput(BaseModel):
    key: str
    title: str
    description: str | None = Field(default=None)


class EnvironmentBuildOutput(BaseModel):
    value: Environment


class EnvironmentApplyProfileInput(BaseModel):
    profile_config_id: UUID
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentApplyProfileOutput(BaseModel):
    value: EnvironmentProfile


class EnvironmentStartSessionInput(BaseModel):
    identity_session_id: UUID
    session_config_id: UUID | None = Field(default=None)
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentStartSessionOutput(BaseModel):
    value: EnvironmentSession


class EnvironmentAttachOntologyInput(BaseModel):
    ontology_id: UUID
    role: str = Field(default="runtime")
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)


class EnvironmentAttachOntologyOutput(BaseModel):
    value: EnvironmentOntology


class EnvironmentUpdatePictureInput(BaseModel):
    image_id: UUID | None = Field(default=None)
    image_sha: str | None = Field(default=None)
    image_mime_type: str | None = Field(default=None)
    image_size_bytes: int | None = Field(default=None)


class EnvironmentUpdatePictureOutput(BaseModel):
    pass


FUNCTIONS = {
    "Environment": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create a runtime Environment territory.\n\nContract:\n- Environment creation does not install an Experience profile.\n- Process, Thread, layout, and branch pointers are explicit follow-up mutations.",
                "is_constructor": True,
            },
            "input": EnvironmentBuildInput,
            "output": EnvironmentBuildOutput,
        },
        "apply_profile": {
            "canonical": {
                "name": "apply_profile",
                "description": "Apply one EnvironmentProfileConfig under this Environment.\n\nContract:\n- Mutates only Environment-owned applied profile membership.\n- ProcessConfig and ThreadConfig remain under EnvironmentProfileConfig.\n- EnvironmentSessionConfig remains under EnvironmentConfig.\n- Does not install or inspect any Experience.",
                "is_constructor": False,
            },
            "input": EnvironmentApplyProfileInput,
            "output": EnvironmentApplyProfileOutput,
        },
        "start_session": {
            "canonical": {
                "name": "start_session",
                "description": "Start or attach one runtime EnvironmentSession under this Environment.\n\nContract:\n- Stable identity is Environment path + Identity Session.\n- `session_config_id` is optional non-key provenance/defaults.\n- Actor membership, ActorRole evidence, and provider sessions live on\n  the linked Identity Session.\n- Process/Thread/Layout selection is EnvironmentSession-owned through\n  navigation contexts and session-thread pins.",
                "is_constructor": False,
            },
            "input": EnvironmentStartSessionInput,
            "output": EnvironmentStartSessionOutput,
        },
        "attach_ontology": {
            "canonical": {
                "name": "attach_ontology",
                "description": "Attach one Ontology authority to this runtime Environment.\n\nContract:\n- Mutates only Environment-owned ontology membership.\n- The target Ontology owns OIGI inventory discovery.\n- Environment does not duplicate ObjectInstanceGraph membership or\n  commit pins.",
                "is_constructor": False,
            },
            "input": EnvironmentAttachOntologyInput,
            "output": EnvironmentAttachOntologyOutput,
        },
        "update_picture": {
            "canonical": {
                "name": "update_picture",
                "description": "Updates (or clears) the environment territory image override.\n\nContract:\n- Raw bytes are uploaded out-of-band via HTTP file operations.\n- Commits must reference commit-backed StorageBlob metadata only.\n- When setting a picture, image_sha/image_mime_type/image_size_bytes must be provided together.\n\nParameters:\n    image_id: Optional uploaded blob id to assert against image_sha-derived stable id.\n    image_sha: SHA-256 hex digest of uploaded bytes.\n    image_mime_type: MIME type of uploaded bytes.\n    image_size_bytes: Size of uploaded bytes.\nReturns: None.",
                "is_constructor": False,
            },
            "input": EnvironmentUpdatePictureInput,
            "output": EnvironmentUpdatePictureOutput,
        },
    },
}

__all__ = [
    "Environment",
    "EnvironmentBuildInput",
    "EnvironmentBuildOutput",
    "EnvironmentApplyProfileInput",
    "EnvironmentApplyProfileOutput",
    "EnvironmentStartSessionInput",
    "EnvironmentStartSessionOutput",
    "EnvironmentAttachOntologyInput",
    "EnvironmentAttachOntologyOutput",
    "EnvironmentUpdatePictureInput",
    "EnvironmentUpdatePictureOutput",
    "FUNCTIONS",
]
