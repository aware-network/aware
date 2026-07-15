from __future__ import annotations

from uuid import UUID

from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_meta.runtime.handler_context import current_handler_session
from aware_orm.session.change_collector import current_change_collector
from aware_orm.session.current_session_ctx import current_session


def _current_code_delete_session():
    try:
        return current_handler_session()
    except RuntimeError:
        session = current_session()
        if session is None:
            raise RuntimeError("Code deletion requires an active handler session or local ORM session") from None
        return session


def iter_session_visible_sections_for_code(code: Code) -> list[CodeSection]:
    visible_by_id: dict[UUID, CodeSection] = {}
    for section in list(code.code_sections):
        section_id = getattr(section, "id", None)
        if isinstance(section_id, UUID):
            visible_by_id.setdefault(section_id, section)

    code_id = code.id
    if not isinstance(code_id, UUID):
        return list(visible_by_id.values())

    session = _current_code_delete_session()
    for obj in session.imap_all_objects():
        if not isinstance(obj, CodeSection):
            continue
        if obj.code_id != code_id or not isinstance(obj.id, UUID):
            continue
        visible_by_id.setdefault(obj.id, obj)
    return list(visible_by_id.values())


async def delete_owned_section_from_code(code_section: CodeSection) -> None:
    await code_section.delete()


async def delete_code_instance(code: Code) -> None:
    collector = current_change_collector()
    if collector is None:
        raise RuntimeError("Code.delete requires an active runtime change collector")

    for existing_section in iter_session_visible_sections_for_code(code):
        await delete_owned_section_from_code(existing_section)
    if code.code_sections:
        code.code_sections[:] = []

    content_part_text = code.content_part_text
    if content_part_text is None and code.content_part_text_id is not None:
        session = _current_code_delete_session()
        content_part_text = session.imap_get(ContentPartText, code.content_part_text_id)

    if content_part_text is not None:
        await content_part_text.delete()

    collector.record_delete(code)
    if code.bound_session is not None:
        code.bound_session.imap_remove(type(code), code.id)
