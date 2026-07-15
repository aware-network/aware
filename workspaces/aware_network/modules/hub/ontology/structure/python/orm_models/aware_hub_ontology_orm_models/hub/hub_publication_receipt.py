from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Hub Ontology Orm Models
from aware_hub_ontology_orm_models.hub.hub_enums import HubPublicationReceiptStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_hub_ontology_orm_models.hub.hub_artifact import HubArtifactRevision
    from aware_hub_ontology_orm_models.hub.hub_code_package_publication import HubCodePackagePublication


class HubPublicationReceipt(ORMModel):
    # Relationships
    artifact_revision: HubArtifactRevision | None = Field(default=None)
    code_package_publication: HubCodePackagePublication | None = Field(default=None)

    # Attributes
    authority_source_url: str | None = Field(default=None)
    detail: JsonObject = Field(default_factory=JsonObject)
    idempotency_key: str | None = Field(default=None)
    message: str | None = Field(default=None)
    operation: str
    publisher_execution_id: str | None = Field(default=None)
    receipt_key: str
    recorded_at_utc: str | None = Field(default=None)
    status: HubPublicationReceiptStatus = Field(default=HubPublicationReceiptStatus.accepted)

    # Foreign Keys
    hub_authority_id: UUID = Field(description="Foreign key for HubAuthority.receipts")
    artifact_revision_id: UUID | None = Field(
        default=None, description="Foreign key for HubPublicationReceipt.artifact_revision"
    )
    code_package_publication_id: UUID | None = Field(
        default=None, description="Foreign key for HubPublicationReceipt.code_package_publication"
    )
