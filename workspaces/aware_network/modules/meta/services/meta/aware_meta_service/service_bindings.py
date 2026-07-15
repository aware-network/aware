from __future__ import annotations

from .api_service_protocol import (
    AwareMetaServiceProtocolHandler,
    build_aware_meta_service_protocol_handler,
)
from aware_meta.runtime.handler_executor import (
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphGeneratedLanguageHandlerResolver,
)


def build_service_bindings(
    *,
    runtime: object | None = None,
    generated_language_handler_resolver: (
        MetaGraphGeneratedLanguageHandlerResolver | None
    ) = None,
    generated_language_handler_module: (
        MetaGraphGeneratedLanguageHandlerModule | None
    ) = None,
) -> dict[str, AwareMetaServiceProtocolHandler]:
    return {
        "aware_meta": build_aware_meta_service_protocol_handler(
            runtime=runtime,
            generated_language_handler_resolver=generated_language_handler_resolver,
            generated_language_handler_module=generated_language_handler_module,
        ),
    }


__all__ = [
    "build_service_bindings",
]
