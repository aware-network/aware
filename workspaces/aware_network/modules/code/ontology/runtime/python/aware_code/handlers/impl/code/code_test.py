from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_test import CodeTest
from aware_code_ontology.code.code_test_unit import CodeTestUnit

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_test_id
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_test_framework import CodeTestFramework
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_unit(
    code_test: CodeTest,
    code_section_id: UUID,
    unit_key: str,
    selector: str,
    kind: str = "function",
    name: str | None = None,
) -> CodeTestUnit:
    """
    Attach one runnable test unit to a concrete CodeSection.
    """

    # --- AWARE: LOGIC START create_unit
    code_test_id = code_test.id
    normalized_selector = (selector or "").strip()
    if not normalized_selector:
        raise RuntimeError("CodeTest.create_unit requires non-empty selector")
    normalized_kind = (kind or "").strip()
    if not normalized_kind:
        raise RuntimeError("CodeTest.create_unit requires non-empty kind")
    normalized_unit_key = (unit_key or "").strip()
    if not normalized_unit_key:
        raise RuntimeError("CodeTest.create_unit requires non-empty unit_key")
    normalized_name = (name or "").strip() or None
    created = await CodeTestUnit.build_via_code_test(
        code_test_id=code_test_id,
        code_section_id=code_section_id,
        unit_key=normalized_unit_key,
        selector=normalized_selector,
        kind=normalized_kind,
        name=normalized_name,
    )
    for existing in code_test.units:
        if existing.id != created.id:
            continue
        if (
            existing.code_test_id != code_test_id
            or existing.code_section_id != code_section_id
            or existing.unit_key != normalized_unit_key
            or existing.selector != normalized_selector
            or existing.kind != normalized_kind
            or existing.name != normalized_name
        ):
            raise RuntimeError(
                "CodeTest.create_unit payload mismatch for existing unit: " + f"code_test_unit_id={created.id}"
            )
        return existing

    code_test.units.append(created)
    return created
    # --- AWARE: LOGIC END create_unit


async def build_via_code(
    code_id: UUID, framework_id: UUID, discovery_kind: str = "language_plugin", selector_prefix: str | None = None
) -> CodeTest:
    """
    Build one framework-specific test surface under a Code object.
    """

    # --- AWARE: LOGIC START build_via_code
    normalized_discovery_kind = (discovery_kind or "").strip()
    if not normalized_discovery_kind:
        raise RuntimeError("CodeTest.build_via_code requires non-empty discovery_kind")

    normalized_selector_prefix = (selector_prefix or "").strip() or None
    session = current_handler_session()
    code = session.imap_get(Code, code_id)
    if code is None:
        raise RuntimeError(
            "CodeTest.build_via_code requires existing Code in the active session: " + f"code_id={code_id}"
        )

    framework = session.imap_get(CodeTestFramework, framework_id)

    code_test_id = stable_code_test_id(
        code_id=code_id,
        framework_id=framework_id,
    )
    existing = session.imap_get(CodeTest, code_test_id)
    if existing is not None:
        if (
            existing.code_id != code_id
            or existing.framework_id != framework_id
            or existing.discovery_kind != normalized_discovery_kind
            or existing.selector_prefix != normalized_selector_prefix
        ):
            raise RuntimeError(
                "CodeTest.build_via_code payload mismatch for existing test: " + f"code_test_id={code_test_id}"
            )
        if framework is not None and existing.framework is not framework:
            existing.framework = framework
        return existing

    return CodeTest(
        id=code_test_id,
        code_id=code_id,
        framework_id=framework_id,
        framework=framework,
        discovery_kind=normalized_discovery_kind,
        selector_prefix=normalized_selector_prefix,
    )
    # --- AWARE: LOGIC END build_via_code
