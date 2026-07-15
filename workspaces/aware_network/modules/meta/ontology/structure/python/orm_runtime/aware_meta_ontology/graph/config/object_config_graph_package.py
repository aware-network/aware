from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_package_implementation_policy_enums import (
    ObjectConfigGraphPackageFunctionImplOwnership,
    ObjectConfigGraphPackageFunctionImplParityPolicy,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package import CodePackage
    from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology.graph.config.object_config_graph_package_dependency import (
        ObjectConfigGraphPackageDependency,
    )
    from aware_meta_ontology.graph.config.object_config_graph_package_language_materialization import (
        ObjectConfigGraphPackageLanguageMaterialization,
    )
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


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

    @classmethod
    async def build(
        cls,
        package_name: str,
        fqn_prefix: str,
        source_code_package_id: UUID | None = None,
        object_config_graph_id: UUID | None = None,
        object_config_graph_object_instance_graph_commit_id: UUID | None = None,
        object_config_graph_package_id: UUID | None = None,
        function_impl_ownership: ObjectConfigGraphPackageFunctionImplOwnership = ObjectConfigGraphPackageFunctionImplOwnership.authored,
        function_impl_parity_policy: ObjectConfigGraphPackageFunctionImplParityPolicy = ObjectConfigGraphPackageFunctionImplParityPolicy.off,
        implementation_policy_source: str = "aware_toml",
        title: str | None = None,
        description: str | None = None,
    ) -> ObjectConfigGraphPackage:
        """
        Create deterministic ObjectConfigGraphPackage for runtime/package proofs.

        Contract:
        - Identity is keyed by `(package_name, fqn_prefix)`.
        - `source_code_package_id` is the explicit provenance link back to canonical source-package truth.
        - `object_config_graph_id` is the semantic graph owned by this package when already materialized.
        - `object_config_graph_object_instance_graph_commit_id` pins the committed OCG root.
        - `function_impl_*` policy is package-level semantic execution authority derived from `aware.toml`.
        """

        payload = {
            "package_name": package_name,
            "fqn_prefix": fqn_prefix,
            "source_code_package_id": source_code_package_id,
            "object_config_graph_id": object_config_graph_id,
            "object_config_graph_object_instance_graph_commit_id": object_config_graph_object_instance_graph_commit_id,
            "object_config_graph_package_id": object_config_graph_package_id,
            "function_impl_ownership": function_impl_ownership,
            "function_impl_parity_policy": function_impl_parity_policy,
            "implementation_policy_source": implementation_policy_source,
            "title": title,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectConfigGraphPackage):
            return value
        return ObjectConfigGraphPackage.validate_invocation_value(value)

    async def attach_object_config_graph(
        self,
        object_config_graph_id: UUID,
        object_config_graph_object_instance_graph_commit_id: UUID | None = None,
        title: str | None = None,
        description: str | None = None,
    ) -> bool:
        """
        Attach canonical `ObjectConfigGraph` leaf truth to this semantic package root.

        Contract:
        - Parent package scope is already resolved by instance invocation.
        - `object_config_graph_id` must point at the canonical graph leaf owned by this package.
        - `object_config_graph_object_instance_graph_commit_id`, when provided, must point at the
          historical OIG commit for that canonical graph leaf.
        - The package shell may exist before the graph leaf is materialized; this method deepens
          the package shell without collapsing package and graph layers.
        """

        payload = {
            "object_config_graph_id": object_config_graph_id,
            "object_config_graph_object_instance_graph_commit_id": object_config_graph_object_instance_graph_commit_id,
            "title": title,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_object_config_graph", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value


class ObjectConfigGraphPackageBuildInput(BaseModel):
    package_name: str
    fqn_prefix: str
    source_code_package_id: UUID | None = Field(default=None)
    object_config_graph_id: UUID | None = Field(default=None)
    object_config_graph_object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_config_graph_package_id: UUID | None = Field(default=None)
    function_impl_ownership: ObjectConfigGraphPackageFunctionImplOwnership = Field(
        default=ObjectConfigGraphPackageFunctionImplOwnership.authored
    )
    function_impl_parity_policy: ObjectConfigGraphPackageFunctionImplParityPolicy = Field(
        default=ObjectConfigGraphPackageFunctionImplParityPolicy.off
    )
    implementation_policy_source: str = Field(default="aware_toml")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ObjectConfigGraphPackageBuildOutput(BaseModel):
    value: ObjectConfigGraphPackage


class ObjectConfigGraphPackageAttachObjectConfigGraphInput(BaseModel):
    object_config_graph_id: UUID
    object_config_graph_object_instance_graph_commit_id: UUID | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ObjectConfigGraphPackageAttachObjectConfigGraphOutput(BaseModel):
    value: bool


FUNCTIONS = {
    "ObjectConfigGraphPackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create deterministic ObjectConfigGraphPackage for runtime/package proofs.\n\nContract:\n- Identity is keyed by `(package_name, fqn_prefix)`.\n- `source_code_package_id` is the explicit provenance link back to canonical source-package truth.\n- `object_config_graph_id` is the semantic graph owned by this package when already materialized.\n- `object_config_graph_object_instance_graph_commit_id` pins the committed OCG root.\n- `function_impl_*` policy is package-level semantic execution authority derived from `aware.toml`.",
                "is_constructor": True,
            },
            "input": ObjectConfigGraphPackageBuildInput,
            "output": ObjectConfigGraphPackageBuildOutput,
        },
        "attach_object_config_graph": {
            "canonical": {
                "name": "attach_object_config_graph",
                "description": "Attach canonical `ObjectConfigGraph` leaf truth to this semantic package root.\n\nContract:\n- Parent package scope is already resolved by instance invocation.\n- `object_config_graph_id` must point at the canonical graph leaf owned by this package.\n- `object_config_graph_object_instance_graph_commit_id`, when provided, must point at the\n  historical OIG commit for that canonical graph leaf.\n- The package shell may exist before the graph leaf is materialized; this method deepens\n  the package shell without collapsing package and graph layers.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphPackageAttachObjectConfigGraphInput,
            "output": ObjectConfigGraphPackageAttachObjectConfigGraphOutput,
        },
    },
}

__all__ = [
    "ObjectConfigGraphPackage",
    "ObjectConfigGraphPackageBuildInput",
    "ObjectConfigGraphPackageBuildOutput",
    "ObjectConfigGraphPackageAttachObjectConfigGraphInput",
    "ObjectConfigGraphPackageAttachObjectConfigGraphOutput",
    "FUNCTIONS",
]
