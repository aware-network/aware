from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization.artifact_lifecycle import (
    LanguageMaterializationProducerStep,
)
from aware_meta.materialization.tool_runner import resolve_language_materialization_tool_spec


_TARGET_SUFFIXES_METADATA_KEY = "materialization_target_suffixes"
_TARGET_SEARCH_ROOTS_METADATA_KEY = "materialization_target_search_roots"
_TARGET_EXCLUDED_SUFFIXES_METADATA_KEY = "materialization_target_excluded_suffixes"


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepPackageContext:
    package_name: str
    package_root: Path
    package_files: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepTargetDiscoveryRequest:
    target_language_plugin_id: CodeLanguage
    tool_id: str
    package_contexts: tuple[LanguageMaterializationPostStepPackageContext, ...] = ()
    candidate_paths: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepPackageTargets:
    package_name: str | None
    package_root: Path | None
    target_paths: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepTargetDiscoveryResult:
    tool_id: str
    package_targets: tuple[LanguageMaterializationPostStepPackageTargets, ...] = ()
    metrics: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepExecutionResult:
    tool_id: str
    package_name: str | None = None
    package_root: Path | None = None
    target_paths: tuple[Path, ...] = ()
    changed_paths: tuple[Path, ...] = ()
    produced_paths: tuple[Path, ...] = ()
    producer_step: LanguageMaterializationProducerStep = (
        LanguageMaterializationProducerStep.post_step
    )
    warnings: tuple[str, ...] = ()
    metrics: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepPackageLifecycleInput:
    package_name: str
    package_root: Path
    package_files: tuple[Path, ...] = ()
    refreshed_package_files: tuple[Path, ...] | None = None


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepPackageLifecycleResult:
    package_name: str
    package_root: Path
    package_files: tuple[Path, ...] = ()
    package_files_changed: bool = False
    has_execution_effects: bool = False
    should_track_outputs: bool = False


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepLifecycleReconciliationRequest:
    target_language_plugin_id: CodeLanguage
    package_contexts: tuple[
        LanguageMaterializationPostStepPackageLifecycleInput, ...
    ] = ()
    execution_results: tuple[
        LanguageMaterializationPostStepExecutionResult, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepLifecycleReconciliationResult:
    target_language_plugin_id: CodeLanguage
    package_results: tuple[
        LanguageMaterializationPostStepPackageLifecycleResult, ...
    ] = ()
    should_track_outputs: bool = False
    metrics: Mapping[str, object] = field(default_factory=dict)


def discover_language_materialization_post_step_targets(
    request: LanguageMaterializationPostStepTargetDiscoveryRequest,
) -> LanguageMaterializationPostStepTargetDiscoveryResult:
    """Discover post-step target paths from Code language tool metadata."""

    spec = resolve_language_materialization_tool_spec(
        target_language_plugin_id=request.target_language_plugin_id,
        tool_id=request.tool_id,
    )
    suffixes = _metadata_csv(spec.metadata.get(_TARGET_SUFFIXES_METADATA_KEY))
    excluded_suffixes = _metadata_csv(
        spec.metadata.get(_TARGET_EXCLUDED_SUFFIXES_METADATA_KEY)
    )
    search_roots = _metadata_csv(spec.metadata.get(_TARGET_SEARCH_ROOTS_METADATA_KEY))
    package_targets: list[LanguageMaterializationPostStepPackageTargets] = []

    if request.package_contexts:
        for context in request.package_contexts:
            package_targets.append(
                LanguageMaterializationPostStepPackageTargets(
                    package_name=context.package_name,
                    package_root=context.package_root.resolve(),
                    target_paths=_filter_target_paths(
                        paths=_candidate_paths_for_package(
                            context=context,
                            search_roots=search_roots,
                        ),
                        suffixes=suffixes,
                        excluded_suffixes=excluded_suffixes,
                    ),
                )
            )
    else:
        package_targets.append(
            LanguageMaterializationPostStepPackageTargets(
                package_name=None,
                package_root=None,
                target_paths=_filter_target_paths(
                    paths=request.candidate_paths,
                    suffixes=suffixes,
                    excluded_suffixes=excluded_suffixes,
                ),
            )
        )

    return LanguageMaterializationPostStepTargetDiscoveryResult(
        tool_id=spec.tool_id,
        package_targets=tuple(package_targets),
        metrics={
            "post_step_target_tool_id": spec.tool_id,
            "post_step_target_count": sum(
                len(item.target_paths) for item in package_targets
            ),
            "post_step_target_package_count": len(package_targets),
        },
    )


def language_materialization_post_step_execution_path_hints(
    results: Iterable[LanguageMaterializationPostStepExecutionResult],
) -> dict[Path, LanguageMaterializationProducerStep]:
    """Return lifecycle producer-step hints from post-step execution records."""

    hints: dict[Path, LanguageMaterializationProducerStep] = {}
    for result in results:
        producer_step = _coerce_producer_step(result.producer_step)
        for path in (*result.changed_paths, *result.produced_paths):
            hints[Path(path).resolve()] = producer_step
    return hints


def reconcile_language_materialization_post_step_lifecycle(
    request: LanguageMaterializationPostStepLifecycleReconciliationRequest,
) -> LanguageMaterializationPostStepLifecycleReconciliationResult:
    """Reconcile package files and tracking policy after post-step execution."""

    effect_packages = {
        result.package_name
        for result in request.execution_results
        if result.package_name is not None
        and (result.changed_paths or result.produced_paths)
    }
    has_global_effects = any(
        result.package_name is None
        and (result.changed_paths or result.produced_paths)
        for result in request.execution_results
    )
    has_any_effects = bool(effect_packages or has_global_effects)
    package_results: list[LanguageMaterializationPostStepPackageLifecycleResult] = []

    for context in request.package_contexts:
        before_files = _normalize_paths(context.package_files)
        after_files = _normalize_paths(
            context.refreshed_package_files
            if context.refreshed_package_files is not None
            else context.package_files
        )
        package_files_changed = before_files != after_files
        has_execution_effects = (
            has_global_effects or context.package_name in effect_packages
        )
        package_results.append(
            LanguageMaterializationPostStepPackageLifecycleResult(
                package_name=context.package_name,
                package_root=Path(context.package_root).resolve(),
                package_files=after_files,
                package_files_changed=package_files_changed,
                has_execution_effects=has_execution_effects,
                should_track_outputs=(
                    package_files_changed or has_execution_effects
                ),
            )
        )

    should_track_outputs = has_any_effects or any(
        item.package_files_changed for item in package_results
    )
    return LanguageMaterializationPostStepLifecycleReconciliationResult(
        target_language_plugin_id=request.target_language_plugin_id,
        package_results=tuple(package_results),
        should_track_outputs=should_track_outputs,
        metrics={
            "post_step_execution_result_count": len(request.execution_results),
            "post_step_execution_effect_path_count": sum(
                len(result.changed_paths) + len(result.produced_paths)
                for result in request.execution_results
            ),
            "post_step_lifecycle_package_count": len(package_results),
            "post_step_lifecycle_refreshed_package_count": sum(
                1 for item in package_results if item.package_files_changed
            ),
            "post_step_lifecycle_should_track_outputs": should_track_outputs,
        },
    )


def _candidate_paths_for_package(
    *,
    context: LanguageMaterializationPostStepPackageContext,
    search_roots: tuple[str, ...],
) -> tuple[Path, ...]:
    candidates: set[Path] = {
        Path(path).resolve()
        for path in context.package_files
        if Path(path).exists() and not Path(path).is_dir()
    }
    package_root = context.package_root.resolve()
    for search_root in search_roots:
        root = (package_root / search_root).resolve()
        if not root.exists():
            continue
        candidates.update(
            path.resolve()
            for path in root.rglob("*")
            if path.exists() and not path.is_dir()
        )
    return tuple(sorted(candidates, key=lambda path: path.as_posix()))


def _filter_target_paths(
    *,
    paths: Iterable[Path],
    suffixes: tuple[str, ...],
    excluded_suffixes: tuple[str, ...],
) -> tuple[Path, ...]:
    targets: list[Path] = []
    for path in paths:
        resolved = Path(path).resolve()
        if not resolved.exists() or resolved.is_dir():
            continue
        if suffixes and not _matches_any_suffix(resolved, suffixes):
            continue
        if excluded_suffixes and _matches_any_suffix(resolved, excluded_suffixes):
            continue
        targets.append(resolved)
    return tuple(sorted(dict.fromkeys(targets), key=lambda path: path.as_posix()))


def _matches_any_suffix(path: Path, suffixes: tuple[str, ...]) -> bool:
    text = path.name.lower()
    return any(text.endswith(suffix.lower()) for suffix in suffixes)


def _coerce_producer_step(value: object) -> LanguageMaterializationProducerStep:
    if isinstance(value, LanguageMaterializationProducerStep):
        return value
    if value is None:
        return LanguageMaterializationProducerStep.post_step
    token = str(value).strip()
    if not token:
        return LanguageMaterializationProducerStep.post_step
    by_member_name = LanguageMaterializationProducerStep.__members__.get(token)
    if by_member_name is not None:
        return by_member_name
    return LanguageMaterializationProducerStep(token)


def _normalize_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    return tuple(
        sorted(
            {Path(path).resolve() for path in paths},
            key=lambda path: path.as_posix(),
        )
    )


def _metadata_csv(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(
        token.strip()
        for token in str(value).split(",")
        if token.strip()
    )


__all__ = [
    "LanguageMaterializationPostStepExecutionResult",
    "LanguageMaterializationPostStepPackageContext",
    "LanguageMaterializationPostStepPackageLifecycleInput",
    "LanguageMaterializationPostStepPackageLifecycleResult",
    "LanguageMaterializationPostStepPackageTargets",
    "LanguageMaterializationPostStepLifecycleReconciliationRequest",
    "LanguageMaterializationPostStepLifecycleReconciliationResult",
    "LanguageMaterializationPostStepTargetDiscoveryRequest",
    "LanguageMaterializationPostStepTargetDiscoveryResult",
    "discover_language_materialization_post_step_targets",
    "language_materialization_post_step_execution_path_hints",
    "reconcile_language_materialization_post_step_lifecycle",
]
