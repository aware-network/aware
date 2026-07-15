from __future__ import annotations

from uuid import uuid4

from aware_environment.handlers._generated import (
    meta_handlers as environment_meta_handlers,
)
from aware_environment.handlers.impl.thread import thread as thread_impl
from aware_environment_ontology.thread.thread import (
    ActorDirectoryEntry,
    ActorDirectoryResponse,
)

_RETIRED_FUNCTION_NAME = "resolve_actor_directory"


def _generated_handler_keys() -> tuple[object, ...]:
    return tuple(
        key
        for registry in (
            environment_meta_handlers.AWARE_META_GRAPH_HANDLERS,
            environment_meta_handlers.AWARE_META_GRAPH_INVOCATION_HANDLERS,
            environment_meta_handlers.AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS,
        )
        for key in registry
    )


def _handler_key_values(key: object) -> tuple[str, ...]:
    return tuple(
        str(getattr(key, field, ""))
        for field in (
            "owner_key",
            "owner_class_fqn",
            "owner_class_name",
            "function_name",
        )
    )


def test_thread_resolve_actor_directory_is_removed_from_generated_meta_handlers() -> (
    None
):
    generated_symbols = tuple(
        name
        for name in dir(environment_meta_handlers)
        if _RETIRED_FUNCTION_NAME in name
    )
    assert generated_symbols == ()

    retired_handler_keys = tuple(
        key
        for key in _generated_handler_keys()
        if any(_RETIRED_FUNCTION_NAME in value for value in _handler_key_values(key))
    )
    assert retired_handler_keys == ()
    assert not hasattr(thread_impl, _RETIRED_FUNCTION_NAME)


def test_actor_directory_response_is_inline_dto_only() -> None:
    actor_id = uuid4()
    identity_id = uuid4()

    response = ActorDirectoryResponse(
        entries=[
            ActorDirectoryEntry(
                actor_id=actor_id,
                identity_id=identity_id,
            )
        ]
    )

    assert response.entries[0].actor_id == actor_id
    assert response.entries[0].identity_id == identity_id
