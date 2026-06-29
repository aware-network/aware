from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.package.code_package import CodePackage
    from aware_meta_ontology_orm_models.graph.config.object_config_graph_package import ObjectConfigGraphPackage
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_ontology_ontology_orm_models.ontology.ontology_config import OntologyConfig
    from aware_ontology_ontology_orm_models.ontology.ontology_package_dependency import OntologyPackageDependency
    from aware_ontology_ontology_orm_models.ontology.ontology_package_runtime_code_package import (
        OntologyPackageRuntimeCodePackage,
    )


class OntologyPackage(ORMModel):
    """
    Semantic owner for one ontology package.
    `ObjectConfigGraphPackage` remains the raw Meta representation package.
    `CodePackage` remains the raw source/runtime package owner. `OntologyPackage`
    is the semantic package root that binds those lower-level package truths into
    the ontology domain so environments can compose ontology meaning instead of
    raw graph leaves.
    """

    # Relationships
    ontology_config: OntologyConfig | None = Field(default=None)
    ontology_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    source_code_package: CodePackage | None = Field(default=None)
    object_config_graph_package: ObjectConfigGraphPackage | None = Field(default=None)
    object_config_graph_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    object_config_graph_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    runtime_code_packages: list[OntologyPackageRuntimeCodePackage] = Field(default_factory=list)
    dependencies: list[OntologyPackageDependency] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    fqn_prefix: str
    manifest_relative_path: str | None = Field(default=None)
    name: str
    package_root: str = Field(default=".")
    sources_root: str = Field(default="modules")
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)

    # Foreign Keys
    ontology_config_id: UUID | None = Field(default=None, description="Foreign key for OntologyPackage.ontology_config")
    ontology_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyPackage.ontology_config_object_instance_graph_commit"
    )
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyPackage.source_code_package"
    )
    object_config_graph_package_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyPackage.object_config_graph_package"
    )
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for OntologyPackage.object_config_graph_package_object_instance_graph_commit",
    )
    object_config_graph_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyPackage.object_config_graph_object_instance_graph_commit"
    )
