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


class SdkPackageImplementationPackage(ORMModel):
    # Relationships
    code_package: CodePackage | None = Field(default=None)

    # Attributes
    entrypoint: str | None = Field(default=None)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    import_root: str
    include_paths: JsonArray = Field(default_factory=JsonArray)
    language: CodeLanguage
    manifest_relative_path: str
    package_name: str
    package_root: str = Field(default=".")
    role: str = Field(default="public_package")

    # Foreign Keys
    sdk_package_id: UUID = Field(description="Foreign key for SdkPackage.implementation_packages")
    code_package_id: UUID = Field(description="Foreign key for SdkPackageImplementationPackage.code_package")

    @classmethod
    async def build_via_sdk_package(
        cls,
        sdk_package_id: UUID,
        code_package_id: UUID,
        package_name: str,
        language: CodeLanguage,
        import_root: str,
        manifest_relative_path: str,
        package_root: str = ".",
        entrypoint: str | None = None,
        role: str = "public_package",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
    ) -> SdkPackageImplementationPackage:
        """
        Create one SDK-owned language implementation package declaration.

        Contract:
        - Parent `SdkPackage` scope is injected by propagation.
        - Identity is keyed by the attached implementation `CodePackage`.
        - The payload is the canonical import/install contract for SDK consumers.
        - Consumers must not infer SDK implementation packages from local layout or target JSON alone.
        """

        payload = {
            "sdk_package_id": sdk_package_id,
            "code_package_id": code_package_id,
            "package_name": package_name,
            "language": language,
            "import_root": import_root,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "entrypoint": entrypoint,
            "role": role,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_sdk_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SdkPackageImplementationPackage):
            return value
        return SdkPackageImplementationPackage.validate_invocation_value(value)


class SdkPackageImplementationPackageBuildViaSdkPackageInput(BaseModel):
    sdk_package_id: UUID = Field(description="Foreign key for SdkPackage.implementation_packages")
    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    import_root: str
    manifest_relative_path: str
    package_root: str = Field(default=".")
    entrypoint: str | None = Field(default=None)
    role: str = Field(default="public_package")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)


class SdkPackageImplementationPackageBuildViaSdkPackageOutput(BaseModel):
    value: SdkPackageImplementationPackage


FUNCTIONS = {
    "SdkPackageImplementationPackage": {
        "build_via_sdk_package": {
            "canonical": {
                "name": "build_via_sdk_package",
                "description": "Create one SDK-owned language implementation package declaration.\n\nContract:\n- Parent `SdkPackage` scope is injected by propagation.\n- Identity is keyed by the attached implementation `CodePackage`.\n- The payload is the canonical import/install contract for SDK consumers.\n- Consumers must not infer SDK implementation packages from local layout or target JSON alone.",
                "is_constructor": True,
            },
            "input": SdkPackageImplementationPackageBuildViaSdkPackageInput,
            "output": SdkPackageImplementationPackageBuildViaSdkPackageOutput,
        },
    },
}

__all__ = [
    "SdkPackageImplementationPackage",
    "SdkPackageImplementationPackageBuildViaSdkPackageInput",
    "SdkPackageImplementationPackageBuildViaSdkPackageOutput",
    "FUNCTIONS",
]
