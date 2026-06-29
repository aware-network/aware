from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.package_strategy import (
    ObjectConfigGraphPackageResult,
    ObjectConfigGraphPackageSpec,
)
from aware_meta.language_plugin import (
    MetaLanguagePackageStrategyConfigurationRequest,
)
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPackageBuildRequest:
    target_language_plugin_id: CodeLanguage
    layout_base_dir: Path
    target_output_dir: Path
    rendered_files: tuple[Path, ...] = ()
    package_specs: tuple[ObjectConfigGraphPackageSpec, ...] = ()
    materialization_source: str | None = None
    renderer_profile: str | None = None
    renderer_kind: str | None = None
    package_kind: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPackageBuildResult:
    package_results: tuple[ObjectConfigGraphPackageResult, ...] = ()
    warnings: tuple[str, ...] = ()
    metrics: Mapping[str, object] = field(default_factory=dict)


def build_language_materialization_packages(
    request: LanguageMaterializationPackageBuildRequest,
) -> LanguageMaterializationPackageBuildResult:
    """Build language materialization packages through the Meta plugin boundary."""

    if not request.package_specs:
        return LanguageMaterializationPackageBuildResult(metrics={"package_count": 0})

    strategy = MetaLanguagePluginRegistry.create_package_strategy(
        request.target_language_plugin_id,
        request.layout_base_dir,
    )
    if strategy is None:
        return LanguageMaterializationPackageBuildResult(
            metrics={
                "package_count": 0,
                "package_strategy_available": False,
            }
        )

    MetaLanguagePluginRegistry.configure_package_strategy(
        request.target_language_plugin_id,
        MetaLanguagePackageStrategyConfigurationRequest(
            target_language_plugin_id=request.target_language_plugin_id,
            strategy=strategy,
            package_specs=request.package_specs,
            materialization_source=request.materialization_source,
            renderer_profile=request.renderer_profile,
            renderer_kind=request.renderer_kind,
            package_kind=request.package_kind,
            metadata=dict(request.metadata),
        ),
    )

    package_results: list[ObjectConfigGraphPackageResult] = []
    for spec in request.package_specs:
        effective_spec = spec
        if effective_spec.package_root is None:
            effective_spec = effective_spec.model_copy(
                update={"package_root": request.target_output_dir}
            )
        package_results.append(
            strategy.build_package(
                list(request.rendered_files),
                effective_spec,
            )
        )

    return LanguageMaterializationPackageBuildResult(
        package_results=tuple(package_results),
        metrics={
            "package_count": len(package_results),
            "package_names": tuple(result.name for result in package_results),
            "changed_file_count": sum(
                len(result.changed_files) for result in package_results
            ),
            "package_strategy_available": True,
            "package_strategy_class": type(strategy).__name__,
        },
    )


__all__ = [
    "LanguageMaterializationPackageBuildRequest",
    "LanguageMaterializationPackageBuildResult",
    "build_language_materialization_packages",
]
