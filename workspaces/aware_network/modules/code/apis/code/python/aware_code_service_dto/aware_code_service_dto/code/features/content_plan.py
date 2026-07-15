from __future__ import annotations

# Standard
from enum import Enum

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Service Dto
from aware_code_service_dto.code.features.package_distribution import CodeLanguage

# Types
from aware_types import JsonObject


class CodeSectionType(Enum):
    """
    Parser-emitted Code content plan DTOs.
    These are transport/materialization-plan values. They are not graph entities
    and do not carry filesystem or Workspace ownership.
    """

    binding = "binding"
    attribute = "attribute"
    class_ = "class"
    comment = "comment"
    decorator = "decorator"
    enum = "enum"
    enum_value = "enum_value"
    expression = "expression"
    function = "function"
    import_ = "import"
    mirror = "mirror"
    annotation = "annotation"
    projection = "projection"
    program = "program"
    event = "event"


class CodeSectionAnnotationPlan(BaseModel):
    """Canonical parser-emitted annotation payload plan."""

    # Attributes
    path: str
    verb: str
    args: list[str] = Field(default_factory=list)


class CodeSegmentPlan(BaseModel):
    """Canonical parser-emitted segment slot plan."""

    # Attributes
    slot_key: str
    byte_start: int
    byte_end: int


class CodeSectionImportNamePlan(BaseModel):
    """Canonical parser-emitted import-name payload plan."""

    # Attributes
    name_text: str
    alias_text: str | None = Field(default=None)
    name_segment_plan: CodeSegmentPlan
    alias_segment_plan: CodeSegmentPlan | None = Field(default=None)


class CodeSectionImportPlan(BaseModel):
    """Canonical parser-emitted import payload plan."""

    # Attributes
    module_text: str
    is_from_import: bool
    is_star_import: bool
    relative_level: int = Field(default=0)
    module_segment_plan: CodeSegmentPlan
    name_plans: list[CodeSectionImportNamePlan] = Field(default_factory=list)


class CodeSectionPlan(BaseModel):
    """Canonical parser-emitted section materialization plan."""

    # Attributes
    section_key: str
    section_type: CodeSectionType
    qualname: str
    identity_hash: str
    byte_start: int
    byte_end: int
    reference: str | None = Field(default=None)
    parent_qualname: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)
    annotation_plan: CodeSectionAnnotationPlan | None = Field(default=None)
    import_plan: CodeSectionImportPlan | None = Field(default=None)


class CodeContentPlan(BaseModel):
    """Canonical code content plan emitted by pure parser/planner rails."""

    # Attributes
    language: CodeLanguage
    content_text: str
    section_plans: list[CodeSectionPlan] = Field(default_factory=list)
