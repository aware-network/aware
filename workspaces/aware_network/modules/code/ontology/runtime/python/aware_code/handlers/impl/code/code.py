from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_plan import CodeContentPlan
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_test import CodeTest
from aware_code_ontology.code.code_test_unit import CodeTestUnit

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.code.delete import (
    delete_code_instance,
    delete_owned_section_from_code,
    iter_session_visible_sections_for_code,
)
from aware_code.ontology.materialization import replace_code_content_from_text
from aware_code.stable_ids import (
    stable_code_id,
    stable_code_test_id,
    stable_code_test_unit_id,
)
from aware_content.handlers.impl.part import (
    content_part_text as content_part_text_handler,
)
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_code_ontology.code.code_test_framework import CodeTestFramework
from aware_orm.session.change_collector import current_change_collector
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_section(
    code: Code,
    section_key: str,
    qualname: str,
    type: CodeSectionType,
    identity_hash: str,
    byte_start: int,
    byte_end: int,
    metadata: JsonObject | None = None,
) -> CodeSection:
    """
    Create a deterministic CodeSection under this Code snapshot.
    """

    # --- AWARE: LOGIC START create_section
    code_id = code.id

    created = await CodeSection.build_via_code(
        code_id=code_id,
        section_key=section_key,
        qualname=qualname,
        type=type,
        identity_hash=identity_hash,
        byte_start=byte_start,
        byte_end=byte_end,
        metadata=metadata,
    )
    for existing in code.code_sections:
        if existing.id != created.id:
            continue
        if (
            existing.code_id != code_id
            or existing.section_key != section_key
            or existing.qualname != qualname
            or existing.type != type
            or existing.identity_hash != identity_hash
        ):
            raise RuntimeError(
                "Code.create_section payload mismatch for existing section: " + f"code_section_id={created.id}"
            )
        return existing

    code.code_sections.append(created)
    return created
    # --- AWARE: LOGIC END create_section


async def create_test(
    code: Code, framework_id: UUID, discovery_kind: str = "language_plugin", selector_prefix: str | None = None
) -> CodeTest:
    """
    Create one canonical test surface for this Code object and framework.
    """

    # --- AWARE: LOGIC START create_test
    code_id = code.id
    normalized_discovery_kind = (discovery_kind or "").strip()
    if not normalized_discovery_kind:
        raise RuntimeError("Code.create_test requires non-empty discovery_kind")
    normalized_selector_prefix = (selector_prefix or "").strip() or None
    created = await CodeTest.build_via_code(
        code_id=code_id,
        framework_id=framework_id,
        discovery_kind=normalized_discovery_kind,
        selector_prefix=normalized_selector_prefix,
    )
    for existing in code.tests:
        if existing.id != created.id:
            continue
        if (
            existing.code_id != code_id
            or existing.framework_id != framework_id
            or existing.discovery_kind != normalized_discovery_kind
            or existing.selector_prefix != normalized_selector_prefix
        ):
            raise RuntimeError("Code.create_test payload mismatch for existing test: " + f"code_test_id={created.id}")
        return existing

    code.tests.append(created)
    return created
    # --- AWARE: LOGIC END create_test


async def sync_test_unit(
    code: Code,
    framework_id: UUID,
    code_section_id: UUID,
    unit_key: str,
    selector: str,
    kind: str = "function",
    name: str | None = None,
    discovery_kind: str = "language_plugin",
    selector_prefix: str | None = None,
) -> CodeTestUnit:
    """
    Upsert one framework-specific test unit under this Code object.

    This is the Code-owned inventory mutation rail used by CodePackage sync.
    """

    # --- AWARE: LOGIC START sync_test_unit
    code_id = code.id
    normalized_discovery_kind = (discovery_kind or "").strip()
    if not normalized_discovery_kind:
        raise RuntimeError("Code.sync_test_unit requires non-empty discovery_kind")
    normalized_selector_prefix = (selector_prefix or "").strip() or None
    normalized_selector = (selector or "").strip()
    if not normalized_selector:
        raise RuntimeError("Code.sync_test_unit requires non-empty selector")
    normalized_kind = (kind or "").strip()
    if not normalized_kind:
        raise RuntimeError("Code.sync_test_unit requires non-empty kind")
    normalized_unit_key = (unit_key or "").strip()
    if not normalized_unit_key:
        raise RuntimeError("Code.sync_test_unit requires non-empty unit_key")
    normalized_name = (name or "").strip() or None

    session = current_handler_session()
    code_section = session.imap_get(CodeSection, code_section_id)
    if code_section is None:
        raise RuntimeError("Code.sync_test_unit requires existing CodeSection: " + f"code_section_id={code_section_id}")
    if code_section.code_id != code_id:
        raise RuntimeError(
            "Code.sync_test_unit requires CodeSection to belong to this Code: "
            + f"code_id={code_id} code_section_id={code_section_id} section_code_id={code_section.code_id}"
        )

    framework = session.imap_get(CodeTestFramework, framework_id)
    code_test_id = stable_code_test_id(
        code_id=code_id,
        framework_id=framework_id,
    )
    code_test = session.imap_get(CodeTest, code_test_id)
    collector = current_change_collector()
    should_update_code_tests = True
    if collector is not None:
        should_track = collector.should_track
        if should_track is None:
            should_update_code_tests = False
        else:
            try:
                should_update_code_tests = not should_track(code)
            except Exception:
                should_update_code_tests = False
    if code_test is None:
        code_test = await CodeTest.build_via_code(
            code_id=code_id,
            framework_id=framework_id,
            discovery_kind=normalized_discovery_kind,
            selector_prefix=normalized_selector_prefix,
        )
        if should_update_code_tests:
            code.tests.append(code_test)
    else:
        if (
            code_test.code_id != code_id
            or code_test.framework_id != framework_id
            or code_test.discovery_kind != normalized_discovery_kind
            or code_test.selector_prefix != normalized_selector_prefix
        ):
            raise RuntimeError(
                "Code.sync_test_unit payload mismatch for existing CodeTest: " + f"code_test_id={code_test_id}"
            )
        if framework is not None and code_test.framework is not framework:
            code_test.framework = framework
        if should_update_code_tests and all(existing.id != code_test.id for existing in code.tests):
            code.tests.append(code_test)

    code_test_unit_id = stable_code_test_unit_id(
        code_test_id=code_test_id,
        code_section_id=code_section_id,
        unit_key=normalized_unit_key,
    )
    existing_unit = session.imap_get(CodeTestUnit, code_test_unit_id)
    if existing_unit is not None:
        if (
            existing_unit.code_test_id != code_test_id
            or existing_unit.code_section_id != code_section_id
            or existing_unit.unit_key != normalized_unit_key
            or existing_unit.selector != normalized_selector
            or existing_unit.kind != normalized_kind
            or existing_unit.name != normalized_name
        ):
            raise RuntimeError(
                "Code.sync_test_unit payload mismatch for existing CodeTestUnit: "
                + f"code_test_unit_id={code_test_unit_id}"
            )
        if existing_unit.code_section is not code_section:
            existing_unit.code_section = code_section
        return existing_unit

    if code_test.is_new:
        created_unit = await CodeTestUnit.build_via_code_test(
            code_test_id=code_test_id,
            code_section_id=code_section_id,
            unit_key=normalized_unit_key,
            selector=normalized_selector,
            kind=normalized_kind,
            name=normalized_name,
        )
        if all(existing.id != created_unit.id for existing in code_test.units):
            code_test.units.append(created_unit)
        return created_unit

    return await code_test.create_unit(
        code_section_id=code_section_id,
        unit_key=normalized_unit_key,
        selector=normalized_selector,
        kind=normalized_kind,
        name=normalized_name,
    )
    # --- AWARE: LOGIC END sync_test_unit


async def apply_content_plan(code: Code, plan: CodeContentPlan) -> Any:
    """
    Apply a canonical code content materialization plan through the owned Code handler rail.
    """

    # --- AWARE: LOGIC START apply_content_plan
    code.language = CodeLanguage(plan.language.value)

    existing_content_part_text: ContentPartText | None = getattr(code, "content_part_text", None)
    if existing_content_part_text is None:
        content_part_text = await content_part_text_handler.create_content_part_text(
            inline_text=plan.content_text,
        )
        session = current_handler_session()
        if getattr(content_part_text, "bound_session", None) is None:
            content_part_text.bind_to_session(session)
        code.content_part_text = content_part_text
        code.content_part_text_id = content_part_text.id
    else:
        await existing_content_part_text.set_inline_text(
            inline_text=plan.content_text,
        )

    for existing_section in iter_session_visible_sections_for_code(code):
        await delete_owned_section_from_code(existing_section)
    if code.code_sections:
        code.code_sections[:] = []

    for descriptor in plan.section_plans:
        created = await code.create_section(
            section_key=descriptor.section_key,
            qualname=descriptor.qualname,
            type=CodeSectionType(descriptor.section_type.value),
            identity_hash=descriptor.identity_hash,
            byte_start=descriptor.byte_start,
            byte_end=descriptor.byte_end,
            metadata=descriptor.metadata,
        )
        section_type = CodeSectionType(descriptor.section_type.value)
        if section_type is CodeSectionType.annotation:
            annotation_plan = descriptor.annotation_plan
            if annotation_plan is None:
                raise RuntimeError(
                    "Code content plan requires annotation payload plan for annotation sections: "
                    + f"code_section_id={created.id}"
                )
            _ = await created.create_annotation(
                path=annotation_plan.path,
                verb=annotation_plan.verb,
                args=list(annotation_plan.args),
            )
        elif section_type is CodeSectionType.import_:
            import_plan = descriptor.import_plan
            if import_plan is None:
                raise RuntimeError(
                    "Code content plan requires import payload plan for import sections: "
                    + f"code_section_id={created.id}"
                )
            created_import = await created.create_import(
                module_text=import_plan.module_text,
                is_from_import=import_plan.is_from_import,
                is_star_import=import_plan.is_star_import,
                relative_level=import_plan.relative_level,
                module_slot_key=import_plan.module_segment_plan.slot_key,
                module_byte_start=import_plan.module_segment_plan.byte_start,
                module_byte_end=import_plan.module_segment_plan.byte_end,
            )
            for name_plan in import_plan.name_plans:
                _ = await created_import.create_name(
                    name_text=name_plan.name_text,
                    alias_text=name_plan.alias_text,
                    name_slot_key=name_plan.name_segment_plan.slot_key,
                    name_byte_start=name_plan.name_segment_plan.byte_start,
                    name_byte_end=name_plan.name_segment_plan.byte_end,
                    alias_slot_key=(
                        name_plan.alias_segment_plan.slot_key if name_plan.alias_segment_plan is not None else None
                    ),
                    alias_byte_start=(
                        name_plan.alias_segment_plan.byte_start if name_plan.alias_segment_plan is not None else None
                    ),
                    alias_byte_end=(
                        name_plan.alias_segment_plan.byte_end if name_plan.alias_segment_plan is not None else None
                    ),
                )
    # --- AWARE: LOGIC END apply_content_plan


async def delete(code: Code) -> Any:
    """
    Delete this Code subtree and owned content payloads.
    """

    # --- AWARE: LOGIC START delete
    await delete_code_instance(code)
    # --- AWARE: LOGIC END delete


async def replace_content(code: Code, content_text: str, language: CodeLanguage | None = None) -> Any:
    """
    Compatibility wrapper that parses inline text and delegates to `apply_content_plan(...)`.
    """

    # --- AWARE: LOGIC START replace_content
    await replace_code_content_from_text(
        code=code,
        content_text=content_text,
        language=language,
    )
    # --- AWARE: LOGIC END replace_content


async def create_via_code_package_code(code_package_code_id: UUID, relative_path: str, plan: CodeContentPlan) -> Code:
    """
    Create a Code instance under one CodePackage from a canonical content plan.
    """

    # --- AWARE: LOGIC START create_via_code_package_code
    normalized_relative_path = (relative_path or "").strip()
    if not normalized_relative_path:
        raise ValueError("Code.create_via_code_package_code requires relative_path")
    code_id = stable_code_id(
        code_package_code_id=code_package_code_id,
        relative_path=normalized_relative_path,
    )
    session = current_handler_session()
    existing = session.imap_get(Code, code_id)
    if existing is not None:
        if existing.code_package_code_id != code_package_code_id or existing.relative_path != normalized_relative_path:
            raise RuntimeError(
                "Code.create_via_code_package_code payload mismatch for existing Code: " + f"code_id={code_id}"
            )
        await existing.apply_content_plan(
            plan=plan.model_copy(deep=True),
        )
        return existing

    content_part_text = await content_part_text_handler.create_content_part_text(
        inline_text=plan.content_text,
    )
    if content_part_text.bound_session is None:
        content_part_text.bind_to_session(session)

    created = Code(
        id=code_id,
        code_package_code_id=code_package_code_id,
        relative_path=normalized_relative_path,
        content_part_text=content_part_text,
        content_part_text_id=content_part_text.id,
        language=CodeLanguage(plan.language.value),
    )
    await created.apply_content_plan(
        plan=plan.model_copy(deep=True),
    )
    return created
    # --- AWARE: LOGIC END create_via_code_package_code
