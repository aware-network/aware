from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Hub Ontology Orm Models
from aware_hub_ontology_orm_models.hub.hub_enums import HubAuthorityVisibility

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_hub_ontology_orm_models.hub.hub_artifact import HubArtifactRevision
    from aware_hub_ontology_orm_models.hub.hub_code_package_publication import HubCodePackagePublication


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
