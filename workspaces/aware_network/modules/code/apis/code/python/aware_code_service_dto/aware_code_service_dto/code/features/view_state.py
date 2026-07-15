from __future__ import annotations

# Standard
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


class CodeViewStatePackage(BaseModel):
    """Code-owned package selector item for service view-state resolution."""

    # Attributes
    selector_key: str
    code_package_id: str | None = Field(default=None)
    code_package_name: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    manifest_path: str | None = Field(default=None)
    package_fqn: str | None = Field(default=None)
    provider_key: str | None = Field(default=None)
    language: str | None = Field(default=None)
    surface: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class CodeViewStateCode(BaseModel):
    """Code-owned source selector item for service view-state resolution."""

    # Attributes
    selector_key: str
    code_id: str | None = Field(default=None)
    code_package_code_id: str | None = Field(default=None)
    code_package_id: str | None = Field(default=None)
    code_package_name: str | None = Field(default=None)
    relative_path: str | None = Field(default=None)
    language: str | None = Field(default=None)
    path_role: str | None = Field(default=None)
    source_hash: str | None = Field(default=None)
    label: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class CodeViewStateSourceRef(BaseModel):
    """Code-owned source reference for editor view-state resolution."""

    # Attributes
    source_key: str
    code_id: str | None = Field(default=None)
    code_package_id: str | None = Field(default=None)
    code_package_code_id: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    relative_path: str | None = Field(default=None)
    language: str | None = Field(default=None)
    source_hash: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class CodeViewStateSectionAnchor(BaseModel):
    """Code-owned source section anchor for editor view-state resolution."""

    # Attributes
    section_key: str
    section_kind: str | None = Field(default=None)
    stable_identity: str | None = Field(default=None)
    byte_start: int | None = Field(default=None)
    byte_end: int | None = Field(default=None)
    line_start: int | None = Field(default=None)
    line_end: int | None = Field(default=None)
    label: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class CodePackageSelectorViewStateV1(BaseModel):
    """API-owned package selector view state over committed CodePackage membership."""

    # Attributes
    status: str = Field(default="waiting")
    source_mode: str = Field(default="code_service")
    selected_package_key: str | None = Field(default=None)
    selected_code_key: str | None = Field(default=None)
    packages: list[CodeViewStatePackage] = Field(default_factory=list)
    codes: list[CodeViewStateCode] = Field(default_factory=list)
    summary: str | None = Field(default=None)
    empty_message: str = Field(default="No Code package selected")
    error: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)


class CodeEditorViewStateV1(BaseModel):
    """API-owned source editor view state over selected Code source and anchors."""

    # Attributes
    status: str = Field(default="waiting")
    source_ref: CodeViewStateSourceRef | None = Field(default=None)
    source_text: str | None = Field(default=None)
    selected_section_key: str | None = Field(default=None)
    section_anchors: list[CodeViewStateSectionAnchor] = Field(default_factory=list)
    semantic_events: list[JsonObject] = Field(default_factory=list)
    semantic_deltas: list[JsonObject] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    materialization: JsonObject | None = Field(default=None)
    summary: str | None = Field(default=None)
    empty_message: str = Field(default="No Code source selected")
    error: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)


class ResolveCodePackageSelectorViewRequest(CodeServiceRequest):
    """Resolve Code package selector view data through the Code service read model."""

    # Discriminator Tag
    operation: Literal["resolve_code_package_selector_view"] = "resolve_code_package_selector_view"

    # Attributes
    selected_package_key: str | None = Field(default=None)
    selected_code_key: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodePackageSelectorViewResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_code_package_selector_view"] = "resolve_code_package_selector_view"

    # Attributes
    status: str = Field(default="waiting")
    source_kind: str = Field(default="ontology_replica")
    branch_id: str | None = Field(default=None)
    selected_package_key: str | None = Field(default=None)
    selected_code_key: str | None = Field(default=None)
    packages: list[CodeViewStatePackage] = Field(default_factory=list)
    codes: list[CodeViewStateCode] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    provenance: JsonObject = Field(default_factory=JsonObject)


class ResolveCodeEditorViewRequest(CodeServiceRequest):
    """Resolve Code editor view data through the Code service read model."""

    # Discriminator Tag
    operation: Literal["resolve_code_editor_view"] = "resolve_code_editor_view"

    # Attributes
    selected_package_key: str | None = Field(default=None)
    selected_code_key: str | None = Field(default=None)
    selected_section_key: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class ResolveCodeEditorViewResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_code_editor_view"] = "resolve_code_editor_view"

    # Attributes
    status: str = Field(default="waiting")
    source_kind: str = Field(default="ontology_replica")
    branch_id: str | None = Field(default=None)
    source_ref: CodeViewStateSourceRef | None = Field(default=None)
    source_text: str | None = Field(default=None)
    selected_section_key: str | None = Field(default=None)
    section_anchors: list[CodeViewStateSectionAnchor] = Field(default_factory=list)
    semantic_events: list[JsonObject] = Field(default_factory=list)
    semantic_deltas: list[JsonObject] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    materialization: JsonObject | None = Field(default=None)
    summary: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)


class SelectCodeViewActionRequest(CodeServiceRequest):
    """Select one Code source and request selector/editor view-state refresh."""

    # Discriminator Tag
    operation: Literal["select_code_view_action"] = "select_code_view_action"

    # Attributes
    selected_package_key: str | None = Field(default=None)
    selected_code_key: str
    metadata: JsonObject | None = Field(default=None)


class SelectCodeViewActionResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["select_code_view_action"] = "select_code_view_action"

    # Attributes
    status: str = Field(default="selected")
    selected_package_key: str | None = Field(default=None)
    selected_code_key: str | None = Field(default=None)
    package_selector_view_state: CodePackageSelectorViewStateV1 | None = Field(default=None)
    editor_view_state: CodeEditorViewStateV1 | None = Field(default=None)
    diagnostics: list[str] = Field(default_factory=list)
    provenance: JsonObject = Field(default_factory=JsonObject)


class SelectCodeSectionViewActionRequest(CodeServiceRequest):
    """Select one Code section anchor and request editor view-state refresh."""

    # Discriminator Tag
    operation: Literal["select_code_section_view_action"] = "select_code_section_view_action"

    # Attributes
    selected_package_key: str | None = Field(default=None)
    selected_code_key: str | None = Field(default=None)
    selected_section_key: str
    metadata: JsonObject | None = Field(default=None)


class SelectCodeSectionViewActionResponse(CodeServiceResponse):
    # Discriminator Tag
    operation: Literal["select_code_section_view_action"] = "select_code_section_view_action"

    # Attributes
    status: str = Field(default="selected")
    selected_package_key: str | None = Field(default=None)
    selected_code_key: str | None = Field(default=None)
    selected_section_key: str | None = Field(default=None)
    editor_view_state: CodeEditorViewStateV1 | None = Field(default=None)
    diagnostics: list[str] = Field(default_factory=list)
    provenance: JsonObject = Field(default_factory=JsonObject)
