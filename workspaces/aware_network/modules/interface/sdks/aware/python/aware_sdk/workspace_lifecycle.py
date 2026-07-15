"""Fresh-root Workspace lifecycle proof for the public aware-sdk rail."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
from typing import Any


class WorkspaceLifecycleProofError(RuntimeError):
    """Raised when the fresh-root Workspace lifecycle proof fails."""


@dataclass(slots=True, frozen=True)
class WorkspaceLifecycleCommandResult:
    """One executed fresh-root lifecycle command and its captured output."""

    step_id: str
    raw_command: str
    resolved_command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    payload: dict[str, Any] | None


@dataclass(slots=True, frozen=True)
class WorkspaceLifecycleProofResult:
    """Receipt metadata for one fresh-root Workspace lifecycle proof."""

    receipt_path: Path
    workspace_root: Path
    module_id: str
    command_results: tuple[WorkspaceLifecycleCommandResult, ...]
    summary: dict[str, Any]


Runner = Callable[
    [Sequence[str], Path],
    subprocess.CompletedProcess[str],
]


@dataclass(slots=True, frozen=True)
class _WorkspaceLifecycleStep:
    step_id: str
    command: tuple[str, ...]
    validate: Callable[[WorkspaceLifecycleCommandResult, Path, str], dict[str, Any]]


def _run_subprocess(
    command: Sequence[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def run_workspace_lifecycle_proof(
    *,
    aware_cli_executable: Path,
    validation_root: Path,
    receipt_path: Path | None = None,
    module_id: str = "sample",
    runner: Runner = _run_subprocess,
) -> WorkspaceLifecycleProofResult:
    """Run the fresh-root Workspace lifecycle against one installed aware-cli."""

    resolved_validation_root = validation_root.resolve()
    resolved_validation_root.mkdir(parents=True, exist_ok=True)
    resolved_workspace_root = (
        resolved_validation_root / "workspace-lifecycle" / "fresh-root"
    ).resolve()
    resolved_workspace_root.mkdir(parents=True, exist_ok=True)
    resolved_receipt_path = (
        receipt_path.resolve()
        if receipt_path is not None
        else (
            resolved_validation_root / "receipts" / "workspace-lifecycle.json"
        ).resolve()
    )
    resolved_receipt_path.parent.mkdir(parents=True, exist_ok=True)

    if not aware_cli_executable.is_file():
        raise FileNotFoundError(
            f"Installed aware-cli launcher not found: {aware_cli_executable}"
        )

    steps = _build_steps(
        aware_cli_executable=aware_cli_executable.resolve(),
        workspace_root=resolved_workspace_root,
        module_id=module_id,
    )
    command_results: list[WorkspaceLifecycleCommandResult] = []
    command_order = [step.step_id for step in steps]
    step_summaries: dict[str, Any] = {}
    status = "verified"
    failure_message: str | None = None

    for step in steps:
        process = runner(step.command, resolved_validation_root)
        payload = _load_json_object_from_command_stdout(process.stdout)
        result = WorkspaceLifecycleCommandResult(
            step_id=step.step_id,
            raw_command=_render_command(step.command),
            resolved_command=tuple(str(part) for part in step.command),
            returncode=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
            payload=payload,
        )
        command_results.append(result)
        if process.returncode != 0:
            status = "command_failed"
            failure_message = (
                f"Workspace lifecycle step '{step.step_id}' failed "
                + f"({process.returncode}): {result.raw_command}"
            )
            break
        try:
            step_summaries[step.step_id] = step.validate(
                result, resolved_workspace_root, module_id
            )
        except WorkspaceLifecycleProofError as exc:
            status = "contract_failed"
            failure_message = str(exc)
            break

    summary = {
        "workspace_root": str(resolved_workspace_root),
        "module_id": module_id,
        "command_order": command_order,
        **step_summaries,
    }
    receipt_payload = {
        "receipt_version": 1,
        "status": status,
        "failure_message": failure_message,
        "workspace_root": str(resolved_workspace_root),
        "module_id": module_id,
        "summary": summary,
        "command_results": [
            {
                "step_id": result.step_id,
                "raw_command": result.raw_command,
                "resolved_command": list(result.resolved_command),
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "payload": result.payload,
            }
            for result in command_results
        ],
        "verified_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    resolved_receipt_path.write_text(
        json.dumps(receipt_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if status != "verified":
        raise WorkspaceLifecycleProofError(
            f"{failure_message}. Workspace lifecycle receipt: {resolved_receipt_path}"
        )

    return WorkspaceLifecycleProofResult(
        receipt_path=resolved_receipt_path,
        workspace_root=resolved_workspace_root,
        module_id=module_id,
        command_results=tuple(command_results),
        summary=summary,
    )


def _build_steps(
    *,
    aware_cli_executable: Path,
    workspace_root: Path,
    module_id: str,
) -> tuple[_WorkspaceLifecycleStep, ...]:
    workspace_root_text = str(workspace_root)
    return (
        _WorkspaceLifecycleStep(
            step_id="initial_status",
            command=(
                str(aware_cli_executable),
                "workspace",
                "status",
                "--repo-root",
                workspace_root_text,
                "--json",
            ),
            validate=_validate_initial_status_step,
        ),
        _WorkspaceLifecycleStep(
            step_id="bootstrap",
            command=(
                str(aware_cli_executable),
                "workspace",
                "bootstrap",
                "--repo-root",
                workspace_root_text,
                "--json",
            ),
            validate=_validate_bootstrap_step,
        ),
        _WorkspaceLifecycleStep(
            step_id="post_bootstrap_status",
            command=(
                str(aware_cli_executable),
                "workspace",
                "status",
                "--repo-root",
                workspace_root_text,
                "--json",
            ),
            validate=_validate_post_bootstrap_status_step,
        ),
        _WorkspaceLifecycleStep(
            step_id="empty_workspace_compile",
            command=(
                str(aware_cli_executable),
                "workspace",
                "compile",
                "--repo-root",
                workspace_root_text,
                "--json",
            ),
            validate=_validate_empty_workspace_compile_step,
        ),
        _WorkspaceLifecycleStep(
            step_id="module_create",
            command=(
                str(aware_cli_executable),
                "module",
                "create",
                module_id,
                "--repo-root",
                workspace_root_text,
                "--json",
            ),
            validate=_validate_module_create_step,
        ),
        _WorkspaceLifecycleStep(
            step_id="module_compile",
            command=(
                str(aware_cli_executable),
                "compile",
                "--repo-root",
                workspace_root_text,
                "--materialization-mode",
                "runtime",
                "--lock-mode",
                "off",
                "--json",
                "module",
                module_id,
            ),
            validate=_validate_module_compile_step,
        ),
    )


def _validate_initial_status_step(
    result: WorkspaceLifecycleCommandResult,
    workspace_root: Path,
    module_id: str,
) -> dict[str, Any]:
    _ = (workspace_root, module_id)
    payload = _require_payload(result, step_id=result.step_id)
    readiness = _require_mapping(
        payload.get("readiness"), field_name="initial_status.readiness"
    )
    call_to_action = _require_mapping(
        readiness.get("call_to_action"),
        field_name="initial_status.readiness.call_to_action",
    )
    summary_kind = _required_string(
        readiness.get("summary_kind"),
        field_name="initial_status.readiness.summary_kind",
    )
    if summary_kind != "bootstrap_required":
        raise WorkspaceLifecycleProofError(
            "Fresh-root initial status must report readiness.summary_kind=bootstrap_required."
        )
    action_id = _required_string(
        call_to_action.get("action_id"),
        field_name="initial_status.readiness.call_to_action.action_id",
    )
    if action_id != "workspace_bootstrap":
        raise WorkspaceLifecycleProofError(
            "Fresh-root initial status must point at the canonical workspace_bootstrap CTA."
        )
    return {
        "status_version": _required_string(
            payload.get("status_version"),
            field_name="initial_status.status_version",
        ),
        "summary_kind": summary_kind,
        "workspace_state": _required_string(
            readiness.get("workspace_state"),
            field_name="initial_status.readiness.workspace_state",
        ),
        "workspace_manifest_present": bool(
            readiness.get("workspace_manifest_present", False)
        ),
        "environment_manifest_present": bool(
            readiness.get("environment_manifest_present", False)
        ),
        "cta_action_id": action_id,
        "cta_command": _required_string(
            call_to_action.get("command"),
            field_name="initial_status.readiness.call_to_action.command",
        ),
    }


def _validate_bootstrap_step(
    result: WorkspaceLifecycleCommandResult,
    workspace_root: Path,
    module_id: str,
) -> dict[str, Any]:
    _ = module_id
    payload = _require_payload(result, step_id=result.step_id)
    status = _required_string(payload.get("status"), field_name="bootstrap.status")
    if status != "ok":
        raise WorkspaceLifecycleProofError(
            "Workspace bootstrap proof must return status=ok."
        )
    bootstrap_summary = _require_mapping(
        payload.get("bootstrap_summary"),
        field_name="bootstrap.bootstrap_summary",
    )
    summary_kind = _required_string(
        bootstrap_summary.get("summary_kind"),
        field_name="bootstrap.bootstrap_summary.summary_kind",
    )
    if summary_kind != "ready_for_module_creation":
        raise WorkspaceLifecycleProofError(
            "Workspace bootstrap proof must report ready_for_module_creation."
        )
    next_action_ids = _extract_action_ids(payload.get("next_required_actions"))
    if "module_create_explicit" not in next_action_ids:
        raise WorkspaceLifecycleProofError(
            "Workspace bootstrap proof must advertise module_create_explicit as the next config action."
        )
    workspace_manifest = _require_mapping(
        payload.get("workspace_manifest"),
        field_name="bootstrap.workspace_manifest",
    )
    workspace_manifest_path = Path(
        _required_string(
            workspace_manifest.get("path"),
            field_name="bootstrap.workspace_manifest.path",
        )
    ).resolve()
    if workspace_manifest_path != (workspace_root / "aware.workspace.toml").resolve():
        raise WorkspaceLifecycleProofError(
            "Workspace bootstrap proof wrote an unexpected aware.workspace.toml path."
        )
    return {
        "status": status,
        "summary_kind": summary_kind,
        "workspace_manifest_path": str(workspace_manifest_path),
        "workspace_manifest_created": bool(workspace_manifest.get("created", False)),
        "next_action_ids": next_action_ids,
    }


def _validate_post_bootstrap_status_step(
    result: WorkspaceLifecycleCommandResult,
    workspace_root: Path,
    module_id: str,
) -> dict[str, Any]:
    _ = (workspace_root, module_id)
    payload = _require_payload(result, step_id=result.step_id)
    readiness = _require_mapping(
        payload.get("readiness"),
        field_name="post_bootstrap_status.readiness",
    )
    summary_kind = _required_string(
        readiness.get("summary_kind"),
        field_name="post_bootstrap_status.readiness.summary_kind",
    )
    if summary_kind != "workspace_ready_no_history":
        raise WorkspaceLifecycleProofError(
            "Post-bootstrap workspace status must report workspace_ready_no_history."
        )
    return {
        "status_version": _required_string(
            payload.get("status_version"),
            field_name="post_bootstrap_status.status_version",
        ),
        "summary_kind": summary_kind,
        "workspace_state": _required_string(
            readiness.get("workspace_state"),
            field_name="post_bootstrap_status.readiness.workspace_state",
        ),
        "history_state": _required_string(
            readiness.get("history_state"),
            field_name="post_bootstrap_status.readiness.history_state",
        ),
    }


def _validate_empty_workspace_compile_step(
    result: WorkspaceLifecycleCommandResult,
    workspace_root: Path,
    module_id: str,
) -> dict[str, Any]:
    _ = (workspace_root, module_id)
    payload = _require_payload(result, step_id=result.step_id)
    preflight_status = _required_string(
        payload.get("preflight_status"),
        field_name="empty_workspace_compile.preflight_status",
    )
    if preflight_status != "ok":
        raise WorkspaceLifecycleProofError(
            "Fresh-root workspace compile proof must complete preflight with status=ok."
        )
    diagnostic = _require_mapping(
        payload.get("diagnostic"),
        field_name="empty_workspace_compile.diagnostic",
    )
    diagnostic_code = _required_string(
        diagnostic.get("code"),
        field_name="empty_workspace_compile.diagnostic.code",
    )
    if diagnostic_code != "workspace.compile.workspace_manifest_empty":
        raise WorkspaceLifecycleProofError(
            "Fresh-root workspace compile proof must preserve workspace_manifest_empty diagnostic."
        )
    next_action_ids = _extract_action_ids(diagnostic.get("next_required_actions"))
    if "module_create_explicit" not in next_action_ids:
        raise WorkspaceLifecycleProofError(
            "Fresh-root workspace compile proof must advertise module_create_explicit."
        )
    return {
        "preflight_status": preflight_status,
        "diagnostic_code": diagnostic_code,
        "target_scope": payload.get("target_scope"),
        "target_ref": payload.get("target_ref"),
        "next_action_ids": next_action_ids,
    }


def _validate_module_create_step(
    result: WorkspaceLifecycleCommandResult,
    workspace_root: Path,
    module_id: str,
) -> dict[str, Any]:
    payload = _require_payload(result, step_id=result.step_id)
    status = _required_string(payload.get("status"), field_name="module_create.status")
    if status != "ok":
        raise WorkspaceLifecycleProofError(
            "Workspace module create proof must return status=ok."
        )
    module_root = Path(
        _required_string(
            payload.get("module_root"), field_name="module_create.module_root"
        )
    ).resolve()
    expected_module_root = (workspace_root / "modules" / module_id).resolve()
    if module_root != expected_module_root:
        raise WorkspaceLifecycleProofError(
            "Workspace module create proof must scaffold the sample module inside "
            f"the fresh workspace modules directory: {expected_module_root}."
        )
    if not module_root.is_dir():
        raise WorkspaceLifecycleProofError(
            f"Workspace module create proof reported a missing module root: {module_root}."
        )
    next_steps = _extract_string_list(payload.get("next_steps"))
    root_pyproject = _as_mapping(payload.get("root_pyproject"))
    return {
        "status": status,
        "module_root": str(module_root),
        "planned_action": _optional_string(
            root_pyproject.get("planned_action") if root_pyproject is not None else None
        ),
        "next_steps": next_steps,
    }


def _validate_module_compile_step(
    result: WorkspaceLifecycleCommandResult,
    workspace_root: Path,
    module_id: str,
) -> dict[str, Any]:
    payload = _require_payload(result, step_id=result.step_id)
    latest_report_path = (
        workspace_root / ".aware" / "reports" / "latest_compile_success.json"
    ).resolve()
    if not latest_report_path.is_file():
        raise WorkspaceLifecycleProofError(
            "Fresh-root module compile proof did not emit .aware/reports/latest_compile_success.json."
        )
    latest_report = _load_json_object(latest_report_path)
    scope_kind = _required_string(
        latest_report.get("scope_kind"),
        field_name="module_compile.latest_report.scope_kind",
    )
    scope_key = _required_string(
        latest_report.get("scope_key"),
        field_name="module_compile.latest_report.scope_key",
    )
    if scope_kind != "module" or scope_key != module_id:
        raise WorkspaceLifecycleProofError(
            "Fresh-root module compile proof must emit a latest module compile success report."
        )
    return {
        "target_scope": payload.get("target_scope"),
        "target_ref": payload.get("target_ref"),
        "preflight_status": payload.get("preflight_status"),
        "latest_report_path": str(latest_report_path),
        "scope_kind": scope_kind,
        "scope_key": scope_key,
    }


def _require_payload(
    result: WorkspaceLifecycleCommandResult,
    *,
    step_id: str,
) -> dict[str, Any]:
    payload = result.payload
    if not isinstance(payload, dict):
        raise WorkspaceLifecycleProofError(
            f"Workspace lifecycle step '{step_id}' must emit a JSON object."
        )
    return payload


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise WorkspaceLifecycleProofError(f"Expected JSON object at {path}.")
    return payload


def _load_json_object_from_command_stdout(stdout: str) -> dict[str, Any] | None:
    raw_stdout = stdout.strip()
    if not raw_stdout:
        return None
    json_start = raw_stdout.find("{")
    if json_start < 0:
        return None
    try:
        payload = json.loads(raw_stdout[json_start:])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _render_command(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _require_mapping(value: object, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WorkspaceLifecycleProofError(
            f"Workspace lifecycle proof requires JSON object field: {field_name}"
        )
    return value


def _as_mapping(value: object) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _required_string(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkspaceLifecycleProofError(
            f"Workspace lifecycle proof requires non-empty string field: {field_name}"
        )
    return value.strip()


def _optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _extract_action_ids(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    action_ids: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        raw_action_id = item.get("action_id")
        if isinstance(raw_action_id, str) and raw_action_id.strip():
            action_ids.append(raw_action_id.strip())
            continue
        raw_code = item.get("code")
        if isinstance(raw_code, str) and raw_code.strip():
            action_ids.append(raw_code.strip())
    return action_ids


def _extract_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    strings: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            strings.append(item.strip())
    return strings
