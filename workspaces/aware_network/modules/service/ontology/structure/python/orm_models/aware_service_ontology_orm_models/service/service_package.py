from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.package.code_package import CodePackage
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_service_ontology_orm_models.service.service_config import ServiceConfig
    from aware_service_ontology_orm_models.service.service_package_implementation_package import (
        ServicePackageImplementationPackage,
    )
    from aware_service_ontology_orm_models.service.service_package_object_config_graph_package import (
        ServicePackageObjectConfigGraphPackage,
    )
    from aware_service_ontology_orm_models.service.service_package_ontology_package import ServicePackageOntologyPackage
    from aware_service_ontology_orm_models.service.service_package_provided_api_package import (
        ServicePackageProvidedApiPackage,
    )
    from aware_service_ontology_orm_models.service.service_package_required_api_package import (
        ServicePackageRequiredApiPackage,
    )


class ServicePackage(ORMModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    implementation_packages: list[ServicePackageImplementationPackage] = Field(default_factory=list)
    ontology_packages: list[ServicePackageOntologyPackage] = Field(default_factory=list)
    object_config_graph_packages: list[ServicePackageObjectConfigGraphPackage] = Field(default_factory=list)
    provided_api_packages: list[ServicePackageProvidedApiPackage] = Field(default_factory=list)
    required_api_packages: list[ServicePackageRequiredApiPackage] = Field(default_factory=list)
    service_config: ServiceConfig | None = Field(default=None)
    service_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    activation_mode: str = Field(default="materialize_and_load_committed")
    aware_service_version: int = Field(default=1)
    compilation_mode: str = Field(default="raw_xor")
    dependencies: JsonArray = Field(default_factory=JsonArray)
    description: str | None = Field(default=None)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    fqn_prefix: str | None = Field(default=None)
    include_paths: JsonArray = Field(default_factory=JsonArray)
    manifest_relative_path: str | None = Field(default=None)
    materialize_on_start: bool = Field(default=True)
    name: str
    package_root: str = Field(default=".")
    service_surface: str = Field(default="service")
    sources_root: str = Field(default="services")
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for ServicePackage.source_code_package"
    )
    service_config_id: UUID = Field(description="Foreign key for ServicePackage.service_config")
    service_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for ServicePackage.service_config_object_instance_graph_commit"
    )
