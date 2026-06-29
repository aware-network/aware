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


class ApiPackageLanguagePackage(ORMModel):
    # Relationships
    code_package: CodePackage | None = Field(default=None)

    # Attributes
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    import_root: str
    include_paths: JsonArray = Field(default_factory=JsonArray)
    language: CodeLanguage
    manifest_relative_path: str
    output_key: str = Field(default="python.public_package")
    package_name: str
    package_root: str = Field(default=".")
    role: str = Field(default="public_package")

    # Foreign Keys
    api_package_id: UUID = Field(description="Foreign key for ApiPackage.language_packages")
    code_package_id: UUID = Field(description="Foreign key for ApiPackageLanguagePackage.code_package")

    @classmethod
    async def build_via_api_package(
        cls,
        api_package_id: UUID,
        code_package_id: UUID,
        package_name: str,
        language: CodeLanguage,
        import_root: str,
        manifest_relative_path: str,
        package_root: str = ".",
        role: str = "public_package",
        output_key: str = "python.public_package",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
    ) -> ApiPackageLanguagePackage:
        """
        Create one API-owned generated language package declaration.

        Contract:
        - Parent `ApiPackage` scope is injected by propagation.
        - Identity is keyed by the attached generated CodePackage.
        - The payload is the canonical import/install contract for API consumers.
        - Consumers must not infer API generated packages from local layout or
          `aware.api.toml` target JSON alone.
        """

        payload = {
            "api_package_id": api_package_id,
            "code_package_id": code_package_id,
            "package_name": package_name,
            "language": language,
            "import_root": import_root,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "role": role,
            "output_key": output_key,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_api_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiPackageLanguagePackage):
            return value
        return ApiPackageLanguagePackage.validate_invocation_value(value)


class ApiPackageLanguagePackageBuildViaApiPackageInput(BaseModel):
    api_package_id: UUID = Field(description="Foreign key for ApiPackage.language_packages")
    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    import_root: str
    manifest_relative_path: str
    package_root: str = Field(default=".")
    role: str = Field(default="public_package")
    output_key: str = Field(default="python.public_package")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)


class ApiPackageLanguagePackageBuildViaApiPackageOutput(BaseModel):
    value: ApiPackageLanguagePackage


FUNCTIONS = {
    "ApiPackageLanguagePackage": {
        "build_via_api_package": {
            "canonical": {
                "name": "build_via_api_package",
                "description": "Create one API-owned generated language package declaration.\n\nContract:\n- Parent `ApiPackage` scope is injected by propagation.\n- Identity is keyed by the attached generated CodePackage.\n- The payload is the canonical import/install contract for API consumers.\n- Consumers must not infer API generated packages from local layout or\n  `aware.api.toml` target JSON alone.",
                "is_constructor": True,
            },
            "input": ApiPackageLanguagePackageBuildViaApiPackageInput,
            "output": ApiPackageLanguagePackageBuildViaApiPackageOutput,
        },
    },
}

__all__ = [
    "ApiPackageLanguagePackage",
    "ApiPackageLanguagePackageBuildViaApiPackageInput",
    "ApiPackageLanguagePackageBuildViaApiPackageOutput",
    "FUNCTIONS",
]
