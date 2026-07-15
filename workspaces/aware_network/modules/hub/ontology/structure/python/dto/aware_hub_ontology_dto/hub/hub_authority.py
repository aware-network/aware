from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Hub Ontology Dto
from aware_hub_ontology_dto.hub.hub_enums import HubAuthorityVisibility

if TYPE_CHECKING:
    from aware_hub_ontology_dto.hub.hub_artifact import HubArtifact
    from aware_hub_ontology_dto.hub.hub_channel import HubChannel
    from aware_hub_ontology_dto.hub.hub_code_package_publication import HubCodePackagePublication
    from aware_hub_ontology_dto.hub.hub_publication_receipt import HubPublicationReceipt


class HubAuthority(BaseModel):
    # Relationships
    artifacts: list[HubArtifact] = Field(default_factory=list)
    channels: list[HubChannel] = Field(default_factory=list)
    code_package_publications: list[HubCodePackagePublication] = Field(default_factory=list)
    receipts: list[HubPublicationReceipt] = Field(default_factory=list)

    # Attributes
    authority_key: str
    base_url: str | None = Field(default=None)
    description: str | None = Field(default=None)
    title: str | None = Field(default=None)
    visibility: HubAuthorityVisibility = Field(default=HubAuthorityVisibility.public)
