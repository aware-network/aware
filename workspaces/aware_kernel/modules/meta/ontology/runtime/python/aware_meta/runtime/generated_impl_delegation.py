from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from inspect import Parameter, isawaitable, signature
import re
from typing import cast
from uuid import UUID

from aware_code.types import JsonArray, JsonObject
from aware_meta.graph.instance.builder import build_object_instance_graph
from aware_meta.runtime.handler_executor.argument_coercion import (
    coerce_meta_handler_call_kwargs,
)
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphFunctionImplementationDescriptor,
    MetaGraphHandlerExecutionRequest,
    MetaGraphPreState,
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
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry
from pydantic import BaseModel


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
        result = self.impl(**coerce_meta_handler_call_kwargs(self.impl, call_kwargs))
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
        result = self.impl(**coerce_meta_handler_call_kwargs(self.impl, call_kwargs))
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
        result = self.impl(**coerce_meta_handler_call_kwargs(self.impl, call_kwargs))
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
    root_model = _root_model_from_pre_state(request=request, pre_state=pre_state)
    target = _find_orm_model_by_id(
        root_model,
        _target_source_object_id_from_pre_state(
            pre_state=pre_state,
            target_object_id=target_object_id,
        ),
    )
    target_orm_class = _owner_orm_class(descriptor)
    if not isinstance(target, target_orm_class):
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
    root_object_id = pre_state.root_object_id
    if root_object_id is None:
        root_class_instance = pre_state.before_oig.root_class_instance
        if (
            root_class_instance is None
            and pre_state.before_oig.root_class_instance_id is not None
        ):
            root_class_instance = next(
                (
                    instance
                    for instance in pre_state.before_oig.class_instances
                    if instance.id == pre_state.before_oig.root_class_instance_id
                ),
                None,
            )
        if root_class_instance is None:
            raise MetaGraphLanguageHandlerExecutionError(
                "Impl-delegated Meta handler cannot resolve root source object id."
            )
        root_object_id = root_class_instance.source_object_id
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


def _target_source_object_id_from_pre_state(
    *,
    pre_state: MetaGraphPreState,
    target_object_id: object,
) -> object:
    if pre_state.oig_index is None:
        return target_object_id
    if not isinstance(target_object_id, UUID):
        return target_object_id
    target_class_instance = pre_state.oig_index.class_instances_by_id.get(
        target_object_id,
    )
    if target_class_instance is None:
        target_class_instance = (
            pre_state.oig_index.class_instances_by_source_object_id.get(
                target_object_id,
            )
        )
    if target_class_instance is None:
        return target_object_id
    return target_class_instance.source_object_id


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
