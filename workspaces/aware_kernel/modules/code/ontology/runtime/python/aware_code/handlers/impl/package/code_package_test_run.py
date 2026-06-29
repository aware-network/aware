from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Code
from aware_code.types import JsonArray

# Code Ontology
from aware_code_ontology.code.code_enums import CodeTestRunStatus
from aware_code_ontology.code.code_test_unit_run import CodeTestUnitRun
from aware_code_ontology.package.code_package_test_run import CodePackageTestRun

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_package_test_run_id
from aware_code_ontology.package.code_package_test import CodePackageTest
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_unit_run(
    code_package_test_run: CodePackageTestRun,
    code_test_unit_id: UUID,
    status: CodeTestRunStatus,
    selector: str,
    failures: JsonArray,
    duration_s: float | None = None,
    error: str | None = None,
) -> CodeTestUnitRun:
    """
    Attach one canonical unit run receipt to this package test run.
    """

    # --- AWARE: LOGIC START create_unit_run
    created = await CodeTestUnitRun.build_via_code_package_test_run(
        code_package_test_run_id=code_package_test_run.id,
        code_test_unit_id=code_test_unit_id,
        status=status,
        selector=selector,
        duration_s=duration_s,
        failures=JsonArray(failures or []),
        error=error,
    )
    for existing in code_package_test_run.unit_runs:
        if existing.id == created.id:
            return existing
    code_package_test_run.unit_runs.append(created)
    return created
    # --- AWARE: LOGIC END create_unit_run


async def build_via_code_package_test(
    code_package_test_id: UUID,
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
    Build one canonical run envelope for a package-owned CodeTest.
    """

    # --- AWARE: LOGIC START build_via_code_package_test
    normalized_run_key = (run_key or "").strip()
    if not normalized_run_key:
        raise RuntimeError("CodePackageTestRun.build_via_code_package_test requires non-empty run_key")

    normalized_backend_kind = (backend_kind or "").strip()
    if not normalized_backend_kind:
        raise RuntimeError("CodePackageTestRun.build_via_code_package_test requires non-empty backend_kind")

    session = current_handler_session()
    code_package_test = session.imap_get(CodePackageTest, code_package_test_id)
    if code_package_test is None:
        raise RuntimeError(
            "CodePackageTestRun.build_via_code_package_test requires existing CodePackageTest: "
            + f"code_package_test_id={code_package_test_id}"
        )

    run_id = stable_code_package_test_run_id(
        code_package_test_id=code_package_test_id,
        run_key=normalized_run_key,
    )
    existing = session.imap_get(CodePackageTestRun, run_id)
    if existing is not None:
        if (
            existing.code_package_test_id != code_package_test_id
            or existing.run_key != normalized_run_key
            or existing.backend_kind != normalized_backend_kind
            or existing.status != status
            or existing.started_at_utc != started_at_utc
            or existing.finished_at_utc != finished_at_utc
            or existing.duration_s != duration_s
            or existing.selected_unit_count != selected_unit_count
            or existing.total_tests != total_tests
            or existing.passed_tests != passed_tests
            or existing.failed_tests != failed_tests
            or existing.skipped_tests != skipped_tests
            or existing.unsupported_tests != unsupported_tests
            or existing.error != error
        ):
            raise RuntimeError(
                "CodePackageTestRun.build_via_code_package_test payload mismatch for existing run: "
                + f"code_package_test_run_id={run_id}"
            )
        return existing

    return CodePackageTestRun(
        id=run_id,
        code_package_test_id=code_package_test_id,
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
    # --- AWARE: LOGIC END build_via_code_package_test
