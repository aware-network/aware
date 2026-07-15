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
    from aware_code_ontology.package.code_package import CodePackage
    from aware_network_ontology.network.network_node_config import NetworkNodeConfig


class NetworkNodePackage(ORMModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    network_node_config: NetworkNodeConfig | None = Field(default=None)

    # Attributes
    name: str

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for NetworkNodePackage.source_code_package"
    )
    network_node_config_id: UUID = Field(description="Foreign key for NetworkNodePackage.network_node_config")

    @classmethod
    async def build(
        cls, name: str, network_node_config_id: UUID, source_code_package_id: UUID | None = None
    ) -> NetworkNodePackage:
        """
        Create the canonical Network-owned package root over an existing `NetworkNodeConfig`.

        Contract:
        - Identity is keyed by Network node package `name`.
        - `NetworkNodePackage` is the package/public root over an existing canonical
          `NetworkNodeConfig`.
        - `network_node_config_id` must point at the canonical NetworkNodeConfig stable id for
          this package root.
        - `source_code_package_id` is the explicit raw-source provenance link for this semantic
          leaf package.
        - Workspace will later mount `NetworkNodePackage`, not raw `NetworkNodeConfig`.
        """

        payload = {
            "name": name,
            "network_node_config_id": network_node_config_id,
            "source_code_package_id": source_code_package_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NetworkNodePackage):
            return value
        return NetworkNodePackage.validate_invocation_value(value)


class NetworkNodePackageBuildInput(BaseModel):
    name: str
    network_node_config_id: UUID
    source_code_package_id: UUID | None = Field(default=None)


class NetworkNodePackageBuildOutput(BaseModel):
    value: NetworkNodePackage


FUNCTIONS = {
    "NetworkNodePackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical Network-owned package root over an existing `NetworkNodeConfig`.\n\nContract:\n- Identity is keyed by Network node package `name`.\n- `NetworkNodePackage` is the package/public root over an existing canonical\n  `NetworkNodeConfig`.\n- `network_node_config_id` must point at the canonical NetworkNodeConfig stable id for\n  this package root.\n- `source_code_package_id` is the explicit raw-source provenance link for this semantic\n  leaf package.\n- Workspace will later mount `NetworkNodePackage`, not raw `NetworkNodeConfig`.",
                "is_constructor": True,
            },
            "input": NetworkNodePackageBuildInput,
            "output": NetworkNodePackageBuildOutput,
        },
    },
}

__all__ = [
    "NetworkNodePackage",
    "NetworkNodePackageBuildInput",
    "NetworkNodePackageBuildOutput",
    "FUNCTIONS",
]
