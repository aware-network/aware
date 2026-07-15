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
    from aware_attention_ontology.attention.attention_package import AttentionPackage


class ExperiencePackageAttentionPackage(ORMModel):
    # Relationships
    attention_package: AttentionPackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    experience_package_id: UUID = Field(description="Foreign key for ExperiencePackage.attention_packages")
    attention_package_id: UUID = Field(
        description="Foreign key for ExperiencePackageAttentionPackage.attention_package"
    )

    @classmethod
    async def build_via_experience_package(
        cls, experience_package_id: UUID, attention_package_id: UUID, description: str | None = None
    ) -> ExperiencePackageAttentionPackage:
        """
        Create one package-level Experience dependency bridge to one Attention package.

        Contract:
        - Parent `ExperiencePackage` scope is injected by propagation.
        - Identity is keyed by the attached `AttentionPackage`.
        - This declares that Experience-authored views and section-graph bindings may target
          layout/section topology from the attached Attention package.
        - It does not grant direct Attention mutation authority.
        """

        payload = {
            "experience_package_id": experience_package_id,
            "attention_package_id": attention_package_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_experience_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperiencePackageAttentionPackage):
            return value
        return ExperiencePackageAttentionPackage.validate_invocation_value(value)


class ExperiencePackageAttentionPackageBuildViaExperiencePackageInput(BaseModel):
    experience_package_id: UUID = Field(description="Foreign key for ExperiencePackage.attention_packages")
    attention_package_id: UUID
    description: str | None = Field(default=None)


class ExperiencePackageAttentionPackageBuildViaExperiencePackageOutput(BaseModel):
    value: ExperiencePackageAttentionPackage


FUNCTIONS = {
    "ExperiencePackageAttentionPackage": {
        "build_via_experience_package": {
            "canonical": {
                "name": "build_via_experience_package",
                "description": "Create one package-level Experience dependency bridge to one Attention package.\n\nContract:\n- Parent `ExperiencePackage` scope is injected by propagation.\n- Identity is keyed by the attached `AttentionPackage`.\n- This declares that Experience-authored views and section-graph bindings may target\n  layout/section topology from the attached Attention package.\n- It does not grant direct Attention mutation authority.",
                "is_constructor": True,
            },
            "input": ExperiencePackageAttentionPackageBuildViaExperiencePackageInput,
            "output": ExperiencePackageAttentionPackageBuildViaExperiencePackageOutput,
        },
    },
}

__all__ = [
    "ExperiencePackageAttentionPackage",
    "ExperiencePackageAttentionPackageBuildViaExperiencePackageInput",
    "ExperiencePackageAttentionPackageBuildViaExperiencePackageOutput",
    "FUNCTIONS",
]
