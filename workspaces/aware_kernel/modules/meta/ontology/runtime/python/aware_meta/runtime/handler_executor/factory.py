from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from aware_meta.runtime.handler_executor.append_ready import (
    MetaGraphAppendReadyChangeAssemblerPhase,
)
from aware_meta.runtime.handler_executor.argument_binding import (
    MetaGraphArgumentBinderPhase,
)
from aware_meta.runtime.handler_executor.executor import (
    MetaGraphPhaseHandlerExecutor,
)
from aware_meta.runtime.handler_executor.implementation_dispatch import (
    MetaGraphImplementationDispatcherPhase,
)
from aware_meta.runtime.handler_executor.function_impl_runner import (
    MetaGraphInstructionBodyFunctionImplRunner,
)
from aware_meta.runtime.handler_executor.language_handler import (
    MetaGraphGeneratedLanguageHandlerCallable,
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphGeneratedLanguageHandlerRegistry,
    MetaGraphGeneratedLanguageHandlerResolver,
    MetaGraphGeneratedLanguageHandlerRunner,
    MetaGraphGeneratedInvocationHandlerResolver,
)
from aware_meta.runtime.handler_executor.mutation_boundary import (
    MetaGraphMutateSelfOnlyPolicy,
    MetaGraphMutationBoundaryPolicy,
    MetaGraphMutationBoundaryValidatorPhase,
)
from aware_meta.runtime.handler_executor.mutation_recording import (
    MetaGraphMutationRecorderPhase,
    MetaGraphSessionDeltaMutationSource,
)
from aware_meta.runtime.handler_executor.pre_state import (
    MetaGraphEmptyLaneBootstrapCallable,
    MetaGraphEmptyLaneBootstrapResolver,
    MetaGraphGeneratedConstructorBootstrapRegistry,
    MetaGraphOigMaterializerPreStateProvider,
    MetaGraphPreStateMaterializerPhase,
    MetaGraphPreStateProvider,
)
from aware_meta.runtime.generated_handler_resolver_chain import (
    meta_graph_runtime_invocation_handler_resolver,
    meta_graph_runtime_language_handler_resolver,
)


class MetaGraphGeneratedLanguageHandlerModule(Protocol):
    AWARE_META_GRAPH_HANDLERS: Mapping[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphGeneratedLanguageHandlerCallable,
    ]


class MetaGraphGeneratedConstructorBootstrapModule(Protocol):
    AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS: Mapping[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphEmptyLaneBootstrapCallable,
    ]


def build_meta_graph_generated_language_handler_registry(
    *,
    module: MetaGraphGeneratedLanguageHandlerModule,
) -> MetaGraphGeneratedLanguageHandlerRegistry:
    return MetaGraphGeneratedLanguageHandlerRegistry(
        handlers_by_key=module.AWARE_META_GRAPH_HANDLERS,
    )


def build_meta_graph_generated_constructor_bootstrap_registry(
    *,
    module: MetaGraphGeneratedConstructorBootstrapModule,
) -> MetaGraphGeneratedConstructorBootstrapRegistry:
    return MetaGraphGeneratedConstructorBootstrapRegistry(
        bootstraps_by_key=module.AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS,
    )


def build_meta_graph_generated_handler_executor(
    *,
    handler_resolver: MetaGraphGeneratedLanguageHandlerResolver,
    invocation_handler_resolver: (
        MetaGraphGeneratedInvocationHandlerResolver | None
    ) = None,
    pre_state_provider: MetaGraphPreStateProvider | None = None,
    empty_lane_bootstrap_resolver: MetaGraphEmptyLaneBootstrapResolver | None = None,
    mutation_boundary_policy: MetaGraphMutationBoundaryPolicy | None = None,
) -> MetaGraphPhaseHandlerExecutor:
    resolved_pre_state_provider = (
        pre_state_provider
        if pre_state_provider is not None
        else MetaGraphOigMaterializerPreStateProvider(
            empty_lane_bootstrap_resolver=empty_lane_bootstrap_resolver,
        )
    )
    resolved_invocation_handler_resolver = (
        meta_graph_runtime_invocation_handler_resolver(
            invocation_handler_resolver,
        )
    )
    resolved_handler_resolver = meta_graph_runtime_language_handler_resolver(
        handler_resolver,
    )
    language_handler_runner = MetaGraphGeneratedLanguageHandlerRunner(
        handler_resolver=resolved_handler_resolver,
        invocation_handler_resolver=resolved_invocation_handler_resolver,
    )
    return MetaGraphPhaseHandlerExecutor(
        pre_state_materializer=MetaGraphPreStateMaterializerPhase(
            provider=resolved_pre_state_provider,
        ),
        argument_binder=MetaGraphArgumentBinderPhase(),
        implementation_dispatcher=MetaGraphImplementationDispatcherPhase(
            aware_function_impl_runner=MetaGraphInstructionBodyFunctionImplRunner(
                language_handler_runner=language_handler_runner,
            ),
            language_handler_runner=language_handler_runner,
        ),
        mutation_recorder=MetaGraphMutationRecorderPhase(
            mutation_source=MetaGraphSessionDeltaMutationSource(),
        ),
        mutation_boundary_validator=MetaGraphMutationBoundaryValidatorPhase(
            policy=mutation_boundary_policy or MetaGraphMutateSelfOnlyPolicy(),
        ),
        append_ready_change_assembler=MetaGraphAppendReadyChangeAssemblerPhase(),
    )


__all__ = [
    "build_meta_graph_generated_constructor_bootstrap_registry",
    "build_meta_graph_generated_handler_executor",
    "build_meta_graph_generated_language_handler_registry",
    "MetaGraphGeneratedConstructorBootstrapModule",
    "MetaGraphGeneratedLanguageHandlerModule",
]
