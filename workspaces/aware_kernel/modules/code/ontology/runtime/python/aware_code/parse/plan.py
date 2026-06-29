from __future__ import annotations

from aware_code.parse.models import SectionPlanDescriptor
from aware_code.parse.sections import collect_top_level_section_identity_descriptors
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodeContentPlan,
    CodeSectionAnnotationPlan,
    CodeSectionImportNamePlan,
    CodeSectionImportPlan,
    CodeSectionPlan,
    CodeSegmentPlan,
)
from aware_code_ontology.code.code_section_enums import CodeSectionType


def _to_section_plan(
    descriptor: SectionPlanDescriptor,
) -> CodeSectionPlan:
    annotation_plan = descriptor.annotation_plan
    import_plan = descriptor.import_plan
    return CodeSectionPlan(
        section_key=descriptor.section_key,
        section_type=descriptor.section_type,
        qualname=descriptor.qualname,
        identity_hash=descriptor.identity_hash,
        byte_start=descriptor.byte_start,
        byte_end=descriptor.byte_end,
        reference=descriptor.reference,
        annotation_plan=(
            CodeSectionAnnotationPlan(
                path=annotation_plan.path,
                verb=annotation_plan.verb,
                args=list(annotation_plan.args),
            )
            if annotation_plan is not None
            else None
        ),
        import_plan=(
            CodeSectionImportPlan(
                module_text=import_plan.module_text,
                is_from_import=import_plan.is_from_import,
                is_star_import=import_plan.is_star_import,
                relative_level=import_plan.relative_level,
                module_segment_plan=CodeSegmentPlan(
                    slot_key=import_plan.module_segment_plan.slot_key,
                    byte_start=import_plan.module_segment_plan.byte_start,
                    byte_end=import_plan.module_segment_plan.byte_end,
                ),
                name_plans=[
                    CodeSectionImportNamePlan(
                        name_text=name_plan.name_text,
                        alias_text=name_plan.alias_text,
                        name_segment_plan=CodeSegmentPlan(
                            slot_key=name_plan.name_segment_plan.slot_key,
                            byte_start=name_plan.name_segment_plan.byte_start,
                            byte_end=name_plan.name_segment_plan.byte_end,
                        ),
                        alias_segment_plan=(
                            CodeSegmentPlan(
                                slot_key=name_plan.alias_segment_plan.slot_key,
                                byte_start=name_plan.alias_segment_plan.byte_start,
                                byte_end=name_plan.alias_segment_plan.byte_end,
                            )
                            if name_plan.alias_segment_plan is not None
                            else None
                        ),
                    )
                    for name_plan in import_plan.name_plans
                ],
            )
            if import_plan is not None
            else None
        ),
    )


def build_code_content_plan(
    *,
    content: str,
    language: CodeLanguage,
) -> CodeContentPlan:
    descriptors = collect_top_level_section_identity_descriptors(
        content=content,
        language=language,
    )
    return CodeContentPlan(
        language=language,
        content_text=content,
        section_plans=[
            _to_section_plan(descriptor) for descriptor in descriptors
        ],
    )
