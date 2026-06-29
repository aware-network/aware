from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_plan import (
    CodeContentPlan,
    CodePackageDeltaProduction,
    CodePackagePathRole,
)
from aware_code_ontology.code.code_test_unit import CodeTestUnit
from aware_code_ontology.package.code_package_code import CodePackageCode

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.package.code_access import resolve_edge_code
from aware_code.package.code_delete import delete_package_code_edge_instance
from aware_code.stable_ids import stable_code_package_code_id
from aware_code_ontology.code.code import Code
from aware_code_ontology.package.code_package import CodePackage
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def sync_test_unit(
    code_package_code: CodePackageCode,
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
    Upsert one runnable Code test unit through the package-code bridge.
    """

    # --- AWARE: LOGIC START sync_test_unit
    code = resolve_edge_code(code_package_code)
    return await code.sync_test_unit(
        framework_id=framework_id,
        code_section_id=code_section_id,
        unit_key=unit_key,
        selector=selector,
        kind=kind,
        name=name,
        discovery_kind=discovery_kind,
        selector_prefix=selector_prefix,
    )
    # --- AWARE: LOGIC END sync_test_unit


async def update_path_role(code_package_code: CodePackageCode, path_role: CodePackagePathRole) -> CodePackageCode:
    """
    Update this package-code edge path role through its own mutation boundary.
    """

    # --- AWARE: LOGIC START update_path_role
    code_package_code.path_role = path_role
    return code_package_code
    # --- AWARE: LOGIC END update_path_role


async def delete(code_package_code: CodePackageCode) -> None:
    """
    Delete this package-owned code attachment and its owned Code.
    """

    # --- AWARE: LOGIC START delete
    code = resolve_edge_code(code_package_code)
    await code.delete()
    delete_package_code_edge_instance(code_package_code)
    # --- AWARE: LOGIC END delete


async def create_via_code_package(
    code_package_id: UUID,
    relative_path: str,
    plan: CodeContentPlan,
    path_role: CodePackagePathRole = CodePackagePathRole.authored_source,
    delta_production: CodePackageDeltaProduction | None = None,
) -> CodePackageCode:
    """
    Create a deterministic package-owned code attachment and owned Code from a canonical content plan.
    """

    # --- AWARE: LOGIC START create_via_code_package
    normalized_relative_path = (relative_path or "").strip()
    if not normalized_relative_path:
        raise RuntimeError("CodePackageCode.create_via_code_package requires non-empty relative_path")

    session = current_handler_session()
    code_package = session.imap_get(CodePackage, code_package_id)
    if code_package is None:
        raise RuntimeError(
            "CodePackageCode.create_via_code_package requires existing CodePackage in the active session identity map: "
            + f"code_package_id={code_package_id}"
        )

    assoc_id = stable_code_package_code_id(
        code_package_id=code_package_id,
        relative_path=normalized_relative_path,
    )
    code = await Code.create_via_code_package_code(
        code_package_code_id=assoc_id,
        relative_path=normalized_relative_path,
        plan=plan.model_copy(deep=True),
    )
    existing = session.imap_get(CodePackageCode, assoc_id)
    if existing is not None:
        if (
            existing.code_package_id != code_package_id
            or (existing.relative_path or "").strip() != normalized_relative_path
        ):
            raise RuntimeError(
                "CodePackageCode.create_via_code_package payload mismatch for existing association: "
                + f"code_package_code_id={assoc_id}"
            )
        if existing.code.id != code.id:
            raise RuntimeError(
                "CodePackageCode.create_via_code_package resolved Code mismatch for existing association: "
                + f"code_package_code_id={assoc_id}"
            )
        if existing.code is not code:
            existing.code = code
        existing.path_role = path_role
        return existing

    return CodePackageCode(
        id=assoc_id,
        code_package_id=code_package_id,
        code=code,
        relative_path=normalized_relative_path,
        path_role=path_role,
    )
    # --- AWARE: LOGIC END create_via_code_package
