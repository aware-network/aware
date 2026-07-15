from __future__ import annotations

from dataclasses import dataclass

from aware_code_ontology.code.code_section_enums import CodeSectionType


@dataclass(frozen=True, slots=True)
class AnnotationPlanDescriptor:
    path: str
    verb: str
    args: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SegmentPlanDescriptor:
    slot_key: str
    byte_start: int
    byte_end: int


@dataclass(frozen=True, slots=True)
class ImportNamePlanDescriptor:
    name_text: str
    alias_text: str | None
    name_segment_plan: SegmentPlanDescriptor
    alias_segment_plan: SegmentPlanDescriptor | None = None


@dataclass(frozen=True, slots=True)
class ImportPlanDescriptor:
    module_text: str
    is_from_import: bool
    is_star_import: bool
    relative_level: int
    module_segment_plan: SegmentPlanDescriptor
    name_plans: tuple[ImportNamePlanDescriptor, ...] = ()


@dataclass(frozen=True, slots=True)
class SectionPlanDescriptor:
    section_key: str
    section_type: CodeSectionType
    qualname: str
    identity_hash: str
    byte_start: int
    byte_end: int
    reference: str | None = None
    annotation_plan: AnnotationPlanDescriptor | None = None
    import_plan: ImportPlanDescriptor | None = None
