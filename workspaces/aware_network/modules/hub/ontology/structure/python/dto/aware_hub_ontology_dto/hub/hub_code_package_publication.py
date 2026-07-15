from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeLanguage

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package import CodePackage
    from aware_hub_ontology_dto.hub.hub_artifact import HubArtifactRevision
    from aware_hub_ontology_dto.hub.hub_producer_provenance import HubProducerProvenance


class HubCodePackagePublication(BaseModel):
    # Relationships
    artifact_revision: HubArtifactRevision | None = Field(default=None)
    code_package: CodePackage | None = Field(default=None)
    producer_provenance: HubProducerProvenance | None = Field(default=None)

    # Attributes
    artifact_sha256: str
    artifact_size_bytes: int | None = Field(default=None)
    artifact_url: str
    channel_key: str
    descriptor_digest: str | None = Field(default=None)
    download_handle: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    language: CodeLanguage
    manifest_kind: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)
    package_name: str
    package_root: str | None = Field(default=None)
    published_at_utc: str | None = Field(default=None)
    revision_id: str
    sources_root: str | None = Field(default=None)
    surface: str
    version: str | None = Field(default=None)
