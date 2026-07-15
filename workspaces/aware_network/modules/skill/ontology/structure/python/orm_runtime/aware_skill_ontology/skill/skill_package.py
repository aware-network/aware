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
    from aware_code_ontology.package.code_package import CodePackage
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_skill_ontology.skill.skill_config import SkillConfig
    from aware_skill_ontology.skill.skill_package_api_package import SkillPackageApiPackage


class SkillPackage(ORMModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    api_packages: list[SkillPackageApiPackage] = Field(default_factory=list)
    skill_config: SkillConfig | None = Field(default=None)
    skill_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    name: str

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for SkillPackage.source_code_package"
    )
    skill_config_id: UUID = Field(description="Foreign key for SkillPackage.skill_config")
    skill_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for SkillPackage.skill_config_object_instance_graph_commit"
    )

    @classmethod
    async def build(
        cls,
        name: str,
        skill_config_id: UUID,
        skill_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
    ) -> SkillPackage:
        """
        Create the canonical Skill-owned package root over an existing `SkillConfig`.

        Contract:
        - Identity is keyed by Skill package `name`.
        - `SkillPackage` is the package/public root over an existing canonical `SkillConfig`.
        - `skill_config_id` must point at the canonical SkillConfig stable id for this package root.
        - `skill_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit
          for the semantic SkillConfig root so package consumers can replay exact skill truth without
          resolving branch head or reopening authoring TOML.
        - `source_code_package_id` is explicit raw-source provenance for this semantic leaf package.
        - Workspace will later mount `SkillPackage`, not raw `SkillConfig`.
        """

        payload = {
            "name": name,
            "skill_config_id": skill_config_id,
            "skill_config_object_instance_graph_commit_id": skill_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SkillPackage):
            return value
        return SkillPackage.validate_invocation_value(value)

    async def attach_api_package(self, api_package_id: UUID, description: str | None = None) -> SkillPackageApiPackage:
        """
        Attach one API package to this SkillPackage.

        Contract:
        - This is the package/import rail for authored Skill source.
        - It declares which API packages are available to this Skill package.
        - Config/runtime semantic API use remains a separate `SkillConfig -> Api` and
          `SkillConfigApiEndpoint -> ApiCapabilityEndpoint` bridge.
        """

        payload = {"api_package_id": api_package_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="attach_api_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_skill_ontology.skill.skill_package_api_package import SkillPackageApiPackage

        if isinstance(value, SkillPackageApiPackage):
            return value
        return SkillPackageApiPackage.validate_invocation_value(value)


class SkillPackageBuildInput(BaseModel):
    name: str
    skill_config_id: UUID
    skill_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)


class SkillPackageBuildOutput(BaseModel):
    value: SkillPackage


class SkillPackageAttachApiPackageInput(BaseModel):
    api_package_id: UUID
    description: str | None = Field(default=None)


class SkillPackageAttachApiPackageOutput(BaseModel):
    value: SkillPackageApiPackage


FUNCTIONS = {
    "SkillPackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical Skill-owned package root over an existing `SkillConfig`.\n\nContract:\n- Identity is keyed by Skill package `name`.\n- `SkillPackage` is the package/public root over an existing canonical `SkillConfig`.\n- `skill_config_id` must point at the canonical SkillConfig stable id for this package root.\n- `skill_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit\n  for the semantic SkillConfig root so package consumers can replay exact skill truth without\n  resolving branch head or reopening authoring TOML.\n- `source_code_package_id` is explicit raw-source provenance for this semantic leaf package.\n- Workspace will later mount `SkillPackage`, not raw `SkillConfig`.",
                "is_constructor": True,
            },
            "input": SkillPackageBuildInput,
            "output": SkillPackageBuildOutput,
        },
        "attach_api_package": {
            "canonical": {
                "name": "attach_api_package",
                "description": "Attach one API package to this SkillPackage.\n\nContract:\n- This is the package/import rail for authored Skill source.\n- It declares which API packages are available to this Skill package.\n- Config/runtime semantic API use remains a separate `SkillConfig -> Api` and\n  `SkillConfigApiEndpoint -> ApiCapabilityEndpoint` bridge.",
                "is_constructor": False,
            },
            "input": SkillPackageAttachApiPackageInput,
            "output": SkillPackageAttachApiPackageOutput,
        },
    },
}

__all__ = [
    "SkillPackage",
    "SkillPackageBuildInput",
    "SkillPackageBuildOutput",
    "SkillPackageAttachApiPackageInput",
    "SkillPackageAttachApiPackageOutput",
    "FUNCTIONS",
]
