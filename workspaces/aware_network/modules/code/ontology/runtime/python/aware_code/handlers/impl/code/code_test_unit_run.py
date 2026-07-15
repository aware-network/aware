from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonArray

# Code Ontology
from aware_code_ontology.code.code_enums import CodeTestRunStatus
from aware_code_ontology.code.code_test_unit_run import CodeTestUnitRun

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_test_unit_run_id
from aware_code_ontology.code.code_test_unit import CodeTestUnit
from aware_code_ontology.package.code_package_test import CodePackageTest
from aware_code_ontology.package.code_package_test_run import CodePackageTestRun
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_code_package_test_run(
    code_package_test_run_id: UUID,
    code_test_unit_id: UUID,
    status: CodeTestRunStatus,
    selector: str,
    failures: JsonArray,
    duration_s: float | None = None,
    error: str | None = None,
) -> CodeTestUnitRun:
    """
    Build one canonical run receipt for a concrete CodeTestUnit.
    """

    # --- AWARE: LOGIC START build_via_code_package_test_run
    normalized_selector = (selector or "").strip()
    if not normalized_selector:
        raise RuntimeError("CodeTestUnitRun.build_via_code_package_test_run requires non-empty selector")

    session = current_handler_session()
    code_package_test_run = session.imap_get(CodePackageTestRun, code_package_test_run_id)
    if code_package_test_run is None:
        raise RuntimeError(
            "CodeTestUnitRun.build_via_code_package_test_run requires existing CodePackageTestRun: "
            + f"code_package_test_run_id={code_package_test_run_id}"
        )

    code_package_test = session.imap_get(CodePackageTest, code_package_test_run.code_package_test_id)
    if code_package_test is None:
        raise RuntimeError(
            "CodeTestUnitRun.build_via_code_package_test_run requires existing CodePackageTest parent: "
            + f"code_package_test_id={code_package_test_run.code_package_test_id}"
        )

    code_test_unit = session.imap_get(CodeTestUnit, code_test_unit_id)
    if code_test_unit is None:
        raise RuntimeError(
            "CodeTestUnitRun.build_via_code_package_test_run requires existing CodeTestUnit: "
            + f"code_test_unit_id={code_test_unit_id}"
        )
    if code_test_unit.code_test_id != code_package_test.code_test_id:
        raise RuntimeError(
            "CodeTestUnitRun.build_via_code_package_test_run requires unit to belong to the parent "
            + "CodePackageTest CodeTest: "
            + f"code_package_test_id={code_package_test.id} code_test_id={code_package_test.code_test_id} "
            + f"code_test_unit_id={code_test_unit_id} unit_code_test_id={code_test_unit.code_test_id}"
        )

    failures_payload = JsonArray(failures or [])
    unit_run_id = stable_code_test_unit_run_id(
        code_package_test_run_id=code_package_test_run_id,
        code_test_unit_id=code_test_unit_id,
    )
    existing = session.imap_get(CodeTestUnitRun, unit_run_id)
    if existing is not None:
        if (
            existing.code_package_test_run_id != code_package_test_run_id
            or existing.code_test_unit_id != code_test_unit_id
            or existing.status != status
            or existing.selector != normalized_selector
            or existing.duration_s != duration_s
            or JsonArray(existing.failures or []) != failures_payload
            or existing.error != error
        ):
            raise RuntimeError(
                "CodeTestUnitRun.build_via_code_package_test_run payload mismatch for existing unit run: "
                + f"code_test_unit_run_id={unit_run_id}"
            )
        if existing.code_test_unit is not code_test_unit:
            existing.code_test_unit = code_test_unit
        return existing

    return CodeTestUnitRun(
        id=unit_run_id,
        code_package_test_run_id=code_package_test_run_id,
        code_test_unit_id=code_test_unit_id,
        code_test_unit=code_test_unit,
        status=status,
        selector=normalized_selector,
        duration_s=duration_s,
        failures=failures_payload,
        error=error,
    )
    # --- AWARE: LOGIC END build_via_code_package_test_run
