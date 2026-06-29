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
    from aware_code_ontology_dto.package.code_package_config_input import CodePackageConfigInput
    from aware_code_ontology_dto.package.code_package_config_output import CodePackageConfigOutput
    from aware_code_ontology_dto.package.code_package_config_runtime_context import CodePackageConfigRuntimeContext


class CodePackageConfig(BaseModel):
    # Relationships
    packages: list[CodePackage] = Field(default_factory=list)
    inputs: list[CodePackageConfigInput] = Field(default_factory=list)
    outputs: list[CodePackageConfigOutput] = Field(default_factory=list)
    runtime_contexts: list[CodePackageConfigRuntimeContext] = Field(default_factory=list)

    # Attributes
    config_key: str
    provider_key: str
    semantic_owner: str
    contract: str
    package_role: str | None = Field(default=None)
    manifest_kind: str
    manifest_filename: str
    semantic_package_family: str | None = Field(default=None)
    semantic_package_kind: str | None = Field(default=None)
    semantic_projection_name: str | None = Field(default=None)
    semantic_root_kind: str | None = Field(default=None)
    default_surface: str | None = Field(default=None)
    materialization_capability: str | None = Field(default=None)
