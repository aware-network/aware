from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Hub Ontology Orm Models
from aware_hub_ontology_orm_models.hub.hub_enums import HubAuthorityVisibility

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_hub_ontology_orm_models.hub.hub_artifact import HubArtifact
    from aware_hub_ontology_orm_models.hub.hub_channel import HubChannel
    from aware_hub_ontology_orm_models.hub.hub_code_package_publication import HubCodePackagePublication
    from aware_hub_ontology_orm_models.hub.hub_publication_receipt import HubPublicationReceipt


class HubAuthority(ORMModel):
    # Relationships
    artifacts: list[HubArtifact] = Field(default_factory=list, exclude=True)
    channels: list[HubChannel] = Field(default_factory=list, exclude=True)
    code_package_publications: list[HubCodePackagePublication] = Field(default_factory=list, exclude=True)
    receipts: list[HubPublicationReceipt] = Field(default_factory=list, exclude=True)

    # Attributes
    authority_key: str
    base_url: str | None = Field(default=None)
    description: str | None = Field(default=None)
    title: str | None = Field(default=None)
    visibility: HubAuthorityVisibility = Field(default=HubAuthorityVisibility.public)
