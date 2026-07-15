from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Code Ontology
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.comment.code_section_comment_enums import CodeSectionCommentType
from aware_code_ontology.expression.code_section_expression_enums import CodeSectionExpressionType
from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation
from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_code_ontology.binding.code_section_binding import CodeSectionBinding
from aware_code_ontology.class_.code_section_class import CodeSectionClass
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.comment.code_section_comment import CodeSectionComment
from aware_code_ontology.decorator.code_section_decorator import CodeSectionDecorator
from aware_code_ontology.enum.code_section_enum import CodeSectionEnum
from aware_code_ontology.enum.code_section_enum_value import CodeSectionEnumValue
from aware_code_ontology.expression.code_section_expression import CodeSectionExpression
from aware_code_ontology.function.code_section_function import CodeSectionFunction
from aware_code_ontology.import_.code_section_import import CodeSectionImport
from aware_code_ontology.mirror.code_section_mirror import CodeSectionMirror
from aware_code_ontology.projection.code_section_projection import CodeSectionProjection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code_ontology.code.code import Code
from aware_code_ontology.stable_ids import stable_code_section_id
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_content_ontology.part.content_part_text_editor_patch import (
    ContentPartTextEditorPatch,
    ContentPartTextSegmentDetach,
    ContentPartTextSegmentOp,
    ContentPartTextSegmentUpsert,
)
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_content_ontology.stable_ids import stable_content_part_text_segment_id
from aware_orm.session.change_collector import current_change_collector
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def delete(code_section: CodeSection) -> None:
    """
    Delete this CodeSection through its owned handler rail.
    """

    # --- AWARE: LOGIC START delete
    collector = current_change_collector()
    if collector is None:
        raise RuntimeError("CodeSection.delete requires an active runtime change collector")

    session = current_handler_session()
    segment = code_section.content_part_text_segment
    content_part_text = None
    if segment is not None and segment.content_part_text_id is not None:
        content_part_text = session.imap_get(
            ContentPartText,
            segment.content_part_text_id,
        )
    if segment is not None and content_part_text is None:
        raise RuntimeError(
            "CodeSection.delete requires ContentPartText in the identity map: "
            f"content_part_text_id={segment.content_part_text_id}"
        )

    annotation_payload = code_section.code_section_annotation
    if annotation_payload is not None:
        await annotation_payload.delete()
        code_section.code_section_annotation = None

    unsupported_payloads = [
        payload_name
        for payload_name, payload_value in (
            ("code_section_attribute", code_section.code_section_attribute),
            ("code_section_binding", code_section.code_section_binding),
            ("code_section_class", code_section.code_section_class),
            ("code_section_comment", code_section.code_section_comment),
            ("code_section_decorator", code_section.code_section_decorator),
            ("code_section_enum", code_section.code_section_enum),
            ("code_section_enum_value", code_section.code_section_enum_value),
            ("code_section_expression", code_section.code_section_expression),
            ("code_section_function", code_section.code_section_function),
            ("code_section_mirror", code_section.code_section_mirror),
            ("code_section_projection", code_section.code_section_projection),
        )
        if payload_value is not None
    ]
    if unsupported_payloads:
        raise RuntimeError(
            "CodeSection.delete currently supports top-level annotation sections plus import payload cleanup only: "
            f"code_section_id={code_section.id} unsupported_payloads={unsupported_payloads!r}"
        )

    import_payload = code_section.code_section_import
    if import_payload is not None:
        if content_part_text is None:
            raise RuntimeError(
                "CodeSection.delete requires ContentPartText before import payload cleanup: "
                f"code_section_id={code_section.id}"
            )
        segment_ids_to_detach: list[UUID] = []
        if import_payload.module_segment_id is not None:
            segment_ids_to_detach.append(import_payload.module_segment_id)
        for import_name in list(import_payload.code_section_import_names):
            if import_name.name_segment_id is not None:
                segment_ids_to_detach.append(import_name.name_segment_id)
            if import_name.alias_segment_id is not None:
                segment_ids_to_detach.append(import_name.alias_segment_id)
        if segment_ids_to_detach:
            await content_part_text.apply_editor_patch(
                patch=ContentPartTextEditorPatch(
                    segment_ops=[
                        ContentPartTextSegmentOp(
                            detach=ContentPartTextSegmentDetach(
                                segment_id=segment_id,
                            )
                        )
                        for segment_id in segment_ids_to_detach
                    ]
                )
            )
        await import_payload.delete()
        code_section.code_section_import = None

    if segment is not None and content_part_text is not None:
        await content_part_text.apply_editor_patch(
            patch=ContentPartTextEditorPatch(
                segment_ops=[
                    ContentPartTextSegmentOp(
                        detach=ContentPartTextSegmentDetach(
                            segment_id=segment.id,
                        )
                    )
                ]
            )
        )

    collector.record_delete(code_section)

    bound_session = code_section.bound_session
    if bound_session is not None:
        bound_session.imap_remove(type(code_section), code_section.id)
    # --- AWARE: LOGIC END delete


async def create_annotation(code_section: CodeSection, path: str, verb: str, args: list[str]) -> CodeSectionAnnotation:
    """
    Create the annotation payload for this section.
    """

    # --- AWARE: LOGIC START create_annotation
    if code_section.id is None:
        raise RuntimeError("CodeSection.create_annotation requires code section id")

    created = await CodeSectionAnnotation.build_via_code_section(
        code_section_id=code_section.id,
        path=path,
        verb=verb,
        args=args,
    )
    existing = code_section.code_section_annotation
    if existing is not None:
        if existing.id != created.id or existing.path != path or existing.verb != verb or existing.args != args:
            raise RuntimeError(
                "CodeSection.create_annotation payload mismatch for existing annotation: "
                f"code_section_id={code_section.id}"
            )
        return existing

    code_section.code_section_annotation = created
    return created
    # --- AWARE: LOGIC END create_annotation


async def create_attribute(code_section: CodeSection) -> CodeSectionAttribute:
    """
    Create the attribute payload for this section.
    """

    # --- AWARE: LOGIC START create_attribute
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_attribute


async def create_binding(code_section: CodeSection) -> CodeSectionBinding:
    """
    Create the binding payload for this section.
    """

    # --- AWARE: LOGIC START create_binding
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_binding


async def create_class(code_section: CodeSection) -> CodeSectionClass:
    """
    Create the class payload for this section.
    """

    # --- AWARE: LOGIC START create_class
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_class


async def create_comment(code_section: CodeSection, type: CodeSectionCommentType) -> CodeSectionComment:
    """
    Create the comment payload for this section.
    """

    # --- AWARE: LOGIC START create_comment
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_comment


async def create_decorator(code_section: CodeSection) -> CodeSectionDecorator:
    """
    Create the decorator payload for this section.
    """

    # --- AWARE: LOGIC START create_decorator
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_decorator


async def create_enum(code_section: CodeSection) -> CodeSectionEnum:
    """
    Create the enum payload for this section.
    """

    # --- AWARE: LOGIC START create_enum
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_enum


async def create_enum_value(code_section: CodeSection, value: str, position: int = 0) -> CodeSectionEnumValue:
    """
    Create the enum-value payload for this section.
    """

    # --- AWARE: LOGIC START create_enum_value
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_enum_value


async def create_expression(code_section: CodeSection, type: CodeSectionExpressionType) -> CodeSectionExpression:
    """
    Create the expression payload for this section.
    """

    # --- AWARE: LOGIC START create_expression
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_expression


async def create_function(code_section: CodeSection) -> CodeSectionFunction:
    """
    Create the function payload for this section.
    """

    # --- AWARE: LOGIC START create_function
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_function


async def create_import(
    code_section: CodeSection,
    module_text: str,
    is_from_import: bool,
    module_slot_key: str,
    module_byte_start: int,
    module_byte_end: int,
    is_star_import: bool = False,
    relative_level: int = 0,
) -> CodeSectionImport:
    """
    Create the import payload for this section.
    """

    # --- AWARE: LOGIC START create_import
    if code_section.id is None:
        raise RuntimeError("CodeSection.create_import requires code section id")

    created = await CodeSectionImport.build_via_code_section(
        code_section_id=code_section.id,
        module_text=module_text,
        is_from_import=is_from_import,
        is_star_import=is_star_import,
        relative_level=relative_level,
        module_slot_key=module_slot_key,
        module_byte_start=module_byte_start,
        module_byte_end=module_byte_end,
    )
    existing = code_section.code_section_import
    if existing is not None:
        if (
            existing.id != created.id
            or existing.module_text != module_text
            or existing.is_from_import != is_from_import
            or existing.is_star_import != is_star_import
            or existing.relative_level != relative_level
        ):
            raise RuntimeError(
                "CodeSection.create_import payload mismatch for existing import payload: "
                f"code_section_id={code_section.id}"
            )
        return existing

    code_section.code_section_import = created
    return created
    # --- AWARE: LOGIC END create_import


async def create_mirror(code_section: CodeSection) -> CodeSectionMirror:
    """
    Create the mirror payload for this section.
    """

    # --- AWARE: LOGIC START create_mirror
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_mirror


async def create_projection(code_section: CodeSection) -> CodeSectionProjection:
    """
    Create the projection payload for this section.
    """

    # --- AWARE: LOGIC START create_projection
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_projection


async def build_via_code(
    code_id: UUID,
    section_key: str,
    qualname: str,
    type: CodeSectionType,
    identity_hash: str,
    byte_start: int,
    byte_end: int,
    metadata: JsonObject | None = None,
) -> CodeSection:
    """
    Build a deterministic CodeSection under a Code snapshot.
    """

    # --- AWARE: LOGIC START build_via_code
    session = current_handler_session()
    code = session.imap_get(Code, code_id)
    if code is None:
        raise RuntimeError(
            "CodeSection.build_via_code requires existing Code in the identity map: " f"code_id={code_id}"
        )
    if code.content_part_text is None or code.content_part_text.id is None:
        raise RuntimeError(
            "CodeSection.build_via_code requires Code.content_part_text before section materialization: "
            f"code_id={code_id}"
        )

    code_section_id = stable_code_section_id(
        code_id=code_id,
        section_key=section_key,
        type=type.value,
    )
    segment_id = stable_content_part_text_segment_id(
        content_part_text_id=code.content_part_text.id,
        key=f"code-section:{code_section_id}",
    )
    existing = session.imap_get(CodeSection, code_section_id)
    if existing is not None:
        segment = existing.content_part_text_segment
        if (
            existing.code_id != code_id
            or existing.section_key != section_key
            or existing.qualname != qualname
            or existing.type != type
            or existing.identity_hash != identity_hash
            or existing.metadata != metadata
            or segment is None
            or existing.content_part_text_segment_id != segment_id
            or segment.byte_start != byte_start
            or segment.byte_end != byte_end
        ):
            raise RuntimeError(
                "CodeSection.build_via_code payload mismatch for existing section: "
                f"code_section_id={code_section_id}"
            )
        return existing

    await code.content_part_text.apply_editor_patch(
        patch=ContentPartTextEditorPatch(
            segment_ops=[
                ContentPartTextSegmentOp(
                    upsert=ContentPartTextSegmentUpsert(
                        segment_id=segment_id,
                        byte_start=byte_start,
                        byte_end=byte_end,
                    )
                )
            ]
        )
    )
    content_part_text_segment = session.imap_get(ContentPartTextSegment, segment_id)
    if content_part_text_segment is None:
        raise RuntimeError(
            "CodeSection.build_via_code expected ContentPartText.apply_editor_patch to materialize the segment: "
            f"segment_id={segment_id}"
        )

    created = CodeSection(
        id=code_section_id,
        code_id=code_id,
        section_key=section_key,
        qualname=qualname,
        type=type,
        identity_hash=identity_hash,
        metadata=metadata,
        content_part_text_segment=content_part_text_segment,
        content_part_text_segment_id=content_part_text_segment.id,
    )
    if created.bound_session is None:
        created.bind_to_session(session)

    return created
    # --- AWARE: LOGIC END build_via_code
