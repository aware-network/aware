from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.code_dto import (
    CodeSectionDeltaEntry,
)
from aware_meta.class_.config.deltas.provider import (
    CLASS_CONFIG_DELTA_FEATURE_PROVIDER,
)
from aware_meta.class_.config.relationship.deltas.provider import (
    RELATIONSHIP_CONFIG_DELTA_FEATURE_PROVIDER,
)
from aware_meta.enum.config.deltas.provider import (
    ENUM_CONFIG_DELTA_FEATURE_PROVIDER,
)
from aware_meta.attribute.config.deltas.provider import (
    ATTRIBUTE_CONFIG_DELTA_FEATURE_PROVIDER,
)
from aware_meta.function.config.deltas.provider import (
    FUNCTION_CONFIG_DELTA_FEATURE_PROVIDER,
)
from aware_meta.function.impl.deltas.provider import (
    FUNCTION_IMPL_DELTA_FEATURE_PROVIDER,
)
from aware_meta.graph.config.deltas.provider import (
    OBJECT_CONFIG_GRAPH_DELTA_FEATURE_PROVIDER,
)
from aware_meta.graph.package.deltas.provider import (
    OBJECT_CONFIG_GRAPH_PACKAGE_DELTA_FEATURE_PROVIDER,
)
from aware_meta.graph.projection.deltas.provider import (
    OBJECT_PROJECTION_GRAPH_DELTA_FEATURE_PROVIDER,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaFeatureProvider,
    MetaProviderDeltaGeneratedMaterializationContext,
    MetaProviderDeltaGeneratedMaterializationFeatureResult,
    MetaProviderDeltaOntologyOperationRegistration,
    MetaProviderDeltaSemanticOperationResolver,
    MetaProviderDeltaSemanticOperationResolverRegistration,
    MetaProviderDeltaSourceProjectionContext,
    MetaProviderDeltaSourceProjectionFeatureResult,
    MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration,
    meta_provider_delta_world_change_event_key,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


_FEATURE_PROVIDERS = (
    OBJECT_CONFIG_GRAPH_PACKAGE_DELTA_FEATURE_PROVIDER,
    OBJECT_CONFIG_GRAPH_DELTA_FEATURE_PROVIDER,
    OBJECT_PROJECTION_GRAPH_DELTA_FEATURE_PROVIDER,
    CLASS_CONFIG_DELTA_FEATURE_PROVIDER,
    ENUM_CONFIG_DELTA_FEATURE_PROVIDER,
    RELATIONSHIP_CONFIG_DELTA_FEATURE_PROVIDER,
    ATTRIBUTE_CONFIG_DELTA_FEATURE_PROVIDER,
    FUNCTION_CONFIG_DELTA_FEATURE_PROVIDER,
    FUNCTION_IMPL_DELTA_FEATURE_PROVIDER,
)


def registered_feature_providers() -> tuple[MetaProviderDeltaFeatureProvider, ...]:
    return _FEATURE_PROVIDERS


def ontology_operation_registrations() -> tuple[
    MetaProviderDeltaOntologyOperationRegistration,
    ...,
]:
    return tuple(
        registration
        for provider in _FEATURE_PROVIDERS
        for registration in provider.ontology_operation_registrations
    )


def typed_operation_dirty_entry_planner_registrations() -> tuple[
    MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration,
    ...,
]:
    return tuple(
        registration
        for provider in _FEATURE_PROVIDERS
        for registration in (
            provider.typed_operation_dirty_entry_planner_registrations
        )
    )


def semantic_operation_resolver_registrations() -> tuple[
    MetaProviderDeltaSemanticOperationResolverRegistration,
    ...,
]:
    return tuple(
        registration
        for provider in _FEATURE_PROVIDERS
        for registration in provider.semantic_operation_resolver_registrations
    )


def semantic_operation_resolver_for_type(
    semantic_operation_type: str,
) -> MetaProviderDeltaSemanticOperationResolver | None:
    for registration in semantic_operation_resolver_registrations():
        if registration.handles_operation_type(semantic_operation_type):
            return registration.resolver
    return None


def typed_operation_dirty_entries_from_feature_provider(
    *,
    entry: Mapping[str, object],
    ontology_subject_kind: str,
    operation_family: str,
) -> tuple[dict[str, object], ...] | None:
    for registration in typed_operation_dirty_entry_planner_registrations():
        if (ontology_subject_kind, operation_family) in registration.registration_keys():
            return registration.planner(entry)
    return None


def code_section_delta_entries_from_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    *,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[CodeSectionDeltaEntry, ...]:
    return tuple(
        entry
        for result in source_projection_feature_results_from_typed_operation(
            operation=operation,
            context=context,
        )
        for entry in result.entries
    )


def source_projection_feature_results_from_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    *,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[MetaProviderDeltaSourceProjectionFeatureResult, ...]:
    results: list[MetaProviderDeltaSourceProjectionFeatureResult] = []
    providers = _feature_providers_for_subject_kind(
        operation.ontology_subject_kind,
    )
    if not providers:
        return (
            MetaProviderDeltaSourceProjectionFeatureResult.skipped(
                feature_key="unregistered",
                operation=operation,
                reason="meta_source_projection_feature_provider_not_registered",
                event_refs=(
                    meta_provider_delta_world_change_event_key(operation=operation),
                ),
            ),
        )
    for provider in providers:
        if provider.source_projection_builder is None:
            results.append(
                MetaProviderDeltaSourceProjectionFeatureResult.skipped(
                    feature_key=provider.feature_key,
                    operation=operation,
                    reason="meta_source_projection_feature_builder_not_declared",
                    event_refs=(
                        meta_provider_delta_world_change_event_key(
                            operation=operation,
                        ),
                    ),
                )
            )
            continue
        results.extend(provider.source_projection_builder(operation, context))
    return tuple(results)


def generated_materialization_feature_results_from_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    *,
    context: MetaProviderDeltaGeneratedMaterializationContext,
) -> tuple[MetaProviderDeltaGeneratedMaterializationFeatureResult, ...]:
    results: list[MetaProviderDeltaGeneratedMaterializationFeatureResult] = []
    providers = _feature_providers_for_subject_kind(
        operation.ontology_subject_kind,
    )
    if not providers:
        return (
            MetaProviderDeltaGeneratedMaterializationFeatureResult.skipped(
                feature_key="unregistered",
                operation=operation,
                reason=(
                    "meta_generated_materialization_feature_provider_not_registered"
                ),
                event_refs=(
                    meta_provider_delta_world_change_event_key(operation=operation),
                ),
            ),
        )
    for provider in providers:
        if provider.generated_materialization_builder is None:
            results.append(
                MetaProviderDeltaGeneratedMaterializationFeatureResult.skipped(
                    feature_key=provider.feature_key,
                    operation=operation,
                    reason=(
                        "meta_generated_materialization_feature_builder_not_declared"
                    ),
                    event_refs=(
                        meta_provider_delta_world_change_event_key(
                            operation=operation,
                        ),
                    ),
                )
            )
            continue
        results.extend(provider.generated_materialization_builder(operation, context))
    return tuple(results)


def _feature_providers_for_subject_kind(
    ontology_subject_kind: str,
) -> tuple[MetaProviderDeltaFeatureProvider, ...]:
    return tuple(
        provider
        for provider in _FEATURE_PROVIDERS
        if provider.handles_subject_kind(ontology_subject_kind)
    )


__all__ = [
    "code_section_delta_entries_from_typed_operation",
    "generated_materialization_feature_results_from_typed_operation",
    "ontology_operation_registrations",
    "registered_feature_providers",
    "semantic_operation_resolver_for_type",
    "semantic_operation_resolver_registrations",
    "source_projection_feature_results_from_typed_operation",
    "typed_operation_dirty_entries_from_feature_provider",
    "typed_operation_dirty_entry_planner_registrations",
]
