from __future__ import annotations

from aware_environment.handlers._generated import (
    meta_handlers as environment_meta_handlers,
)
from aware_environment.handlers.impl.environment import environment as environment_impl


_RETIRED_ENVIRONMENT_EXPERIENCE_MARKERS = (
    "EnvironmentExperience",
    "EnvironmentExperienceProfile",
    "environment_experience",
)
_RETIRED_ENVIRONMENT_METHOD = "create_experience_profile"


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


def test_environment_environment_experience_has_no_generated_meta_handlers() -> None:
    generated_symbols = tuple(
        name
        for name in dir(environment_meta_handlers)
        if any(marker in name for marker in _RETIRED_ENVIRONMENT_EXPERIENCE_MARKERS)
        or _RETIRED_ENVIRONMENT_METHOD in name
    )
    assert generated_symbols == ()

    retired_handler_keys = tuple(
        key
        for key in _generated_handler_keys()
        if any(
            marker in value
            for value in _handler_key_values(key)
            for marker in _RETIRED_ENVIRONMENT_EXPERIENCE_MARKERS
        )
        or _RETIRED_ENVIRONMENT_METHOD in _handler_key_values(key)
    )
    assert retired_handler_keys == ()


def test_environment_environment_create_experience_profile_is_retired() -> None:
    assert not hasattr(environment_impl, "create_experience_profile")
