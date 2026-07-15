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
    from aware_experience_ontology_orm_models.environment.environment_experience import EnvironmentExperience
    from aware_experience_ontology_orm_models.environment.experience_package_api_package import (
        ExperiencePackageApiPackage,
    )
    from aware_experience_ontology_orm_models.environment.experience_package_attention_package import (
        ExperiencePackageAttentionPackage,
    )
    from aware_experience_ontology_orm_models.environment.experience_package_dependency import (
        ExperiencePackageDependency,
    )
    from aware_experience_ontology_orm_models.environment.experience_package_language_package import (
        ExperiencePackageLanguagePackage,
    )
    from aware_experience_ontology_orm_models.environment.experience_package_sdk_package import (
        ExperiencePackageSdkPackage,
    )


class ExperiencePackage(ORMModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    attention_packages: list[ExperiencePackageAttentionPackage] = Field(default_factory=list)
    api_packages: list[ExperiencePackageApiPackage] = Field(default_factory=list)
    environment_experience: EnvironmentExperience | None = Field(default=None)
    experience_package_dependencies: list[ExperiencePackageDependency] = Field(default_factory=list)
    language_packages: list[ExperiencePackageLanguagePackage] = Field(default_factory=list)
    sdk_packages: list[ExperiencePackageSdkPackage] = Field(default_factory=list)

    # Attributes
    name: str

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for ExperiencePackage.source_code_package"
    )
    environment_experience_id: UUID = Field(description="Foreign key for ExperiencePackage.environment_experience")
