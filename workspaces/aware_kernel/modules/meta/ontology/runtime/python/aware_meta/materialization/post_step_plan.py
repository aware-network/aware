from __future__ import annotations

from dataclasses import dataclass, field

from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.language.tooling import CodeLanguageToolSpec
from aware_code_ontology.code.code_enums import CodeLanguage


_DEFAULT_METADATA_KEY = "materialization_post_step_default"
_ORDER_METADATA_KEY = "materialization_post_step_order"
_LEGACY_NAMES_METADATA_KEY = "materialization_post_step_legacy_names"
_WARN_IF_MISSING_METADATA_KEY = "materialization_post_step_warn_if_missing"
_MISSING_WARNING_METADATA_KEY = "materialization_post_step_missing_warning"


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepInput:
    name: str
    packages: tuple[str, ...] = ()
    on_fail: str = "fail"
    args: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepPlanRequest:
    target_language_plugin_id: CodeLanguage
    explicit_steps: tuple[LanguageMaterializationPostStepInput, ...] = ()
    has_packages: bool = False


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepPlanItem:
    tool_id: str
    packages: tuple[str, ...] = ()
    on_fail: str = "fail"
    args: tuple[str, ...] = ()
    source: str = "explicit"
    requested_name: str | None = None


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPostStepPlan:
    steps: tuple[LanguageMaterializationPostStepPlanItem, ...] = ()
    warnings: tuple[str, ...] = ()
    metrics: dict[str, object] = field(default_factory=dict)


def plan_language_materialization_post_steps(
    request: LanguageMaterializationPostStepPlanRequest,
) -> LanguageMaterializationPostStepPlan:
    """Plan materialization post steps from Code language tool declarations."""

    tool_specs = _language_tool_specs(request.target_language_plugin_id)
    specs_by_name = _tool_specs_by_name(tool_specs)

    if request.explicit_steps:
        planned_steps = tuple(
            _plan_explicit_step(step=step, specs_by_name=specs_by_name)
            for step in request.explicit_steps
            if step.name.strip()
        )
        warnings = _missing_expected_tool_warnings(
            has_packages=request.has_packages,
            planned_tool_ids=tuple(step.tool_id for step in planned_steps),
            tool_specs=tool_specs,
        )
        return LanguageMaterializationPostStepPlan(
            steps=planned_steps,
            warnings=warnings,
            metrics=_plan_metrics(planned_steps),
        )

    if not request.has_packages:
        return LanguageMaterializationPostStepPlan(
            metrics={"post_step_count": 0, "post_step_source": "none"},
        )

    default_specs = sorted(
        (
            spec
            for spec in tool_specs
            if _metadata_bool(spec.metadata.get(_DEFAULT_METADATA_KEY))
        ),
        key=_tool_default_sort_key,
    )
    planned_steps = tuple(
        LanguageMaterializationPostStepPlanItem(
            tool_id=spec.tool_id,
            packages=(),
            on_fail="fail",
            args=(),
            source="default",
        )
        for spec in default_specs
    )
    return LanguageMaterializationPostStepPlan(
        steps=planned_steps,
        metrics=_plan_metrics(planned_steps),
    )


def canonical_language_materialization_post_step_tool_id(
    *,
    target_language_plugin_id: CodeLanguage,
    step_name: str,
) -> str:
    """Return the Code tool id for a post-step name or legacy alias."""

    specs_by_name = _tool_specs_by_name(_language_tool_specs(target_language_plugin_id))
    return _canonical_tool_id(step_name=step_name, specs_by_name=specs_by_name)


def _plan_explicit_step(
    *,
    step: LanguageMaterializationPostStepInput,
    specs_by_name: dict[str, CodeLanguageToolSpec],
) -> LanguageMaterializationPostStepPlanItem:
    return LanguageMaterializationPostStepPlanItem(
        tool_id=_canonical_tool_id(step_name=step.name, specs_by_name=specs_by_name),
        packages=step.packages,
        on_fail=step.on_fail,
        args=step.args,
        source="explicit",
        requested_name=step.name,
    )


def _canonical_tool_id(
    *,
    step_name: str,
    specs_by_name: dict[str, CodeLanguageToolSpec],
) -> str:
    normalized = step_name.strip()
    if not normalized:
        return normalized
    spec = specs_by_name.get(normalized)
    if spec is not None:
        return spec.tool_id
    return normalized


def _tool_specs_by_name(
    tool_specs: tuple[CodeLanguageToolSpec, ...],
) -> dict[str, CodeLanguageToolSpec]:
    out: dict[str, CodeLanguageToolSpec] = {}
    for spec in tool_specs:
        out[spec.tool_id] = spec
        for legacy_name in _metadata_csv(spec.metadata.get(_LEGACY_NAMES_METADATA_KEY)):
            out[legacy_name] = spec
    return out


def _missing_expected_tool_warnings(
    *,
    has_packages: bool,
    planned_tool_ids: tuple[str, ...],
    tool_specs: tuple[CodeLanguageToolSpec, ...],
) -> tuple[str, ...]:
    if not has_packages:
        return ()
    planned = set(planned_tool_ids)
    warnings: list[str] = []
    for spec in tool_specs:
        if spec.tool_id in planned:
            continue
        if not _metadata_bool(spec.metadata.get(_WARN_IF_MISSING_METADATA_KEY)):
            continue
        warning = spec.metadata.get(_MISSING_WARNING_METADATA_KEY)
        if not warning:
            warning = f"Materialization post-step {spec.tool_id!r} is not configured."
        warnings.append(warning)
    return tuple(warnings)


def _plan_metrics(
    planned_steps: tuple[LanguageMaterializationPostStepPlanItem, ...],
) -> dict[str, object]:
    return {
        "post_step_count": len(planned_steps),
        "post_step_tool_ids": tuple(step.tool_id for step in planned_steps),
        "post_step_sources": tuple(step.source for step in planned_steps),
    }


def _language_tool_specs(language: CodeLanguage) -> tuple[CodeLanguageToolSpec, ...]:
    try:
        plugin = CodeLanguagePluginRegistry.get(language)
    except KeyError:
        try:
            from aware_code.setup_language_plugins import setup_code_plugins
        except Exception:
            raise
        setup_code_plugins()
        plugin = CodeLanguagePluginRegistry.get(language)
    return tuple(plugin.tooling)


def _tool_default_sort_key(spec: CodeLanguageToolSpec) -> tuple[int, str]:
    raw = spec.metadata.get(_ORDER_METADATA_KEY)
    try:
        order = int(str(raw or "").strip())
    except Exception:
        order = 1000
    return order, spec.tool_id


def _metadata_bool(value: object) -> bool:
    normalized = str(value or "").strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def _metadata_csv(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(
        token.strip()
        for token in str(value).split(",")
        if token.strip()
    )


__all__ = [
    "LanguageMaterializationPostStepInput",
    "LanguageMaterializationPostStepPlan",
    "LanguageMaterializationPostStepPlanItem",
    "LanguageMaterializationPostStepPlanRequest",
    "canonical_language_materialization_post_step_tool_id",
    "plan_language_materialization_post_steps",
]
