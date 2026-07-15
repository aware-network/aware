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
from aware_hub_ontology.hub.hub_enums import HubPublicationReceiptStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_hub_ontology.hub.hub_artifact import HubArtifactRevision
    from aware_hub_ontology.hub.hub_code_package_publication import HubCodePackagePublication


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

    @classmethod
    async def build_via_hub_authority(
        cls,
        hub_authority_id: UUID,
        receipt_key: str,
        operation: str,
        status: HubPublicationReceiptStatus = HubPublicationReceiptStatus.accepted,
        publisher_execution_id: str | None = None,
        idempotency_key: str | None = None,
        artifact_revision_id: UUID | None = None,
        code_package_publication_id: UUID | None = None,
        authority_source_url: str | None = None,
        message: str | None = None,
        recorded_at_utc: str | None = None,
        detail: JsonObject = {},
    ) -> HubPublicationReceipt:
        """Create one Hub authority receipt."""

        payload = {
            "hub_authority_id": hub_authority_id,
            "receipt_key": receipt_key,
            "operation": operation,
            "status": status,
            "publisher_execution_id": publisher_execution_id,
            "idempotency_key": idempotency_key,
            "artifact_revision_id": artifact_revision_id,
            "code_package_publication_id": code_package_publication_id,
            "authority_source_url": authority_source_url,
            "message": message,
            "recorded_at_utc": recorded_at_utc,
            "detail": detail,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_hub_authority", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, HubPublicationReceipt):
            return value
        return HubPublicationReceipt.validate_invocation_value(value)


class HubPublicationReceiptBuildViaHubAuthorityInput(BaseModel):
    hub_authority_id: UUID = Field(description="Foreign key for HubAuthority.receipts")
    receipt_key: str
    operation: str
    status: HubPublicationReceiptStatus = Field(default=HubPublicationReceiptStatus.accepted)
    publisher_execution_id: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    artifact_revision_id: UUID | None = Field(default=None)
    code_package_publication_id: UUID | None = Field(default=None)
    authority_source_url: str | None = Field(default=None)
    message: str | None = Field(default=None)
    recorded_at_utc: str | None = Field(default=None)
    detail: JsonObject = Field(default_factory=JsonObject)


class HubPublicationReceiptBuildViaHubAuthorityOutput(BaseModel):
    value: HubPublicationReceipt


FUNCTIONS = {
    "HubPublicationReceipt": {
        "build_via_hub_authority": {
            "canonical": {
                "name": "build_via_hub_authority",
                "description": "Create one Hub authority receipt.",
                "is_constructor": True,
            },
            "input": HubPublicationReceiptBuildViaHubAuthorityInput,
            "output": HubPublicationReceiptBuildViaHubAuthorityOutput,
        },
    },
}

__all__ = [
    "HubPublicationReceipt",
    "HubPublicationReceiptBuildViaHubAuthorityInput",
    "HubPublicationReceiptBuildViaHubAuthorityOutput",
    "FUNCTIONS",
]
