from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from inspect import Parameter, isawaitable, signature
import os
import re
from typing import Any, cast
from uuid import UUID

from aware_code.types import JsonArray, JsonObject
from aware_meta.graph.instance.commit.perf_trace import commit_perf_span
from aware_meta.graph.instance.diff import (
    build_object_instance_graph_class_instance_update_changes,
)
from aware_meta.graph.instance.diff_orm import (
    OrmChangeTranslationError,
    build_object_instance_graph_evidence_from_orm_change_set,
)
from aware_meta.graph.instance.commit.body_codec import OigCommitBodyDraft
from aware_meta.graph.instance.builder import build_object_instance_graph
from aware_meta.attribute.instance.builder import build_attribute
from aware_meta.runtime.handler_executor.argument_coercion import (
    coerce_meta_handler_call_kwargs,
)
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphFunctionImplementationDescriptor,
    MetaGraphHandlerExecutionRequest,
    MetaGraphPreState,
)
from aware_meta.runtime.handler_executor.execution_context import (
    MetaGraphHandlerExecutionContext,
    current_meta_graph_handler_execution_context_or_none,
)
from aware_meta.runtime.handler_executor.language_handler import (
    MetaGraphGeneratedInvocationHandlerCallable,
    MetaGraphGeneratedInvocationHandlerResolver,
    MetaGraphGeneratedLanguageHandlerCallable,
    MetaGraphGeneratedLanguageHandlerResolver,
    MetaGraphGeneratedLanguageHandlerResolutionError,
    MetaGraphLanguageHandlerExecution,
    MetaGraphLanguageHandlerExecutionError,
)
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry
from aware_orm.session.change_collector import ORMChangeSet, current_change_collector
from pydantic import BaseModel


_IMPL_DELEGATION_DIRECT_CHANGE_EVIDENCE_ENV = (
    "AWARE_META_IMPL_DELEGATION_DIRECT_CHANGE_EVIDENCE"
)
_IMPL_DELEGATION_SIMPLE_SCALAR_DIRECT_CHANGE_EVIDENCE_ENV = (
    "AWARE_META_IMPL_DELEGATION_SIMPLE_SCALAR_DIRECT_CHANGE_EVIDENCE"
)


@dataclass(frozen=True, slots=True)
class _SimpleScalarDirectChangeAttempt:
    changes: tuple[ObjectInstanceGraphChange, ...] = ()
    fallback_reason: str | None = None


@dataclass(frozen=True, slots=True)
class MetaGraphImplDelegatingLanguageHandlerResolver:
    """Resolve generated language-handler calls to authored Meta handler impls."""

    delegate: MetaGraphGeneratedLanguageHandlerResolver | None = None

    def resolve_generated_language_handler(
        self,
        descriptor: MetaGraphFunctionImplementationDescriptor,
    ) -> MetaGraphGeneratedLanguageHandlerCallable:
        impl = resolve_meta_handler_impl(descriptor)
        if impl is not None:
            return _MetaGraphImplDelegatingLanguageHandler(
                descriptor=descriptor,
                impl=impl,
            )
        if self.delegate is None:
            key = descriptor.function_config.owner_key
            function_name = descriptor.function_config.name
            raise MetaGraphGeneratedLanguageHandlerResolutionError(
                "No generated Meta language handler or authored impl "
                "registered: "
                f"owner_key={key} function_name={function_name} "
                f"is_constructor={descriptor.is_constructor}"
            )
        return self.delegate.resolve_generated_language_handler(descriptor)


def meta_graph_impl_delegating_language_handler_resolver(
    delegate: MetaGraphGeneratedLanguageHandlerResolver | None,
) -> MetaGraphGeneratedLanguageHandlerResolver:
    return MetaGraphImplDelegatingLanguageHandlerResolver(delegate=delegate)


@dataclass(frozen=True, slots=True)
class MetaGraphImplDelegatingInvocationHandlerResolver:
    """Resolve generated invocation calls to authored Meta handler impls."""

    delegate: MetaGraphGeneratedInvocationHandlerResolver | None = None

    def resolve_generated_invocation_handler(
        self,
        descriptor: MetaGraphFunctionImplementationDescriptor,
    ) -> MetaGraphGeneratedInvocationHandlerCallable:
        impl = resolve_meta_handler_impl(descriptor)
        if impl is not None:
            return _MetaGraphImplDelegatingInvocationHandler(
                descriptor=descriptor,
                impl=impl,
            )
        if self.delegate is None:
            key = descriptor.function_config.owner_key
            function_name = descriptor.function_config.name
            raise MetaGraphGeneratedLanguageHandlerResolutionError(
                "No generated Meta invocation handler or authored impl "
                "registered: "
                f"owner_key={key} function_name={function_name} "
                f"is_constructor={descriptor.is_constructor}"
            )
        return self.delegate.resolve_generated_invocation_handler(descriptor)


def meta_graph_impl_delegating_invocation_handler_resolver(
    delegate: MetaGraphGeneratedInvocationHandlerResolver | None,
) -> MetaGraphGeneratedInvocationHandlerResolver:
    return MetaGraphImplDelegatingInvocationHandlerResolver(delegate=delegate)


def resolve_meta_handler_impl(
    descriptor: MetaGraphFunctionImplementationDescriptor,
) -> Callable[..., object] | None:
    function_name = descriptor.function_config.name
    for module_name in _candidate_impl_module_names(descriptor):
        try:
            module_spec = find_spec(module_name)
        except ModuleNotFoundError:
            continue
        if module_spec is None:
            continue
        module = import_module(module_name)
        impl = getattr(module, function_name, None)
        if callable(impl):
            return cast(Callable[..., object], impl)
    return None


@dataclass(frozen=True, slots=True)
class _MetaGraphImplDelegatingInvocationHandler:
    descriptor: MetaGraphFunctionImplementationDescriptor
    impl: Callable[..., object]

    async def __call__(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        target: ORMModel | type[ORMModel],
        positional: JsonArray,
        keyword: JsonObject,
    ) -> object:
        _ = request, pre_state
        call_kwargs = _bind_impl_call_kwargs(
            impl=self.impl,
            target=target,
            positional=positional,
            keyword=keyword,
            is_constructor=self.descriptor.is_constructor,
        )
        result = self.impl(
            **_coerce_impl_call_kwargs(
                impl=self.impl,
                call_kwargs=call_kwargs,
                is_constructor=self.descriptor.is_constructor,
            )
        )
        if isawaitable(result):
            return await cast(Awaitable[object], result)
        return result


@dataclass(frozen=True, slots=True)
class _MetaGraphImplDelegatingLanguageHandler:
    descriptor: MetaGraphFunctionImplementationDescriptor
    impl: Callable[..., object]

    async def __call__(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        positional: JsonArray,
        keyword: JsonObject,
    ) -> MetaGraphLanguageHandlerExecution:
        if self.descriptor.is_constructor:
            return await self._call_constructor(
                request=request,
                pre_state=pre_state,
                positional=positional,
                keyword=keyword,
            )
        root_model, target = _language_handler_root_and_target_models(
            descriptor=self.descriptor,
            request=request,
            pre_state=pre_state,
        )
        call_kwargs = _bind_impl_call_kwargs(
            impl=self.impl,
            target=target,
            positional=positional,
            keyword=keyword,
            is_constructor=self.descriptor.is_constructor,
        )
        result = self.impl(
            **_coerce_impl_call_kwargs(
                impl=self.impl,
                call_kwargs=call_kwargs,
                is_constructor=self.descriptor.is_constructor,
            )
        )
        if isawaitable(result):
            result = await cast(Awaitable[object], result)

        return _language_handler_execution(
            request=request,
            pre_state=pre_state,
            root_model=root_model,
            result=result,
        )

    async def _call_constructor(
        self,
        *,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        positional: JsonArray,
        keyword: JsonObject,
    ) -> MetaGraphLanguageHandlerExecution:
        target = _owner_orm_class(self.descriptor)
        call_kwargs = _bind_impl_call_kwargs(
            impl=self.impl,
            target=target,
            positional=positional,
            keyword=keyword,
            is_constructor=True,
        )
        result = self.impl(
            **_coerce_impl_call_kwargs(
                impl=self.impl,
                call_kwargs=call_kwargs,
                is_constructor=self.descriptor.is_constructor,
            )
        )
        if isawaitable(result):
            result = await cast(Awaitable[object], result)
        if not isinstance(result, ORMModel):
            raise MetaGraphLanguageHandlerExecutionError(
                "Impl-delegated Meta constructor handler must return ORMModel."
            )
        root_model = result
        if pre_state.root_object_id is not None:
            root_model.id = pre_state.root_object_id
        return _language_handler_execution(
            request=request,
            pre_state=pre_state,
            root_model=root_model,
            result=result,
        )


def _bind_impl_call_kwargs(
    *,
    impl: Callable[..., object],
    target: ORMModel | type[ORMModel],
    positional: JsonArray,
    keyword: JsonObject,
    is_constructor: bool,
) -> dict[str, object]:
    parameters = _impl_call_parameters(impl)
    if not parameters:
        return {str(key): value for key, value in dict(keyword).items()}

    target_parameter_name: str | None = None
    field_parameters = parameters
    if not is_constructor:
        if not isinstance(target, ORMModel):
            raise MetaGraphLanguageHandlerExecutionError(
                "Impl-delegated Meta instance invocation requires ORMModel "
                f"target: target_type={type(target).__name__}"
            )
        target_parameter_name = parameters[0]
        field_parameters = parameters[1:]

    if len(positional) > len(field_parameters):
        raise MetaGraphLanguageHandlerExecutionError(
            "Too many positional arguments for impl-delegated Meta invocation: "
            f"function={impl.__module__}.{impl.__name__} "
            f"positional_count={len(positional)} "
            f"expected_at_most={len(field_parameters)}"
        )

    bound: dict[str, object] = {str(key): value for key, value in dict(keyword).items()}
    if target_parameter_name is not None:
        bound[target_parameter_name] = target
    for index, value in enumerate(positional):
        field_name = field_parameters[index]
        if field_name in bound:
            raise MetaGraphLanguageHandlerExecutionError(
                "Duplicate argument for impl-delegated Meta invocation: "
                f"function={impl.__module__}.{impl.__name__} "
                f"field_name={field_name}"
            )
        bound[field_name] = value
    return bound


def _coerce_impl_call_kwargs(
    *,
    impl: Callable[..., object],
    call_kwargs: dict[str, object],
    is_constructor: bool,
) -> dict[str, object]:
    return coerce_meta_handler_call_kwargs(
        impl,
        call_kwargs,
        trusted_parameter_names=_trusted_impl_target_parameter_names(
            impl=impl,
            is_constructor=is_constructor,
        ),
    )


def _trusted_impl_target_parameter_names(
    *,
    impl: Callable[..., object],
    is_constructor: bool,
) -> frozenset[str]:
    if is_constructor:
        return frozenset()
    parameters = _impl_call_parameters(impl)
    if not parameters:
        return frozenset()
    return frozenset({parameters[0]})


def _impl_call_parameters(impl: Callable[..., object]) -> tuple[str, ...]:
    try:
        impl_signature = signature(impl)
    except (TypeError, ValueError):
        return ()
    return tuple(
        name
        for name, parameter in impl_signature.parameters.items()
        if parameter.kind
        in {
            Parameter.POSITIONAL_ONLY,
            Parameter.POSITIONAL_OR_KEYWORD,
            Parameter.KEYWORD_ONLY,
        }
    )


def _language_handler_root_and_target_models(
    *,
    descriptor: MetaGraphFunctionImplementationDescriptor,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
) -> tuple[ORMModel, ORMModel | type[ORMModel]]:
    if descriptor.is_constructor:
        owner_orm_class = _owner_orm_class(descriptor)
        root_model = _root_model_from_pre_state(request=request, pre_state=pre_state)
        return root_model, owner_orm_class
    return _root_and_target_models_from_pre_state(
        descriptor=descriptor,
        request=request,
        pre_state=pre_state,
    )


def _language_handler_execution(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    root_model: ORMModel,
    result: object,
) -> MetaGraphLanguageHandlerExecution:
    if _impl_delegation_direct_change_evidence_enabled():
        direct_changes = _direct_change_evidence_from_current_collector(
            request=request,
            pre_state=pre_state,
            result=result,
        )
        if direct_changes is not None:
            changes, body_draft, constructed_class_instance_ids = direct_changes
            return MetaGraphLanguageHandlerExecution(
                success=True,
                payload={"value": _json_payload_value(result)},
                changes=changes,
                body_draft=body_draft,
                root_object_id=root_model.id,
                root_class_instance_identity_id=pre_state.root_class_instance_identity_id,
                constructed_class_instance_ids=constructed_class_instance_ids,
            )

    metadata = _impl_delegation_trace_metadata(request)
    if _impl_delegation_simple_scalar_direct_change_evidence_enabled():
        with commit_perf_span(
            phase=(
                "handler_execution.impl_delegation."
                "build_simple_scalar_direct_evidence"
            ),
            category="meta.runtime.handler_execution",
            metadata=metadata,
        ):
            simple_attempt = (
                _simple_scalar_direct_change_evidence_from_current_collector(
                    request=request,
                    pre_state=pre_state,
                )
            )
        if simple_attempt.changes:
            with commit_perf_span(
                phase=(
                    "handler_execution.impl_delegation."
                    "simple_scalar_direct_evidence_success"
                ),
                category="meta.runtime.handler_execution",
                metadata={
                    **metadata,
                    "change_count": len(simple_attempt.changes),
                },
            ):
                pass
            return MetaGraphLanguageHandlerExecution(
                success=True,
                payload={"value": _json_payload_value(result)},
                changes=simple_attempt.changes,
                root_object_id=root_model.id,
                root_class_instance_identity_id=(
                    pre_state.root_class_instance_identity_id
                ),
            )
        with commit_perf_span(
            phase=(
                "handler_execution.impl_delegation."
                "simple_scalar_direct_evidence_fallback"
            ),
            category="meta.runtime.handler_execution",
            metadata={
                **metadata,
                "fallback_reason": simple_attempt.fallback_reason or "unknown",
            },
        ):
            pass

    with commit_perf_span(
        phase="handler_execution.impl_delegation.build_post_oig_fallback",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        post_oig = build_object_instance_graph(
            root_instance=root_model,
            object_config_graph=request.execution_plan.index.ocg,
            object_projection_graph=request.execution_plan.object_projection_graph,
            key=pre_state.before_oig.key or str(pre_state.before_oig.id),
            name=(
                pre_state.before_oig.name
                or request.execution_plan.object_projection_graph.name
            ),
            description=pre_state.before_oig.description or "",
            oig_id=pre_state.before_oig.id,
            enum_option_resolver=default_meta_enum_option_resolver,
        )
    return MetaGraphLanguageHandlerExecution(
        success=True,
        payload={"value": _json_payload_value(result)},
        post_oig=post_oig,
        root_object_id=root_model.id,
        root_class_instance_identity_id=pre_state.root_class_instance_identity_id,
        constructed_class_instance_ids=_constructed_class_instance_ids_from_post_oig(
            pre_state=pre_state,
            post_oig=post_oig,
        ),
    )


def _simple_scalar_direct_change_evidence_from_current_collector(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
) -> _SimpleScalarDirectChangeAttempt:
    if request.execution_plan.implementation.is_constructor:
        return _SimpleScalarDirectChangeAttempt(fallback_reason="constructor")
    collector = current_change_collector()
    if collector is None:
        return _SimpleScalarDirectChangeAttempt(fallback_reason="missing_collector")
    change_set = collector.snapshot()
    return _simple_scalar_direct_change_evidence_from_change_set(
        request=request,
        pre_state=pre_state,
        change_set=change_set,
    )


def _simple_scalar_direct_change_evidence_from_change_set(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    change_set: ORMChangeSet,
) -> _SimpleScalarDirectChangeAttempt:
    if change_set.created_ids:
        return _SimpleScalarDirectChangeAttempt(fallback_reason="has_created_ids")
    if change_set.deleted_ids:
        return _SimpleScalarDirectChangeAttempt(fallback_reason="has_deleted_ids")
    if (
        change_set.list_fields_by_id
        or change_set.list_baseline
        or change_set.list_added
        or change_set.list_removed
    ):
        return _SimpleScalarDirectChangeAttempt(fallback_reason="has_list_changes")
    if not change_set.scalar_fields_by_id:
        return _SimpleScalarDirectChangeAttempt(fallback_reason="no_scalar_changes")
    if pre_state.oig_index is None:
        return _SimpleScalarDirectChangeAttempt(fallback_reason="missing_oig_index")

    candidate_ids = set(change_set.scalar_fields_by_id)
    if not candidate_ids:
        return _SimpleScalarDirectChangeAttempt(fallback_reason="no_candidate_ids")
    if candidate_ids - set(change_set.touched_ids):
        return _SimpleScalarDirectChangeAttempt(
            fallback_reason="scalar_candidate_not_touched"
        )

    old_class_instances: list[ClassInstance] = []
    new_class_instances: list[ClassInstance] = []
    for source_object_id in sorted(candidate_ids, key=str):
        source_model = change_set.objects_by_id.get(source_object_id)
        if not isinstance(source_model, ORMModel):
            return _SimpleScalarDirectChangeAttempt(
                fallback_reason="dirty_object_not_orm_model"
            )
        before_class_instance = (
            pre_state.oig_index.class_instances_by_source_object_id.get(
                source_object_id
            )
        )
        if before_class_instance is None:
            return _SimpleScalarDirectChangeAttempt(
                fallback_reason="missing_pre_state_class_instance"
            )
        class_config_id = before_class_instance.class_config_id
        class_config = (
            request.execution_plan.index.class_configs_by_id.get(class_config_id)
            or before_class_instance.class_config
        )
        if not isinstance(class_config, ClassConfig):
            return _SimpleScalarDirectChangeAttempt(
                fallback_reason="missing_class_config"
            )
        changed_fields = change_set.scalar_fields_by_id.get(source_object_id) or set()
        if not changed_fields:
            return _SimpleScalarDirectChangeAttempt(
                fallback_reason="empty_scalar_field_set"
            )
        attribute_configs_by_name = _attribute_configs_by_name(class_config)
        relationship_attribute_ids = _relationship_attribute_config_ids_for_class(
            class_config=class_config,
            relationships_by_id=request.execution_plan.index.relationships_by_id,
        )
        new_class_instance = before_class_instance.model_copy(deep=True)
        for field_name in sorted(changed_fields):
            attribute_config = attribute_configs_by_name.get(field_name)
            if attribute_config is None:
                return _SimpleScalarDirectChangeAttempt(
                    fallback_reason="scalar_field_not_attribute"
                )
            if attribute_config.is_virtual:
                return _SimpleScalarDirectChangeAttempt(
                    fallback_reason="virtual_attribute"
                )
            if attribute_config.id in relationship_attribute_ids:
                return _SimpleScalarDirectChangeAttempt(
                    fallback_reason="relationship_attribute"
                )
            found, raw_value = source_model.try_attribute_value(attribute_config)
            if not found:
                return _SimpleScalarDirectChangeAttempt(
                    fallback_reason="attribute_value_not_found"
                )
            attribute = build_attribute(
                owner_key=source_object_id,
                attribute_config=attribute_config,
                value=raw_value,
                class_configs_by_id=dict(
                    request.execution_plan.index.class_configs_by_id
                ),
                enum_option_resolver=default_meta_enum_option_resolver,
            )
            _replace_class_instance_attribute(
                class_instance=new_class_instance,
                attribute=attribute,
            )
        old_class_instances.append(before_class_instance)
        new_class_instances.append(new_class_instance)

    try:
        changes = tuple(
            build_object_instance_graph_class_instance_update_changes(
                graph=pre_state.before_oig,
                old_class_instances=old_class_instances,
                new_class_instances=new_class_instances,
                object_instance_graph_identity_id=(
                    request.staged_call.lane_scope.object_instance_graph_identity_id
                ),
                created_at=change_set.collected_at,
            )
        )
    except (TypeError, ValueError) as exc:
        return _SimpleScalarDirectChangeAttempt(
            fallback_reason=f"change_build_{type(exc).__name__}"
        )
    if not changes:
        return _SimpleScalarDirectChangeAttempt(fallback_reason="no_changes")
    return _SimpleScalarDirectChangeAttempt(changes=changes)


def _attribute_configs_by_name(class_config: ClassConfig) -> dict[str, AttributeConfig]:
    out: dict[str, AttributeConfig] = {}
    for link in class_config.class_config_attribute_configs:
        attribute_config = getattr(link, "attribute_config", None)
        attribute_name = getattr(attribute_config, "name", None)
        if isinstance(attribute_config, AttributeConfig) and isinstance(
            attribute_name,
            str,
        ):
            out.setdefault(attribute_name, attribute_config)
    return out


def _relationship_attribute_config_ids_for_class(
    *,
    class_config: ClassConfig,
    relationships_by_id: Mapping[UUID, ClassConfigRelationship],
) -> frozenset[UUID]:
    class_attribute_ids = {
        link.attribute_config.id
        for link in class_config.class_config_attribute_configs
        if getattr(link, "attribute_config", None) is not None
        and link.attribute_config.id is not None
    }
    relationship_attribute_ids: set[UUID] = set()
    relationships = list(getattr(class_config, "class_config_relationships", ()) or [])
    if hasattr(relationships_by_id, "values"):
        relationships.extend(list(relationships_by_id.values()))
    for relationship in relationships:
        for rel_attr in (
            getattr(relationship, "class_config_relationship_attributes", ()) or ()
        ):
            attribute_id = getattr(rel_attr, "attribute_config_id", None)
            if isinstance(attribute_id, UUID) and attribute_id in class_attribute_ids:
                relationship_attribute_ids.add(attribute_id)
    return frozenset(relationship_attribute_ids)


def _replace_class_instance_attribute(
    *,
    class_instance: ClassInstance,
    attribute: Attribute,
) -> None:
    attribute_id = getattr(attribute, "id", None)
    if not isinstance(attribute_id, UUID):
        raise MetaGraphLanguageHandlerExecutionError(
            "Simple scalar direct evidence built Attribute without id."
        )
    attribute_config_id = getattr(attribute, "attribute_config_id", None)
    for edge in class_instance.class_instance_attributes:
        edge_attribute_config_id = getattr(
            getattr(edge, "attribute", None),
            "attribute_config_id",
            None,
        )
        if edge.attribute_id != attribute_id and (
            not isinstance(attribute_config_id, UUID)
            or edge_attribute_config_id != attribute_config_id
        ):
            continue
        cast(Any, edge).attribute = attribute
        edge.attribute_id = attribute_id
        return
    from aware_meta.class_.instance.handlers import link_attribute  # noqa: WPS433

    link_attribute(class_instance, attribute)


def _direct_change_evidence_from_current_collector(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    result: object,
) -> (
    tuple[
        tuple[ObjectInstanceGraphChange, ...],
        OigCommitBodyDraft | None,
        tuple[UUID, ...],
    ]
    | None
):
    collector = current_change_collector()
    if collector is None:
        return None
    metadata = _impl_delegation_trace_metadata(request)
    with commit_perf_span(
        phase="handler_execution.impl_delegation.snapshot_orm_changes",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        change_set = collector.snapshot()
    with commit_perf_span(
        phase="handler_execution.impl_delegation.build_direct_change_evidence",
        category="meta.runtime.handler_execution",
        metadata=metadata,
    ):
        try:
            evidence = build_object_instance_graph_evidence_from_orm_change_set(
                before_oig=pre_state.before_oig,
                object_instance_graph_identity_id=(
                    request.staged_call.lane_scope.object_instance_graph_identity_id
                ),
                ocg=request.execution_plan.index.ocg,
                opg=request.execution_plan.object_projection_graph,
                change_set=change_set,
                class_configs_by_id=(request.execution_plan.index.class_configs_by_id),
                relationships_by_id=(request.execution_plan.index.relationships_by_id),
                enum_option_resolver=default_meta_enum_option_resolver,
                index_cache=(request.execution_plan.orm_change_translation_index_cache),
            )
        except OrmChangeTranslationError as exc:
            with commit_perf_span(
                phase=(
                    "handler_execution.impl_delegation."
                    "direct_change_evidence_fallback"
                ),
                category="meta.runtime.handler_execution",
                metadata={
                    **metadata,
                    "fallback_reason": type(exc).__name__,
                },
            ):
                return None
    changes = evidence.changes
    body_draft = evidence.body_draft
    if (
        not changes
        and body_draft is None
        and (
            _change_set_has_mutations(change_set)
            or _result_requires_post_oig_fallback(
                pre_state=pre_state,
                result=result,
            )
        )
    ):
        with commit_perf_span(
            phase="handler_execution.impl_delegation.direct_change_evidence_fallback",
            category="meta.runtime.handler_execution",
            metadata={
                **metadata,
                "fallback_reason": "dirty_empty_translation",
            },
        ):
            return None
    evidence_roots = body_draft.roots if body_draft is not None else changes
    constructed_class_instance_ids = tuple(
        class_change.class_instance_id
        for root_change in evidence_roots
        for class_change in root_change.class_instance_changes
        if getattr(class_change.change.type, "value", class_change.change.type)
        == "create"
    )
    return changes, body_draft, constructed_class_instance_ids


def _impl_delegation_direct_change_evidence_enabled() -> bool:
    raw = os.getenv(_IMPL_DELEGATION_DIRECT_CHANGE_EVIDENCE_ENV, "1")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _change_set_has_mutations(change_set: ORMChangeSet) -> bool:
    return bool(
        change_set.created_ids
        or change_set.touched_ids
        or change_set.deleted_ids
        or change_set.scalar_fields_by_id
        or change_set.list_fields_by_id
        or change_set.list_added
        or change_set.list_removed
    )


def _impl_delegation_simple_scalar_direct_change_evidence_enabled() -> bool:
    raw = os.getenv(_IMPL_DELEGATION_SIMPLE_SCALAR_DIRECT_CHANGE_EVIDENCE_ENV, "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _result_requires_post_oig_fallback(
    *,
    pre_state: MetaGraphPreState,
    result: object,
) -> bool:
    if not isinstance(result, ORMModel):
        return False
    result_id = getattr(result, "id", None)
    if not isinstance(result_id, UUID):
        return False
    if pre_state.oig_index is not None:
        return result_id not in pre_state.oig_index.class_instances_by_source_object_id
    return all(
        getattr(class_instance, "source_object_id", None) != result_id
        for class_instance in pre_state.before_oig.class_instances
    )


def _impl_delegation_trace_metadata(
    request: MetaGraphHandlerExecutionRequest,
) -> dict[str, object]:
    implementation = request.execution_plan.implementation
    owner_class_config = implementation.owner_class_config
    request_payload = request.request
    return {
        "call_target": getattr(request_payload.call_target, "value", None),
        "domain_projection_hash": getattr(
            request_payload, "domain_projection_hash", None
        ),
        "function_call_id": str(request.staged_call.function_call.id),
        "function_id": str(implementation.function_config.id),
        "function_name": implementation.function_config.name,
        "owner_class": owner_class_config.name if owner_class_config else None,
    }


def _root_and_target_models_from_pre_state(
    *,
    descriptor: MetaGraphFunctionImplementationDescriptor,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
) -> tuple[ORMModel, ORMModel]:
    target_object_id = (
        pre_state.target_object_id
        or request.execution_plan.target_object_id
        or request.request.target_object_id
        or pre_state.root_object_id
    )
    if target_object_id is None:
        raise MetaGraphLanguageHandlerExecutionError(
            "Impl-delegated Meta instance handler requires a target object id."
        )
    target_orm_class = _owner_orm_class(descriptor)
    root_model = _root_model_from_pre_state(request=request, pre_state=pre_state)
    active_context = _exact_active_handler_context(request)
    target_class_instance = _class_instance_from_pre_state(
        pre_state=pre_state,
        target_object_id=target_object_id,
    )
    if active_context is not None:
        target = _require_prebound_model(
            context=active_context,
            orm_class=target_orm_class,
            source_object_id=(
                target_class_instance.source_object_id
                if target_class_instance is not None
                else target_object_id
            ),
            graph_invocation_target_id=(
                target_class_instance.id
                if target_class_instance is not None
                else target_object_id
            ),
            role="target",
        )
    else:
        target = _find_orm_model_by_id(
            root_model,
            (
                target_class_instance.source_object_id
                if target_class_instance is not None
                else target_object_id
            ),
        )
    if target is None or not _model_matches_owner_class(
        model=target,
        owner_class=target_orm_class,
        owner_class_config=descriptor.owner_class_config,
    ):
        raise MetaGraphLanguageHandlerExecutionError(
            "Impl-delegated Meta instance handler cannot resolve target model "
            "in the rooted projection model: "
            f"class_name={descriptor.owner_class_config.name if descriptor.owner_class_config else None} "
            f"target_object_id={target_object_id}"
        )
    return root_model, target


def _root_model_from_pre_state(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
) -> ORMModel:
    root_orm_class = _root_orm_class_from_projection(request)
    root_class_instance = _root_class_instance_from_pre_state(pre_state)
    root_object_id = pre_state.root_object_id or (
        root_class_instance.source_object_id
        if root_class_instance is not None
        else None
    )
    if root_object_id is None:
        raise MetaGraphLanguageHandlerExecutionError(
            "Impl-delegated Meta handler cannot resolve root source object id."
        )
    active_context = _exact_active_handler_context(request)
    if active_context is not None:
        return _require_prebound_model(
            context=active_context,
            orm_class=root_orm_class,
            source_object_id=root_object_id,
            graph_invocation_target_id=(
                root_class_instance.id
                if root_class_instance is not None
                else root_object_id
            ),
            role="root",
        )
    root = reify_oig_root_model(
        index=request.execution_plan.index,
        opg=request.execution_plan.object_projection_graph,
        oig=pre_state.before_oig,
        model_type=root_orm_class,
        root_id=root_object_id,
        branch_id=request.execution_plan.staged_call.lane_scope.domain_branch_id,
    )
    if root is None:
        raise MetaGraphLanguageHandlerExecutionError(
            "Impl-delegated Meta handler cannot reify rooted projection model: "
            f"root_object_id={root_object_id}"
        )
    return root


def _exact_active_handler_context(
    request: MetaGraphHandlerExecutionRequest,
) -> MetaGraphHandlerExecutionContext | None:
    context = current_meta_graph_handler_execution_context_or_none()
    if context is None or context.request is not request:
        return None
    if context.index is not request.execution_plan.index:
        raise MetaGraphLanguageHandlerExecutionError(
            "Impl-delegated Meta handler active context runtime index mismatch."
        )
    if context.function_call is not request.staged_call.function_call:
        raise MetaGraphLanguageHandlerExecutionError(
            "Impl-delegated Meta handler active context FunctionCall mismatch."
        )
    return context


def _require_prebound_model(
    *,
    context: MetaGraphHandlerExecutionContext,
    orm_class: type[ORMModel],
    source_object_id: object,
    graph_invocation_target_id: object,
    role: str,
) -> ORMModel:
    if not isinstance(source_object_id, UUID):
        raise MetaGraphLanguageHandlerExecutionError(
            f"Impl-delegated Meta handler {role} source object id is not UUID."
        )
    model = context.session.imap_get(orm_class, source_object_id)
    if model is None:
        raise MetaGraphLanguageHandlerExecutionError(
            f"Impl-delegated Meta handler missing exact prebound {role} model: "
            f"class={orm_class.__module__}.{orm_class.__name__} "
            f"source_object_id={source_object_id}"
        )
    if not isinstance(graph_invocation_target_id, UUID):
        raise MetaGraphLanguageHandlerExecutionError(
            f"Impl-delegated Meta handler {role} graph invocation target is not UUID."
        )
    if model.graph_invocation_target_id != graph_invocation_target_id:
        raise MetaGraphLanguageHandlerExecutionError(
            f"Impl-delegated Meta handler prebound {role} graph target mismatch: "
            f"expected={graph_invocation_target_id} "
            f"actual={model.graph_invocation_target_id}"
        )
    return model


def _root_class_instance_from_pre_state(
    pre_state: MetaGraphPreState,
) -> ClassInstance | None:
    root_class_instance = pre_state.before_oig.root_class_instance
    if root_class_instance is not None:
        return root_class_instance
    root_class_instance_id = pre_state.before_oig.root_class_instance_id
    if root_class_instance_id is None:
        return None
    return next(
        (
            instance
            for instance in pre_state.before_oig.class_instances
            if instance.id == root_class_instance_id
        ),
        None,
    )


def _class_instance_from_pre_state(
    *,
    pre_state: MetaGraphPreState,
    target_object_id: object,
) -> ClassInstance | None:
    if isinstance(target_object_id, UUID) and pre_state.oig_index is not None:
        target = pre_state.oig_index.class_instances_by_id.get(target_object_id)
        if target is None:
            target = pre_state.oig_index.class_instances_by_source_object_id.get(
                target_object_id
            )
        if target is not None:
            return target
    return next(
        (
            instance
            for instance in pre_state.before_oig.class_instances
            if instance.id == target_object_id
            or instance.source_object_id == target_object_id
        ),
        None,
    )


def _root_orm_class_from_projection(
    request: MetaGraphHandlerExecutionRequest,
) -> type[ORMModel]:
    root_nodes = tuple(
        node
        for node in request.execution_plan.object_projection_graph.object_projection_graph_nodes
        if node.is_root
    )
    if len(root_nodes) != 1:
        raise MetaGraphLanguageHandlerExecutionError(
            "Impl-delegated Meta handler requires exactly one OPG root node: "
            f"have={len(root_nodes)} "
            "object_projection_graph_id="
            f"{request.execution_plan.object_projection_graph.id}"
        )
    orm_class = ORMModelRegistry.get_class_by_class_config_id(
        root_nodes[0].class_config_id,
    )
    if orm_class is None:
        raise MetaGraphLanguageHandlerExecutionError(
            "Impl-delegated Meta handler cannot resolve root ORM class: "
            f"class_config_id={root_nodes[0].class_config_id}"
        )
    return cast(type[ORMModel], orm_class)


def _owner_orm_class(
    descriptor: MetaGraphFunctionImplementationDescriptor,
) -> type[ORMModel]:
    owner_class_config = descriptor.owner_class_config
    if not isinstance(owner_class_config, ClassConfig):
        raise MetaGraphLanguageHandlerExecutionError(
            "Impl-delegated Meta handler requires a resolved owner ClassConfig."
        )
    orm_class = ORMModelRegistry.get_class_by_class_config_id(owner_class_config.id)
    if orm_class is None:
        raise MetaGraphLanguageHandlerExecutionError(
            "Impl-delegated Meta handler cannot resolve owner ORM class: "
            f"class_config_id={owner_class_config.id} "
            f"class_name={owner_class_config.name}"
        )
    return cast(type[ORMModel], orm_class)


def _model_matches_owner_class(
    *,
    model: ORMModel | None,
    owner_class: type[ORMModel],
    owner_class_config: ClassConfig | None,
) -> bool:
    if model is None:
        return False
    if isinstance(model, owner_class):
        return True
    if not isinstance(owner_class_config, ClassConfig):
        return False
    model_class_config = type(model).get_class_config()
    return getattr(model_class_config, "id", None) == owner_class_config.id


def _find_orm_model_by_id(root_model: ORMModel, object_id: object) -> ORMModel | None:
    stack: list[object] = [root_model]
    seen: set[int] = set()
    while stack:
        current = stack.pop()
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        if isinstance(current, ORMModel):
            if current.id == object_id:
                return current
            stack.extend(current.__dict__.values())
            continue
        if isinstance(current, (list, tuple, set)):
            stack.extend(current)
            continue
        if isinstance(current, dict):
            stack.extend(current.values())
    return None


def _constructed_class_instance_ids_from_post_oig(
    *,
    pre_state: MetaGraphPreState,
    post_oig: ObjectInstanceGraph,
) -> tuple[UUID, ...]:
    before_ids = {instance.id for instance in pre_state.before_oig.class_instances}
    return tuple(
        instance.id
        for instance in post_oig.class_instances
        if getattr(instance, "id", None) not in before_ids
    )


def _json_payload_value(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_json_payload_value(item) for item in value]
    if isinstance(value, tuple):
        return [_json_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_payload_value(item) for key, item in value.items()}
    return value


def _candidate_impl_module_names(
    descriptor: MetaGraphFunctionImplementationDescriptor,
) -> tuple[str, ...]:
    owner_tokens = tuple(
        token
        for token in (
            descriptor.owner_class_config.class_fqn
            if descriptor.owner_class_config is not None
            else descriptor.function_config.owner_key
        ).split(".")
        if token
    )
    owner_class_name = (
        descriptor.owner_class_config.name
        if descriptor.owner_class_config is not None
        else owner_tokens[-1] if owner_tokens else None
    )
    if owner_class_name is None:
        return ()

    owner_package = _owner_impl_package(owner_tokens)
    candidates: list[str] = []
    if owner_package is not None:
        candidates.append(
            "aware_meta.handlers.impl."
            f"{owner_package}.{_camel_to_snake(owner_class_name)}",
        )
    for package_candidate in _package_owned_impl_modules(
        owner_tokens=owner_tokens,
        owner_class_name=owner_class_name,
    ):
        if package_candidate not in candidates:
            candidates.append(package_candidate)
    return tuple(candidates)


def _owner_impl_package(owner_tokens: tuple[str, ...]) -> str | None:
    if not owner_tokens or owner_tokens[0] != "aware_meta":
        return None
    if len(owner_tokens) >= 3 and owner_tokens[1] == "default":
        return _python_identifier_segment(owner_tokens[2])
    if len(owner_tokens) >= 3 and owner_tokens[1] == "graph":
        return _python_identifier_segment(owner_tokens[2])
    return None


def _package_owned_impl_modules(
    *,
    owner_tokens: tuple[str, ...],
    owner_class_name: str,
) -> tuple[str, ...]:
    if len(owner_tokens) < 3:
        return ()
    package_root = owner_tokens[0]
    if not package_root.startswith("aware_"):
        return ()
    path_tokens = owner_tokens[1:-1]
    if path_tokens and path_tokens[0] == "default":
        path_tokens = path_tokens[1:]
    if not path_tokens:
        return ()
    candidate_paths: list[str] = []
    package_namespace = package_root.removeprefix("aware_")
    if path_tokens[0] == package_namespace and len(path_tokens) > 1:
        candidate_paths.append(_impl_module_path(path_tokens[1:], owner_class_name))
    candidate_paths.append(_impl_module_path(path_tokens, owner_class_name))
    return tuple(f"{package_root}.handlers.impl.{path}" for path in candidate_paths)


def _impl_module_path(path_tokens: tuple[str, ...], owner_class_name: str) -> str:
    return ".".join(
        (
            *(_python_identifier_segment(token) for token in path_tokens),
            _camel_to_snake(owner_class_name),
        ),
    )


def _python_identifier_segment(segment: str) -> str:
    if segment == "class":
        return "class_"
    return segment


def _camel_to_snake(value: str) -> str:
    first_pass = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", value)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", first_pass).lower()


__all__ = [
    "MetaGraphImplDelegatingLanguageHandlerResolver",
    "MetaGraphImplDelegatingInvocationHandlerResolver",
    "meta_graph_impl_delegating_language_handler_resolver",
    "meta_graph_impl_delegating_invocation_handler_resolver",
    "resolve_meta_handler_impl",
]
