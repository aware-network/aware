from __future__ import annotations

# Standard
from typing import Literal

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Service Dto
from aware_code_service_dto.code.features.package_common import CodePackagePathRole
from aware_code_service_dto.code.service import (
    CodeServiceRequest,
    CodeServiceResponse,
)

# Types
from aware_types import JsonObject


class CodePackageLayoutPathRole(BaseModel):
    """One semantic path-role pattern inside a package layout contract."""

    # Attributes
    role: CodePackagePathRole
    include_patterns: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)
    semantic_owner_hints: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodePackageLayoutContract(BaseModel):
    """API-owned package layout contract used by local FileSystem SDK classification."""

    # Attributes
    package_name: str | None = Field(default=None)
    package_root: str
    sources_root: str | None = Field(default=None)
    surface: str | None = Field(default=None)
    generated_roots: list[str] = Field(default_factory=list)
    manifest_relative_path: str | None = Field(default=None)
    path_roles: list[CodePackageLayoutPathRole] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class DescribeCodePackageLayoutRequest(CodeServiceRequest):
    """Describe one package layout contract by package coordinates."""

    # Discriminator Tag
    operation: Literal["describe_package_layout"] = "describe_package_layout"

    # Attributes
    package_name: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    package_fqn: str | None = Field(default=None)


class DescribeCodePackageLayoutResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["describe_package_layout"] = "describe_package_layout"

    # Attributes
    layout_contract: CodePackageLayoutContract | None = Field(default=None)


class DiscoverCodePackageLayoutsRequest(CodeServiceRequest):
    """Discover package layout contracts from explicit manifest paths."""

    # Discriminator Tag
    operation: Literal["discover_code_package_layouts"] = "discover_code_package_layouts"

    # Attributes
    workspace_root: str = Field(default=".")
    manifest_paths: list[str] = Field(default_factory=list)


class DiscoverCodePackageLayoutsResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["discover_code_package_layouts"] = "discover_code_package_layouts"

    # Attributes
    layout_contracts: list[CodePackageLayoutContract] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)


class ValidateCodePackageLayoutRequest(CodeServiceRequest):
    """Validate path-role/layout truth before local filesystem classification."""

    # Discriminator Tag
    operation: Literal["validate_package_layout"] = "validate_package_layout"

    # Attributes
    layout_contract: CodePackageLayoutContract


class ValidateCodePackageLayoutResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["validate_package_layout"] = "validate_package_layout"

    # Attributes
    valid: bool = Field(default=False)
    diagnostics: list[str] = Field(default_factory=list)
