"""Opinionated workspace quality-gate planner/executor."""

from __future__ import annotations

import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from aware_workspace_operator.models import (
    WorkspaceQualityCommandResult,
    WorkspaceQualityOptions,
    WorkspaceQualityOutcome,
    WorkspaceQualityReport,
)

_MAX_OUTPUT_CHARS = 8000
_QUALITY_POLICY_REL_PATH = Path("configs/contracts/quality_gates.toml")
_SOURCE_CHECKOUT_POLICY_PATH = (
    Path(__file__).resolve().parent
    / "assets"
    / "contracts"
    / "aware_repo_quality_gates.toml"
)
_EXTENSION_TO_LANGUAGE = {
    ".aware": "aware",
    ".dart": "dart",
    ".py": "python",
    ".sql": "sql",
}
_LANGUAGE_ORDER = ("aware", "python", "dart", "sql")
_PYTHON_FALLBACK_GATES = (
    (
        "python.flake8",
        "Run Python lint checks with flake8.",
        ("uv", "run", "flake8"),
        "paths",
    ),
    (
        "python.mypy",
        "Run Python type checks with mypy.",
        ("uv", "run", "mypy"),
        "paths",
    ),
    (
        "python.basedpyright",
        "Run Python type checks with basedpyright.",
        ("uv", "run", "basedpyright"),
        "paths",
    ),
)
_DART_FALLBACK_GATES = (
    (
        "dart.analyze",
        "Run Dart static analysis.",
        ("dart", "analyze"),
        "paths",
    ),
)
_FALLBACK_GATES_BY_LANGUAGE = {
    "python": _PYTHON_FALLBACK_GATES,
    "dart": _DART_FALLBACK_GATES,
}


@dataclass(frozen=True)
class _GateSpec:
    gate_id: str
    language: str
    description: str
    command: tuple[str, ...]
    target_mode: Literal["paths", "repo_root", "none"] = "paths"


@dataclass(frozen=True)
class _PathProfileRule:
    language: str
    path_prefix: str
    profile: str


@dataclass(frozen=True)
class _QualityPolicy:
    gate_by_id: dict[str, _GateSpec]
    profiles_by_language: dict[str, dict[str, tuple[str, ...]]]
    default_profile_by_language: dict[str, str]
    path_profiles: tuple[_PathProfileRule, ...]


def run_workspace_quality_gates(
    *,
    options: WorkspaceQualityOptions,
) -> WorkspaceQualityOutcome:
    """Run canonical quality gates for detected languages in a workspace."""

    repo_root = Path(options.repo_root).expanduser().resolve()
    if not repo_root.exists():
        raise FileNotFoundError(f"Repo root does not exist: {repo_root}")
    if not repo_root.is_dir():
        raise NotADirectoryError(f"Repo root must be a directory: {repo_root}")

    target_paths = _resolve_target_paths(
        repo_root=repo_root,
        raw_paths=tuple(options.target_paths),
    )
    detected_languages = tuple(_detect_languages(target_paths=target_paths))
    selected_languages = _resolve_selected_languages(
        detected_languages=detected_languages,
        requested_languages=tuple(options.include_languages),
    )
    gate_specs = _resolve_gate_specs(
        repo_root=repo_root,
        target_paths=target_paths,
        detected_languages=selected_languages,
        requested_gate_ids=tuple(options.include_gate_ids),
    )

    command_results: list[WorkspaceQualityCommandResult] = []
    has_failed = False
    for gate in gate_specs:
        command, command_targets = _build_command(
            gate=gate,
            repo_root=repo_root,
            target_paths=target_paths,
        )
        if not options.run_commands:
            command_results.append(
                WorkspaceQualityCommandResult(
                    gate_id=gate.gate_id,
                    language=gate.language,
                    description=gate.description,
                    command=list(command),
                    target_paths=list(command_targets),
                    status="planned",
                )
            )
            continue

        try:
            completed = subprocess.run(
                list(command),
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            status: Literal["passed", "failed"] = (
                "passed" if completed.returncode == 0 else "failed"
            )
            has_failed = has_failed or status == "failed"
            command_results.append(
                WorkspaceQualityCommandResult(
                    gate_id=gate.gate_id,
                    language=gate.language,
                    description=gate.description,
                    command=list(command),
                    target_paths=list(command_targets),
                    status=status,
                    exit_code=int(completed.returncode),
                    stdout=_truncate_output(completed.stdout),
                    stderr=_truncate_output(completed.stderr),
                )
            )
        except FileNotFoundError as exc:
            missing_status: Literal["failed", "skipped"] = (
                "failed" if options.fail_on_missing_command else "skipped"
            )
            has_failed = has_failed or missing_status == "failed"
            command_results.append(
                WorkspaceQualityCommandResult(
                    gate_id=gate.gate_id,
                    language=gate.language,
                    description=gate.description,
                    command=list(command),
                    target_paths=list(command_targets),
                    status=missing_status,
                    reason=f"Tool not found: {exc}",
                )
            )

    report = WorkspaceQualityReport(
        repo_root=repo_root.as_posix(),
        target_paths=[
            _display_path(path=path, repo_root=repo_root) for path in target_paths
        ],
        detected_languages=list(selected_languages),
        commands=command_results,
        status="failed" if has_failed else "ok",
    )
    return WorkspaceQualityOutcome(
        report=report,
        exit_code=2 if report.status == "failed" else 0,
    )


def print_workspace_quality_report(*, report: WorkspaceQualityReport) -> None:
    """Render human-readable quality gate summary."""

    print(f"Workspace quality gates: {report.status.upper()}")
    print(f"Repo root: {report.repo_root}")
    targets = ", ".join(report.target_paths) if report.target_paths else "(none)"
    print(f"Targets: {targets}")
    languages = (
        ", ".join(report.detected_languages) if report.detected_languages else "(none)"
    )
    print(f"Detected languages: {languages}")
    if not report.commands:
        print("No quality gates selected for detected paths.")
        return

    print("Quality gates:")
    for item in report.commands:
        command_text = " ".join(item.command)
        print(f"- [{item.status}] {item.gate_id} ({item.language}) :: {command_text}")
        if item.exit_code is not None:
            print(f"    exit_code={item.exit_code}")
        if item.reason:
            print(f"    reason={item.reason}")
        if item.status == "failed":
            if item.stderr.strip():
                print(f"    stderr: {item.stderr.strip()}")
            elif item.stdout.strip():
                print(f"    stdout: {item.stdout.strip()}")


def print_workspace_quality_result(*, payload: dict[str, object]) -> None:
    """Compatibility adapter for CLI callers that pass dict payloads."""

    report = WorkspaceQualityReport.model_validate(payload)
    print_workspace_quality_report(report=report)


def _resolve_target_paths(
    *, repo_root: Path, raw_paths: tuple[str, ...]
) -> tuple[Path, ...]:
    if not raw_paths:
        return (repo_root,)

    resolved_paths: list[Path] = []
    seen: set[Path] = set()
    for raw_path in raw_paths:
        candidate = Path(raw_path.strip()).expanduser()
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        if not candidate.exists():
            raise FileNotFoundError(f"Target path does not exist: {candidate}")
        try:
            _ = candidate.relative_to(repo_root)
        except Exception as exc:
            raise ValueError(
                f"Target path escapes repo root: {candidate} (repo_root={repo_root})"
            ) from exc
        if candidate in seen:
            continue
        seen.add(candidate)
        resolved_paths.append(candidate)
    return tuple(resolved_paths)


def _detect_languages(*, target_paths: tuple[Path, ...]) -> list[str]:
    detected: set[str] = set()
    for path in target_paths:
        if path.is_file():
            language = _EXTENSION_TO_LANGUAGE.get(path.suffix.lower())
            if language:
                detected.add(language)
            continue
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue
            language = _EXTENSION_TO_LANGUAGE.get(file_path.suffix.lower())
            if language:
                detected.add(language)
    ordered = [language for language in _LANGUAGE_ORDER if language in detected]
    extras = sorted(
        language for language in detected if language not in _LANGUAGE_ORDER
    )
    ordered.extend(extras)
    return ordered


def _resolve_selected_languages(
    *,
    detected_languages: tuple[str, ...],
    requested_languages: tuple[str, ...],
) -> tuple[str, ...]:
    if not requested_languages:
        return detected_languages

    normalized: list[str] = []
    seen: set[str] = set()
    for raw in requested_languages:
        language = raw.strip().lower()
        if not language or language in seen:
            continue
        normalized.append(language)
        seen.add(language)

    detected_set = set(detected_languages)
    missing = [language for language in normalized if language not in detected_set]
    if missing:
        detected = ", ".join(detected_languages) if detected_languages else "(none)"
        raise ValueError(
            f"Requested languages are not detected in target scope: {', '.join(missing)} (detected={detected})"
        )
    return tuple(normalized)


def _resolve_gate_specs(
    *,
    repo_root: Path,
    target_paths: tuple[Path, ...],
    detected_languages: tuple[str, ...],
    requested_gate_ids: tuple[str, ...],
) -> list[_GateSpec]:
    policy = _load_quality_policy(repo_root=repo_root)
    plugin_specs = _load_plugin_gate_specs(detected_languages=detected_languages)
    resolved: list[_GateSpec] = []
    for language in detected_languages:
        language_specs = _resolve_language_gate_specs_from_policy(
            policy=policy,
            language=language,
            repo_root=repo_root,
            target_paths=target_paths,
        )
        if language_specs is not None:
            resolved.extend(language_specs)
            continue
        if language in plugin_specs:
            resolved.extend(plugin_specs[language])
            continue
        for (
            gate_id,
            description,
            command,
            target_mode,
        ) in _FALLBACK_GATES_BY_LANGUAGE.get(language, ()):
            resolved.append(
                _GateSpec(
                    gate_id=gate_id,
                    language=language,
                    description=description,
                    command=tuple(command),
                    target_mode=cast(
                        Literal["paths", "repo_root", "none"], target_mode
                    ),
                )
            )
    _augment_with_requested_policy_gates(
        gate_specs=resolved,
        requested_gate_ids=requested_gate_ids,
        detected_languages=detected_languages,
        policy=policy,
    )
    return _filter_requested_gate_ids(
        gate_specs=resolved,
        requested_gate_ids=requested_gate_ids,
    )


def _augment_with_requested_policy_gates(
    *,
    gate_specs: list[_GateSpec],
    requested_gate_ids: tuple[str, ...],
    detected_languages: tuple[str, ...],
    policy: _QualityPolicy | None,
) -> None:
    if policy is None or not requested_gate_ids:
        return

    detected_language_set = set(detected_languages)
    existing_gate_ids = {spec.gate_id for spec in gate_specs}
    for raw_gate_id in requested_gate_ids:
        gate_id = raw_gate_id.strip()
        if not gate_id or gate_id in existing_gate_ids:
            continue
        gate = policy.gate_by_id.get(gate_id)
        if gate is None or gate.language not in detected_language_set:
            continue
        gate_specs.append(gate)
        existing_gate_ids.add(gate_id)


def _filter_requested_gate_ids(
    *,
    gate_specs: list[_GateSpec],
    requested_gate_ids: tuple[str, ...],
) -> list[_GateSpec]:
    if not requested_gate_ids:
        return gate_specs

    requested: list[str] = []
    seen: set[str] = set()
    for raw in requested_gate_ids:
        gate_id = raw.strip()
        if not gate_id or gate_id in seen:
            continue
        requested.append(gate_id)
        seen.add(gate_id)

    by_id = {spec.gate_id: spec for spec in gate_specs}
    missing = [gate_id for gate_id in requested if gate_id not in by_id]
    if missing:
        available = ", ".join(sorted(by_id)) if by_id else "(none)"
        raise ValueError(
            f"Requested quality gates are not available for selected scope: {', '.join(missing)} "
            + f"(available={available})"
        )
    return [by_id[gate_id] for gate_id in requested]


def _load_plugin_gate_specs(
    *, detected_languages: tuple[str, ...]
) -> dict[str, tuple[_GateSpec, ...]]:
    try:
        from aware_code.language.registry import CodeLanguagePluginRegistry
        from aware_code.setup_language_plugins import setup_code_plugins
        from aware_code_ontology.code.code_enums import CodeLanguage
    except Exception:
        return {}

    try:
        setup_code_plugins()
    except Exception:
        return {}
    specs: dict[str, tuple[_GateSpec, ...]] = {}
    for language in detected_languages:
        try:
            enum_language = CodeLanguage(language)
        except Exception:
            continue
        try:
            plugin = CodeLanguagePluginRegistry.get(enum_language)
        except Exception:
            continue
        plugin_gates_raw = getattr(plugin, "quality_gates", ())
        plugin_gates = cast(tuple[object, ...], tuple(plugin_gates_raw or ()))
        if not plugin_gates:
            continue
        language_specs: list[_GateSpec] = []
        for gate in plugin_gates:
            command = tuple(
                str(part).strip()
                for part in tuple(getattr(gate, "command", ()) or ())
                if str(part).strip()
            )
            if not command:
                continue
            target_mode_raw = (
                str(getattr(gate, "target_mode", "paths")).strip() or "paths"
            )
            if target_mode_raw not in {"paths", "repo_root", "none"}:
                target_mode_raw = "paths"
            language_specs.append(
                _GateSpec(
                    gate_id=str(getattr(gate, "gate_id", f"{language}.quality")).strip()
                    or f"{language}.quality",
                    language=language,
                    description=str(getattr(gate, "description", "")).strip()
                    or f"Run {language} quality gate.",
                    command=command,
                    target_mode=cast(
                        Literal["paths", "repo_root", "none"], target_mode_raw
                    ),
                )
            )
        if language_specs:
            specs[language] = tuple(language_specs)
    return specs


def _resolve_language_gate_specs_from_policy(
    *,
    policy: _QualityPolicy | None,
    language: str,
    repo_root: Path,
    target_paths: tuple[Path, ...],
) -> tuple[_GateSpec, ...] | None:
    if policy is None:
        return None
    profiles = policy.profiles_by_language.get(language)
    has_default = language in policy.default_profile_by_language
    has_path_rules = any(rule.language == language for rule in policy.path_profiles)
    if profiles is None and not has_default and not has_path_rules:
        return None
    if profiles is None:
        raise ValueError(f"Quality policy has no profiles for language={language!r}.")

    profile_name = _resolve_profile_name_for_language(
        policy=policy,
        language=language,
        repo_root=repo_root,
        target_paths=target_paths,
    )
    gate_ids = profiles.get(profile_name)
    if gate_ids is None:
        available = ", ".join(sorted(profiles)) if profiles else "(none)"
        raise ValueError(
            f"Quality profile {profile_name!r} not found for language={language!r} (available={available})."
        )

    gate_specs: list[_GateSpec] = []
    for gate_id in gate_ids:
        gate = policy.gate_by_id.get(gate_id)
        if gate is None:
            raise ValueError(f"Quality profile references unknown gate id: {gate_id!r}")
        if gate.language != language:
            raise ValueError(
                f"Quality profile gate language mismatch for {gate_id!r}: expected language={language!r}, "
                + f"gate.language={gate.language!r}"
            )
        gate_specs.append(gate)
    return tuple(gate_specs)


def _resolve_profile_name_for_language(
    *,
    policy: _QualityPolicy,
    language: str,
    repo_root: Path,
    target_paths: tuple[Path, ...],
) -> str:
    matching_rules = [
        rule
        for rule in policy.path_profiles
        if rule.language == language
        and any(
            _target_matches_prefix(
                target_path=target_path,
                path_prefix=rule.path_prefix,
                repo_root=repo_root,
            )
            for target_path in target_paths
        )
    ]
    if matching_rules:
        max_prefix_len = max(len(rule.path_prefix) for rule in matching_rules)
        most_specific = [
            rule for rule in matching_rules if len(rule.path_prefix) == max_prefix_len
        ]
        profiles = {rule.profile for rule in most_specific}
        if len(profiles) != 1:
            raise ValueError(
                f"Ambiguous quality profile mapping for language={language!r}: "
                + f"path rules resolve to multiple profiles {sorted(profiles)}"
            )
        return most_specific[0].profile

    default_profile = policy.default_profile_by_language.get(language)
    if default_profile:
        return default_profile

    profiles = policy.profiles_by_language.get(language, {})
    if "standard" in profiles:
        return "standard"
    if len(profiles) == 1:
        return next(iter(profiles))
    available = ", ".join(sorted(profiles)) if profiles else "(none)"
    raise ValueError(
        f"Quality policy has no default profile for language={language!r} (available_profiles={available})."
    )


def _target_matches_prefix(
    *, target_path: Path, path_prefix: str, repo_root: Path
) -> bool:
    target_rel = _display_path(path=target_path, repo_root=repo_root)
    if target_rel in {"", "."}:
        return False
    prefix = path_prefix.strip().strip("/")
    if not prefix:
        return False
    if target_rel == prefix:
        return True
    return target_rel.startswith(prefix + "/")


def _load_quality_policy(*, repo_root: Path) -> _QualityPolicy | None:
    policy_path = (repo_root / _QUALITY_POLICY_REL_PATH).resolve()
    if not policy_path.is_file() and (repo_root / "aware.repo.toml").is_file():
        policy_path = _SOURCE_CHECKOUT_POLICY_PATH.resolve()
    if not policy_path.is_file():
        return None

    data = cast(
        dict[str, object], tomllib.loads(policy_path.read_text(encoding="utf-8"))
    )

    gate_by_id = _parse_policy_gates(data=data, policy_path=policy_path)
    profiles_by_language = _parse_policy_profiles(
        data=data,
        gate_by_id=gate_by_id,
        policy_path=policy_path,
    )
    default_profile_by_language = _parse_policy_default_profiles(
        data=data,
        policy_path=policy_path,
    )
    path_profiles = _parse_policy_path_profiles(
        data=data,
        profiles_by_language=profiles_by_language,
        policy_path=policy_path,
    )
    return _QualityPolicy(
        gate_by_id=gate_by_id,
        profiles_by_language=profiles_by_language,
        default_profile_by_language=default_profile_by_language,
        path_profiles=path_profiles,
    )


def _parse_policy_gates(
    *, data: dict[str, object], policy_path: Path
) -> dict[str, _GateSpec]:
    raw_gates = data.get("gates")
    if raw_gates is None:
        return {}
    gates_table = _require_toml_table(
        raw_gates, context="[gates]", policy_path=policy_path
    )

    parsed: dict[str, _GateSpec] = {}
    for raw_key, raw_value in gates_table.items():
        gate_table = _require_toml_table(
            raw_value, context=f"[gates.{raw_key}]", policy_path=policy_path
        )

        language = str(gate_table.get("language", "")).strip().lower()
        if not language:
            raise ValueError(f"Gate {raw_key!r} missing language in {policy_path}")

        gate_id = str(gate_table.get("gate_id", raw_key.replace("_", "."))).strip()
        if not gate_id:
            raise ValueError(f"Gate {raw_key!r} missing gate_id in {policy_path}")

        command_raw = gate_table.get("command")
        command_list = _require_toml_list(
            command_raw,
            context=f"[gates.{raw_key}].command",
            policy_path=policy_path,
        )
        command = tuple(str(part).strip() for part in command_list if str(part).strip())
        if not command:
            raise ValueError(
                f"Gate {gate_id!r} command cannot be empty in {policy_path}"
            )

        target_mode_raw = str(gate_table.get("target_mode", "paths")).strip() or "paths"
        if target_mode_raw not in {"paths", "repo_root", "none"}:
            raise ValueError(
                f"Gate {gate_id!r} has invalid target_mode={target_mode_raw!r} in {policy_path}"
            )

        description = (
            str(gate_table.get("description", "")).strip()
            or f"Run {language} quality gate {gate_id}."
        )
        if gate_id in parsed:
            raise ValueError(f"Duplicate gate_id {gate_id!r} in {policy_path}")
        parsed[gate_id] = _GateSpec(
            gate_id=gate_id,
            language=language,
            description=description,
            command=command,
            target_mode=cast(Literal["paths", "repo_root", "none"], target_mode_raw),
        )
    return parsed


def _parse_policy_profiles(
    *,
    data: dict[str, object],
    gate_by_id: dict[str, _GateSpec],
    policy_path: Path,
) -> dict[str, dict[str, tuple[str, ...]]]:
    raw_profiles = data.get("profiles")
    if raw_profiles is None:
        return {}
    profiles_table = _require_toml_table(
        raw_profiles, context="[profiles]", policy_path=policy_path
    )

    parsed: dict[str, dict[str, tuple[str, ...]]] = {}
    for raw_language, raw_language_profiles in profiles_table.items():
        language_table = _require_toml_table(
            raw_language_profiles,
            context=f"[profiles.{raw_language}]",
            policy_path=policy_path,
        )
        language = raw_language.strip().lower()
        if not language:
            raise ValueError(f"Invalid empty language profile section in {policy_path}")

        language_profiles: dict[str, tuple[str, ...]] = {}
        for raw_profile_name, raw_profile_value in language_table.items():
            profile_table = _require_toml_table(
                raw_profile_value,
                context=f"[profiles.{language}.{raw_profile_name}]",
                policy_path=policy_path,
            )
            profile_name = raw_profile_name.strip()
            gate_ids_raw = profile_table.get("gates")
            gate_ids_list = _require_toml_list(
                gate_ids_raw,
                context=f"[profiles.{language}.{profile_name}].gates",
                policy_path=policy_path,
            )

            gate_ids: list[str] = []
            seen_gate_ids: set[str] = set()
            for raw_gate_id in gate_ids_list:
                gate_id = str(raw_gate_id).strip()
                if not gate_id or gate_id in seen_gate_ids:
                    continue
                gate = gate_by_id.get(gate_id)
                if gate is None:
                    raise ValueError(
                        f"Profile [profiles.{language}.{profile_name}] references unknown gate {gate_id!r} "
                        + f"in {policy_path}"
                    )
                if gate.language != language:
                    raise ValueError(
                        f"Profile [profiles.{language}.{profile_name}] gate {gate_id!r} has "
                        + f"language={gate.language!r}"
                    )
                gate_ids.append(gate_id)
                seen_gate_ids.add(gate_id)

            if not gate_ids:
                raise ValueError(
                    f"Profile [profiles.{language}.{profile_name}] has no gates in {policy_path}"
                )
            language_profiles[profile_name] = tuple(gate_ids)
        if language_profiles:
            parsed[language] = language_profiles
    return parsed


def _parse_policy_default_profiles(
    *,
    data: dict[str, object],
    policy_path: Path,
) -> dict[str, str]:
    defaults_raw = data.get("defaults")
    if defaults_raw is None:
        return {}
    defaults_table = _require_toml_table(
        defaults_raw, context="[defaults]", policy_path=policy_path
    )
    mapping_raw = defaults_table.get("profile_by_language")
    if mapping_raw is None:
        return {}
    mapping_table = _require_toml_table(
        mapping_raw,
        context="[defaults.profile_by_language]",
        policy_path=policy_path,
    )

    parsed: dict[str, str] = {}
    for raw_language, raw_profile in mapping_table.items():
        language = str(raw_language).strip().lower()
        profile = str(raw_profile).strip()
        if not language or not profile:
            continue
        parsed[language] = profile
    return parsed


def _parse_policy_path_profiles(
    *,
    data: dict[str, object],
    profiles_by_language: dict[str, dict[str, tuple[str, ...]]],
    policy_path: Path,
) -> tuple[_PathProfileRule, ...]:
    raw_rules = data.get("path_profiles")
    if raw_rules is None:
        return ()
    path_profiles_list = _require_toml_list(
        raw_rules, context="[[path_profiles]]", policy_path=policy_path
    )

    parsed: list[_PathProfileRule] = []
    for raw_rule in path_profiles_list:
        rule_table = _require_toml_table(
            raw_rule, context="[[path_profiles]]", policy_path=policy_path
        )
        language = str(rule_table.get("language", "")).strip().lower()
        path_prefix = str(rule_table.get("path_prefix", "")).strip().strip("/")
        profile = str(rule_table.get("profile", "")).strip()
        if not language or not path_prefix or not profile:
            raise ValueError(
                f"Each [[path_profiles]] entry must define non-empty language/path_prefix/profile in {policy_path}"
            )
        available_profiles = profiles_by_language.get(language, {})
        if profile not in available_profiles:
            available = (
                ", ".join(sorted(available_profiles))
                if available_profiles
                else "(none)"
            )
            raise ValueError(
                f"[[path_profiles]] references unknown profile={profile!r} for language={language!r} "
                + f"(available={available}) in {policy_path}"
            )
        parsed.append(
            _PathProfileRule(
                language=language,
                path_prefix=path_prefix,
                profile=profile,
            )
        )
    return tuple(parsed)


def _require_toml_table(
    value: object,
    *,
    context: str,
    policy_path: Path,
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a TOML table in {policy_path}")
    return cast(dict[str, object], value)


def _require_toml_list(
    value: object,
    *,
    context: str,
    policy_path: Path,
) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{context} must be a TOML list in {policy_path}")
    return cast(list[object], value)


def _build_command(
    *,
    gate: _GateSpec,
    repo_root: Path,
    target_paths: tuple[Path, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if gate.target_mode == "none":
        return gate.command, ()
    if gate.target_mode == "repo_root":
        repo_arg = _display_path(path=repo_root, repo_root=repo_root)
        return (*gate.command, repo_arg), (repo_arg,)
    target_args = tuple(
        _display_path(path=path, repo_root=repo_root) for path in target_paths
    )
    return (*gate.command, *target_args), target_args


def _display_path(*, path: Path, repo_root: Path) -> str:
    try:
        relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
        return relative or "."
    except Exception:
        return path.resolve().as_posix()


def _truncate_output(text: str) -> str:
    if len(text) <= _MAX_OUTPUT_CHARS:
        return text
    remainder = len(text) - _MAX_OUTPUT_CHARS
    return f"{text[:_MAX_OUTPUT_CHARS]}\n...[truncated {remainder} chars]"


__all__ = [
    "print_workspace_quality_report",
    "print_workspace_quality_result",
    "run_workspace_quality_gates",
]
