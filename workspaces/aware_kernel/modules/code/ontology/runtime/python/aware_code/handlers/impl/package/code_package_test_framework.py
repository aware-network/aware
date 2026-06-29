from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.package.code_package_test_framework import CodePackageTestFramework

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_package_test_framework_id
from aware_code_ontology.code.code_test_framework import CodeTestFramework
from aware_code_ontology.package.code_package import CodePackage
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_code_package(
    code_package_id: UUID,
    code_test_framework_id: UUID,
    declaration_kind: str = "unknown",
    declaration_ref: str | None = None,
) -> CodePackageTestFramework:
    """
    Attach an existing CodeTestFramework under this CodePackage.
    """

    # --- AWARE: LOGIC START build_via_code_package
    normalized_declaration_kind = (declaration_kind or "").strip() or "unknown"
    normalized_declaration_ref = (declaration_ref or "").strip() or None
    session = current_handler_session()

    code_package = session.imap_get(CodePackage, code_package_id)
    if code_package is None:
        raise RuntimeError(
            "CodePackageTestFramework.build_via_code_package requires existing CodePackage: "
            + f"code_package_id={code_package_id}"
        )

    framework = session.imap_get(CodeTestFramework, code_test_framework_id)

    edge_id = stable_code_package_test_framework_id(
        code_package_id=code_package_id,
        code_test_framework_id=code_test_framework_id,
    )
    existing = session.imap_get(CodePackageTestFramework, edge_id)
    if existing is not None:
        if existing.code_package_id != code_package_id or existing.code_test_framework_id != code_test_framework_id:
            raise RuntimeError(
                "CodePackageTestFramework.build_via_code_package payload mismatch for existing edge: "
                + f"code_package_test_framework_id={edge_id}"
            )
        existing.declaration_kind = normalized_declaration_kind
        existing.declaration_ref = normalized_declaration_ref
        if framework is not None and existing.code_test_framework is not framework:
            existing.code_test_framework = framework
        return existing

    return CodePackageTestFramework(
        id=edge_id,
        code_package_id=code_package_id,
        code_test_framework_id=code_test_framework_id,
        code_test_framework=framework,
        declaration_kind=normalized_declaration_kind,
        declaration_ref=normalized_declaration_ref,
    )
    # --- AWARE: LOGIC END build_via_code_package
