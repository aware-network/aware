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
    from aware_attention_ontology.layout.layout_config import LayoutConfig


class AttentionPackageLayoutConfig(ORMModel):
    # Relationships
    layout_config: LayoutConfig | None = Field(default=None)

    # Foreign Keys
    attention_package_id: UUID = Field(description="Foreign key for AttentionPackage.layout_configs")
    layout_config_id: UUID = Field(description="Foreign key for AttentionPackageLayoutConfig.layout_config")

    @classmethod
    async def build_via_attention_package(
        cls, attention_package_id: UUID, layout_config_id: UUID
    ) -> AttentionPackageLayoutConfig:
        """
        Create one package-level Attention bridge to one `LayoutConfig`.

        Contract:
        - Parent `AttentionPackage` scope is injected by propagation.
        - Identity is keyed by the attached `LayoutConfig`.
        - This preserves AttentionPackage as the package/public root while `LayoutConfig` remains
          the canonical topology object.
        """

        payload = {"attention_package_id": attention_package_id, "layout_config_id": layout_config_id}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_attention_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttentionPackageLayoutConfig):
            return value
        return AttentionPackageLayoutConfig.validate_invocation_value(value)


class AttentionPackageLayoutConfigBuildViaAttentionPackageInput(BaseModel):
    attention_package_id: UUID = Field(description="Foreign key for AttentionPackage.layout_configs")
    layout_config_id: UUID


class AttentionPackageLayoutConfigBuildViaAttentionPackageOutput(BaseModel):
    value: AttentionPackageLayoutConfig


FUNCTIONS = {
    "AttentionPackageLayoutConfig": {
        "build_via_attention_package": {
            "canonical": {
                "name": "build_via_attention_package",
                "description": "Create one package-level Attention bridge to one `LayoutConfig`.\n\nContract:\n- Parent `AttentionPackage` scope is injected by propagation.\n- Identity is keyed by the attached `LayoutConfig`.\n- This preserves AttentionPackage as the package/public root while `LayoutConfig` remains\n  the canonical topology object.",
                "is_constructor": True,
            },
            "input": AttentionPackageLayoutConfigBuildViaAttentionPackageInput,
            "output": AttentionPackageLayoutConfigBuildViaAttentionPackageOutput,
        },
    },
}

__all__ = [
    "AttentionPackageLayoutConfig",
    "AttentionPackageLayoutConfigBuildViaAttentionPackageInput",
    "AttentionPackageLayoutConfigBuildViaAttentionPackageOutput",
    "FUNCTIONS",
]
