from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_section_annotation_id
from aware_code_ontology.code.code_section import CodeSection
from aware_orm.session.change_collector import current_change_collector
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def delete(code_section_annotation: CodeSectionAnnotation) -> None:
    """
    Delete this annotation payload through its owned handler rail.
    """

    # --- AWARE: LOGIC START delete
    collector = current_change_collector()
    if collector is None:
        raise RuntimeError("CodeSectionAnnotation.delete requires an active runtime change collector")

    collector.record_delete(code_section_annotation)
    bound_session = code_section_annotation.bound_session
    if bound_session is not None:
        bound_session.imap_remove(type(code_section_annotation), code_section_annotation.id)
    # --- AWARE: LOGIC END delete


async def build_via_code_section(
    code_section_id: UUID, path: str, verb: str, args: list[str] = []
) -> CodeSectionAnnotation:
    """
    Build the unique annotation payload under a CodeSection.
    """

    # --- AWARE: LOGIC START build_via_code_section
    path_clean = (path or "").strip()
    verb_clean = (verb or "").strip()
    args_clean = [arg.strip() for arg in (args or [])]

    session = current_handler_session()
    code_section = session.imap_get(CodeSection, code_section_id)
    if code_section is None:
        raise RuntimeError(
            "CodeSectionAnnotation.build_via_code_section requires existing CodeSection in the identity map: "
            f"code_section_id={code_section_id}"
        )

    annotation_id = stable_code_section_annotation_id(
        code_section_id=code_section_id,
    )
    existing = session.imap_get(CodeSectionAnnotation, annotation_id)
    if existing is not None:
        if existing.path != path_clean or existing.verb != verb_clean or existing.args != args_clean:
            raise RuntimeError(
                "CodeSectionAnnotation.build payload mismatch for existing annotation: "
                f"annotation_id={annotation_id}"
            )
        if existing.code_section_id != code_section_id:
            raise RuntimeError(
                "CodeSectionAnnotation.build owner mismatch for existing annotation: " f"annotation_id={annotation_id}"
            )
        if existing.code_section is None:
            existing.code_section = code_section
        return existing

    return CodeSectionAnnotation(
        id=annotation_id,
        code_section=code_section,
        code_section_id=code_section_id,
        path=path_clean,
        verb=verb_clean,
        args=args_clean,
    )
    # --- AWARE: LOGIC END build_via_code_section
