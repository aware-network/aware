from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_package import ApiPackage
    from aware_api_ontology_orm_models.api.api_package_language_package import ApiPackageLanguagePackage
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ServicePackageProvidedApiPackage(ORMModel):
    # Relationships
    api_package: ApiPackage | None = Field(default=None)
    api_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    service_protocol_package: ApiPackageLanguagePackage | None = Field(default=None)

    # Attributes
    service_protocol_plan_hash_sha256: str
    description: str | None = Field(default=None)

    # Foreign Keys
    service_package_id: UUID = Field(description="Foreign key for ServicePackage.provided_api_packages")
    api_package_id: UUID = Field(description="Foreign key for ServicePackageProvidedApiPackage.api_package")
    api_package_object_instance_graph_commit_id: UUID = Field(
        description="Foreign key for ServicePackageProvidedApiPackage.api_package_object_instance_graph_commit"
    )
    service_protocol_package_id: UUID = Field(
        description="Foreign key for ServicePackageProvidedApiPackage.service_protocol_package"
    )
