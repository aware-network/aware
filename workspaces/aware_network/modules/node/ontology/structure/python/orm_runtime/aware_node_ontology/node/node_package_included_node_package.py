from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_node_ontology.node.node_package import NodePackage


class NodePackageIncludedNodePackage(ORMModel):
    # Relationships
    included_node_package: NodePackage | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    include_key: str | None = Field(default=None)
    included_package_name: str

    # Foreign Keys
    node_package_id: UUID = Field(description="Foreign key for NodePackage.included_node_packages")
    included_node_package_id: UUID = Field(
        description="Foreign key for NodePackageIncludedNodePackage.included_node_package"
    )

    @classmethod
    async def build_via_node_package(
        cls,
        node_package_id: UUID,
        included_package_name: str,
        include_key: str | None = None,
        description: str | None = None,
    ) -> NodePackageIncludedNodePackage:
        """
        Create one package-level Node composition include bridge.

        Contract:
        - Parent `NodePackage` scope is injected by propagation.
        - Identity is keyed by authored semantic package name, not a raw UUID.
        - `included_node_package` stores the canonical relational target derived from that name.
        - The bridge does not flatten included targets into the authoring package; deployment
          derives effective composition from committed package closure.
        """

        payload = {
            "node_package_id": node_package_id,
            "included_package_name": included_package_name,
            "include_key": include_key,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_node_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NodePackageIncludedNodePackage):
            return value
        return NodePackageIncludedNodePackage.validate_invocation_value(value)


class NodePackageIncludedNodePackageBuildViaNodePackageInput(BaseModel):
    node_package_id: UUID = Field(description="Foreign key for NodePackage.included_node_packages")
    included_package_name: str
    include_key: str | None = Field(default=None)
    description: str | None = Field(default=None)


class NodePackageIncludedNodePackageBuildViaNodePackageOutput(BaseModel):
    value: NodePackageIncludedNodePackage


FUNCTIONS = {
    "NodePackageIncludedNodePackage": {
        "build_via_node_package": {
            "canonical": {
                "name": "build_via_node_package",
                "description": "Create one package-level Node composition include bridge.\n\nContract:\n- Parent `NodePackage` scope is injected by propagation.\n- Identity is keyed by authored semantic package name, not a raw UUID.\n- `included_node_package` stores the canonical relational target derived from that name.\n- The bridge does not flatten included targets into the authoring package; deployment\n  derives effective composition from committed package closure.",
                "is_constructor": True,
            },
            "input": NodePackageIncludedNodePackageBuildViaNodePackageInput,
            "output": NodePackageIncludedNodePackageBuildViaNodePackageOutput,
        },
    },
}

__all__ = [
    "NodePackageIncludedNodePackage",
    "NodePackageIncludedNodePackageBuildViaNodePackageInput",
    "NodePackageIncludedNodePackageBuildViaNodePackageOutput",
    "FUNCTIONS",
]
