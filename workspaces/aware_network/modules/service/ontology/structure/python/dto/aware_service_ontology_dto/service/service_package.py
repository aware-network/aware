from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package import CodePackage
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_service_ontology_dto.service.service_config import ServiceConfig
    from aware_service_ontology_dto.service.service_package_implementation_package import (
        ServicePackageImplementationPackage,
    )
    from aware_service_ontology_dto.service.service_package_object_config_graph_package import (
        ServicePackageObjectConfigGraphPackage,
    )
    from aware_service_ontology_dto.service.service_package_ontology_package import ServicePackageOntologyPackage
    from aware_service_ontology_dto.service.service_package_provided_api_package import ServicePackageProvidedApiPackage
    from aware_service_ontology_dto.service.service_package_required_api_package import ServicePackageRequiredApiPackage


class ServicePackage(BaseModel):
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
