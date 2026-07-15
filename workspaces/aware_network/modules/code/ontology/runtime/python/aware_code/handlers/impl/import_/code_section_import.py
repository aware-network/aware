from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.import_.code_section_import import CodeSectionImport
from aware_code_ontology.import_.code_section_import_name import CodeSectionImportName

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.stable_ids import stable_code_section_import_id
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_content_ontology.part.content_part_text_editor_patch import (
    ContentPartTextEditorPatch,
    ContentPartTextSegmentOp,
    ContentPartTextSegmentUpsert,
)
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_content_ontology.stable_ids import stable_content_part_text_segment_id
from aware_orm.session.change_collector import current_change_collector
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def delete(code_section_import: CodeSectionImport) -> None:
    """
    Delete this import payload and its owned import-name entries through the owned handler rail.
    """

    # --- AWARE: LOGIC START delete
    collector = current_change_collector()
    if collector is None:
        raise RuntimeError("CodeSectionImport.delete requires an active runtime change collector")

    for existing_name in list(code_section_import.code_section_import_names):
        await existing_name.delete()
    if code_section_import.code_section_import_names:
        code_section_import.code_section_import_names[:] = []

    collector.record_delete(code_section_import)
    bound_session = code_section_import.bound_session
    if bound_session is not None:
        bound_session.imap_remove(type(code_section_import), code_section_import.id)
    # --- AWARE: LOGIC END delete


async def create_name(
    code_section_import: CodeSectionImport,
    name_text: str,
    name_slot_key: str,
    name_byte_start: int,
    name_byte_end: int,
    alias_text: str | None = None,
    alias_slot_key: str | None = None,
    alias_byte_start: int | None = None,
    alias_byte_end: int | None = None,
) -> CodeSectionImportName:
    """
    Create a deterministic import-name entry under this import.
    """

    # --- AWARE: LOGIC START create_name
    if code_section_import.id is None:
        raise RuntimeError("CodeSectionImport.create_name requires import payload id")

    created = await CodeSectionImportName.build_via_code_section_import(
        code_section_import_id=code_section_import.id,
        name_text=name_text,
        alias_text=alias_text,
        name_slot_key=name_slot_key,
        name_byte_start=name_byte_start,
        name_byte_end=name_byte_end,
        alias_slot_key=alias_slot_key,
        alias_byte_start=alias_byte_start,
        alias_byte_end=alias_byte_end,
    )
    for existing in code_section_import.code_section_import_names:
        if existing.id != created.id:
            continue
        if existing.name_text != name_text or existing.alias_text != alias_text:
            raise RuntimeError(
                "CodeSectionImport.create_name payload mismatch for existing import name: "
                f"code_section_import_name_id={created.id}"
            )
        return existing

    code_section_import.code_section_import_names.append(created)
    return created
    # --- AWARE: LOGIC END create_name


async def build_via_code_section(
    code_section_id: UUID,
    module_text: str,
    is_from_import: bool,
    module_slot_key: str,
    module_byte_start: int,
    module_byte_end: int,
    is_star_import: bool = False,
    relative_level: int = 0,
) -> CodeSectionImport:
    """
    Build the import payload under a CodeSection.
    """

    # --- AWARE: LOGIC START build_via_code_section
    module_text_clean = (module_text or "").strip()
    module_slot_key_clean = (module_slot_key or "").strip()
    if not module_text_clean:
        raise ValueError("CodeSectionImport.build_via_code_section requires module_text")
    if not module_slot_key_clean:
        raise ValueError("CodeSectionImport.build_via_code_section requires module_slot_key")

    session = current_handler_session()
    code_section = session.imap_get(CodeSection, code_section_id)
    if code_section is None:
        raise RuntimeError(
            "CodeSectionImport.build_via_code_section requires existing CodeSection in the identity map: "
            f"code_section_id={code_section_id}"
        )
    code_section_segment = code_section.content_part_text_segment
    if code_section_segment is None or code_section_segment.content_part_text_id is None:
        raise RuntimeError(
            "CodeSectionImport.build_via_code_section requires CodeSection content segment before payload materialization: "
            f"code_section_id={code_section_id}"
        )
    content_part_text = session.imap_get(ContentPartText, code_section_segment.content_part_text_id)
    if content_part_text is None:
        raise RuntimeError(
            "CodeSectionImport.build_via_code_section requires ContentPartText in the identity map: "
            f"content_part_text_id={code_section_segment.content_part_text_id}"
        )

    code_section_import_id = stable_code_section_import_id(code_section_id=code_section_id)
    module_segment_id = stable_content_part_text_segment_id(
        content_part_text_id=content_part_text.id,
        key=f"code-section-import:{code_section_import_id}:{module_slot_key_clean}",
    )
    existing = session.imap_get(CodeSectionImport, code_section_import_id)
    if existing is not None:
        module_segment = existing.module_segment
        if (
            existing.code_section_id != code_section_id
            or existing.module_text != module_text_clean
            or existing.is_from_import != is_from_import
            or existing.is_star_import != is_star_import
            or existing.relative_level != relative_level
            or module_segment is None
            or existing.module_segment_id != module_segment_id
            or module_segment.byte_start != module_byte_start
            or module_segment.byte_end != module_byte_end
        ):
            raise RuntimeError(
                "CodeSectionImport.build_via_code_section payload mismatch for existing import payload: "
                f"code_section_import_id={code_section_import_id}"
            )
        if existing.code_section is None:
            existing.code_section = code_section
        return existing

    await content_part_text.apply_editor_patch(
        patch=ContentPartTextEditorPatch(
            segment_ops=[
                ContentPartTextSegmentOp(
                    upsert=ContentPartTextSegmentUpsert(
                        segment_id=module_segment_id,
                        byte_start=module_byte_start,
                        byte_end=module_byte_end,
                        parent_id=code_section_segment.id,
                    )
                )
            ]
        )
    )
    module_segment = session.imap_get(ContentPartTextSegment, module_segment_id)
    if module_segment is None:
        raise RuntimeError(
            "CodeSectionImport.build_via_code_section expected module segment to be materialized: "
            f"segment_id={module_segment_id}"
        )

    created = CodeSectionImport(
        id=code_section_import_id,
        code_section=code_section,
        code_section_id=code_section_id,
        module_segment=module_segment,
        module_segment_id=module_segment.id,
        module_text=module_text_clean,
        is_from_import=is_from_import,
        is_star_import=is_star_import,
        relative_level=relative_level,
        code_section_import_names=[],
    )
    if created.bound_session is None:
        created.bind_to_session(session)
    return created
    # --- AWARE: LOGIC END build_via_code_section
