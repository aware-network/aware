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
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package import CodePackage
    from aware_service_ontology.service.service_config_code_package_config import ServiceConfigCodePackageConfig


class NodeConfigServiceCodePackage(ORMModel):
    # Relationships
    service_config_code_package_config: ServiceConfigCodePackageConfig | None = Field(default=None, exclude=True)
    code_package: CodePackage | None = Field(default=None, exclude=True)

    # Attributes
    slot_key: str
    package_name: str
    language: CodeLanguage = Field(default=CodeLanguage.aware)
    description: str | None = Field(default=None)

    # Foreign Keys
    node_config_service_target_id: UUID = Field(description="Foreign key for NodeConfigServiceTarget.code_packages")
    service_config_code_package_config_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigServiceCodePackage.service_config_code_package_config"
    )
    code_package_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigServiceCodePackage.code_package"
    )

    @classmethod
    async def build_via_node_config_service_target(
        cls,
        node_config_service_target_id: UUID,
        slot_key: str,
        package_name: str,
        language: CodeLanguage = CodeLanguage.aware,
        service_config_code_package_config_id: UUID | None = None,
        code_package_id: UUID | None = None,
        description: str | None = None,
    ) -> NodeConfigServiceCodePackage:
        """
        Create one Node-owned service CodePackage activation.

        Contract:
        - Parent `NodeConfigServiceTarget` scope is injected by propagation.
        - Identity is keyed by `(node_config_service_target_id, slot_key, package_name, language)`.
        - This object is deployment intent. ServiceConfigCodePackageConfig remains capability
          truth; CodePackage remains concrete package truth.
        """

        payload = {
            "node_config_service_target_id": node_config_service_target_id,
            "slot_key": slot_key,
            "package_name": package_name,
            "language": language,
            "service_config_code_package_config_id": service_config_code_package_config_id,
            "code_package_id": code_package_id,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_node_config_service_target", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NodeConfigServiceCodePackage):
            return value
        return NodeConfigServiceCodePackage.validate_invocation_value(value)


class NodeConfigServiceCodePackageBuildViaNodeConfigServiceTargetInput(BaseModel):
    node_config_service_target_id: UUID = Field(description="Foreign key for NodeConfigServiceTarget.code_packages")
    slot_key: str
    package_name: str
    language: CodeLanguage = Field(default=CodeLanguage.aware)
    service_config_code_package_config_id: UUID | None = Field(default=None)
    code_package_id: UUID | None = Field(default=None)
    description: str | None = Field(default=None)


class NodeConfigServiceCodePackageBuildViaNodeConfigServiceTargetOutput(BaseModel):
    value: NodeConfigServiceCodePackage


FUNCTIONS = {
    "NodeConfigServiceCodePackage": {
        "build_via_node_config_service_target": {
            "canonical": {
                "name": "build_via_node_config_service_target",
                "description": "Create one Node-owned service CodePackage activation.\n\nContract:\n- Parent `NodeConfigServiceTarget` scope is injected by propagation.\n- Identity is keyed by `(node_config_service_target_id, slot_key, package_name, language)`.\n- This object is deployment intent. ServiceConfigCodePackageConfig remains capability\n  truth; CodePackage remains concrete package truth.",
                "is_constructor": True,
            },
            "input": NodeConfigServiceCodePackageBuildViaNodeConfigServiceTargetInput,
            "output": NodeConfigServiceCodePackageBuildViaNodeConfigServiceTargetOutput,
        },
    },
}

__all__ = [
    "NodeConfigServiceCodePackage",
    "NodeConfigServiceCodePackageBuildViaNodeConfigServiceTargetInput",
    "NodeConfigServiceCodePackageBuildViaNodeConfigServiceTargetOutput",
    "FUNCTIONS",
]
