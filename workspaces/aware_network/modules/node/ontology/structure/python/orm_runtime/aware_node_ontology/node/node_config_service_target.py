from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_node_ontology.node.node_config_service_code_package import NodeConfigServiceCodePackage
    from aware_service_ontology.service.service_config import ServiceConfig


class NodeConfigServiceTarget(ORMModel):
    # Relationships
    service_config: ServiceConfig | None = Field(default=None)
    code_packages: list[NodeConfigServiceCodePackage] = Field(default_factory=list)

    # Attributes
    service_name: str

    # Foreign Keys
    node_config_id: UUID = Field(description="Foreign key for NodeConfig.service_targets")
    service_config_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigServiceTarget.service_config"
    )

    async def activate_code_package(
        self,
        slot_key: str,
        package_name: str,
        language: CodeLanguage = CodeLanguage.aware,
        service_config_code_package_config_id: UUID | None = None,
        code_package_id: UUID | None = None,
        description: str | None = None,
    ) -> NodeConfigServiceCodePackage:
        """
        Activate one concrete CodePackage under this service target.

        Contract:
        - Parent `NodeConfigServiceTarget` scope is injected by propagation.
        - The activation is deployment intent only; the service declaration owns hostable slots.
        - Local-dev sources may name `slot_key` and `package_name` before WorkspaceRevision has
          resolved package refs. When available, materializers can attach the Service slot and
          CodePackage relationships.
        """

        payload = {
            "slot_key": slot_key,
            "package_name": package_name,
            "language": language,
            "service_config_code_package_config_id": service_config_code_package_config_id,
            "code_package_id": code_package_id,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="activate_code_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_node_ontology.node.node_config_service_code_package import NodeConfigServiceCodePackage

        if isinstance(value, NodeConfigServiceCodePackage):
            return value
        return NodeConfigServiceCodePackage.validate_invocation_value(value)

    @classmethod
    async def build_via_node_config(cls, node_config_id: UUID, service_name: str) -> NodeConfigServiceTarget:
        """
        Create one Node-owned service target by canonical service name.

        Contract:
        - Parent `NodeConfig` scope is injected by propagation.
        - Identity is keyed by `(node_config_id, service_name)`.
        - The target `ServiceConfig` portal is resolved from `service_name` without storing a raw
          relationship-id attribute as semantic source.
        """

        payload = {"node_config_id": node_config_id, "service_name": service_name}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_node_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NodeConfigServiceTarget):
            return value
        return NodeConfigServiceTarget.validate_invocation_value(value)


class NodeConfigServiceTargetActivateCodePackageInput(BaseModel):
    slot_key: str
    package_name: str
    language: CodeLanguage = Field(default=CodeLanguage.aware)
    service_config_code_package_config_id: UUID | None = Field(default=None)
    code_package_id: UUID | None = Field(default=None)
    description: str | None = Field(default=None)


class NodeConfigServiceTargetActivateCodePackageOutput(BaseModel):
    value: NodeConfigServiceCodePackage


class NodeConfigServiceTargetBuildViaNodeConfigInput(BaseModel):
    node_config_id: UUID = Field(description="Foreign key for NodeConfig.service_targets")
    service_name: str


class NodeConfigServiceTargetBuildViaNodeConfigOutput(BaseModel):
    value: NodeConfigServiceTarget


FUNCTIONS = {
    "NodeConfigServiceTarget": {
        "activate_code_package": {
            "canonical": {
                "name": "activate_code_package",
                "description": "Activate one concrete CodePackage under this service target.\n\nContract:\n- Parent `NodeConfigServiceTarget` scope is injected by propagation.\n- The activation is deployment intent only; the service declaration owns hostable slots.\n- Local-dev sources may name `slot_key` and `package_name` before WorkspaceRevision has\n  resolved package refs. When available, materializers can attach the Service slot and\n  CodePackage relationships.",
                "is_constructor": False,
            },
            "input": NodeConfigServiceTargetActivateCodePackageInput,
            "output": NodeConfigServiceTargetActivateCodePackageOutput,
        },
        "build_via_node_config": {
            "canonical": {
                "name": "build_via_node_config",
                "description": "Create one Node-owned service target by canonical service name.\n\nContract:\n- Parent `NodeConfig` scope is injected by propagation.\n- Identity is keyed by `(node_config_id, service_name)`.\n- The target `ServiceConfig` portal is resolved from `service_name` without storing a raw\n  relationship-id attribute as semantic source.",
                "is_constructor": True,
            },
            "input": NodeConfigServiceTargetBuildViaNodeConfigInput,
            "output": NodeConfigServiceTargetBuildViaNodeConfigOutput,
        },
    },
}

__all__ = [
    "NodeConfigServiceTarget",
    "NodeConfigServiceTargetActivateCodePackageInput",
    "NodeConfigServiceTargetActivateCodePackageOutput",
    "NodeConfigServiceTargetBuildViaNodeConfigInput",
    "NodeConfigServiceTargetBuildViaNodeConfigOutput",
    "FUNCTIONS",
]
