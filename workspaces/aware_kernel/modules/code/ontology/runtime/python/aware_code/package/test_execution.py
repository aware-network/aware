"""CodePackage test execution adapter."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Protocol
from uuid import UUID

from aware_code.stable_ids import (
    stable_code_package_test_run_id,
    stable_code_test_unit_run_id,
)
from aware_code.types import JsonArray
from aware_code.package.test_inventory import (
    CodePackageTestInventory,
    CodePackageTestUnitInventory,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_enums import (
    CodeTestRunStatus as OntologyCodeTestRunStatus,
)
from aware_code_ontology.code.code_test_unit import CodeTestUnit
from aware_code_ontology.code.code_test_unit_run import CodeTestUnitRun
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_test import CodePackageTest
from aware_code_ontology.package.code_package_test_run import CodePackageTestRun


CodePackageTestRunStatus = Literal["passed", "failed", "skipped", "unsupported"]
_BACKEND_KIND = "aware_test_runner"
_PYTEST_SUBPROCESS_UNSET_ENV_KEYS: tuple[str, ...] = (
    # Workspace service uses this to select its own persistence backend. Package
    # tests must resolve persistence as they would under direct package pytest.
    "AWARE_PERSISTENCE_BACKEND",
)
_PYTEST_SUBPROCESS_SCRIPT = r"""
import json
import os
import sys
import traceback
from pathlib import Path

import pytest

from aware_test_runner.core.collector import TestResultCollector


def _diagnostic_payload(diagnostic):
    if diagnostic is None:
        return None
    return {
        "code": str(getattr(diagnostic, "code", "") or ""),
        "summary": str(getattr(diagnostic, "summary", "") or ""),
    }


def _failure_payload(failure):
    if failure is None:
        return None
    return {
        "test_name": str(getattr(failure, "test_name", "") or ""),
        "failure_reason": str(getattr(failure, "failure_reason", "") or ""),
        "file_path": str(getattr(failure, "file_path", "") or ""),
        "line_number": int(getattr(failure, "line_number", 0) or 0),
        "runtime_diagnostic": _diagnostic_payload(
            getattr(failure, "runtime_diagnostic", None)
        ),
    }


def _test_case_payload(test_case):
    return {
        "nodeid": str(getattr(test_case, "nodeid", "") or ""),
        "test_name": str(getattr(test_case, "test_name", "") or ""),
        "outcome": str(getattr(test_case, "outcome", "") or ""),
        "duration": float(getattr(test_case, "duration", 0.0) or 0.0),
        "failure": _failure_payload(getattr(test_case, "failure", None)),
    }


def _write_payload(payload):
    result_path = Path(os.environ["AWARE_CODE_PYTEST_RESULT_JSON"])
    result_path.write_text(json.dumps(payload), encoding="utf-8")


def _main():
    pytest_args = json.loads(os.environ.get("AWARE_CODE_PYTEST_ARGS_JSON") or "[]")
    collector = TestResultCollector()
    exit_code = int(pytest.main(pytest_args, plugins=[collector]))
    total_tests, passed_tests, failed_tests, skipped_tests, failures = (
        collector.get_results()
    )
    _write_payload(
        {
            "exit_code": exit_code,
            "passed": exit_code == 0,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "failures": [_failure_payload(failure) for failure in failures],
            "test_cases": [
                _test_case_payload(test_case)
                for test_case in collector.get_test_cases()
            ],
            "duration": collector.get_duration(),
        }
    )
    return 0


try:
    _exit_code = _main()
except BaseException as exc:
    _write_payload(
        {
            "exit_code": 1,
            "passed": False,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 1,
            "skipped_tests": 0,
            "failures": [
                {
                    "test_name": "pytest_subprocess",
                    "failure_reason": traceback.format_exc() or str(exc),
                    "file_path": "",
                    "line_number": 0,
                    "runtime_diagnostic": None,
                }
            ],
            "test_cases": [],
            "duration": 0.0,
        }
    )
    sys.exit(1)
sys.exit(_exit_code)
"""


class _RunnerDiagnostic(Protocol):
    code: str
    summary: str


class _RunnerTestFailure(Protocol):
    test_name: str
    failure_reason: str
    file_path: str
    line_number: int
    runtime_diagnostic: _RunnerDiagnostic | None


class _RunnerTestCaseResult(Protocol):
    nodeid: str
    test_name: str
    outcome: str
    duration: float
    failure: _RunnerTestFailure | None


class _RunnerTestResult(Protocol):
    exit_code: int
    passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    failures: list[_RunnerTestFailure]
    test_cases: list[_RunnerTestCaseResult]
    duration: float


@dataclass(frozen=True, slots=True)
class _SubprocessRunnerDiagnostic:
    code: str
    summary: str


@dataclass(frozen=True, slots=True)
class _SubprocessRunnerTestFailure:
    test_name: str
    failure_reason: str
    file_path: str
    line_number: int = 0
    runtime_diagnostic: _SubprocessRunnerDiagnostic | None = None


@dataclass(frozen=True, slots=True)
class _SubprocessRunnerTestCaseResult:
    nodeid: str
    test_name: str
    outcome: str
    duration: float = 0.0
    failure: _SubprocessRunnerTestFailure | None = None


@dataclass(frozen=True, slots=True)
class _SubprocessRunnerTestResult:
    exit_code: int
    passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    failures: list[_SubprocessRunnerTestFailure]
    test_cases: list[_SubprocessRunnerTestCaseResult]
    duration: float


@dataclass(frozen=True, slots=True)
class CodePackageTestFailureReceipt:
    """Failure detail from a Code-owned test execution receipt."""

    test_name: str
    failure_reason: str
    file_path: str
    line_number: int
    runtime_diagnostic_code: str | None = None
    runtime_diagnostic_summary: str | None = None


@dataclass(frozen=True, slots=True)
class CodePackageTestUnitRunReceipt:
    """Execution receipt for one canonical CodePackage test unit."""

    code_package_id: UUID
    code_package_code_id: UUID
    code_id: UUID
    code_section_id: UUID
    code_test_framework_id: UUID
    code_test_id: UUID
    code_package_test_id: UUID
    code_test_unit_id: UUID
    framework_name: str
    relative_path: str
    selector: str
    unit_key: str
    backend_kind: str
    status: CodePackageTestRunStatus
    exit_code: int
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    duration_s: float
    failures: tuple[CodePackageTestFailureReceipt, ...] = ()
    error: str | None = None


@dataclass(frozen=True, slots=True)
class CodePackageTestRunReceipt:
    """Execution receipt for a selected CodePackage test inventory run."""

    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    manifest_kind: str
    manifest_relative_path: str
    package_root: str
    backend_kind: str
    status: CodePackageTestRunStatus
    started_at_utc: datetime
    finished_at_utc: datetime
    duration_s: float
    selected_unit_count: int
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    unit_receipts: tuple[CodePackageTestUnitRunReceipt, ...] = ()
    error: str | None = None


def run_code_package_test_inventory(
    *,
    inventory: CodePackageTestInventory,
    workspace_root: Path,
    code_test_unit_ids: Iterable[UUID] | None = None,
    selectors: Iterable[str] | None = None,
    verbose: bool = False,
    fail_fast: bool = False,
    no_warnings: bool = True,
) -> CodePackageTestRunReceipt:
    """Execute selected CodePackage test units through the test-runner backend."""

    started_at_utc = _utc_now()
    started_perf = time.perf_counter()
    selected_units = _select_units(
        inventory=inventory,
        code_test_unit_ids=code_test_unit_ids,
        selectors=selectors,
    )
    package_root = _resolve_package_root(
        workspace_root=workspace_root,
        package_root=inventory.package_root,
    )

    if not selected_units:
        return CodePackageTestRunReceipt(
            code_package_id=inventory.code_package_id,
            package_name=inventory.package_name,
            language=inventory.language,
            manifest_kind=inventory.manifest_kind,
            manifest_relative_path=inventory.manifest_relative_path,
            package_root=package_root.as_posix(),
            backend_kind=_BACKEND_KIND,
            status="skipped",
            started_at_utc=started_at_utc,
            finished_at_utc=_utc_now(),
            duration_s=time.perf_counter() - started_perf,
            selected_unit_count=0,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            skipped_tests=0,
            error="No CodePackageTestUnit selected for execution",
        )

    unit_receipts = _run_code_package_test_units(
        inventory=inventory,
        units=selected_units,
        workspace_root=workspace_root,
        package_root=package_root,
        verbose=verbose,
        fail_fast=fail_fast,
        no_warnings=no_warnings,
    )
    status = _aggregate_status(unit_receipts)
    return CodePackageTestRunReceipt(
        code_package_id=inventory.code_package_id,
        package_name=inventory.package_name,
        language=inventory.language,
        manifest_kind=inventory.manifest_kind,
        manifest_relative_path=inventory.manifest_relative_path,
        package_root=package_root.as_posix(),
        backend_kind=_BACKEND_KIND,
        status=status,
        started_at_utc=started_at_utc,
        finished_at_utc=_utc_now(),
        duration_s=time.perf_counter() - started_perf,
        selected_unit_count=len(unit_receipts),
        total_tests=sum(receipt.total_tests for receipt in unit_receipts),
        passed_tests=sum(receipt.passed_tests for receipt in unit_receipts),
        failed_tests=sum(receipt.failed_tests for receipt in unit_receipts),
        skipped_tests=sum(receipt.skipped_tests for receipt in unit_receipts),
        unit_receipts=unit_receipts,
        error=_aggregate_error(unit_receipts),
    )


def _run_code_package_test_units(
    *,
    inventory: CodePackageTestInventory,
    units: tuple[CodePackageTestUnitInventory, ...],
    workspace_root: Path,
    package_root: Path,
    verbose: bool,
    fail_fast: bool,
    no_warnings: bool,
) -> tuple[CodePackageTestUnitRunReceipt, ...]:
    pytest_units: list[CodePackageTestUnitInventory] = []
    unsupported_receipts: dict[UUID, CodePackageTestUnitRunReceipt] = {}
    for unit in units:
        if _is_supported_python_pytest_runnable_unit(inventory=inventory, unit=unit):
            pytest_units.append(unit)
            continue
        unsupported_receipts[unit.code_test_unit_id] = _unsupported_unit_receipt(
            inventory=inventory,
            unit=unit,
            duration_s=0.0,
            error=(
                "CodePackage test execution currently supports Python pytest units only: "
                + f"language={inventory.language.value} framework={unit.framework_name}"
            ),
        )

    pytest_receipts: dict[UUID, CodePackageTestUnitRunReceipt] = {}
    if pytest_units:
        pytest_receipts = {
            receipt.code_test_unit_id: receipt
            for receipt in _run_python_pytest_unit_batch(
                inventory=inventory,
                units=tuple(pytest_units),
                workspace_root=workspace_root,
                package_root=package_root,
                verbose=verbose,
                fail_fast=fail_fast,
                no_warnings=no_warnings,
            )
        }
    ordered_receipts: list[CodePackageTestUnitRunReceipt] = []
    for unit in units:
        receipt = pytest_receipts.get(unit.code_test_unit_id)
        if receipt is None:
            receipt = unsupported_receipts.get(unit.code_test_unit_id)
        if receipt is None:
            raise RuntimeError(
                "CodePackage test execution did not produce a unit receipt for "
                + f"selector={unit.selector}"
            )
        ordered_receipts.append(receipt)
    return tuple(ordered_receipts)


async def materialize_code_package_test_run_receipt(
    *,
    code_package: CodePackage,
    receipt: CodePackageTestRunReceipt,
    run_key: str,
) -> tuple[CodePackageTestRun, ...]:
    """Materialize a runtime package receipt into canonical CodePackageTestRun objects."""

    if code_package.id != receipt.code_package_id:
        raise RuntimeError(
            "CodePackage test run receipt belongs to a different CodePackage: "
            + f"code_package_id={code_package.id} receipt_code_package_id={receipt.code_package_id}"
        )

    normalized_run_key = (run_key or "").strip()
    if not normalized_run_key:
        raise RuntimeError(
            "materialize_code_package_test_run_receipt requires non-empty run_key"
        )

    runs: list[CodePackageTestRun] = []
    for (
        code_package_test_id,
        unit_receipts,
    ) in _group_unit_receipts_by_code_package_test_id(receipt.unit_receipts).items():
        code_package_test = _find_code_package_test(
            code_package=code_package,
            code_package_test_id=code_package_test_id,
        )
        status = _ontology_status(_aggregate_status(unit_receipts))
        run = await code_package_test.create_run(
            run_key=normalized_run_key,
            backend_kind=receipt.backend_kind,
            status=status,
            started_at_utc=receipt.started_at_utc,
            finished_at_utc=receipt.finished_at_utc,
            duration_s=sum(unit_receipt.duration_s for unit_receipt in unit_receipts),
            selected_unit_count=len(unit_receipts),
            total_tests=sum(unit_receipt.total_tests for unit_receipt in unit_receipts),
            passed_tests=sum(
                unit_receipt.passed_tests for unit_receipt in unit_receipts
            ),
            failed_tests=sum(
                unit_receipt.failed_tests for unit_receipt in unit_receipts
            ),
            skipped_tests=sum(
                unit_receipt.skipped_tests for unit_receipt in unit_receipts
            ),
            unsupported_tests=sum(
                1
                for unit_receipt in unit_receipts
                if unit_receipt.status == "unsupported"
            ),
            error=_aggregate_error(unit_receipts),
        )
        for unit_receipt in unit_receipts:
            _ = await run.create_unit_run(
                code_test_unit_id=unit_receipt.code_test_unit_id,
                status=_ontology_status(unit_receipt.status),
                selector=unit_receipt.selector,
                duration_s=unit_receipt.duration_s,
                failures=JsonArray(
                    [asdict(failure) for failure in unit_receipt.failures]
                ),
                error=unit_receipt.error,
            )
        runs.append(run)
    return tuple(runs)


def build_ephemeral_code_package_test_runs_from_receipt(
    *,
    receipt: CodePackageTestRunReceipt,
    run_key: str,
) -> tuple[CodePackageTestRun, ...]:
    """Build read-only CodePackageTestRun evidence without invoking mutation rails."""

    normalized_run_key = (run_key or "").strip()
    if not normalized_run_key:
        raise RuntimeError(
            "build_ephemeral_code_package_test_runs_from_receipt requires non-empty run_key"
        )

    runs: list[CodePackageTestRun] = []
    for (
        code_package_test_id,
        unit_receipts,
    ) in _group_unit_receipts_by_code_package_test_id(receipt.unit_receipts).items():
        status = _ontology_status(_aggregate_status(unit_receipts))
        run_id = stable_code_package_test_run_id(
            code_package_test_id=code_package_test_id,
            run_key=normalized_run_key,
        )
        run = CodePackageTestRun(
            id=run_id,
            code_package_test_id=code_package_test_id,
            run_key=normalized_run_key,
            backend_kind=receipt.backend_kind,
            status=status,
            started_at_utc=receipt.started_at_utc,
            finished_at_utc=receipt.finished_at_utc,
            duration_s=sum(unit_receipt.duration_s for unit_receipt in unit_receipts),
            selected_unit_count=len(unit_receipts),
            total_tests=sum(unit_receipt.total_tests for unit_receipt in unit_receipts),
            passed_tests=sum(
                unit_receipt.passed_tests for unit_receipt in unit_receipts
            ),
            failed_tests=sum(
                unit_receipt.failed_tests for unit_receipt in unit_receipts
            ),
            skipped_tests=sum(
                unit_receipt.skipped_tests for unit_receipt in unit_receipts
            ),
            unsupported_tests=sum(
                1
                for unit_receipt in unit_receipts
                if unit_receipt.status == "unsupported"
            ),
            error=_aggregate_error(unit_receipts),
        )
        for unit_receipt in unit_receipts:
            code_test_unit = CodeTestUnit.model_construct(
                id=unit_receipt.code_test_unit_id,
                code_test_id=unit_receipt.code_test_id,
                code_section_id=unit_receipt.code_section_id,
                unit_key=unit_receipt.unit_key,
                selector=unit_receipt.selector,
                kind="function",
                name=None,
            )
            run.unit_runs.append(
                CodeTestUnitRun(
                    id=stable_code_test_unit_run_id(
                        code_package_test_run_id=run_id,
                        code_test_unit_id=unit_receipt.code_test_unit_id,
                    ),
                    code_package_test_run_id=run_id,
                    code_test_unit_id=unit_receipt.code_test_unit_id,
                    code_test_unit=code_test_unit,
                    status=_ontology_status(unit_receipt.status),
                    selector=unit_receipt.selector,
                    duration_s=unit_receipt.duration_s,
                    failures=JsonArray(
                        [asdict(failure) for failure in unit_receipt.failures]
                    ),
                    error=unit_receipt.error,
                )
            )
        runs.append(run)
    return tuple(runs)


def _run_code_package_test_unit(
    *,
    inventory: CodePackageTestInventory,
    unit: CodePackageTestUnitInventory,
    workspace_root: Path,
    package_root: Path,
    verbose: bool,
    fail_fast: bool,
    no_warnings: bool,
) -> CodePackageTestUnitRunReceipt:
    if not _is_supported_python_pytest_runnable_unit(inventory=inventory, unit=unit):
        return _unsupported_unit_receipt(
            inventory=inventory,
            unit=unit,
            duration_s=0.0,
            error=(
                "CodePackage test execution currently supports Python pytest units only: "
                + f"language={inventory.language.value} framework={unit.framework_name}"
            ),
        )

    result = _run_python_unit(
        inventory=inventory,
        unit=unit,
        workspace_root=workspace_root,
        package_root=package_root,
        verbose=verbose,
        fail_fast=fail_fast,
        no_warnings=no_warnings,
    )
    status: CodePackageTestRunStatus = "passed" if result.passed else "failed"
    return CodePackageTestUnitRunReceipt(
        code_package_id=inventory.code_package_id,
        code_package_code_id=unit.code_package_code_id,
        code_id=unit.code_id,
        code_section_id=unit.code_section_id,
        code_test_framework_id=unit.code_test_framework_id,
        code_test_id=unit.code_test_id,
        code_package_test_id=unit.code_package_test_id,
        code_test_unit_id=unit.code_test_unit_id,
        framework_name=unit.framework_name,
        relative_path=unit.relative_path,
        selector=unit.selector,
        unit_key=unit.unit_key,
        backend_kind=_BACKEND_KIND,
        status=status,
        exit_code=result.exit_code,
        total_tests=result.total_tests,
        passed_tests=result.passed_tests,
        failed_tests=result.failed_tests,
        skipped_tests=result.skipped_tests,
        duration_s=result.duration,
        failures=tuple(
            _failure_receipt_from_runner_failure(failure) for failure in result.failures
        ),
        error=None if result.passed else _failure_error(result),
    )


def _is_supported_python_pytest_runnable_unit(
    *,
    inventory: CodePackageTestInventory,
    unit: CodePackageTestUnitInventory,
) -> bool:
    return (
        inventory.language is CodeLanguage.python
        and unit.framework_name.strip().casefold() in {"pytest", "unittest"}
    )


def _run_python_pytest_unit_batch(
    *,
    inventory: CodePackageTestInventory,
    units: tuple[CodePackageTestUnitInventory, ...],
    workspace_root: Path,
    package_root: Path,
    verbose: bool,
    fail_fast: bool,
    no_warnings: bool,
) -> tuple[CodePackageTestUnitRunReceipt, ...]:
    result = _run_python_units(
        inventory=inventory,
        units=units,
        workspace_root=workspace_root,
        package_root=package_root,
        verbose=verbose,
        fail_fast=fail_fast,
        no_warnings=no_warnings,
    )
    test_cases_by_selector = _runner_test_cases_by_selector(
        result=result,
        units=units,
        package_root=package_root,
    )
    return tuple(
        _pytest_unit_receipt_from_batch_result(
            inventory=inventory,
            unit=unit,
            result=result,
            test_cases=test_cases_by_selector.get(unit.selector, ()),
            fail_fast=fail_fast,
        )
        for unit in units
    )


def _run_python_unit(
    *,
    inventory: CodePackageTestInventory,
    unit: CodePackageTestUnitInventory,
    workspace_root: Path,
    package_root: Path,
    verbose: bool,
    fail_fast: bool,
    no_warnings: bool,
) -> _RunnerTestResult:
    return _run_python_units(
        inventory=inventory,
        units=(unit,),
        workspace_root=workspace_root,
        package_root=package_root,
        verbose=verbose,
        fail_fast=fail_fast,
        no_warnings=no_warnings,
    )


def _run_python_units(
    *,
    inventory: CodePackageTestInventory,
    units: tuple[CodePackageTestUnitInventory, ...],
    workspace_root: Path,
    package_root: Path,
    verbose: bool,
    fail_fast: bool,
    no_warnings: bool,
) -> _RunnerTestResult:
    del inventory
    return _run_python_units_subprocess(
        units=units,
        workspace_root=workspace_root,
        package_root=package_root,
        verbose=verbose,
        fail_fast=fail_fast,
        no_warnings=no_warnings,
    )


def _run_python_units_subprocess(
    *,
    units: tuple[CodePackageTestUnitInventory, ...],
    workspace_root: Path,
    package_root: Path,
    verbose: bool,
    fail_fast: bool,
    no_warnings: bool,
) -> _SubprocessRunnerTestResult:
    pytest_args = _python_pytest_args(
        units=units,
        verbose=verbose,
        fail_fast=fail_fast,
        no_warnings=no_warnings,
    )
    with tempfile.TemporaryDirectory(prefix="aware-code-pytest-") as tmp_dir:
        result_path = Path(tmp_dir) / "result.json"
        env = _python_pytest_subprocess_env(
            workspace_root=workspace_root,
            package_root=package_root,
            result_path=result_path,
            pytest_args=pytest_args,
        )
        completed = subprocess.run(
            [sys.executable, "-c", _PYTEST_SUBPROCESS_SCRIPT],
            cwd=package_root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if not result_path.is_file():
            return _subprocess_infrastructure_failure_result(
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        try:
            payload = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return _subprocess_infrastructure_failure_result(
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=f"{completed.stderr}\n{exc}",
            )
    return _subprocess_runner_result_from_payload(payload=payload)


def _python_pytest_args(
    *,
    units: tuple[CodePackageTestUnitInventory, ...],
    verbose: bool,
    fail_fast: bool,
    no_warnings: bool,
) -> list[str]:
    pytest_args: list[str] = []
    if no_warnings:
        pytest_args.extend(["-p", "no:warnings"])
    if fail_fast:
        pytest_args.append("-x")
    pytest_args.append("--import-mode=importlib")
    pytest_args.extend(["--tb=no", "--no-header", "--disable-warnings", "-rN"])
    if not verbose:
        pytest_args.append("-q")
    else:
        pytest_args.extend(["-v", "--tb=short", "--log-cli-level=INFO"])
        if "--tb=no" in pytest_args:
            pytest_args.remove("--tb=no")
    pytest_args.extend(_pytest_selector_for_unit(unit) for unit in units)
    pytest_args.extend(["-p", "no:cacheprovider"])
    return pytest_args


def _python_pytest_subprocess_env(
    *,
    workspace_root: Path,
    package_root: Path,
    result_path: Path,
    pytest_args: list[str],
) -> dict[str, str]:
    env = os.environ.copy()
    for key in _PYTEST_SUBPROCESS_UNSET_ENV_KEYS:
        env.pop(key, None)
    pythonpath_entries = [
        package_root.resolve().as_posix(),
        workspace_root.resolve().as_posix(),
    ]
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_entries.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
    env["AWARE_CODE_PYTEST_ARGS_JSON"] = json.dumps(pytest_args)
    env["AWARE_CODE_PYTEST_RESULT_JSON"] = result_path.as_posix()
    env.setdefault("AWARE_RUNTIME_ACTOR_ROLE_ACL_MODE", "off")
    env.setdefault("PYTHONWARNINGS", "ignore")
    return env


def _subprocess_infrastructure_failure_result(
    *,
    returncode: int,
    stdout: str,
    stderr: str,
) -> _SubprocessRunnerTestResult:
    output = "\n".join(part.strip() for part in (stderr, stdout) if part.strip())
    failure_reason = output[-4000:] if output else "pytest subprocess did not report"
    failure = _SubprocessRunnerTestFailure(
        test_name="pytest_subprocess",
        failure_reason=failure_reason,
        file_path="",
    )
    return _SubprocessRunnerTestResult(
        exit_code=returncode or 1,
        passed=False,
        total_tests=0,
        passed_tests=0,
        failed_tests=1,
        skipped_tests=0,
        failures=[failure],
        test_cases=[],
        duration=0.0,
    )


def _subprocess_runner_result_from_payload(
    *,
    payload: object,
) -> _SubprocessRunnerTestResult:
    if not isinstance(payload, dict):
        return _subprocess_infrastructure_failure_result(
            returncode=1,
            stdout="",
            stderr="pytest subprocess wrote invalid result payload",
        )
    failures = [
        _subprocess_failure_from_payload(item)
        for item in _payload_list(payload.get("failures"))
    ]
    test_cases = [
        _subprocess_test_case_from_payload(item)
        for item in _payload_list(payload.get("test_cases"))
    ]
    return _SubprocessRunnerTestResult(
        exit_code=int(payload.get("exit_code") or 0),
        passed=bool(payload.get("passed")),
        total_tests=int(payload.get("total_tests") or 0),
        passed_tests=int(payload.get("passed_tests") or 0),
        failed_tests=int(payload.get("failed_tests") or 0),
        skipped_tests=int(payload.get("skipped_tests") or 0),
        failures=failures,
        test_cases=test_cases,
        duration=float(payload.get("duration") or 0.0),
    )


def _subprocess_failure_from_payload(payload: object) -> _SubprocessRunnerTestFailure:
    if not isinstance(payload, dict):
        return _SubprocessRunnerTestFailure(
            test_name="pytest",
            failure_reason=str(payload),
            file_path="",
        )
    runtime_diagnostic = payload.get("runtime_diagnostic")
    return _SubprocessRunnerTestFailure(
        test_name=str(payload.get("test_name") or ""),
        failure_reason=str(payload.get("failure_reason") or ""),
        file_path=str(payload.get("file_path") or ""),
        line_number=int(payload.get("line_number") or 0),
        runtime_diagnostic=(
            _subprocess_diagnostic_from_payload(runtime_diagnostic)
            if isinstance(runtime_diagnostic, dict)
            else None
        ),
    )


def _subprocess_test_case_from_payload(
    payload: object,
) -> _SubprocessRunnerTestCaseResult:
    if not isinstance(payload, dict):
        return _SubprocessRunnerTestCaseResult(
            nodeid=str(payload),
            test_name=str(payload),
            outcome="failed",
            failure=_SubprocessRunnerTestFailure(
                test_name=str(payload),
                failure_reason="Invalid pytest test case payload",
                file_path="",
            ),
        )
    failure = payload.get("failure")
    return _SubprocessRunnerTestCaseResult(
        nodeid=str(payload.get("nodeid") or ""),
        test_name=str(payload.get("test_name") or ""),
        outcome=str(payload.get("outcome") or ""),
        duration=float(payload.get("duration") or 0.0),
        failure=(
            _subprocess_failure_from_payload(failure)
            if isinstance(failure, dict)
            else None
        ),
    )


def _subprocess_diagnostic_from_payload(
    payload: dict[str, object],
) -> _SubprocessRunnerDiagnostic:
    return _SubprocessRunnerDiagnostic(
        code=str(payload.get("code") or ""),
        summary=str(payload.get("summary") or ""),
    )


def _payload_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _runner_test_cases_by_selector(
    *,
    result: _RunnerTestResult,
    units: tuple[CodePackageTestUnitInventory, ...],
    package_root: Path,
) -> dict[str, tuple[_RunnerTestCaseResult, ...]]:
    selectors_by_pytest_selector: dict[str, list[str]] = {}
    for unit in units:
        selectors_by_pytest_selector.setdefault(
            _pytest_selector_for_unit(unit), []
        ).append(unit.selector)
    pytest_selectors = tuple(selectors_by_pytest_selector)
    cases_by_selector: dict[str, list[_RunnerTestCaseResult]] = {}
    for test_case in getattr(result, "test_cases", ()) or ():
        pytest_selector = _selector_from_runner_nodeid(
            nodeid=test_case.nodeid,
            package_root=package_root,
        )
        selectors = selectors_by_pytest_selector.get(pytest_selector)
        if selectors is None:
            pytest_selector = _selector_from_runner_nodeid_suffix(
                nodeid=test_case.nodeid,
                selectors=pytest_selectors,
            )
            selectors = selectors_by_pytest_selector.get(pytest_selector)
        if selectors is None:
            continue
        for selector in selectors:
            cases_by_selector.setdefault(selector, []).append(test_case)
    return {
        selector: tuple(test_cases)
        for selector, test_cases in cases_by_selector.items()
    }


def _selector_from_runner_nodeid(*, nodeid: str, package_root: Path) -> str:
    normalized = nodeid.replace("\\", "/")
    package_name = package_root.name
    prefix = f"{package_name}/"
    if normalized.startswith(prefix):
        return normalized[len(prefix) :]
    package_root_text = package_root.as_posix().rstrip("/")
    prefix = f"{package_root_text}/"
    if normalized.startswith(prefix):
        return normalized[len(prefix) :]
    try:
        repo_relative_package_root = package_root.resolve().relative_to(
            Path.cwd().resolve()
        )
    except ValueError:
        repo_relative_package_root = None
    if repo_relative_package_root is not None:
        prefix = f"{repo_relative_package_root.as_posix().rstrip('/')}/"
        if normalized.startswith(prefix):
            return normalized[len(prefix) :]
    return normalized


def _selector_from_runner_nodeid_suffix(
    *,
    nodeid: str,
    selectors: tuple[str, ...],
) -> str:
    normalized = nodeid.replace("\\", "/")
    for selector in selectors:
        if (
            normalized == selector
            or normalized.endswith(f"/{selector}")
            or normalized.startswith(f"{selector}[")
            or f"/{selector}[" in normalized
        ):
            return selector
    return normalized


def _pytest_selector_for_unit(unit: CodePackageTestUnitInventory) -> str:
    framework_name = unit.framework_name.strip().casefold()
    if framework_name != "unittest":
        return unit.selector

    module_name = Path(unit.relative_path).with_suffix("").as_posix().replace("/", ".")
    prefix = f"{module_name}."
    if not unit.selector.startswith(prefix):
        return unit.selector
    qualname = unit.selector[len(prefix) :].replace(".", "::")
    return f"{unit.relative_path}::{qualname}"


def _pytest_unit_receipt_from_batch_result(
    *,
    inventory: CodePackageTestInventory,
    unit: CodePackageTestUnitInventory,
    result: _RunnerTestResult,
    test_cases: tuple[_RunnerTestCaseResult, ...],
    fail_fast: bool,
) -> CodePackageTestUnitRunReceipt:
    if not test_cases:
        status: CodePackageTestRunStatus = (
            "skipped" if fail_fast and result.exit_code != 0 else "failed"
        )
        error = (
            "Test runner did not report selected unit"
            if status == "failed"
            else "Test runner did not report selected unit after fail-fast"
        )
        return _unit_receipt(
            inventory=inventory,
            unit=unit,
            status=status,
            exit_code=result.exit_code if status == "failed" else 0,
            total_tests=0,
            passed_tests=0,
            failed_tests=1 if status == "failed" else 0,
            skipped_tests=1 if status == "skipped" else 0,
            duration_s=0.0,
            failures=(),
            error=error,
        )

    outcomes = tuple(
        (test_case.outcome or "").strip().casefold() for test_case in test_cases
    )
    failed_cases = tuple(
        test_case
        for test_case, outcome in zip(test_cases, outcomes, strict=True)
        if outcome not in {"passed", "skipped"}
    )
    passed_tests = sum(1 for outcome in outcomes if outcome == "passed")
    skipped_tests = sum(1 for outcome in outcomes if outcome == "skipped")
    failed_tests = len(failed_cases)
    total_tests = len(test_cases)
    duration_s = sum(float(test_case.duration or 0.0) for test_case in test_cases)

    if failed_tests == 0:
        status: CodePackageTestRunStatus = (
            "skipped" if skipped_tests == total_tests else "passed"
        )
        return _unit_receipt(
            inventory=inventory,
            unit=unit,
            status=status,
            exit_code=0,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=0,
            skipped_tests=skipped_tests,
            duration_s=duration_s,
            failures=(),
            error=None,
        )

    failures = tuple(
        _failure_receipt_from_runner_failure(test_case.failure)
        for test_case in failed_cases
        if test_case.failure is not None
    )
    error = "; ".join(
        failure.failure_reason for failure in failures if failure.failure_reason
    )
    return _unit_receipt(
        inventory=inventory,
        unit=unit,
        status="failed",
        exit_code=result.exit_code,
        total_tests=total_tests,
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        skipped_tests=skipped_tests,
        duration_s=duration_s,
        failures=failures,
        error=error or _failure_error(result),
    )


def _unit_receipt(
    *,
    inventory: CodePackageTestInventory,
    unit: CodePackageTestUnitInventory,
    status: CodePackageTestRunStatus,
    exit_code: int,
    total_tests: int,
    passed_tests: int,
    failed_tests: int,
    skipped_tests: int,
    duration_s: float,
    failures: tuple[CodePackageTestFailureReceipt, ...],
    error: str | None,
) -> CodePackageTestUnitRunReceipt:
    return CodePackageTestUnitRunReceipt(
        code_package_id=inventory.code_package_id,
        code_package_code_id=unit.code_package_code_id,
        code_id=unit.code_id,
        code_section_id=unit.code_section_id,
        code_test_framework_id=unit.code_test_framework_id,
        code_test_id=unit.code_test_id,
        code_package_test_id=unit.code_package_test_id,
        code_test_unit_id=unit.code_test_unit_id,
        framework_name=unit.framework_name,
        relative_path=unit.relative_path,
        selector=unit.selector,
        unit_key=unit.unit_key,
        backend_kind=_BACKEND_KIND,
        status=status,
        exit_code=exit_code,
        total_tests=total_tests,
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        skipped_tests=skipped_tests,
        duration_s=duration_s,
        failures=failures,
        error=error,
    )


def _unsupported_unit_receipt(
    *,
    inventory: CodePackageTestInventory,
    unit: CodePackageTestUnitInventory,
    duration_s: float,
    error: str,
) -> CodePackageTestUnitRunReceipt:
    return CodePackageTestUnitRunReceipt(
        code_package_id=inventory.code_package_id,
        code_package_code_id=unit.code_package_code_id,
        code_id=unit.code_id,
        code_section_id=unit.code_section_id,
        code_test_framework_id=unit.code_test_framework_id,
        code_test_id=unit.code_test_id,
        code_package_test_id=unit.code_package_test_id,
        code_test_unit_id=unit.code_test_unit_id,
        framework_name=unit.framework_name,
        relative_path=unit.relative_path,
        selector=unit.selector,
        unit_key=unit.unit_key,
        backend_kind=_BACKEND_KIND,
        status="unsupported",
        exit_code=1,
        total_tests=0,
        passed_tests=0,
        failed_tests=0,
        skipped_tests=0,
        duration_s=duration_s,
        error=error,
    )


def _select_units(
    *,
    inventory: CodePackageTestInventory,
    code_test_unit_ids: Iterable[UUID] | None,
    selectors: Iterable[str] | None,
) -> tuple[CodePackageTestUnitInventory, ...]:
    selected_unit_ids = frozenset(code_test_unit_ids or ())
    selected_selectors = frozenset(
        selector.strip() for selector in selectors or () if selector.strip()
    )
    if not selected_unit_ids and not selected_selectors:
        return inventory.units
    return tuple(
        unit
        for unit in inventory.units
        if (not selected_unit_ids or unit.code_test_unit_id in selected_unit_ids)
        and (not selected_selectors or unit.selector in selected_selectors)
    )


def _resolve_package_root(*, workspace_root: Path, package_root: str) -> Path:
    package_root_path = Path(package_root)
    if package_root_path.is_absolute():
        return package_root_path.resolve()
    return (workspace_root / package_root_path).resolve()


def _failure_receipt_from_runner_failure(
    failure: _RunnerTestFailure,
) -> CodePackageTestFailureReceipt:
    diagnostic = failure.runtime_diagnostic
    return CodePackageTestFailureReceipt(
        test_name=failure.test_name,
        failure_reason=failure.failure_reason,
        file_path=failure.file_path,
        line_number=failure.line_number,
        runtime_diagnostic_code=diagnostic.code if diagnostic is not None else None,
        runtime_diagnostic_summary=(
            diagnostic.summary if diagnostic is not None else None
        ),
    )


def _failure_error(result: _RunnerTestResult) -> str:
    if result.failures:
        return "; ".join(
            failure.failure_reason
            for failure in result.failures
            if failure.failure_reason
        )
    return f"Test runner exited with code {result.exit_code}"


def _aggregate_status(
    unit_receipts: tuple[CodePackageTestUnitRunReceipt, ...],
) -> CodePackageTestRunStatus:
    if not unit_receipts:
        return "skipped"
    statuses = {receipt.status for receipt in unit_receipts}
    if "failed" in statuses:
        return "failed"
    if statuses == {"unsupported"}:
        return "unsupported"
    if "unsupported" in statuses:
        return "failed"
    if statuses == {"skipped"}:
        return "skipped"
    return "passed"


def _aggregate_error(
    unit_receipts: tuple[CodePackageTestUnitRunReceipt, ...]
) -> str | None:
    errors = tuple(receipt.error for receipt in unit_receipts if receipt.error)
    if not errors:
        return None
    return "; ".join(errors)


def _group_unit_receipts_by_code_package_test_id(
    unit_receipts: tuple[CodePackageTestUnitRunReceipt, ...],
) -> dict[UUID, tuple[CodePackageTestUnitRunReceipt, ...]]:
    grouped: dict[UUID, list[CodePackageTestUnitRunReceipt]] = {}
    for unit_receipt in unit_receipts:
        grouped.setdefault(unit_receipt.code_package_test_id, []).append(unit_receipt)
    return {
        code_package_test_id: tuple(grouped_unit_receipts)
        for code_package_test_id, grouped_unit_receipts in grouped.items()
    }


def _find_code_package_test(
    *, code_package: CodePackage, code_package_test_id: UUID
) -> CodePackageTest:
    for code_package_test in code_package.tests:
        if code_package_test.id == code_package_test_id:
            return code_package_test
    raise RuntimeError(
        "CodePackage test run receipt references a CodePackageTest not attached to the package: "
        + f"code_package_id={code_package.id} code_package_test_id={code_package_test_id}"
    )


def _ontology_status(status: CodePackageTestRunStatus) -> OntologyCodeTestRunStatus:
    return OntologyCodeTestRunStatus(status)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


__all__ = [
    "CodePackageTestFailureReceipt",
    "CodePackageTestRunReceipt",
    "CodePackageTestRunStatus",
    "CodePackageTestUnitRunReceipt",
    "build_ephemeral_code_package_test_runs_from_receipt",
    "materialize_code_package_test_run_receipt",
    "run_code_package_test_inventory",
]
