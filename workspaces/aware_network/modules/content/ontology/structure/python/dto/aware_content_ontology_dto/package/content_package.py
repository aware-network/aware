from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_content_ontology_dto.content.content import Content
    from aware_content_ontology_dto.package.content_package_artifact import ContentPackageArtifact
    from aware_content_ontology_dto.package.content_package_content import ContentPackageContent


class ContentPackage(BaseModel):
    # Relationships
    artifacts: list[ContentPackageArtifact] = Field(default_factory=list)

    # Attributes
    package_name: str
    package_root: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    title: str | None = Field(default=None)
    package_kind: str | None = Field(default="content")
    source_provider_key: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)
