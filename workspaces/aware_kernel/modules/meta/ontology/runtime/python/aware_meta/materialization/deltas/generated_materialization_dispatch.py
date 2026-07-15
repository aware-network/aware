from __future__ import annotations

from collections.abc import Iterable
from typing import cast

from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta.language_plugin import MetaLanguagePlugin
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta.materialization.deltas.coercion import mapping_value, optional_text
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaGeneratedMaterializationBuilder,
    MetaProviderDeltaGeneratedMaterializationContext,
    MetaProviderDeltaGeneratedMaterializationFeatureResult,
    meta_provider_delta_world_change_event_key,
)
from aware_meta.materialization.deltas.language_renderer_contracts import (
    MetaLanguageGeneratedMaterializationDeltaContext,
    MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    MetaLanguageGeneratedMaterializationTargetHint,
)
from aware_meta.generated_materialization_contract import (
    generated_materialization_intent_target_metadata,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


PYTHON_COMPATIBILITY_TARGET_LANGUAGE = "python"


def explicit_language_generated_materialization_feature_result(
    *,
    feature_key: str,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaGeneratedMaterializationContext,
    dispatch_python: bool = False,
) -> MetaProviderDeltaGeneratedMaterializationFeatureResult | None:
    """Dispatch explicit generated materialization to language plugins.

    Python target-language contexts return ``None`` by default so the current
    Python ORM compatibility path stays unchanged for non-migrated providers.
    """

    target_language = _generated_materialization_dispatch_target_language(context)
    if target_language is None:
        return None
    if (
        target_language == PYTHON_COMPATIBILITY_TARGET_LANGUAGE
        and optional_text(context.target_language_plugin_id) is None
        and not dispatch_python
    ):
        return None

    event_refs = (meta_provider_delta_world_change_event_key(operation=operation),)
    try:
        code_language = CodeLanguage(target_language)
    except ValueError:
        return MetaProviderDeltaGeneratedMaterializationFeatureResult.from_blocked(
            feature_key=feature_key,
            operation=operation,
            reason="meta_generated_materialization_target_language_unknown",
            event_refs=event_refs,
            diagnostics=(f"target_language_not_supported:{target_language}",),
        )

    if not _ensure_target_language_plugin(code_language):
        return MetaProviderDeltaGeneratedMaterializationFeatureResult.from_blocked(
            feature_key=feature_key,
            operation=operation,
            reason="meta_generated_materialization_language_plugin_not_registered",
            event_refs=event_refs,
            diagnostics=(f"target_language_plugin_missing:{target_language}",),
        )
    plugin = MetaLanguagePluginRegistry.get(code_language)

    render_result = plugin.render_generated_materialization_delta(
        MetaLanguageGeneratedMaterializationDeltaRenderRequest(
            operation=operation,
            context=MetaLanguageGeneratedMaterializationDeltaContext.from_provider_context(
                context,
                target_hints=_generated_materialization_target_hints(
                    operation=operation,
                ),
            ),
        )
    )
    if (
        render_result.handled
        and render_result.delta_request is not None
        and render_result.result is not None
    ):
        return MetaProviderDeltaGeneratedMaterializationFeatureResult.from_evidence(
            feature_key=feature_key,
            operation=operation,
            delta_request=render_result.delta_request,
            result=render_result.result,
            reason="meta_generated_materialization_language_plugin_rendered",
        )

    return MetaProviderDeltaGeneratedMaterializationFeatureResult.from_blocked(
        feature_key=feature_key,
        operation=operation,
        reason=render_result.reason,
        event_refs=event_refs,
        diagnostics=(render_result.reason,),
    )


def target_language_generated_materialization_feature_results(
    *,
    feature_key: str,
    ontology_subject_kinds: Iterable[str],
    subject_not_supported_reason: str,
) -> MetaProviderDeltaGeneratedMaterializationBuilder:
    supported_subject_kinds = frozenset(ontology_subject_kinds)

    def _builder(
        operation: MetaProviderDeltaTypedOperation,
        context: MetaProviderDeltaGeneratedMaterializationContext,
    ) -> tuple[MetaProviderDeltaGeneratedMaterializationFeatureResult, ...]:
        event_refs = (meta_provider_delta_world_change_event_key(operation=operation),)
        if operation.ontology_subject_kind not in supported_subject_kinds:
            return (
                MetaProviderDeltaGeneratedMaterializationFeatureResult.skipped(
                    feature_key=feature_key,
                    operation=operation,
                    reason=subject_not_supported_reason,
                    event_refs=event_refs,
                ),
            )
        if _generated_materialization_requested_target_language(context) is None:
            return (
                MetaProviderDeltaGeneratedMaterializationFeatureResult.from_blocked(
                    feature_key=feature_key,
                    operation=operation,
                    reason="meta_generated_materialization_target_language_required",
                    event_refs=event_refs,
                    required_evidence_fields=("target_language",),
                    missing_evidence_fields=("target_language",),
                    diagnostics=("target_language_missing",),
                ),
            )

        dispatched = explicit_language_generated_materialization_feature_result(
            feature_key=feature_key,
            operation=operation,
            context=context,
            dispatch_python=True,
        )
        if dispatched is not None:
            return (dispatched,)

        return (
            MetaProviderDeltaGeneratedMaterializationFeatureResult.from_blocked(
                feature_key=feature_key,
                operation=operation,
                reason="meta_generated_materialization_language_dispatch_required",
                event_refs=event_refs,
                diagnostics=("language_dispatch_result_missing",),
            ),
        )

    return _builder


def _generated_materialization_target_hints(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[MetaLanguageGeneratedMaterializationTargetHint, ...]:
    hints: list[MetaLanguageGeneratedMaterializationTargetHint] = []
    seen: set[tuple[str | None, str | None, str | None, str | None]] = set()
    for payload in _generated_materialization_payloads(operation=operation):
        generated = mapping_value(payload.get("generated_materialization"))
        if not generated:
            continue
        for descriptor_key, target_payload in mapping_value(
            generated.get("targets")
        ).items():
            target = mapping_value(target_payload)
            hint = _target_hint_from_payload(
                descriptor_key=str(descriptor_key),
                target=target,
                owner_payload=payload,
            )
            if hint is None:
                continue
            key = (
                hint.descriptor_key,
                hint.capability_key,
                hint.owner_key,
                hint.relative_path,
            )
            if key not in seen:
                hints.append(hint)
                seen.add(key)
    return tuple(hints)


def _generated_materialization_payloads(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[dict[str, object], ...]:
    payloads: list[dict[str, object]] = []
    current = dict(operation.current)
    baseline = mapping_value(operation.baseline)
    baseline_object = mapping_value(baseline.get("object"))
    current_payload = mapping_value(current.get("payload"))
    for payload in (
        current,
        dict(current_payload),
        dict(baseline_object),
        dict(baseline),
        dict(operation.semantic_change_projection or {}),
        dict(operation.extra),
    ):
        if payload and any(
            existing is payload or existing == payload for existing in payloads
        ):
            continue
        payloads.append(payload)
    return tuple(payloads)


def _target_hint_from_payload(
    *,
    descriptor_key: str,
    target: dict[str, object],
    owner_payload: dict[str, object],
) -> MetaLanguageGeneratedMaterializationTargetHint | None:
    relative_path = optional_text(target.get("relative_path"))
    if relative_path is None:
        return None
    return MetaLanguageGeneratedMaterializationTargetHint(
        descriptor_key=optional_text(target.get("descriptor_key")) or descriptor_key,
        capability_key=optional_text(target.get("capability_key")) or descriptor_key,
        target_language=optional_text(target.get("target_language")),
        target_language_plugin_id=optional_text(
            target.get("target_language_plugin_id")
        ),
        renderer_profile=optional_text(target.get("renderer_profile")),
        materialization_source=optional_text(target.get("materialization_source")),
        product_intent=optional_text(target.get("product_intent")),
        semantic_key=(
            optional_text(target.get("semantic_key"))
            or optional_text(owner_payload.get("semantic_key"))
        ),
        owner_key=optional_text(target.get("owner_key"))
        or _owner_key_from_payload(owner_payload),
        target_key=optional_text(target.get("target_key")),
        output_key=optional_text(target.get("output_key")),
        relative_path=relative_path,
        artifact_family=optional_text(target.get("artifact_family")),
        artifact_role=optional_text(target.get("artifact_role")),
    )


def _generated_materialization_dispatch_target_language(
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> str | None:
    return optional_text(context.target_language_plugin_id) or optional_text(
        context.target_language
    )


def _generated_materialization_requested_target_language(
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> str | None:
    return optional_text(context.target_language) or optional_text(
        context.target_language_plugin_id
    )


def _ensure_target_language_plugin(target_language_plugin_id: CodeLanguage) -> bool:
    if MetaLanguagePluginRegistry.has_language(target_language_plugin_id):
        return True
    for plugin in AwareModulePluginRegistry.get_builtin_meta_language_plugins():
        MetaLanguagePluginRegistry.register(cast(MetaLanguagePlugin, plugin))
    return MetaLanguagePluginRegistry.has_language(target_language_plugin_id)


def _owner_key_from_payload(payload: dict[str, object]) -> str | None:
    return (
        optional_text(payload.get("owner_key"))
        or optional_text(payload.get("class_fqn"))
        or optional_text(payload.get("enum_fqn"))
    )


__all__ = [
    "explicit_language_generated_materialization_feature_result",
    "generated_materialization_intent_target_metadata",
    "target_language_generated_materialization_feature_results",
]
