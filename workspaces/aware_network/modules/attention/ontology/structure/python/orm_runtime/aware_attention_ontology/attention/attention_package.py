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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_attention_ontology.attention.attention_package_layout_config import AttentionPackageLayoutConfig
    from aware_code_ontology.package.code_package import CodePackage


class AttentionPackage(ORMModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    layout_configs: list[AttentionPackageLayoutConfig] = Field(default_factory=list)

    # Attributes
    name: str

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionPackage.source_code_package"
    )

    @classmethod
    async def build(cls, name: str, source_code_package_id: UUID | None = None) -> AttentionPackage:
        """
        Create the canonical Attention-owned semantic package root.

        Contract:
        - Identity is keyed by Attention package `name`.
        - `AttentionPackage` is the package/public root over authored layout topology owned by one
          `aware.attention.toml` package.
        - `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf
          package.
        - Workspace and later Interface/workflow rails should mount `AttentionPackage`, not raw
          `LayoutConfig` objects.
        """

        payload = {"name": name, "source_code_package_id": source_code_package_id}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttentionPackage):
            return value
        return AttentionPackage.validate_invocation_value(value)

    async def attach_layout_config(self, layout_config_id: UUID) -> AttentionPackageLayoutConfig:
        """
        Attach one canonical `LayoutConfig` under this Attention package root.

        Contract:
        - Parent `AttentionPackage` scope is injected by propagation.
        - Identity is keyed by the attached `LayoutConfig`.
        - One Attention package may own multiple layouts without collapsing package truth and layout
          topology into one object.
        """

        payload = {"layout_config_id": layout_config_id}
        result = await invoke_instance(orm_model=self, function_name="attach_layout_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.attention.attention_package_layout_config import AttentionPackageLayoutConfig

        if isinstance(value, AttentionPackageLayoutConfig):
            return value
        return AttentionPackageLayoutConfig.validate_invocation_value(value)


class AttentionPackageBuildInput(BaseModel):
    name: str
    source_code_package_id: UUID | None = Field(default=None)


class AttentionPackageBuildOutput(BaseModel):
    value: AttentionPackage


class AttentionPackageAttachLayoutConfigInput(BaseModel):
    layout_config_id: UUID


class AttentionPackageAttachLayoutConfigOutput(BaseModel):
    value: AttentionPackageLayoutConfig


FUNCTIONS = {
    "AttentionPackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical Attention-owned semantic package root.\n\nContract:\n- Identity is keyed by Attention package `name`.\n- `AttentionPackage` is the package/public root over authored layout topology owned by one\n  `aware.attention.toml` package.\n- `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf\n  package.\n- Workspace and later Interface/workflow rails should mount `AttentionPackage`, not raw\n  `LayoutConfig` objects.",
                "is_constructor": True,
            },
            "input": AttentionPackageBuildInput,
            "output": AttentionPackageBuildOutput,
        },
        "attach_layout_config": {
            "canonical": {
                "name": "attach_layout_config",
                "description": "Attach one canonical `LayoutConfig` under this Attention package root.\n\nContract:\n- Parent `AttentionPackage` scope is injected by propagation.\n- Identity is keyed by the attached `LayoutConfig`.\n- One Attention package may own multiple layouts without collapsing package truth and layout\n  topology into one object.",
                "is_constructor": False,
            },
            "input": AttentionPackageAttachLayoutConfigInput,
            "output": AttentionPackageAttachLayoutConfigOutput,
        },
    },
}

__all__ = [
    "AttentionPackage",
    "AttentionPackageBuildInput",
    "AttentionPackageBuildOutput",
    "AttentionPackageAttachLayoutConfigInput",
    "AttentionPackageAttachLayoutConfigOutput",
    "FUNCTIONS",
]
