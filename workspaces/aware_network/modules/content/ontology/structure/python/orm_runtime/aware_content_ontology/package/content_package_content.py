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
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_content_ontology.content.content import Content


class ContentPackageContent(ORMModel):
    """
    Package-owned Content membership.
    Contract:
    - ContentPackageContent is membership/projection metadata only.
    - Content remains the multimodal content truth owner.
    - `relative_path` is a materialization coordinate for checkouts, not the
    content identity.
    """

    # Relationships
    content: Content | None = Field(default=None, exclude=True, description="Association target reference to Content")

    # Attributes
    relative_path: str
    content_role: str = Field(default="content")
    position: int | None = Field(default=None)
    media_type: str | None = Field(default=None)
    title: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)
    receipt_payload: JsonObject | None = Field(default=None)

    # Foreign Keys
    content_id: UUID = Field(description="Join FK to Content")
    content_package_id: UUID = Field(description="Join FK to ContentPackage")

    @classmethod
    async def build_via_content_package(
        cls,
        content_package_id: UUID,
        content_id: UUID,
        relative_path: str,
        content_role: str = "content",
        position: int | None = None,
        media_type: str | None = None,
        title: str | None = None,
        source_ref: str | None = None,
        provider_payload: JsonObject | None = None,
        receipt_payload: JsonObject | None = None,
    ) -> ContentPackageContent:
        """
        Attach an existing Content object to a ContentPackage.

        Contract:
        - Parent ContentPackage context is propagated by constructor lowering.
        - Content identity stays with Content; package membership is keyed by
          role and relative materialization coordinate.
        - Providers may record source/service provenance in payload fields, but
          that provenance is not a WorkspaceRevision pin.
        """

        payload = {
            "content_package_id": content_package_id,
            "content_id": content_id,
            "relative_path": relative_path,
            "content_role": content_role,
            "position": position,
            "media_type": media_type,
            "title": title,
            "source_ref": source_ref,
            "provider_payload": provider_payload,
            "receipt_payload": receipt_payload,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_content_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPackageContent):
            return value
        return ContentPackageContent.validate_invocation_value(value)


class ContentPackageContentBuildViaContentPackageInput(BaseModel):
    content_package_id: UUID = Field(description="Join FK to ContentPackage")
    content_id: UUID
    relative_path: str
    content_role: str = Field(default="content")
    position: int | None = Field(default=None)
    media_type: str | None = Field(default=None)
    title: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)
    receipt_payload: JsonObject | None = Field(default=None)


class ContentPackageContentBuildViaContentPackageOutput(BaseModel):
    value: ContentPackageContent


FUNCTIONS = {
    "ContentPackageContent": {
        "build_via_content_package": {
            "canonical": {
                "name": "build_via_content_package",
                "description": "Attach an existing Content object to a ContentPackage.\n\nContract:\n- Parent ContentPackage context is propagated by constructor lowering.\n- Content identity stays with Content; package membership is keyed by\n  role and relative materialization coordinate.\n- Providers may record source/service provenance in payload fields, but\n  that provenance is not a WorkspaceRevision pin.",
                "is_constructor": True,
            },
            "input": ContentPackageContentBuildViaContentPackageInput,
            "output": ContentPackageContentBuildViaContentPackageOutput,
        },
    },
}

__all__ = [
    "ContentPackageContent",
    "ContentPackageContentBuildViaContentPackageInput",
    "ContentPackageContentBuildViaContentPackageOutput",
    "FUNCTIONS",
]
