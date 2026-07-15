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
    from aware_ontology_ontology.ontology.ontology_package import OntologyPackage


class NodeConfigOntologyTarget(ORMModel):
    # Relationships
    ontology_package: OntologyPackage | None = Field(default=None)

    # Attributes
    package_name: str

    # Foreign Keys
    node_config_id: UUID = Field(description="Foreign key for NodeConfig.ontology_targets")
    ontology_package_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigOntologyTarget.ontology_package"
    )

    @classmethod
    async def build_via_node_config(cls, node_config_id: UUID, package_name: str) -> NodeConfigOntologyTarget:
        """
        Create one Node-owned ontology target by canonical ontology package name.

        Contract:
        - Parent `NodeConfig` scope is injected by propagation.
        - Identity is keyed by `(node_config_id, package_name)`.
        - The target `OntologyPackage` portal is resolved from `package_name`
          without storing raw graph/package refs as Node source truth.
        - Ontology targets select semantic package authority; runtime service
          exposure is a later host concern and must not be encoded as a raw
          Service target workaround.
        """

        payload = {"node_config_id": node_config_id, "package_name": package_name}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_node_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NodeConfigOntologyTarget):
            return value
        return NodeConfigOntologyTarget.validate_invocation_value(value)


class NodeConfigOntologyTargetBuildViaNodeConfigInput(BaseModel):
    node_config_id: UUID = Field(description="Foreign key for NodeConfig.ontology_targets")
    package_name: str


class NodeConfigOntologyTargetBuildViaNodeConfigOutput(BaseModel):
    value: NodeConfigOntologyTarget


FUNCTIONS = {
    "NodeConfigOntologyTarget": {
        "build_via_node_config": {
            "canonical": {
                "name": "build_via_node_config",
                "description": "Create one Node-owned ontology target by canonical ontology package name.\n\nContract:\n- Parent `NodeConfig` scope is injected by propagation.\n- Identity is keyed by `(node_config_id, package_name)`.\n- The target `OntologyPackage` portal is resolved from `package_name`\n  without storing raw graph/package refs as Node source truth.\n- Ontology targets select semantic package authority; runtime service\n  exposure is a later host concern and must not be encoded as a raw\n  Service target workaround.",
                "is_constructor": True,
            },
            "input": NodeConfigOntologyTargetBuildViaNodeConfigInput,
            "output": NodeConfigOntologyTargetBuildViaNodeConfigOutput,
        },
    },
}

__all__ = [
    "NodeConfigOntologyTarget",
    "NodeConfigOntologyTargetBuildViaNodeConfigInput",
    "NodeConfigOntologyTargetBuildViaNodeConfigOutput",
    "FUNCTIONS",
]
