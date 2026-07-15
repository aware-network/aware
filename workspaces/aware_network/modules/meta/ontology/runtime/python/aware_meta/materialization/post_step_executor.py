from __future__ import annotations

import importlib
import os
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter

from aware_code.language.tooling import CodeLanguageToolSpec
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization.artifact_lifecycle import (
    LanguageMaterializationProducerStep,
)
from aware_meta.materialization.post_step_plan import (
    LanguageMaterializationPostStepInput,
    LanguageMaterializationPostStepPlanItem,
    LanguageMaterializationPostStepPlanRequest,
    plan_language_materialization_post_steps,
)
from aware_meta.materialization.post_step_target_result import (
    LanguageMaterializationPostStepExecutionResult,
    LanguageMaterializationPostStepPackageContext,
    LanguageMaterializationPostStepTargetDiscoveryRequest,
    discover_language_materialization_post_step_targets,
)
from aware_meta.materialization.tool_runner import (
    LanguageMaterializationToolCommandRequest,
    prepare_language_materialization_tool_command,
    resolve_language_materialization_tool_spec,
)


_PYTHON_API_BACKEND = "python_api"
_CLI_BACKEND = "cli"
_FORMATTER_ROLE = "formatter"


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepExecutionRequest:
    target_language_plugin_id: CodeLanguage
    output_root: Path
    generated_file_paths: tuple[Path, ...] = ()
    package_name: str | None = None
    materialization_source: str | None = None
    renderer_profile: str | None = None
    renderer_kind: str | None = None
    explicit_steps: tuple[LanguageMaterializationPostStepInput, ...] = ()
    timeout_s: float | None = None
    tool_env_by_tool_id: Mapping[str, Mapping[str, str]] = field(default_factory=dict)
    executable_overrides_by_tool_id: Mapping[str, Mapping[str, str]] = field(
        default_factory=dict
    )


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepReceipt:
    tool_id: str
    target_language_plugin_id: CodeLanguage
    status: str
    backend: str
    role: str
    output_root: Path
    package_name: str | None = None
    materialization_source: str | None = None
    renderer_profile: str | None = None
    renderer_kind: str | None = None
    source: str = "default"
    target_count: int = 0
    changed_path_count: int = 0
    produced_path_count: int = 0
    duration_s: float = 0.0
    warning_count: int = 0
    state_env: Mapping[str, str] = field(default_factory=dict)
    executable_overrides: Mapping[str, str] = field(default_factory=dict)

    def as_payload(self) -> dict[str, object]:
        return {
            "schema": ("aware.meta.language_materialization.post_step_receipt.v1"),
            "tool_id": self.tool_id,
            "target_language_plugin_id": self.target_language_plugin_id.value,
            "status": self.status,
            "backend": self.backend,
            "role": self.role,
            "output_root": self.output_root.as_posix(),
            "package_name": self.package_name,
            "materialization_source": self.materialization_source,
            "renderer_profile": self.renderer_profile,
            "renderer_kind": self.renderer_kind,
            "source": self.source,
            "target_count": self.target_count,
            "changed_path_count": self.changed_path_count,
            "produced_path_count": self.produced_path_count,
            "duration_s": self.duration_s,
            "warning_count": self.warning_count,
            "state_env": dict(self.state_env),
            "executable_overrides": dict(self.executable_overrides),
        }


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepExecution:
    execution_results: tuple[LanguageMaterializationPostStepExecutionResult, ...] = ()
    receipts: tuple[dict[str, object], ...] = ()
    warnings: tuple[str, ...] = ()
    metrics: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class _LanguageMaterializationToolEffects:
    changed_paths: tuple[Path, ...] = ()
    produced_paths: tuple[Path, ...] = ()


def execute_language_materialization_post_steps(
    request: LanguageMaterializationPostStepExecutionRequest,
) -> LanguageMaterializationPostStepExecution:
    """Execute materialization post-steps declared by Code plugins."""

    generated_file_paths = _existing_files(request.generated_file_paths)
    package_contexts = _package_contexts(
        request=request,
        generated_file_paths=generated_file_paths,
    )
    plan = plan_language_materialization_post_steps(
        LanguageMaterializationPostStepPlanRequest(
            target_language_plugin_id=request.target_language_plugin_id,
            explicit_steps=request.explicit_steps,
            has_packages=bool(package_contexts),
        )
    )
    warnings: list[str] = list(plan.warnings)
    execution_results: list[LanguageMaterializationPostStepExecutionResult] = []
    receipts: list[dict[str, object]] = []

    for step in plan.steps:
        spec = resolve_language_materialization_tool_spec(
            target_language_plugin_id=request.target_language_plugin_id,
            tool_id=step.tool_id,
        )
        targets = _step_targets(
            request=request,
            step=step,
            package_contexts=package_contexts,
            generated_file_paths=generated_file_paths,
        )
        state_env = _tool_state_env(request=request, spec=spec)
        executable_overrides = _tool_executable_overrides(
            request=request,
            spec=spec,
        )
        started_at = perf_counter()
        try:
            effects = _execute_tool(
                spec=spec,
                targets=targets,
                args=step.args,
                cwd=request.output_root,
                timeout_s=request.timeout_s,
                state_env=state_env,
                executable_overrides=executable_overrides,
            )
            duration_s = round(perf_counter() - started_at, 6)
            execution_results.append(
                LanguageMaterializationPostStepExecutionResult(
                    tool_id=spec.tool_id,
                    package_name=request.package_name,
                    package_root=request.output_root.resolve(),
                    target_paths=targets,
                    changed_paths=effects.changed_paths,
                    produced_paths=effects.produced_paths,
                    producer_step=(
                        LanguageMaterializationProducerStep.format_
                        if spec.role == _FORMATTER_ROLE
                        else LanguageMaterializationProducerStep.post_step
                    ),
                )
            )
            receipts.append(
                _receipt(
                    request=request,
                    spec=spec,
                    step=step,
                    status="succeeded",
                    target_count=len(targets),
                    changed_path_count=len(effects.changed_paths),
                    produced_path_count=len(effects.produced_paths),
                    duration_s=duration_s,
                    state_env=state_env,
                    executable_overrides=executable_overrides,
                ).as_payload()
            )
        except Exception as exc:
            if step.on_fail != "warn":
                raise
            duration_s = round(perf_counter() - started_at, 6)
            warning = f"Materialization post-step {spec.tool_id!r} failed: {exc}"
            warnings.append(warning)
            receipts.append(
                _receipt(
                    request=request,
                    spec=spec,
                    step=step,
                    status="failed",
                    target_count=len(targets),
                    duration_s=duration_s,
                    warning_count=1,
                    state_env=state_env,
                    executable_overrides=executable_overrides,
                ).as_payload()
            )

    return LanguageMaterializationPostStepExecution(
        execution_results=tuple(execution_results),
        receipts=tuple(receipts),
        warnings=tuple(warnings),
        metrics={
            **plan.metrics,
            "post_step_receipt_count": len(receipts),
            "post_step_target_count": sum(
                receipt.get("target_count", 0) for receipt in receipts
            ),
            "post_step_changed_path_count": sum(
                receipt.get("changed_path_count", 0) for receipt in receipts
            ),
        },
    )


def _package_contexts(
    *,
    request: LanguageMaterializationPostStepExecutionRequest,
    generated_file_paths: tuple[Path, ...],
) -> tuple[LanguageMaterializationPostStepPackageContext, ...]:
    if not generated_file_paths:
        return ()
    return (
        LanguageMaterializationPostStepPackageContext(
            package_name=(
                request.package_name
                or request.materialization_source
                or request.target_language_plugin_id.value
            ),
            package_root=request.output_root.resolve(),
            package_files=generated_file_paths,
        ),
    )


def _step_targets(
    *,
    request: LanguageMaterializationPostStepExecutionRequest,
    step: LanguageMaterializationPostStepPlanItem,
    package_contexts: tuple[LanguageMaterializationPostStepPackageContext, ...],
    generated_file_paths: tuple[Path, ...],
) -> tuple[Path, ...]:
    selected_contexts = package_contexts
    if step.packages:
        wanted = set(step.packages)
        selected_contexts = tuple(
            context for context in package_contexts if context.package_name in wanted
        )
    discovery = discover_language_materialization_post_step_targets(
        LanguageMaterializationPostStepTargetDiscoveryRequest(
            target_language_plugin_id=request.target_language_plugin_id,
            tool_id=step.tool_id,
            package_contexts=selected_contexts,
            candidate_paths=(generated_file_paths if not selected_contexts else ()),
        )
    )
    return _dedupe_paths(
        path
        for package_target in discovery.package_targets
        for path in package_target.target_paths
    )


def _tool_state_env(
    *,
    request: LanguageMaterializationPostStepExecutionRequest,
    spec: CodeLanguageToolSpec,
) -> Mapping[str, str]:
    return _tool_mapping_for_spec(
        mappings=request.tool_env_by_tool_id,
        spec=spec,
    )


def _tool_executable_overrides(
    *,
    request: LanguageMaterializationPostStepExecutionRequest,
    spec: CodeLanguageToolSpec,
) -> Mapping[str, str]:
    return _tool_mapping_for_spec(
        mappings=request.executable_overrides_by_tool_id,
        spec=spec,
    )


def _tool_mapping_for_spec(
    *,
    mappings: Mapping[str, Mapping[str, str]],
    spec: CodeLanguageToolSpec,
) -> Mapping[str, str]:
    for key in (
        spec.tool_id,
        f"{spec.language.value}:{spec.tool_id}",
        spec.language.value,
    ):
        value = mappings.get(key)
        if isinstance(value, Mapping):
            return {
                str(env_key): str(env_value)
                for env_key, env_value in value.items()
                if str(env_key).strip()
            }
    return {}


def _validate_cli_tooling_state(
    *,
    spec: CodeLanguageToolSpec,
    state_env: Mapping[str, str],
) -> None:
    missing_env = tuple(
        requirement.env_var
        for requirement in spec.state_requirements
        if requirement.required
        and requirement.env_var
        and requirement.env_var not in state_env
    )
    if not missing_env:
        return
    raise RuntimeError(
        "language_tooling_state_required: "
        f"language={spec.language.value!r} "
        f"tool_id={spec.tool_id!r} "
        f"missing_env={','.join(missing_env)!r}"
    )


def _execute_tool(
    *,
    spec: CodeLanguageToolSpec,
    targets: tuple[Path, ...],
    args: tuple[str, ...],
    cwd: Path,
    timeout_s: float | None,
    state_env: Mapping[str, str],
    executable_overrides: Mapping[str, str],
) -> _LanguageMaterializationToolEffects:
    if not targets:
        return _LanguageMaterializationToolEffects()
    if spec.backend == _PYTHON_API_BACKEND:
        return _LanguageMaterializationToolEffects(
            changed_paths=_execute_python_api_tool(spec=spec, targets=targets)
        )
    if spec.backend == _CLI_BACKEND:
        _validate_cli_tooling_state(spec=spec, state_env=state_env)
        return _execute_cli_tool(
            spec=spec,
            targets=targets,
            args=args,
            cwd=cwd,
            timeout_s=timeout_s,
            state_env=state_env,
            executable_overrides=executable_overrides,
        )
    raise ValueError(
        f"Unsupported materialization post-step backend {spec.backend!r} "
        + f"for tool {spec.tool_id!r}."
    )


def _execute_python_api_tool(
    *,
    spec: CodeLanguageToolSpec,
    targets: tuple[Path, ...],
) -> tuple[Path, ...]:
    if spec.role != _FORMATTER_ROLE:
        raise ValueError(
            f"Python API post-step {spec.tool_id!r} has unsupported role "
            + f"{spec.role!r}."
        )
    if not spec.module or not spec.callable_name:
        raise ValueError(
            f"Python API post-step {spec.tool_id!r} must declare module "
            + "and callable_name."
        )
    module = importlib.import_module(spec.module)
    api_callable = _module_attribute(module, spec.callable_name)
    changed_paths: list[Path] = []
    for target in targets:
        before = target.read_bytes()
        _invoke_python_formatter(
            module=module,
            api_callable=api_callable,
            spec=spec,
            target=target,
        )
        after = target.read_bytes()
        if before != after:
            changed_paths.append(target)
    return tuple(changed_paths)


def _invoke_python_formatter(
    *,
    module: object,
    api_callable: object,
    spec: CodeLanguageToolSpec,
    target: Path,
) -> None:
    if not callable(api_callable):
        raise TypeError(f"Tool {spec.tool_id!r} callable is not callable.")
    try:
        result = api_callable(target)
    except TypeError:
        result = _invoke_path_formatter_protocol(
            module=module,
            api_callable=api_callable,
            spec=spec,
            target=target,
        )
    _apply_formatter_return_value(target=target, result=result)


def _invoke_path_formatter_protocol(
    *,
    module: object,
    api_callable: object,
    spec: CodeLanguageToolSpec,
    target: Path,
) -> object:
    file_mode_factory = _module_attribute(module, "FileMode")
    write_back_type = _module_attribute(module, "WriteBack")
    report_factory = _module_attribute(module, "Report")
    line_length = _metadata_int(spec.metadata, "line_length", default=120)
    mode = file_mode_factory(line_length=line_length)
    write_back = write_back_type.YES
    report = report_factory(check=False, quiet=True)
    return api_callable(target, False, mode, write_back, report)


def _execute_cli_tool(
    *,
    spec: CodeLanguageToolSpec,
    targets: tuple[Path, ...],
    args: tuple[str, ...],
    cwd: Path,
    timeout_s: float | None,
    state_env: Mapping[str, str],
    executable_overrides: Mapping[str, str],
) -> _LanguageMaterializationToolEffects:
    before = {path: path.read_bytes() for path in targets}
    _prepare_cli_tool_state(spec=spec, cwd=cwd)
    before_effect_paths = _tool_effect_snapshot(
        spec=spec,
        cwd=cwd,
        targets=targets,
    )
    prepared = prepare_language_materialization_tool_command(
        LanguageMaterializationToolCommandRequest(
            target_language_plugin_id=spec.language,
            tool_id=spec.tool_id,
            cwd=cwd,
            targets=targets,
            args=args,
            env=state_env,
            timeout_s=timeout_s,
            executable_overrides=executable_overrides,
        )
    )
    completed = subprocess.run(
        prepared.command,
        cwd=str(prepared.cwd) if prepared.cwd is not None else None,
        env={**os.environ, **dict(prepared.env)},
        stdin=subprocess.DEVNULL,
        text=True,
        capture_output=True,
        timeout=prepared.timeout_s,
        check=False,
    )
    if completed.returncode != 0:
        stderr = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(
            f"Post-step {spec.tool_id!r} failed with exit code "
            + f"{completed.returncode}: {stderr}"
        )
    after_effect_paths = _tool_effect_snapshot(
        spec=spec,
        cwd=cwd,
        targets=targets,
    )
    changed_paths = _dedupe_paths(
        path
        for path, content in after_effect_paths.items()
        if path in before_effect_paths
        and (
            before_effect_paths.get(path) != content
            or (path in before and before.get(path) != content)
        )
    )
    produced_paths = _dedupe_paths(
        path for path in after_effect_paths if path not in before_effect_paths
    )
    return _LanguageMaterializationToolEffects(
        changed_paths=changed_paths,
        produced_paths=produced_paths,
    )


def _prepare_cli_tool_state(*, spec: CodeLanguageToolSpec, cwd: Path) -> None:
    if spec.tool_id != "dart.build_runner":
        return
    build_lock_root = (cwd.resolve() / ".dart_tool" / "build" / "lock").resolve()
    if not _is_path_within(path=build_lock_root, root=cwd.resolve()):
        raise RuntimeError(
            "Dart build_runner lock root escapes package root: "
            f"cwd={cwd} build_lock_root={build_lock_root}"
        )
    shutil.rmtree(build_lock_root, ignore_errors=True)


def _receipt(
    *,
    request: LanguageMaterializationPostStepExecutionRequest,
    spec: CodeLanguageToolSpec,
    step: LanguageMaterializationPostStepPlanItem,
    status: str,
    target_count: int,
    changed_path_count: int = 0,
    produced_path_count: int = 0,
    duration_s: float,
    warning_count: int = 0,
    state_env: Mapping[str, str] | None = None,
    executable_overrides: Mapping[str, str] | None = None,
) -> LanguageMaterializationPostStepReceipt:
    return LanguageMaterializationPostStepReceipt(
        tool_id=spec.tool_id,
        target_language_plugin_id=request.target_language_plugin_id,
        status=status,
        backend=spec.backend,
        role=spec.role,
        output_root=request.output_root.resolve(),
        package_name=request.package_name,
        materialization_source=request.materialization_source,
        renderer_profile=request.renderer_profile,
        renderer_kind=request.renderer_kind,
        source=step.source,
        target_count=target_count,
        changed_path_count=changed_path_count,
        produced_path_count=produced_path_count,
        duration_s=duration_s,
        warning_count=warning_count,
        state_env=dict(state_env or {}),
        executable_overrides=dict(executable_overrides or {}),
    )


def _apply_formatter_return_value(*, target: Path, result: object) -> None:
    if isinstance(result, str):
        target.write_text(result, encoding="utf-8")
    elif isinstance(result, bytes):
        target.write_bytes(result)


def _existing_files(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    return _dedupe_paths(path for path in paths if path.exists() and path.is_file())


def _tool_effect_snapshot(
    *,
    spec: CodeLanguageToolSpec,
    cwd: Path,
    targets: tuple[Path, ...],
) -> dict[Path, bytes]:
    return {
        path: path.read_bytes()
        for path in _tool_effect_candidate_paths(spec=spec, cwd=cwd, targets=targets)
        if path.exists() and path.is_file()
    }


def _tool_effect_candidate_paths(
    *,
    spec: CodeLanguageToolSpec,
    cwd: Path,
    targets: tuple[Path, ...],
) -> tuple[Path, ...]:
    candidates: set[Path] = {path.resolve() for path in targets}
    root = cwd.resolve()
    for search_root in _metadata_csv(
        spec.metadata.get("materialization_target_search_roots")
    ):
        candidate_root = (root / search_root).resolve()
        if not candidate_root.exists() or not candidate_root.is_dir():
            continue
        if not _is_path_within(path=candidate_root, root=root):
            continue
        candidates.update(
            path.resolve()
            for path in candidate_root.rglob("*")
            if path.exists() and path.is_file() and not path.is_symlink()
        )
    return _dedupe_paths(candidates)


def _dedupe_paths(paths) -> tuple[Path, ...]:
    return tuple(
        sorted(
            {Path(path).resolve() for path in paths},
            key=lambda p: p.as_posix(),
        )
    )


def _is_path_within(*, path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _module_attribute(module: object, name: str) -> object:
    try:
        return getattr(module, name)
    except AttributeError as exc:
        raise ValueError(f"Module {module!r} does not expose {name!r}.") from exc


def _metadata_int(
    metadata: Mapping[str, str],
    key: str,
    *,
    default: int,
) -> int:
    try:
        return int(str(metadata.get(key) or "").strip())
    except Exception:
        return default


def _metadata_csv(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(token.strip() for token in str(value).split(",") if token.strip())


__all__ = [
    "LanguageMaterializationPostStepExecution",
    "LanguageMaterializationPostStepExecutionRequest",
    "LanguageMaterializationPostStepReceipt",
    "execute_language_materialization_post_steps",
]
