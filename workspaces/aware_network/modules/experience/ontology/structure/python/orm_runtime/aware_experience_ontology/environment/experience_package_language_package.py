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

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package import CodePackage


class ExperiencePackageLanguagePackage(ORMModel):
    # Relationships
    code_package: CodePackage | None = Field(default=None)

    # Attributes
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    import_root: str
    include_paths: JsonArray = Field(default_factory=JsonArray)
    language: CodeLanguage
    manifest_relative_path: str
    output_key: str = Field(default="experience.language_contract.generated_code_packages")
    package_name: str
    package_root: str = Field(default=".")
    role: str = Field(default="view_model_package")
    sources_root: str | None = Field(default=None)

    # Foreign Keys
    experience_package_id: UUID = Field(description="Foreign key for ExperiencePackage.language_packages")
    code_package_id: UUID = Field(description="Foreign key for ExperiencePackageLanguagePackage.code_package")

    @classmethod
    async def build_via_experience_package(
        cls,
        experience_package_id: UUID,
        code_package_id: UUID,
        package_name: str,
        language: CodeLanguage,
        import_root: str,
        manifest_relative_path: str,
        package_root: str = ".",
        sources_root: str | None = None,
        role: str = "view_model_package",
        output_key: str = "experience.language_contract.generated_code_packages",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
    ) -> ExperiencePackageLanguagePackage:
        """
        Create one Experience-owned generated language package declaration.

        Contract:
        - Parent `ExperiencePackage` scope is injected by propagation.
        - Identity is keyed by the attached generated CodePackage.
        - The payload is the canonical import/install contract for Experience consumers.
        - Consumers must not infer generated Experience packages from local layout or
          `aware.experience.toml` targets alone.
        """

        payload = {
            "experience_package_id": experience_package_id,
            "code_package_id": code_package_id,
            "package_name": package_name,
            "language": language,
            "import_root": import_root,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "role": role,
            "output_key": output_key,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_experience_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperiencePackageLanguagePackage):
            return value
        return ExperiencePackageLanguagePackage.validate_invocation_value(value)


class ExperiencePackageLanguagePackageBuildViaExperiencePackageInput(BaseModel):
    experience_package_id: UUID = Field(description="Foreign key for ExperiencePackage.language_packages")
    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    import_root: str
    manifest_relative_path: str
    package_root: str = Field(default=".")
    sources_root: str | None = Field(default=None)
    role: str = Field(default="view_model_package")
    output_key: str = Field(default="experience.language_contract.generated_code_packages")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)


class ExperiencePackageLanguagePackageBuildViaExperiencePackageOutput(BaseModel):
    value: ExperiencePackageLanguagePackage


FUNCTIONS = {
    "ExperiencePackageLanguagePackage": {
        "build_via_experience_package": {
            "canonical": {
                "name": "build_via_experience_package",
                "description": "Create one Experience-owned generated language package declaration.\n\nContract:\n- Parent `ExperiencePackage` scope is injected by propagation.\n- Identity is keyed by the attached generated CodePackage.\n- The payload is the canonical import/install contract for Experience consumers.\n- Consumers must not infer generated Experience packages from local layout or\n  `aware.experience.toml` targets alone.",
                "is_constructor": True,
            },
            "input": ExperiencePackageLanguagePackageBuildViaExperiencePackageInput,
            "output": ExperiencePackageLanguagePackageBuildViaExperiencePackageOutput,
        },
    },
}

__all__ = [
    "ExperiencePackageLanguagePackage",
    "ExperiencePackageLanguagePackageBuildViaExperiencePackageInput",
    "ExperiencePackageLanguagePackageBuildViaExperiencePackageOutput",
    "FUNCTIONS",
]
