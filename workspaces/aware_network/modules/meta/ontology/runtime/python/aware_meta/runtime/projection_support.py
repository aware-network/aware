from __future__ import annotations

from uuid import UUID

from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex


def build_meta_graph_opgi_index(
    *,
    index: MetaGraphRuntimeIndex,
) -> dict[str, tuple[UUID, set[str]]]:
    by_key: dict[str, tuple[UUID, set[str]]] = {}
    for opg in index.ocg.object_projection_graphs:
        _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
            index=index,
            projection_hash=opg.projection_hash,
        )
        if opgi is None:
            continue
        key = (opgi.projection_name or "").strip()
        if not key:
            continue
        view_keys = {
            (observable.observable_key or "").strip()
            for observable in (opgi.object_projection_graph_observables or [])
            if (observable.observable_key or "").strip()
        }
        if not view_keys:
            view_keys = {
                (observable.key or "").strip()
                for observable in (opgi.object_projection_graph_observables or [])
                if (observable.key or "").strip()
            }
        by_key[key] = (opgi.id, view_keys)
    return by_key


__all__ = ["build_meta_graph_opgi_index"]
