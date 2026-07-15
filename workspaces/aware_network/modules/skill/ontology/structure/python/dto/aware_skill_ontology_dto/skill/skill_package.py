from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package import CodePackage
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_skill_ontology_dto.skill.skill_config import SkillConfig
    from aware_skill_ontology_dto.skill.skill_package_api_package import SkillPackageApiPackage


class SkillPackage(BaseModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    api_packages: list[SkillPackageApiPackage] = Field(default_factory=list)
    skill_config: SkillConfig | None = Field(default=None)
    skill_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    name: str
