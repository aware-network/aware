from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_package import ApiPackage
    from aware_api_ontology_dto.api.api_package_language_package import ApiPackageLanguagePackage
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ServicePackageProvidedApiPackage(BaseModel):
    # Relationships
    api_package: ApiPackage | None = Field(default=None)
    api_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    service_protocol_package: ApiPackageLanguagePackage | None = Field(default=None)

    # Attributes
    service_protocol_plan_hash_sha256: str
    description: str | None = Field(default=None)
