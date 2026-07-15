from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeTestRunStatus
from aware_code_ontology.package.code_package_test import CodePackageTest
from aware_code_ontology.package.code_package_test_run import CodePackageTestRun

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.package.code_access import normalize_package_relative_path
from aware_code.stable_ids import stable_code_package_test_id
from aware_code_ontology.code.code_test import CodeTest
from aware_code_ontology.package.code_package import CodePackage
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_run(
    code_package_test: CodePackageTest,
    run_key: str,
    backend_kind: str,
    status: CodeTestRunStatus,
    started_at_utc: datetime | None = None,
    finished_at_utc: datetime | None = None,
    duration_s: float | None = None,
    selected_unit_count: int = 0,
    total_tests: int = 0,
    passed_tests: int = 0,
    failed_tests: int = 0,
    skipped_tests: int = 0,
    unsupported_tests: int = 0,
    error: str | None = None,
) -> CodePackageTestRun:
    """
    Create one canonical run envelope for this package-owned CodeTest.
    """

    # --- AWARE: LOGIC START create_run
    normalized_run_key = (run_key or "").strip()
    if not normalized_run_key:
        raise RuntimeError("CodePackageTest.create_run requires non-empty run_key")

    normalized_backend_kind = (backend_kind or "").strip()
    if not normalized_backend_kind:
        raise RuntimeError("CodePackageTest.create_run requires non-empty backend_kind")

    created = await CodePackageTestRun.build_via_code_package_test(
        code_package_test_id=code_package_test.id,
        run_key=normalized_run_key,
        backend_kind=normalized_backend_kind,
        status=status,
        started_at_utc=started_at_utc,
        finished_at_utc=finished_at_utc,
        duration_s=duration_s,
        selected_unit_count=selected_unit_count,
        total_tests=total_tests,
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        skipped_tests=skipped_tests,
        unsupported_tests=unsupported_tests,
        error=error,
    )
    for existing in code_package_test.runs:
        if existing.id == created.id:
            return existing
    code_package_test.runs.append(created)
    return created
    # --- AWARE: LOGIC END create_run


async def build_via_code_package(code_package_id: UUID, code_test_id: UUID, relative_path: str) -> CodePackageTest:
    """
    Attach an existing CodeTest under this CodePackage inventory.
    """

    # --- AWARE: LOGIC START build_via_code_package
    normalized_relative_path = normalize_package_relative_path(relative_path)
    session = current_handler_session()

    code_package = session.imap_get(CodePackage, code_package_id)
    if code_package is None:
        raise RuntimeError(
            "CodePackageTest.build_via_code_package requires existing CodePackage: "
            + f"code_package_id={code_package_id}"
        )

    code_test = session.imap_get(CodeTest, code_test_id)
    if code_test is None:
        raise RuntimeError(
            "CodePackageTest.build_via_code_package requires existing CodeTest: " + f"code_test_id={code_test_id}"
        )

    package_test_id = stable_code_package_test_id(
        code_package_id=code_package_id,
        code_test_id=code_test_id,
        relative_path=normalized_relative_path,
    )
    existing = session.imap_get(CodePackageTest, package_test_id)
    if existing is not None:
        if (
            existing.code_package_id != code_package_id
            or existing.code_test_id != code_test_id
            or existing.relative_path != normalized_relative_path
        ):
            raise RuntimeError(
                "CodePackageTest.build_via_code_package payload mismatch for existing package test: "
                + f"code_package_test_id={package_test_id}"
            )
        if existing.code_test is not code_test:
            existing.code_test = code_test
        return existing

    return CodePackageTest(
        id=package_test_id,
        code_package_id=code_package_id,
        code_test_id=code_test_id,
        code_test=code_test,
        relative_path=normalized_relative_path,
    )
    # --- AWARE: LOGIC END build_via_code_package
