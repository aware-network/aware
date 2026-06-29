from __future__ import annotations

from collections.abc import Awaitable, Mapping
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from inspect import isawaitable
from typing import Protocol, TypeVar, cast
from uuid import UUID

from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphBoundArguments,
    MetaGraphFunctionImplementationDescriptor,
    MetaGraphHandlerDispatchResult,
    MetaGraphHandlerExecutionRequest,
    MetaGraphImplementationKind,
    MetaGraphPreState,
)
from aware_meta.runtime.handler_executor.execution_context import (
    build_meta_graph_handler_execution_context,
    scoped_meta_graph_handler_execution_context,
)
from aware_meta.runtime.handler_executor.session import (
    MetaGraphExecutionSessionDeltaBuilder,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    InvocationProvider,
    reset_invocation_provider,
    set_invocation_provider,
)
from aware_orm.session.change_collector import scoped_change_collection
from aware_orm.session.current_session_ctx import set_session


_TGeneratedHandlerValue = TypeVar("_TGeneratedHandlerValue", bound=object)


class MetaGraphLanguageHandlerExecutionError(RuntimeError):
    """Raised when language-handler execution evidence is invalid."""


class MetaGraphGeneratedLanguageHandlerResolutionError(
    MetaGraphLanguageHandlerExecutionError
):
    """Raised when a generated language-handler callable cannot be resolved."""


@dataclass(frozen=True, slots=True)
class MetaGraphLanguageHandlerExecution:
    success: bool
    payload: JsonValue | None = None
    error_message: str | None = None
    execution_time_ms: int = 0
    changes: tuple[ObjectInstanceGraphChange, ...] = ()
    post_oig: ObjectInstanceGraph | None = None
    expected_graph_hash_post: str | None = None
    root_object_id: UUID | None = None
    root_class_instance_identity_id: UUID | None = None
    constructed_class_instance_ids: tuple[UUID, ...] = ()


class MetaGraphLanguageHandlerImplementation(Protocol):
    async def execute_language_handler(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphLanguageHandlerExecution: ...


class MetaGraphGeneratedLanguageHandlerCallable(Protocol):
    def __call__(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        positional: JsonArray,
        keyword: JsonObject,
    ) -> (
        MetaGraphLanguageHandlerExecution | Awaitable[MetaGraphLanguageHandlerExecution]
    ): ...


class MetaGraphGeneratedInvocationHandlerCallable(Protocol):
    def __call__(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        target: ORMModel | type[ORMModel],
        positional: JsonArray,
        keyword: JsonObject,
    ) -> object | Awaitable[object]: ...


@dataclass(frozen=True, slots=True)
class MetaGraphGeneratedLanguageHandlerKey:
    owner_key: str
    function_name: str
    is_constructor: bool
    function_id: UUID | None = None
    owner_class_fqn: str | None = None
    owner_class_name: str | None = None

    @classmethod
    def from_descriptor(
        cls,
        descriptor: MetaGraphFunctionImplementationDescriptor,
        *,
        include_function_id: bool = True,
    ) -> MetaGraphGeneratedLanguageHandlerKey:
        function_config = descriptor.function_config
        owner_class_config = descriptor.owner_class_config
        owner_class_fqn = None
        owner_class_name = None
        if owner_class_config is not None:
            owner_class_fqn = owner_class_config.class_fqn
            owner_class_name = owner_class_config.name
        return cls(
            owner_key=function_config.owner_key,
            function_name=function_config.name,
            is_constructor=descriptor.is_constructor,
            function_id=function_config.id if include_function_id else None,
            owner_class_fqn=owner_class_fqn,
            owner_class_name=owner_class_name,
        )

    def describe(self) -> str:
        function_id = self.function_id or "<symbolic>"
        owner_class_fqn = self.owner_class_fqn or "<unbound>"
        owner_class_name = self.owner_class_name or "<unbound>"
        return (
            f"function_id={function_id} "
            f"owner_key={self.owner_key} "
            f"function_name={self.function_name} "
            f"owner_class_fqn={owner_class_fqn} "
            f"owner_class_name={owner_class_name} "
            f"is_constructor={self.is_constructor}"
        )

    def without_owner_class(self) -> MetaGraphGeneratedLanguageHandlerKey:
        return MetaGraphGeneratedLanguageHandlerKey(
            owner_key=self.owner_key,
            function_name=self.function_name,
            is_constructor=self.is_constructor,
            function_id=self.function_id,
        )


class MetaGraphGeneratedLanguageHandlerResolver(Protocol):
    def resolve_generated_language_handler(
        self,
        descriptor: MetaGraphFunctionImplementationDescriptor,
    ) -> MetaGraphGeneratedLanguageHandlerCallable: ...


class MetaGraphGeneratedInvocationHandlerResolver(Protocol):
    def resolve_generated_invocation_handler(
        self,
        descriptor: MetaGraphFunctionImplementationDescriptor,
    ) -> MetaGraphGeneratedInvocationHandlerCallable: ...


@dataclass(frozen=True, slots=True)
class MetaGraphGeneratedLanguageHandlerRegistry:
    """Resolve generated Meta language handlers from descriptor keys."""

    handlers_by_key: Mapping[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphGeneratedLanguageHandlerCallable,
    ]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "handlers_by_key",
            _expand_generated_handler_key_map(
                self.handlers_by_key,
                value_label="language handler",
            ),
        )

    def resolve_generated_language_handler(
        self,
        descriptor: MetaGraphFunctionImplementationDescriptor,
    ) -> MetaGraphGeneratedLanguageHandlerCallable:
        if descriptor.kind is not MetaGraphImplementationKind.language_handler:
            raise MetaGraphGeneratedLanguageHandlerResolutionError(
                "Generated Meta language handler resolution requires a "
                "language-handler descriptor. "
                f"implementation_kind={descriptor.kind.value}"
            )
        key = MetaGraphGeneratedLanguageHandlerKey.from_descriptor(
            descriptor,
            include_function_id=True,
        )
        handler = self.handlers_by_key.get(key)
        if handler is None:
            symbolic_key = MetaGraphGeneratedLanguageHandlerKey.from_descriptor(
                descriptor,
                include_function_id=False,
            )
            handler = self.handlers_by_key.get(symbolic_key)
        if handler is None:
            semantic_key = key.without_owner_class()
            handler = self.handlers_by_key.get(semantic_key)
        if handler is None:
            semantic_symbolic_key = (
                MetaGraphGeneratedLanguageHandlerKey.from_descriptor(
                    descriptor,
                    include_function_id=False,
                ).without_owner_class()
            )
            handler = self.handlers_by_key.get(semantic_symbolic_key)
        if handler is None:
            raise MetaGraphGeneratedLanguageHandlerResolutionError(
                "No generated Meta language handler registered. " f"{key.describe()}"
            )
        return handler


@dataclass(frozen=True, slots=True)
class MetaGraphGeneratedInvocationHandlerRegistry:
    """Resolve generated Meta invocation handlers from descriptor keys."""

    handlers_by_key: Mapping[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphGeneratedInvocationHandlerCallable,
    ]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "handlers_by_key",
            _expand_generated_handler_key_map(
                self.handlers_by_key,
                value_label="invocation handler",
            ),
        )

    def resolve_generated_invocation_handler(
        self,
        descriptor: MetaGraphFunctionImplementationDescriptor,
    ) -> MetaGraphGeneratedInvocationHandlerCallable:
        if descriptor.kind is not MetaGraphImplementationKind.language_handler:
            raise MetaGraphGeneratedLanguageHandlerResolutionError(
                "Generated Meta invocation handler resolution requires a "
                "language-handler descriptor. "
                f"implementation_kind={descriptor.kind.value}"
            )
        key = MetaGraphGeneratedLanguageHandlerKey.from_descriptor(
            descriptor,
            include_function_id=True,
        )
        handler = self.handlers_by_key.get(key)
        if handler is None:
            symbolic_key = MetaGraphGeneratedLanguageHandlerKey.from_descriptor(
                descriptor,
                include_function_id=False,
            )
            handler = self.handlers_by_key.get(symbolic_key)
        if handler is None:
            semantic_key = key.without_owner_class()
            handler = self.handlers_by_key.get(semantic_key)
        if handler is None:
            semantic_symbolic_key = (
                MetaGraphGeneratedLanguageHandlerKey.from_descriptor(
                    descriptor,
                    include_function_id=False,
                ).without_owner_class()
            )
            handler = self.handlers_by_key.get(semantic_symbolic_key)
        if handler is None:
            raise MetaGraphGeneratedLanguageHandlerResolutionError(
                "No generated Meta invocation handler registered. " f"{key.describe()}"
            )
        return handler


@dataclass(frozen=True, slots=True)
class MetaGraphGeneratedLanguageHandlerImplementation:
    """Call a generated Meta language handler with bound JSON arguments."""

    handler: MetaGraphGeneratedLanguageHandlerCallable
    invocation_handler_resolver: MetaGraphGeneratedInvocationHandlerResolver | None = (
        None
    )

    async def execute_language_handler(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphLanguageHandlerExecution:
        context = build_meta_graph_handler_execution_context(request=request)
        invocation_provider = (
            _MetaGraphGeneratedInvocationProvider(
                request=request,
                pre_state=pre_state,
                handler_resolver=self.invocation_handler_resolver,
            )
            if self.invocation_handler_resolver is not None
            else None
        )
        invocation_scope = (
            _scoped_invocation_provider(invocation_provider)
            if invocation_provider is not None
            else nullcontext()
        )
        with (
            invocation_scope,
            scoped_meta_graph_handler_execution_context(context),
            set_session(
                context.session,
                branch_id=request.staged_call.lane_scope.domain_branch_id,
            ),
            scoped_change_collection(),
        ):
            from aware_meta.runtime.oig_model_reifier import (  # noqa: WPS433
                bind_oig_models_to_current_handler_session,
            )

            if _should_bind_pre_state_models_to_handler_session(
                request=request,
                pre_state=pre_state,
            ):
                bind_oig_models_to_current_handler_session(
                    index=request.execution_plan.index,
                    opg=request.execution_plan.object_projection_graph,
                    oig=pre_state.before_oig,
                    branch_id=request.staged_call.lane_scope.domain_branch_id,
                )
            result = self.handler(
                request,
                pre_state,
                JsonArray(list(bound_arguments.positional)),
                JsonObject(dict(bound_arguments.keyword)),
            )
            if isawaitable(result):
                result = await cast(
                    Awaitable[MetaGraphLanguageHandlerExecution],
                    result,
                )
        if not isinstance(result, MetaGraphLanguageHandlerExecution):
            raise MetaGraphLanguageHandlerExecutionError(
                "Generated Meta language handler must return "
                "MetaGraphLanguageHandlerExecution evidence."
            )
        return result


def _should_bind_pre_state_models_to_handler_session(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
) -> bool:
    if (
        request.request.call_target.value == "opg_constructor"
        and pre_state.head_commit_id is None
    ):
        return False
    return True


@dataclass(frozen=True, slots=True)
class _MetaGraphGeneratedInvocationProvider(InvocationProvider):
    request: MetaGraphHandlerExecutionRequest
    pre_state: MetaGraphPreState
    handler_resolver: MetaGraphGeneratedInvocationHandlerResolver

    async def invoke_instance(
        self,
        *,
        orm_model: ORMModel,
        function_name: str,
        payload: Mapping[str, object],
    ) -> object:
        descriptor = _resolve_invocation_descriptor(
            request=self.request,
            orm_class=type(orm_model),
            function_name=function_name,
            is_constructor=False,
        )
        handler = self.handler_resolver.resolve_generated_invocation_handler(
            descriptor,
        )
        result = handler(
            self.request,
            self.pre_state,
            orm_model,
            JsonArray(),
            JsonObject({str(key): value for key, value in dict(payload).items()}),
        )
        if isawaitable(result):
            result = await cast(Awaitable[object], result)
        return result

    async def invoke_constructor(
        self,
        *,
        orm_class: type[ORMModel],
        function_name: str,
        payload: Mapping[str, object],
    ) -> object:
        descriptor = _resolve_invocation_descriptor(
            request=self.request,
            orm_class=orm_class,
            function_name=function_name,
            is_constructor=True,
        )
        handler = self.handler_resolver.resolve_generated_invocation_handler(
            descriptor,
        )
        result = handler(
            self.request,
            self.pre_state,
            orm_class,
            JsonArray(),
            JsonObject({str(key): value for key, value in dict(payload).items()}),
        )
        if isawaitable(result):
            result = await cast(Awaitable[object], result)
        return result


@contextmanager
def _scoped_invocation_provider(provider: InvocationProvider):
    token = set_invocation_provider(provider)
    try:
        yield
    finally:
        reset_invocation_provider(token)


def _resolve_invocation_descriptor(
    *,
    request: MetaGraphHandlerExecutionRequest,
    orm_class: type[ORMModel],
    function_name: str,
    is_constructor: bool,
) -> MetaGraphFunctionImplementationDescriptor:
    owner_class_config = _owner_class_config_for_orm_class(
        request=request,
        orm_class=orm_class,
    )
    class_function_edge = _class_function_edge(
        owner_class_config=owner_class_config,
        function_name=function_name,
        is_constructor=is_constructor,
    )
    function_config = class_function_edge.function_config
    return MetaGraphFunctionImplementationDescriptor(
        kind=MetaGraphImplementationKind.language_handler,
        function_config=function_config,
        owner_class_config=owner_class_config,
        class_function_edge=class_function_edge,
        is_constructor=is_constructor,
    )


def _owner_class_config_for_orm_class(
    *,
    request: MetaGraphHandlerExecutionRequest,
    orm_class: type[ORMModel],
):
    bound_class_config = orm_class.get_class_config()
    class_config_id = bound_class_config.id if bound_class_config is not None else None
    if class_config_id is None:
        raise MetaGraphLanguageHandlerExecutionError(
            "Meta generated handler invocation requires a bound ClassConfig id: "
            f"class={orm_class.__module__}.{orm_class.__name__}"
        )
    owner_class_config = request.execution_plan.index.class_configs_by_id.get(
        class_config_id,
    )
    if owner_class_config is None:
        raise MetaGraphLanguageHandlerExecutionError(
            "Meta generated handler invocation cannot resolve ClassConfig in "
            "the execution index: "
            f"class={orm_class.__module__}.{orm_class.__name__} "
            f"class_config_id={class_config_id}"
        )
    return owner_class_config


def _class_function_edge(
    *,
    owner_class_config,
    function_name: str,
    is_constructor: bool,
):
    matches = [
        edge
        for edge in owner_class_config.class_config_function_configs
        if edge.function_config is not None
        and edge.function_config.name == function_name
        and bool(edge.is_constructor) is bool(is_constructor)
    ]
    if len(matches) == 1:
        return matches[0]
    owner_name = owner_class_config.name
    if not matches:
        raise MetaGraphLanguageHandlerExecutionError(
            "Meta generated handler invocation cannot resolve FunctionConfig: "
            f"class={owner_name} function_name={function_name} "
            f"is_constructor={is_constructor}"
        )
    raise MetaGraphLanguageHandlerExecutionError(
        "Meta generated handler invocation found ambiguous FunctionConfig: "
        f"class={owner_name} function_name={function_name} "
        f"is_constructor={is_constructor} count={len(matches)}"
    )


@dataclass(frozen=True, slots=True)
class MetaGraphSessionDeltaLanguageHandlerRunner:
    """Adapt language-handler execution evidence into Meta dispatch output."""

    implementation: MetaGraphLanguageHandlerImplementation
    delta_builder: MetaGraphExecutionSessionDeltaBuilder = field(
        default_factory=MetaGraphExecutionSessionDeltaBuilder,
    )

    async def run_language_handler(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphHandlerDispatchResult:
        execution = await self.implementation.execute_language_handler(
            request,
            pre_state,
            bound_arguments,
        )
        if execution.post_oig is not None and execution.changes:
            raise MetaGraphLanguageHandlerExecutionError(
                "Language-handler execution must return either post_oig evidence "
                "or change-tree evidence, not both."
            )
        if execution.post_oig is not None:
            session_delta = self.delta_builder.build_delta_from_post_oig(
                request=request,
                pre_state=pre_state,
                post_oig=execution.post_oig,
                expected_graph_hash_post=execution.expected_graph_hash_post,
                root_object_id=execution.root_object_id,
                root_class_instance_identity_id=(
                    execution.root_class_instance_identity_id
                ),
                constructed_class_instance_ids=(
                    execution.constructed_class_instance_ids
                ),
            )
        else:
            session_delta = self.delta_builder.build_delta_from_changes(
                request=request,
                pre_state=pre_state,
                changes=execution.changes,
                expected_graph_hash_post=execution.expected_graph_hash_post,
                root_object_id=execution.root_object_id,
                root_class_instance_identity_id=(
                    execution.root_class_instance_identity_id
                ),
                constructed_class_instance_ids=(
                    execution.constructed_class_instance_ids
                ),
            )
        return MetaGraphHandlerDispatchResult(
            execution_plan=request.execution_plan,
            success=execution.success,
            payload=execution.payload,
            error_message=execution.error_message,
            execution_time_ms=execution.execution_time_ms,
            session_delta=session_delta,
        )


@dataclass(frozen=True, slots=True)
class MetaGraphGeneratedLanguageHandlerRunner:
    """Resolve and execute generated Meta language handlers."""

    handler_resolver: MetaGraphGeneratedLanguageHandlerResolver
    invocation_handler_resolver: MetaGraphGeneratedInvocationHandlerResolver | None = (
        None
    )
    delta_builder: MetaGraphExecutionSessionDeltaBuilder = field(
        default_factory=MetaGraphExecutionSessionDeltaBuilder,
    )

    async def run_language_handler(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphHandlerDispatchResult:
        handler = self.handler_resolver.resolve_generated_language_handler(
            request.execution_plan.implementation,
        )
        implementation = MetaGraphGeneratedLanguageHandlerImplementation(
            handler=handler,
            invocation_handler_resolver=self.invocation_handler_resolver,
        )
        runner = MetaGraphSessionDeltaLanguageHandlerRunner(
            implementation=implementation,
            delta_builder=self.delta_builder,
        )
        return await runner.run_language_handler(
            request,
            pre_state,
            bound_arguments,
        )


def _expand_generated_handler_key_map(
    source: Mapping[
        MetaGraphGeneratedLanguageHandlerKey,
        _TGeneratedHandlerValue,
    ],
    *,
    value_label: str,
) -> dict[
    MetaGraphGeneratedLanguageHandlerKey,
    _TGeneratedHandlerValue,
]:
    expanded: dict[
        MetaGraphGeneratedLanguageHandlerKey,
        _TGeneratedHandlerValue,
    ] = {}
    for key, value in source.items():
        _insert_generated_handler_key(
            expanded=expanded,
            key=key,
            value=value,
            value_label=value_label,
        )
        semantic_key = key.without_owner_class()
        if semantic_key != key:
            _insert_generated_handler_key(
                expanded=expanded,
                key=semantic_key,
                value=value,
                value_label=value_label,
            )
    return expanded


def _insert_generated_handler_key(
    *,
    expanded: dict[
        MetaGraphGeneratedLanguageHandlerKey,
        _TGeneratedHandlerValue,
    ],
    key: MetaGraphGeneratedLanguageHandlerKey,
    value: _TGeneratedHandlerValue,
    value_label: str,
) -> None:
    existing = expanded.get(key)
    if existing is not None and existing is not value:
        raise ValueError(
            "Duplicate generated Meta " f"{value_label} semantic key: {key.describe()}"
        )
    expanded[key] = value


__all__ = [
    "MetaGraphGeneratedLanguageHandlerCallable",
    "MetaGraphGeneratedLanguageHandlerImplementation",
    "MetaGraphGeneratedLanguageHandlerKey",
    "MetaGraphGeneratedLanguageHandlerRegistry",
    "MetaGraphGeneratedLanguageHandlerResolutionError",
    "MetaGraphGeneratedLanguageHandlerResolver",
    "MetaGraphGeneratedLanguageHandlerRunner",
    "MetaGraphGeneratedInvocationHandlerCallable",
    "MetaGraphGeneratedInvocationHandlerRegistry",
    "MetaGraphGeneratedInvocationHandlerResolver",
    "MetaGraphLanguageHandlerExecution",
    "MetaGraphLanguageHandlerExecutionError",
    "MetaGraphLanguageHandlerImplementation",
    "MetaGraphSessionDeltaLanguageHandlerRunner",
]
