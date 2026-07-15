from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Hub Ontology Dto
from aware_hub_ontology_dto.hub.hub_enums import HubPublicationReceiptStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_hub_ontology_dto.hub.hub_artifact import HubArtifactRevision
    from aware_hub_ontology_dto.hub.hub_code_package_publication import HubCodePackagePublication


class HubPublicationReceipt(BaseModel):
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
