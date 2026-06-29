from __future__ import annotations

from aware_meta.runtime.generated_impl_delegation import (
    meta_graph_impl_delegating_invocation_handler_resolver,
    meta_graph_impl_delegating_language_handler_resolver,
)
from aware_meta.runtime.handler_executor.language_handler import (
    MetaGraphGeneratedInvocationHandlerResolver,
    MetaGraphGeneratedLanguageHandlerResolver,
)


def meta_graph_strict_language_handler_resolver(
    delegate: MetaGraphGeneratedLanguageHandlerResolver | None,
) -> MetaGraphGeneratedLanguageHandlerResolver:
    """Build the strict Meta language-handler resolver chain.

    Runtime resolution is strict: authored impl delegation wraps the generated
    delegate directly, with no compatibility overlay layer.
    """

    return meta_graph_impl_delegating_language_handler_resolver(delegate)


def meta_graph_strict_invocation_handler_resolver(
    delegate: MetaGraphGeneratedInvocationHandlerResolver | None,
) -> MetaGraphGeneratedInvocationHandlerResolver:
    """Build the strict Meta nested-invocation resolver chain."""

    return meta_graph_impl_delegating_invocation_handler_resolver(delegate)


def meta_graph_runtime_language_handler_resolver(
    delegate: MetaGraphGeneratedLanguageHandlerResolver | None,
) -> MetaGraphGeneratedLanguageHandlerResolver:
    """Build the canonical Meta language-handler resolver chain."""

    return meta_graph_strict_language_handler_resolver(delegate)


def meta_graph_runtime_invocation_handler_resolver(
    delegate: MetaGraphGeneratedInvocationHandlerResolver | None,
) -> MetaGraphGeneratedInvocationHandlerResolver | None:
    """Build the canonical Meta nested-invocation resolver chain."""

    return meta_graph_strict_invocation_handler_resolver(delegate)


__all__ = [
    "meta_graph_runtime_invocation_handler_resolver",
    "meta_graph_runtime_language_handler_resolver",
    "meta_graph_strict_invocation_handler_resolver",
    "meta_graph_strict_language_handler_resolver",
]
