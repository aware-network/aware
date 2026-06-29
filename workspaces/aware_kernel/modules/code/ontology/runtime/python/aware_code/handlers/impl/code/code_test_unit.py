from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_test_unit import CodeTestUnit

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_test_unit_id
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_test import CodeTest
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_code_test(
    code_test_id: UUID,
    code_section_id: UUID,
    unit_key: str,
    selector: str,
    kind: str = "function",
    name: str | None = None,
) -> CodeTestUnit:
    """
    Build one runnable test unit for a concrete CodeSection.
    """

    # --- AWARE: LOGIC START build_via_code_test
    normalized_selector = (selector or "").strip()
    if not normalized_selector:
        raise RuntimeError("CodeTestUnit.build_via_code_test requires non-empty selector")

    normalized_kind = (kind or "").strip()
    if not normalized_kind:
        raise RuntimeError("CodeTestUnit.build_via_code_test requires non-empty kind")

    normalized_unit_key = (unit_key or "").strip()
    if not normalized_unit_key:
        raise RuntimeError("CodeTestUnit.build_via_code_test requires non-empty unit_key")

    normalized_name = (name or "").strip() or None
    session = current_handler_session()
    code_test = session.imap_get(CodeTest, code_test_id)
    if code_test is None:
        raise RuntimeError(
            "CodeTestUnit.build_via_code_test requires existing CodeTest in the active session: "
            + f"code_test_id={code_test_id}"
        )

    code_section = session.imap_get(CodeSection, code_section_id)
    if code_section is None:
        raise RuntimeError(
            "CodeTestUnit.build_via_code_test requires existing CodeSection in the active session: "
            + f"code_section_id={code_section_id}"
        )
    if code_section.code_id != code_test.code_id:
        raise RuntimeError(
            "CodeTestUnit.build_via_code_test requires CodeSection to belong to the parent CodeTest Code: "
            + f"code_test_id={code_test_id} code_id={code_test.code_id} code_section_id={code_section_id} "
            + f"section_code_id={code_section.code_id}"
        )

    code_test_unit_id = stable_code_test_unit_id(
        code_test_id=code_test_id,
        code_section_id=code_section_id,
        unit_key=normalized_unit_key,
    )
    existing = session.imap_get(CodeTestUnit, code_test_unit_id)
    if existing is not None:
        if (
            existing.code_test_id != code_test_id
            or existing.code_section_id != code_section_id
            or existing.unit_key != normalized_unit_key
            or existing.selector != normalized_selector
            or existing.kind != normalized_kind
            or existing.name != normalized_name
        ):
            raise RuntimeError(
                "CodeTestUnit.build_via_code_test payload mismatch for existing unit: "
                + f"code_test_unit_id={code_test_unit_id}"
            )
        if existing.code_section is not code_section:
            existing.code_section = code_section
        return existing

    return CodeTestUnit(
        id=code_test_unit_id,
        code_test_id=code_test_id,
        code_section_id=code_section_id,
        code_section=code_section,
        unit_key=normalized_unit_key,
        selector=normalized_selector,
        kind=normalized_kind,
        name=normalized_name,
    )
    # --- AWARE: LOGIC END build_via_code_test
