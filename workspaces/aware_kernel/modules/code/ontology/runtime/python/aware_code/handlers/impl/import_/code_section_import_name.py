from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.import_.code_section_import_name import CodeSectionImportName

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code_ontology.import_.code_section_import import CodeSectionImport
from aware_code_ontology.stable_ids import stable_code_section_import_name_id
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


async def delete(code_section_import_name: CodeSectionImportName) -> None:
    """
    Delete this import-name payload through its owned handler rail.
    """

    # --- AWARE: LOGIC START delete
    collector = current_change_collector()
    if collector is None:
        raise RuntimeError("CodeSectionImportName.delete requires an active runtime change collector")

    collector.record_delete(code_section_import_name)
    bound_session = code_section_import_name.bound_session
    if bound_session is not None:
        bound_session.imap_remove(type(code_section_import_name), code_section_import_name.id)
    # --- AWARE: LOGIC END delete


async def build_via_code_section_import(
    code_section_import_id: UUID,
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
    Build a deterministic import-name entry under an import section.
    """

    # --- AWARE: LOGIC START build_via_code_section_import
    name_text_clean = (name_text or "").strip()
    name_slot_key_clean = (name_slot_key or "").strip()
    alias_text_clean = (alias_text or "").strip() or None
    alias_slot_key_clean = (alias_slot_key or "").strip() or None
    if not name_text_clean:
        raise ValueError("CodeSectionImportName.build_via_code_section_import requires name_text")
    if not name_slot_key_clean:
        raise ValueError("CodeSectionImportName.build_via_code_section_import requires name_slot_key")
    if alias_text_clean is None:
        if alias_slot_key_clean is not None or alias_byte_start is not None or alias_byte_end is not None:
            raise ValueError("CodeSectionImportName.build_via_code_section_import alias slot/range requires alias_text")
    else:
        if alias_slot_key_clean is None or alias_byte_start is None or alias_byte_end is None:
            raise ValueError("CodeSectionImportName.build_via_code_section_import alias_text requires alias slot/range")

    session = current_handler_session()
    code_section_import = session.imap_get(CodeSectionImport, code_section_import_id)
    if code_section_import is None:
        raise RuntimeError(
            "CodeSectionImportName.build_via_code_section_import requires existing CodeSectionImport in the identity map: "
            f"code_section_import_id={code_section_import_id}"
        )
    code_section = code_section_import.code_section
    if code_section is None:
        raise RuntimeError(
            "CodeSectionImportName.build_via_code_section_import requires CodeSectionImport.code_section: "
            f"code_section_import_id={code_section_import_id}"
        )
    code_section_segment = code_section.content_part_text_segment
    if code_section_segment is None or code_section_segment.content_part_text_id is None:
        raise RuntimeError(
            "CodeSectionImportName.build_via_code_section_import requires CodeSection content segment: "
            f"code_section_import_id={code_section_import_id}"
        )
    content_part_text = session.imap_get(ContentPartText, code_section_segment.content_part_text_id)
    if content_part_text is None:
        raise RuntimeError(
            "CodeSectionImportName.build_via_code_section_import requires ContentPartText in the identity map: "
            f"content_part_text_id={code_section_segment.content_part_text_id}"
        )

    code_section_import_name_id = stable_code_section_import_name_id(
        code_section_import_id=code_section_import_id,
        name_text=name_text_clean,
    )
    name_segment_id = stable_content_part_text_segment_id(
        content_part_text_id=content_part_text.id,
        key=f"code-section-import-name:{code_section_import_name_id}:{name_slot_key_clean}",
    )
    alias_segment_id = (
        stable_content_part_text_segment_id(
            content_part_text_id=content_part_text.id,
            key=f"code-section-import-name:{code_section_import_name_id}:{alias_slot_key_clean}",
        )
        if alias_slot_key_clean is not None
        else None
    )
    existing = session.imap_get(CodeSectionImportName, code_section_import_name_id)
    if existing is not None:
        name_segment = existing.name_segment
        alias_segment = existing.alias_segment
        if (
            existing.code_section_import_id != code_section_import_id
            or existing.name_text != name_text_clean
            or existing.alias_text != alias_text_clean
            or name_segment is None
            or existing.name_segment_id != name_segment_id
            or name_segment.byte_start != name_byte_start
            or name_segment.byte_end != name_byte_end
            or existing.alias_segment_id != alias_segment_id
            or (
                alias_segment_id is not None
                and (
                    alias_segment is None
                    or alias_segment.byte_start != alias_byte_start
                    or alias_segment.byte_end != alias_byte_end
                )
            )
            or (alias_segment_id is None and alias_segment is not None)
        ):
            raise RuntimeError(
                "CodeSectionImportName.build_via_code_section_import payload mismatch for existing import name: "
                f"code_section_import_name_id={code_section_import_name_id}"
            )
        return existing

    segment_ops = [
        ContentPartTextSegmentOp(
            upsert=ContentPartTextSegmentUpsert(
                segment_id=name_segment_id,
                byte_start=name_byte_start,
                byte_end=name_byte_end,
                parent_id=code_section_segment.id,
            )
        )
    ]
    if alias_segment_id is not None and alias_byte_start is not None and alias_byte_end is not None:
        segment_ops.append(
            ContentPartTextSegmentOp(
                upsert=ContentPartTextSegmentUpsert(
                    segment_id=alias_segment_id,
                    byte_start=alias_byte_start,
                    byte_end=alias_byte_end,
                    parent_id=code_section_segment.id,
                )
            )
        )
    await content_part_text.apply_editor_patch(
        patch=ContentPartTextEditorPatch(
            segment_ops=segment_ops,
        )
    )
    name_segment = session.imap_get(ContentPartTextSegment, name_segment_id)
    if name_segment is None:
        raise RuntimeError(
            "CodeSectionImportName.build_via_code_section_import expected name segment to be materialized: "
            f"segment_id={name_segment_id}"
        )
    alias_segment = session.imap_get(ContentPartTextSegment, alias_segment_id) if alias_segment_id is not None else None
    if alias_segment_id is not None and alias_segment is None:
        raise RuntimeError(
            "CodeSectionImportName.build_via_code_section_import expected alias segment to be materialized: "
            f"segment_id={alias_segment_id}"
        )

    created = CodeSectionImportName(
        id=code_section_import_name_id,
        code_section_import_id=code_section_import_id,
        name_text=name_text_clean,
        alias_text=alias_text_clean,
        name_segment=name_segment,
        name_segment_id=name_segment.id,
        alias_segment=alias_segment,
        alias_segment_id=alias_segment.id if alias_segment is not None else None,
    )
    if created.bound_session is None:
        created.bind_to_session(session)
    return created
    # --- AWARE: LOGIC END build_via_code_section_import
