from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from aware_api_ontology.stable_ids import (
    stable_api_capability_endpoint_id,
    stable_api_capability_id,
    stable_api_id,
    stable_api_view_capability_endpoint_id,
    stable_api_view_id,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from .ir import APICompilePlan
from .ontology_graph.materialization.resolution import (
    _collect_accessible_object_config_graphs,
    _resolve_object_projection_graph_observable,
)


@dataclass(frozen=True, slots=True)
class ApiViewCapabilityEndpointBinding:
    api_ref: str
    api_view_ref: str
    endpoint_ref: str
    action_key: str
    api_view_id: UUID
    api_capability_endpoint_id: UUID
    api_view_capability_endpoint_id: UUID
    description: str | None = None


def api_view_capability_endpoint_bindings_from_compile_plan(
    *,
    plan: APICompilePlan,
    index: MetaGraphRuntimeIndex,
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
) -> tuple[ApiViewCapabilityEndpointBinding, ...]:
    api_accessible_graphs = _collect_accessible_object_config_graphs(
        index=index,
        extra_graphs=accessible_graphs,
    )
    bindings: list[ApiViewCapabilityEndpointBinding] = []
    for api_plan in plan.api_ontology:
        api_id = stable_api_id(name=api_plan.api.name)
        endpoint_ids_by_ref: dict[str, UUID] = {}
        for endpoint in api_plan.capability_endpoints:
            capability_id = stable_api_capability_id(
                api_id=api_id,
                name=endpoint.capability_name,
            )
            endpoint_id = stable_api_capability_endpoint_id(
                api_capability_id=capability_id,
                name=endpoint.name,
            )
            endpoint_ref = (
                f"{api_plan.api.name}.{endpoint.capability_name}.{endpoint.name}"
            )
            endpoint_ids_by_ref[endpoint_ref.casefold()] = endpoint_id

        view_ids_by_name: dict[str, UUID] = {}
        view_refs_by_name: dict[str, str] = {}
        for view in api_plan.views:
            observable = _resolve_object_projection_graph_observable(
                index=index,
                accessible_graphs=api_accessible_graphs,
                observable_ref=view.observable_ref,
            )
            api_view_id = stable_api_view_id(
                api_id=api_id,
                object_projection_graph_observable_id=observable.id,
                name=view.name,
            )
            view_ids_by_name[view.name.casefold()] = api_view_id
            view_refs_by_name[view.name.casefold()] = view.view_ref

        for view_endpoint in api_plan.view_capability_endpoints:
            endpoint_id = endpoint_ids_by_ref.get(view_endpoint.endpoint_ref.casefold())
            api_view_id = view_ids_by_name.get(view_endpoint.view_name.casefold())
            api_view_ref = view_refs_by_name.get(view_endpoint.view_name.casefold())
            if endpoint_id is None:
                raise RuntimeError(
                    "API view binding compile-plan resolution could not resolve "
                    + "capability endpoint: "
                    + f"api={api_plan.api.name!r} "
                    + f"endpoint_ref={view_endpoint.endpoint_ref!r}"
                )
            if api_view_id is None or api_view_ref is None:
                raise RuntimeError(
                    "API view binding compile-plan resolution could not resolve "
                    + "view: "
                    + f"api={api_plan.api.name!r} "
                    + f"view_name={view_endpoint.view_name!r}"
                )
            bindings.append(
                ApiViewCapabilityEndpointBinding(
                    api_ref=api_plan.api.name,
                    api_view_ref=api_view_ref,
                    endpoint_ref=view_endpoint.endpoint_ref,
                    action_key=view_endpoint.action_key,
                    api_view_id=api_view_id,
                    api_capability_endpoint_id=endpoint_id,
                    api_view_capability_endpoint_id=(
                        stable_api_view_capability_endpoint_id(
                            api_view_id=api_view_id,
                            api_capability_endpoint_id=endpoint_id,
                        )
                    ),
                    description=view_endpoint.description,
                )
            )
    return _validate_unique_bindings(bindings=bindings)


def _validate_unique_bindings(
    *,
    bindings: Sequence[ApiViewCapabilityEndpointBinding],
) -> tuple[ApiViewCapabilityEndpointBinding, ...]:
    seen: dict[tuple[str, str], ApiViewCapabilityEndpointBinding] = {}
    for binding in bindings:
        key = (binding.api_view_ref.casefold(), binding.endpoint_ref.casefold())
        existing = seen.get(key)
        if existing is not None:
            raise RuntimeError(
                "API view capability endpoint compile-plan catalog has duplicate "
                + "view/endpoint binding: "
                + f"api_view_ref={binding.api_view_ref!r} "
                + f"endpoint_ref={binding.endpoint_ref!r}"
            )
        seen[key] = binding
    return tuple(
        sorted(
            seen.values(),
            key=lambda item: (
                item.api_ref.casefold(),
                item.api_view_ref.casefold(),
                item.endpoint_ref.casefold(),
            ),
        )
    )


def api_view_capability_endpoint_catalog_from_bindings(
    *,
    bindings: Sequence[ApiViewCapabilityEndpointBinding],
) -> dict[tuple[str, str], ApiViewCapabilityEndpointBinding]:
    return {
        (binding.api_view_ref.casefold(), binding.endpoint_ref.casefold()): binding
        for binding in _validate_unique_bindings(bindings=bindings)
    }


__all__ = [
    "ApiViewCapabilityEndpointBinding",
    "api_view_capability_endpoint_bindings_from_compile_plan",
    "api_view_capability_endpoint_catalog_from_bindings",
]
