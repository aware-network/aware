from __future__ import annotations

__all__ = [
    "build_meta_runtime_ocg_function_call_plan_previews",
    "materialize_delta",
]


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(name)

    from aware_meta.materialization.deltas import service

    return getattr(service, name)
