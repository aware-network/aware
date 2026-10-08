from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_IDS: tuple[str, ...] = (
    "AR-01",
    "AR-02",
    "AR-03",
    "AR-04",
    "AR-05",
    "AR-06",
    "AR-07",
    "AR-08",
    "AR-09",
    "AR-10",
)
ALLOWED_STATUSES: set[str] = {"pass", "fail", "skip"}
PROTOCOL_VERSION = "act-react.v1"
STEP_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
STEP_KINDS: set[str] = {
    "input",
    "let",
    "expect_event_config",
    "intent_action_config",
    "invoke",
}
CONTRACT_ONLY_STEP_KINDS: set[str] = {
    "expect_event_config",
    "intent_action_config",
}
PURE_STEP_KINDS: set[str] = STEP_KINDS - {"invoke"}


@dataclass(frozen=True, slots=True)
class ConformanceRow:
    check_id: str
    status: str
    details: str


@dataclass(frozen=True, slots=True)
class ConformanceReport:
    protocol_version: str
    runtime_id: str
    rows: tuple[ConformanceRow, ...]


def _load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("report root must be a JSON object")
    return raw


def _parse_report(payload: dict[str, Any]) -> ConformanceReport:
    protocol_version = str(payload.get("protocol_version") or "").strip()
    runtime_id = str(payload.get("runtime_id") or "").strip()
    raw_results = payload.get("results")

    if not protocol_version:
        raise ValueError("missing protocol_version")
    if protocol_version != PROTOCOL_VERSION:
        raise ValueError(
            f"unsupported protocol_version={protocol_version!r} (expected {PROTOCOL_VERSION!r})"
        )
    if not runtime_id:
        raise ValueError("missing runtime_id")
    if not isinstance(raw_results, list):
        raise ValueError("results must be an array")

    rows: list[ConformanceRow] = []
    for index, item in enumerate(raw_results):
        if not isinstance(item, dict):
            raise ValueError(f"results[{index}] must be an object")
        check_id = str(item.get("id") or "").strip()
        status = str(item.get("status") or "").strip().lower()
        details = str(item.get("details") or "").strip()
        if not check_id:
            raise ValueError(f"results[{index}] missing id")
        if status not in ALLOWED_STATUSES:
            raise ValueError(
                f"results[{index}] invalid status={status!r} (allowed={sorted(ALLOWED_STATUSES)})"
            )
        rows.append(
            ConformanceRow(
                check_id=check_id,
                status=status,
                details=details,
            )
        )

    return ConformanceReport(
        protocol_version=protocol_version,
        runtime_id=runtime_id,
        rows=tuple(rows),
    )


def _validate_report(
    report: ConformanceReport,
    *,
    allow_skip: bool,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    by_id: dict[str, ConformanceRow] = {}

    for row in report.rows:
        if row.check_id in by_id:
            errors.append(f"duplicate result id: {row.check_id}")
            continue
        by_id[row.check_id] = row

    required = set(REQUIRED_IDS)
    seen = set(by_id.keys())

    missing = sorted(required - seen)
    unknown = sorted(seen - required)
    for check_id in missing:
        errors.append(f"missing required result id: {check_id}")
    for check_id in unknown:
        errors.append(f"unknown result id: {check_id}")

    for check_id in REQUIRED_IDS:
        row = by_id.get(check_id)
        if row is None:
            continue
        if row.status == "fail":
            errors.append(
                f"{check_id} failed"
                + (f" ({row.details})" if row.details else "")
            )
        if row.status == "skip" and not allow_skip:
            errors.append(
                f"{check_id} skipped (use --allow-skip for incremental adoption)"
            )

    ok = not errors
    summary = [
        f"protocol_version={report.protocol_version}",
        f"runtime_id={report.runtime_id}",
        f"results={len(report.rows)}",
        f"required={len(REQUIRED_IDS)}",
        f"status={'PASS' if ok else 'FAIL'}",
    ]
    return ok, summary + errors


def _validate_program_ir(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []

    version = str(payload.get("version") or "").strip()
    if version != PROTOCOL_VERSION:
        errors.append(
            f"program_ir.version must be {PROTOCOL_VERSION!r}; got {version!r}"
        )

    program_ref = str(payload.get("program_ref") or "").strip()
    if not program_ref:
        errors.append("program_ir.program_ref is required")

    raw_steps = payload.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        errors.append("program_ir.steps must be a non-empty array")
        raw_steps = []

    seen_step_ids: set[str] = set()
    for index, raw_step in enumerate(raw_steps):
        if not isinstance(raw_step, dict):
            errors.append(f"program_ir.steps[{index}] must be an object")
            continue

        step_id = str(raw_step.get("step_id") or "").strip()
        if not step_id:
            errors.append(f"program_ir.steps[{index}] missing step_id")
        elif not STEP_ID_PATTERN.fullmatch(step_id):
            errors.append(
                f"program_ir.steps[{index}] invalid step_id format: {step_id!r}"
            )
        elif step_id in seen_step_ids:
            errors.append(f"program_ir duplicate step_id: {step_id!r}")
        else:
            seen_step_ids.add(step_id)

        kind = str(raw_step.get("kind") or "").strip()
        if kind not in STEP_KINDS:
            errors.append(f"program_ir.steps[{index}] unknown kind: {kind!r}")
            continue

        if kind == "invoke":
            invoke_kind = str(raw_step.get("invoke_kind") or "").strip()
            if invoke_kind != "effect":
                errors.append(
                    "program_ir invoke step must set invoke_kind='effect'"
                )
            if not isinstance(raw_step.get("call"), dict):
                errors.append("program_ir invoke step must include call object")
        else:
            if "invoke_kind" in raw_step:
                errors.append(
                    f"program_ir.steps[{index}] pure step must not declare invoke_kind"
                )
            if "call" in raw_step:
                errors.append(
                    f"program_ir.steps[{index}] pure step must not declare call"
                )

        if kind in CONTRACT_ONLY_STEP_KINDS:
            if "invoke_kind" in raw_step or "call" in raw_step:
                errors.append(
                    f"program_ir.steps[{index}] contract-only step cannot carry effects"
                )

    ok = not errors
    summary = [
        f"program_ir.version={version or '<missing>'}",
        f"program_ir.program_ref={program_ref or '<missing>'}",
        f"program_ir.steps={len(raw_steps)}",
        f"program_ir.pure_step_kinds={sorted(PURE_STEP_KINDS)}",
        f"program_ir.status={'PASS' if ok else 'FAIL'}",
    ]
    return ok, summary + errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate ACT-REACT v1 conformance report."
    )
    parser.add_argument(
        "--report",
        type=Path,
        required=True,
        help="Path to report JSON.",
    )
    parser.add_argument(
        "--allow-skip",
        action="store_true",
        help="Allow 'skip' status without failing.",
    )
    parser.add_argument(
        "--program-ir",
        type=Path,
        help=(
            "Optional path to Program IR JSON. When provided, validates "
            "step_id presence/uniqueness and invoke-only effect boundary."
        ),
    )
    args = parser.parse_args()

    try:
        payload = _load_json(args.report)
        report = _parse_report(payload)
        report_ok, report_lines = _validate_report(report, allow_skip=args.allow_skip)
        ir_ok = True
        ir_lines: list[str] = []
        if args.program_ir is not None:
            ir_payload = _load_json(args.program_ir)
            ir_ok, ir_lines = _validate_program_ir(ir_payload)
        ok = report_ok and ir_ok
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        return 1

    for line in report_lines:
        print(f"report:{line}")
    for line in ir_lines:
        print(f"program_ir:{line}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
