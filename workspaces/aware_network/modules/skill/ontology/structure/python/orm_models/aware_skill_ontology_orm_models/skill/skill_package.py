from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.package.code_package import CodePackage
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_skill_ontology_orm_models.skill.skill_config import SkillConfig
    from aware_skill_ontology_orm_models.skill.skill_package_api_package import SkillPackageApiPackage


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
