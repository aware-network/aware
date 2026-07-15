from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.graph.config.object_config_graph_package_implementation_policy_enums import (
    ObjectConfigGraphPackageFunctionImplOwnership,
    ObjectConfigGraphPackageFunctionImplParityPolicy,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.package.code_package import CodePackage
    from aware_meta_ontology_orm_models.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology_orm_models.graph.config.object_config_graph_package_dependency import (
        ObjectConfigGraphPackageDependency,
    )
    from aware_meta_ontology_orm_models.graph.config.object_config_graph_package_language_materialization import (
        ObjectConfigGraphPackageLanguageMaterialization,
    )
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ObjectConfigGraphPackage(ORMModel):
    """
    Canonical package spine for an ObjectConfigGraph (OCG).
    This object is intentionally CANONICAL-only: a package exists only for
    a canonical OCG derived from `.aware` sources (SSOT).
    Other languages (python/dart/sql) may provide derived materializations.
    Their generated package outputs are tracked below
    `ObjectConfigGraphPackageLanguageMaterialization`; they remain distinct from
    this authored source package spine.
    The package spine declares identity and the explicit dependency universe
    (commit-pinned) required for deterministic cross-OCG linking.
    NOTE: `source_code_package` is the authored `.aware` CodePackage.
    Generated language CodePackages are owned by language materialization output
    child objects.
    """

    # Relationships
    source_code_package: CodePackage | None = Field(
        default=None,
        description="Canonical source code package from which this semantic package is derived.\nThis keeps package provenance explicit and bottom-up: source code package first,\nsemantic OCG package second.",
    )
    object_config_graph: ObjectConfigGraph | None = Field(
        default=None,
        description="Canonical graph identity owned by this package.\nOptional until the first successful build produces an OCG artifact.",
    )
    object_config_graph_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(
        default=None,
        description="Historical OIG commit for the owned `ObjectConfigGraph` root.\nThis is distinct from the package shell commit: package consumers need the\nexact semantic OCG root commit to replay environment runtime truth from\nWorkspaceRevision receipts without reopening source TOMLs.",
    )
    dependencies: list[ObjectConfigGraphPackageDependency] = Field(
        default_factory=list, description="Direct dependencies declared by this package."
    )
    language_materializations: list[ObjectConfigGraphPackageLanguageMaterialization] = Field(
        default_factory=list, description="Language CodePackage materialization targets declared by this package."
    )

    # Attributes
    package_name: str = Field(
        description="Stable package name (distribution/materialization identity; may include hyphens)."
    )
    fqn_prefix: str = Field(
        description="Stable FQN prefix owned by this package (used to prevent collisions in cross-OCG linking)."
    )
    title: str | None = Field(default=None, description="Human metadata")
    description: str | None = Field(default=None)
    function_impl_ownership: ObjectConfigGraphPackageFunctionImplOwnership = Field(
        default=ObjectConfigGraphPackageFunctionImplOwnership.authored,
        description="Package-level FunctionImpl execution authority derived from `aware.toml`.",
    )
    function_impl_parity_policy: ObjectConfigGraphPackageFunctionImplParityPolicy = Field(
        default=ObjectConfigGraphPackageFunctionImplParityPolicy.off,
        description="Transition parity gate for language handlers versus `.aware` FunctionImpl bodies.",
    )
    implementation_policy_source: str = Field(
        default="aware_toml",
        description='Provenance for package-level implementation policy. Expected canonical value is "aware_toml".',
    )

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphPackage.source_code_package"
    )
    object_config_graph_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphPackage.object_config_graph"
    )
    object_config_graph_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for ObjectConfigGraphPackage.object_config_graph_object_instance_graph_commit",
    )
