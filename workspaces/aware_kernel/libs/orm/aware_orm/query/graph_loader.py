from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from uuid import UUID

from aware_orm.models.base_model import BaseORMModel


def bind_graph_value(session: Any, value: Any) -> Any:
    """Bind nested graph payload values to the session identity map recursively."""

    if isinstance(value, BaseORMModel):
        return _bind_graph_model(session, value)

    if isinstance(value, list):
        return [bind_graph_value(session, item) for item in value]

    if isinstance(value, tuple):
        return tuple(bind_graph_value(session, item) for item in value)

    if isinstance(value, dict):
        return {key: bind_graph_value(session, item) for key, item in value.items()}

    return value


def merge_graph_model(session: Any, cached: BaseORMModel, fresh: BaseORMModel) -> BaseORMModel:
    """Merge a freshly hydrated graph model into an identity-map cached instance."""

    for field_name in type(fresh).model_fields:
        value = getattr(fresh, field_name, None)
        if value is None:
            continue
        setattr(cached, field_name, bind_graph_value(session, value))

    _mark_loaded(session, cached)
    return cached


def extract_graph_list(rows: Iterable[dict[str, Any]]) -> list[Any]:
    """Normalize GraphSQL list rows into a list of graph payloads."""

    row_list = list(rows)
    if not row_list:
        return []
    graph_value = row_list[0].get("graph")
    if graph_value is None:
        return []
    if isinstance(graph_value, list):
        return graph_value
    return [graph_value]


def _bind_graph_model(session: Any, instance: BaseORMModel) -> BaseORMModel:
    obj_id = getattr(instance, "id", None)
    if isinstance(obj_id, str):
        try:
            obj_id = UUID(obj_id)
        except Exception:
            pass

    cached = None
    if obj_id is not None:
        try:
            cached = session.imap_get(type(instance), obj_id)
        except Exception:
            cached = None
    if cached is not None and cached is not instance:
        return merge_graph_model(session, cached, instance)

    for field_name in type(instance).model_fields:
        value = getattr(instance, field_name, None)
        bound_value = bind_graph_value(session, value)
        if bound_value is not value:
            setattr(instance, field_name, bound_value)

    _mark_loaded(session, instance)
    try:
        session.imap_add(instance)
    except Exception:
        pass
    return instance


def _mark_loaded(session: Any, instance: BaseORMModel) -> None:
    try:
        instance._is_new = False
        instance._bound_session = session
        branch_id = getattr(session, "_branch_id", None)
        if isinstance(branch_id, UUID):
            instance._branch_id = branch_id
    except Exception:
        pass


__all__ = ["bind_graph_value", "extract_graph_list", "merge_graph_model"]
