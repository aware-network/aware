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
    from aware_experience_ontology_dto.environment.environment_experience import EnvironmentExperience
    from aware_experience_ontology_dto.environment.experience_package_api_package import ExperiencePackageApiPackage
    from aware_experience_ontology_dto.environment.experience_package_attention_package import (
        ExperiencePackageAttentionPackage,
    )
    from aware_experience_ontology_dto.environment.experience_package_dependency import ExperiencePackageDependency
    from aware_experience_ontology_dto.environment.experience_package_language_package import (
        ExperiencePackageLanguagePackage,
    )
    from aware_experience_ontology_dto.environment.experience_package_sdk_package import ExperiencePackageSdkPackage


class ExperiencePackage(BaseModel):
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
