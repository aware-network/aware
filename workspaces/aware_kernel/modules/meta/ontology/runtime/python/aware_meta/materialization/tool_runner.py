from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from aware_code.language.plugin import CodeLanguagePlugin
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.language.tooling import CodeLanguageToolSpec
from aware_code_ontology.code.code_enums import CodeLanguage


@dataclass(frozen=True, slots=True)
class LanguageMaterializationToolCommandRequest:
    target_language_plugin_id: CodeLanguage
    tool_id: str
    cwd: Path | None = None
    targets: tuple[str | Path, ...] = ()
    args: tuple[str, ...] = ()
    env: Mapping[str, str] = field(default_factory=dict)
    timeout_s: float | None = None
    executable_overrides: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPreparedToolCommand:
    target_language_plugin_id: CodeLanguage
    tool_id: str
    backend: str
    target_mode: str
    command: tuple[str, ...]
    cwd: Path | None = None
    env: Mapping[str, str] = field(default_factory=dict)
    timeout_s: float | None = None
    mutates_targets: bool = False


def resolve_language_materialization_tool_spec(
    *,
    target_language_plugin_id: CodeLanguage,
    tool_id: str,
) -> CodeLanguageToolSpec:
    plugin = _resolve_code_language_plugin(target_language_plugin_id)
    wanted = tool_id.strip()
    for spec in plugin.tooling:
        if spec.tool_id == wanted:
            return spec
    raise KeyError(
        f"No Code language tool {wanted!r} registered for "
        + f"{target_language_plugin_id.value!r}"
    )


def prepare_language_materialization_tool_command(
    request: LanguageMaterializationToolCommandRequest,
) -> LanguageMaterializationPreparedToolCommand:
    spec = resolve_language_materialization_tool_spec(
        target_language_plugin_id=request.target_language_plugin_id,
        tool_id=request.tool_id,
    )
    if spec.backend != "cli":
        raise ValueError(
            f"Tool {spec.tool_id!r} uses backend {spec.backend!r}; "
            + "only CLI tools can be prepared as commands."
        )
    if not spec.command:
        raise ValueError(f"Tool {spec.tool_id!r} does not declare a command.")

    command = list(spec.command)
    if command:
        command[0] = request.executable_overrides.get(command[0], command[0])

    if request.args:
        command.extend(str(arg) for arg in request.args if str(arg).strip())

    if spec.target_mode == "paths":
        command.extend(_target_token(target) for target in request.targets)
    elif spec.target_mode == "none":
        if request.targets:
            raise ValueError(f"Tool {spec.tool_id!r} does not accept targets.")
    elif spec.target_mode in {"package_root", "repo_root"}:
        # The target root is represented by cwd for these tool modes.
        # Individual generated files are only used for change detection and to
        # decide whether the post-step should run.
        pass
    else:
        raise ValueError(
            f"Unsupported target mode {spec.target_mode!r} for tool {spec.tool_id!r}."
        )

    return LanguageMaterializationPreparedToolCommand(
        target_language_plugin_id=request.target_language_plugin_id,
        tool_id=spec.tool_id,
        backend=spec.backend,
        target_mode=spec.target_mode,
        command=tuple(command),
        cwd=request.cwd.resolve() if request.cwd is not None else None,
        env=dict(request.env),
        timeout_s=request.timeout_s if request.timeout_s is not None else spec.default_timeout_s,
        mutates_targets=spec.mutates_targets,
    )


def _target_token(target: str | Path) -> str:
    if isinstance(target, Path):
        return target.as_posix()
    return str(target)


def _resolve_code_language_plugin(
    language: CodeLanguage,
) -> CodeLanguagePlugin[object]:
    try:
        return CodeLanguagePluginRegistry.get(language)
    except KeyError:
        try:
            from aware_code.setup_language_plugins import setup_code_plugins
        except Exception:
            raise
        setup_code_plugins()
        return CodeLanguagePluginRegistry.get(language)


__all__ = [
    "LanguageMaterializationPreparedToolCommand",
    "LanguageMaterializationToolCommandRequest",
    "prepare_language_materialization_tool_command",
    "resolve_language_materialization_tool_spec",
]
