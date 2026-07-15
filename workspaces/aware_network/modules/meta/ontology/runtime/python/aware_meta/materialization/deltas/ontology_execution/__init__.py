from __future__ import annotations

__all__ = ["build_provider_delta_ontology_execution_plan"]


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(name)

    from aware_meta.materialization.deltas.ontology_execution import service

    return getattr(service, name)
