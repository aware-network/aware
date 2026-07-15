from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.content.content import Content
    from aware_content_ontology_orm_models.package.content_package_artifact import ContentPackageArtifact
    from aware_content_ontology_orm_models.package.content_package_content import ContentPackageContent


class ContentPackage(ORMModel):
    # Relationships
    artifacts: list[ContentPackageArtifact] = Field(default_factory=list, exclude=True)

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

    # Edges
    content_package_contents: list[ContentPackageContent] = Field(
        default_factory=list, exclude=True, description="Edge association helper for contents"
    )

    @property
    def contents(self) -> list[Content]:
        return [edge.content for edge in self.content_package_contents if edge.content is not None]
