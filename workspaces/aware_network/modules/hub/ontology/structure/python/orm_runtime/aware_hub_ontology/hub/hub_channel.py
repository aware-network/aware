from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Hub Ontology
from aware_hub_ontology.hub.hub_enums import HubAuthorityVisibility

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_hub_ontology.hub.hub_artifact import HubArtifactRevision
    from aware_hub_ontology.hub.hub_code_package_publication import HubCodePackagePublication


class HubChannel(ORMModel):
    # Relationships
    heads: list[HubChannelHead] = Field(default_factory=list)

    # Attributes
    channel_key: str
    description: str | None = Field(default=None)
    title: str | None = Field(default=None)
    visibility: HubAuthorityVisibility = Field(default=HubAuthorityVisibility.public)

    # Foreign Keys
    hub_authority_id: UUID = Field(description="Foreign key for HubAuthority.channels")

    async def upsert_head(
        self,
        artifact_family: str,
        artifact_key: str,
        revision_id: str,
        selector_key: str | None = None,
        artifact_revision_id: UUID | None = None,
        code_package_publication_id: UUID | None = None,
        updated_at_utc: str | None = None,
    ) -> HubChannelHead:
        """Move a channel head to one artifact revision/publication."""

        payload = {
            "artifact_family": artifact_family,
            "artifact_key": artifact_key,
            "revision_id": revision_id,
            "selector_key": selector_key,
            "artifact_revision_id": artifact_revision_id,
            "code_package_publication_id": code_package_publication_id,
            "updated_at_utc": updated_at_utc,
        }
        result = await invoke_instance(orm_model=self, function_name="upsert_head", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, HubChannelHead):
            return value
        return HubChannelHead.validate_invocation_value(value)

    @classmethod
    async def build_via_hub_authority(
        cls,
        hub_authority_id: UUID,
        channel_key: str,
        title: str | None = None,
        description: str | None = None,
        visibility: HubAuthorityVisibility = HubAuthorityVisibility.public,
    ) -> HubChannel:
        """Create one Hub-owned channel."""

        payload = {
            "hub_authority_id": hub_authority_id,
            "channel_key": channel_key,
            "title": title,
            "description": description,
            "visibility": visibility,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_hub_authority", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, HubChannel):
            return value
        return HubChannel.validate_invocation_value(value)


class HubChannelUpsertHeadInput(BaseModel):
    artifact_family: str
    artifact_key: str
    revision_id: str
    selector_key: str | None = Field(default=None)
    artifact_revision_id: UUID | None = Field(default=None)
    code_package_publication_id: UUID | None = Field(default=None)
    updated_at_utc: str | None = Field(default=None)


class HubChannelUpsertHeadOutput(BaseModel):
    value: HubChannelHead


class HubChannelBuildViaHubAuthorityInput(BaseModel):
    hub_authority_id: UUID = Field(description="Foreign key for HubAuthority.channels")
    channel_key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    visibility: HubAuthorityVisibility = Field(default=HubAuthorityVisibility.public)


class HubChannelBuildViaHubAuthorityOutput(BaseModel):
    value: HubChannel


class HubChannelHead(ORMModel):
    # Relationships
    artifact_revision: HubArtifactRevision | None = Field(default=None)
    code_package_publication: HubCodePackagePublication | None = Field(default=None)

    # Attributes
    artifact_family: str
    artifact_key: str
    revision_id: str
    selector_key: str | None = Field(default=None)
    updated_at_utc: str | None = Field(default=None)

    # Foreign Keys
    hub_channel_id: UUID = Field(description="Foreign key for HubChannel.heads")
    artifact_revision_id: UUID | None = Field(
        default=None, description="Foreign key for HubChannelHead.artifact_revision"
    )
    code_package_publication_id: UUID | None = Field(
        default=None, description="Foreign key for HubChannelHead.code_package_publication"
    )

    async def move(
        self,
        revision_id: str,
        selector_key: str | None = None,
        artifact_revision_id: UUID | None = None,
        code_package_publication_id: UUID | None = None,
        updated_at_utc: str | None = None,
    ) -> HubChannelHead:
        """Move this channel head through its own mutation boundary."""

        payload = {
            "revision_id": revision_id,
            "selector_key": selector_key,
            "artifact_revision_id": artifact_revision_id,
            "code_package_publication_id": code_package_publication_id,
            "updated_at_utc": updated_at_utc,
        }
        result = await invoke_instance(orm_model=self, function_name="move", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, HubChannelHead):
            return value
        return HubChannelHead.validate_invocation_value(value)

    @classmethod
    async def build_via_hub_channel(
        cls,
        hub_channel_id: UUID,
        artifact_family: str,
        artifact_key: str,
        revision_id: str,
        selector_key: str | None = None,
        artifact_revision_id: UUID | None = None,
        code_package_publication_id: UUID | None = None,
        updated_at_utc: str | None = None,
    ) -> HubChannelHead:
        """Create one channel head row scoped by channel, artifact family, and artifact key."""

        payload = {
            "hub_channel_id": hub_channel_id,
            "artifact_family": artifact_family,
            "artifact_key": artifact_key,
            "revision_id": revision_id,
            "selector_key": selector_key,
            "artifact_revision_id": artifact_revision_id,
            "code_package_publication_id": code_package_publication_id,
            "updated_at_utc": updated_at_utc,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_hub_channel", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, HubChannelHead):
            return value
        return HubChannelHead.validate_invocation_value(value)


class HubChannelHeadMoveInput(BaseModel):
    revision_id: str
    selector_key: str | None = Field(default=None)
    artifact_revision_id: UUID | None = Field(default=None)
    code_package_publication_id: UUID | None = Field(default=None)
    updated_at_utc: str | None = Field(default=None)


class HubChannelHeadMoveOutput(BaseModel):
    value: HubChannelHead


class HubChannelHeadBuildViaHubChannelInput(BaseModel):
    hub_channel_id: UUID = Field(description="Foreign key for HubChannel.heads")
    artifact_family: str
    artifact_key: str
    revision_id: str
    selector_key: str | None = Field(default=None)
    artifact_revision_id: UUID | None = Field(default=None)
    code_package_publication_id: UUID | None = Field(default=None)
    updated_at_utc: str | None = Field(default=None)


class HubChannelHeadBuildViaHubChannelOutput(BaseModel):
    value: HubChannelHead


FUNCTIONS = {
    "HubChannel": {
        "upsert_head": {
            "canonical": {
                "name": "upsert_head",
                "description": "Move a channel head to one artifact revision/publication.",
                "is_constructor": False,
            },
            "input": HubChannelUpsertHeadInput,
            "output": HubChannelUpsertHeadOutput,
        },
        "build_via_hub_authority": {
            "canonical": {
                "name": "build_via_hub_authority",
                "description": "Create one Hub-owned channel.",
                "is_constructor": True,
            },
            "input": HubChannelBuildViaHubAuthorityInput,
            "output": HubChannelBuildViaHubAuthorityOutput,
        },
    },
    "HubChannelHead": {
        "move": {
            "canonical": {
                "name": "move",
                "description": "Move this channel head through its own mutation boundary.",
                "is_constructor": False,
            },
            "input": HubChannelHeadMoveInput,
            "output": HubChannelHeadMoveOutput,
        },
        "build_via_hub_channel": {
            "canonical": {
                "name": "build_via_hub_channel",
                "description": "Create one channel head row scoped by channel, artifact family, and artifact key.",
                "is_constructor": True,
            },
            "input": HubChannelHeadBuildViaHubChannelInput,
            "output": HubChannelHeadBuildViaHubChannelOutput,
        },
    },
}

__all__ = [
    "HubChannel",
    "HubChannelUpsertHeadInput",
    "HubChannelUpsertHeadOutput",
    "HubChannelBuildViaHubAuthorityInput",
    "HubChannelBuildViaHubAuthorityOutput",
    "HubChannelHead",
    "HubChannelHeadMoveInput",
    "HubChannelHeadMoveOutput",
    "HubChannelHeadBuildViaHubChannelInput",
    "HubChannelHeadBuildViaHubChannelOutput",
    "FUNCTIONS",
]
