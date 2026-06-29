from __future__ import annotations

# Standard
from enum import Enum
from typing import Literal

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Service Dto
from aware_code_service_dto.code.service import (
    CodeServiceRequest,
    CodeServiceResponse,
)

# Types
from aware_types import JsonObject


class CodeSourceOwnershipClassification(Enum):
    """Code-owned classification for observed source paths."""

    source_owned = "source_owned"
    generated_fallout = "generated_fallout"
    unmapped = "unmapped"


class CodeSourceOwnershipPackageBinding(BaseModel):
    """One package boundary accepted by the Code source_ownership capability."""

    # Attributes
    package_name: str
    package_root: str
    sources_root: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    language: str | None = Field(default=None)
    surface: str | None = Field(default=None)
    manifest_kind: str | None = Field(default=None)
    generated_roots: list[str] = Field(default_factory=list)
    owned_file_paths: list[str] = Field(default_factory=list)
    metadata: JsonObject | None = Field(default=None)


class CodeSourceOwnershipObservedPath(BaseModel):
    """One observed workspace-relative path to classify against package bindings."""

    # Attributes
    path: str
    language: str | None = Field(default=None)
    is_structural: bool | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSourceOwnershipPathMatch(BaseModel):
    """Code-owned classification result for one observed path."""

    # Attributes
    path: str
    classification: CodeSourceOwnershipClassification
    package_name: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    sources_root: str | None = Field(default=None)
    package_relative_path: str | None = Field(default=None)
    binding_index: int | None = Field(default=None)
    language: str | None = Field(default=None)
    is_structural: bool | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class CodeSourceOwnershipRequest(BaseModel):
    """Request envelope for Code-owned source ownership classification."""

    # Attributes
    workspace_root: str | None = Field(default=None)
    package_bindings: list[CodeSourceOwnershipPackageBinding] = Field(default_factory=list)
    observed_paths: list[CodeSourceOwnershipObservedPath] = Field(default_factory=list)
    strict: bool = Field(default=True)
    metadata: JsonObject | None = Field(default=None)


class CodeSourceOwnershipResult(BaseModel):
    """Result envelope for Code-owned source ownership classification."""

    # Attributes
    matches: list[CodeSourceOwnershipPathMatch] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    package_count: int = Field(default=0)
    path_count: int = Field(default=0)
    source_owned_path_count: int = Field(default=0)
    generated_fallout_path_count: int = Field(default=0)
    unmapped_path_count: int = Field(default=0)
    metadata: JsonObject | None = Field(default=None)


class ClassifyCodeSourceOwnershipRequest(CodeServiceRequest):
    """Classify observed paths through Code-owned package boundary rules."""

    # Discriminator Tag
    operation: Literal["classify_source_ownership"] = "classify_source_ownership"

    # Attributes
    ownership_request: CodeSourceOwnershipRequest


class ClassifyCodeSourceOwnershipResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["classify_source_ownership"] = "classify_source_ownership"

    # Attributes
    ownership_result: CodeSourceOwnershipResult | None = Field(default=None)
