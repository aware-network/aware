from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from ..models import APIOwnership


@dataclass(frozen=True, slots=True)
class APIOntologyApiOperation:
    name: str
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class APIOntologyCapabilityOperation:
    api_name: str
    name: str
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class APIOntologyCapabilityEndpointOperation:
    api_name: str
    capability_name: str
    name: str
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class APIOntologyCapabilityEndpointRequestConfigOperation:
    api_name: str
    capability_name: str
    endpoint_name: str
    class_ref: str
    class_config_id: UUID | None
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class APIOntologyCapabilityEndpointResponseConfigOperation:
    api_name: str
    capability_name: str
    endpoint_name: str
    class_ref: str
    class_config_id: UUID | None
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class APIOntologyCapabilityEndpointStreamConfigOperation:
    api_name: str
    capability_name: str
    endpoint_name: str
    stream_mode: str
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class APIOntologyCapabilityEndpointStreamEventConfigOperation:
    api_name: str
    capability_name: str
    endpoint_name: str
    kind: str
    class_ref: str
    class_config_id: UUID | None
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class APIOntologyCapabilityEndpointFunctionOperation:
    api_name: str
    capability_name: str
    endpoint_name: str
    name: str
    graph_target: str
    graph_capability_function_name: str
    source_path: str


@dataclass(frozen=True, slots=True)
class APIOntologyGraphOperation:
    api_name: str
    target: str
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class APIOntologyGraphFunctionOperation:
    api_name: str
    graph_target: str
    target: str
    source_path: str


@dataclass(frozen=True, slots=True)
class APIOntologyGraphProjectionOperation:
    api_name: str
    graph_target: str
    target: str
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class APIOntologyGraphCapabilityOperation:
    api_name: str
    graph_target: str
    capability_name: str
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class APIOntologyGraphCapabilityFunctionOperation:
    api_name: str
    graph_target: str
    capability_name: str
    name: str
    target: str
    source_path: str


@dataclass(frozen=True, slots=True)
class APIOntologyPlan:
    api: APIOntologyApiOperation
    capabilities: tuple[APIOntologyCapabilityOperation, ...]
    capability_endpoints: tuple[APIOntologyCapabilityEndpointOperation, ...]
    capability_endpoint_request_configs: tuple[
        APIOntologyCapabilityEndpointRequestConfigOperation, ...
    ]
    capability_endpoint_response_configs: tuple[
        APIOntologyCapabilityEndpointResponseConfigOperation, ...
    ]
    capability_endpoint_stream_configs: tuple[
        APIOntologyCapabilityEndpointStreamConfigOperation, ...
    ]
    capability_endpoint_stream_event_configs: tuple[
        APIOntologyCapabilityEndpointStreamEventConfigOperation, ...
    ]
    capability_endpoint_functions: tuple[
        APIOntologyCapabilityEndpointFunctionOperation, ...
    ]
    graphs: tuple[APIOntologyGraphOperation, ...]
    graph_functions: tuple[APIOntologyGraphFunctionOperation, ...]
    graph_projections: tuple[APIOntologyGraphProjectionOperation, ...]
    graph_capabilities: tuple[APIOntologyGraphCapabilityOperation, ...]
    graph_capability_functions: tuple[APIOntologyGraphCapabilityFunctionOperation, ...]


def build_api_ontology_plans(
    *,
    api_ownership: tuple[APIOwnership, ...],
) -> tuple[APIOntologyPlan, ...]:
    plans: list[APIOntologyPlan] = []
    for ownership in api_ownership:
        api_name = _required_str_token(ownership.name, field_name="api_ownership.name")
        source_path = _required_str_token(
            ownership.source_path,
            field_name=f"api_ownership[{api_name}].source_path",
        )

        capability_rows: list[APIOntologyCapabilityOperation] = []
        capability_endpoint_rows: list[APIOntologyCapabilityEndpointOperation] = []
        capability_endpoint_request_config_rows: list[
            APIOntologyCapabilityEndpointRequestConfigOperation
        ] = []
        capability_endpoint_response_config_rows: list[
            APIOntologyCapabilityEndpointResponseConfigOperation
        ] = []
        capability_endpoint_stream_config_rows: list[
            APIOntologyCapabilityEndpointStreamConfigOperation
        ] = []
        capability_endpoint_stream_event_config_rows: list[
            APIOntologyCapabilityEndpointStreamEventConfigOperation
        ] = []
        capability_endpoint_function_rows: list[
            APIOntologyCapabilityEndpointFunctionOperation
        ] = []
        graph_rows: list[APIOntologyGraphOperation] = []
        graph_function_rows_by_key: dict[
            tuple[str, str], APIOntologyGraphFunctionOperation
        ] = {}
        graph_projection_rows: list[APIOntologyGraphProjectionOperation] = []
        graph_capability_rows: list[APIOntologyGraphCapabilityOperation] = []
        graph_capability_function_rows: list[
            APIOntologyGraphCapabilityFunctionOperation
        ] = []

        for capability in ownership.capabilities:
            capability_rows.append(
                APIOntologyCapabilityOperation(
                    api_name=api_name,
                    name=_required_str_token(
                        capability.name,
                        field_name=f"api_ownership[{api_name}].capabilities[].name",
                    ),
                    description=capability.description,
                    source_path=_required_str_token(
                        capability.source_path,
                        field_name=f"api_ownership[{api_name}].capabilities[{capability.name}].source_path",
                    ),
                )
            )
            capability_name = _required_str_token(
                capability.name,
                field_name=f"api_ownership[{api_name}].capabilities[].name",
            )
            for endpoint in capability.endpoints:
                endpoint_name = _required_str_token(
                    endpoint.name,
                    field_name=(
                        f"api_ownership[{api_name}].capabilities[{capability_name}].endpoints[].name"
                    ),
                )
                capability_endpoint_rows.append(
                    APIOntologyCapabilityEndpointOperation(
                        api_name=api_name,
                        capability_name=capability_name,
                        name=endpoint_name,
                        description=endpoint.description,
                        source_path=_required_str_token(
                            endpoint.source_path,
                            field_name=(
                                f"api_ownership[{api_name}].capabilities[{capability_name}].endpoints[].source_path"
                            ),
                        ),
                    )
                )
                request_config = endpoint.request_config
                capability_endpoint_request_config_rows.append(
                    APIOntologyCapabilityEndpointRequestConfigOperation(
                        api_name=api_name,
                        capability_name=capability_name,
                        endpoint_name=endpoint_name,
                        class_ref=_required_str_token(
                            request_config.class_ref,
                            field_name=(
                                f"api_ownership[{api_name}].capabilities[{capability_name}]"
                                + f".endpoints[{endpoint_name}].request_config.class_ref"
                            ),
                        ),
                        class_config_id=request_config.class_config_id,
                        description=request_config.description,
                        source_path=_required_str_token(
                            request_config.source_path,
                            field_name=(
                                f"api_ownership[{api_name}].capabilities[{capability_name}]"
                                + f".endpoints[{endpoint_name}].request_config.source_path"
                            ),
                        ),
                    )
                )
                if request_config.response_config is not None:
                    response_config = request_config.response_config
                    capability_endpoint_response_config_rows.append(
                        APIOntologyCapabilityEndpointResponseConfigOperation(
                            api_name=api_name,
                            capability_name=capability_name,
                            endpoint_name=endpoint_name,
                            class_ref=_required_str_token(
                                response_config.class_ref,
                                field_name=(
                                    f"api_ownership[{api_name}].capabilities[{capability_name}]"
                                    + f".endpoints[{endpoint_name}].request_config.response_config.class_ref"
                                ),
                            ),
                            class_config_id=response_config.class_config_id,
                            description=response_config.description,
                            source_path=_required_str_token(
                                response_config.source_path,
                                field_name=(
                                    f"api_ownership[{api_name}].capabilities[{capability_name}]"
                                    + f".endpoints[{endpoint_name}].request_config.response_config.source_path"
                                ),
                            ),
                        )
                    )
                if request_config.stream_config is not None:
                    stream_config = request_config.stream_config
                    capability_endpoint_stream_config_rows.append(
                        APIOntologyCapabilityEndpointStreamConfigOperation(
                            api_name=api_name,
                            capability_name=capability_name,
                            endpoint_name=endpoint_name,
                            stream_mode=_required_str_token(
                                stream_config.stream_mode,
                                field_name=(
                                    f"api_ownership[{api_name}].capabilities[{capability_name}]"
                                    + f".endpoints[{endpoint_name}].request_config.stream_config.stream_mode"
                                ),
                            ),
                            description=stream_config.description,
                            source_path=_required_str_token(
                                stream_config.source_path,
                                field_name=(
                                    f"api_ownership[{api_name}].capabilities[{capability_name}]"
                                    + f".endpoints[{endpoint_name}].request_config.stream_config.source_path"
                                ),
                            ),
                        )
                    )
                    for event_config in stream_config.event_configs:
                        capability_endpoint_stream_event_config_rows.append(
                            APIOntologyCapabilityEndpointStreamEventConfigOperation(
                                api_name=api_name,
                                capability_name=capability_name,
                                endpoint_name=endpoint_name,
                                kind=_required_str_token(
                                    event_config.kind,
                                    field_name=(
                                        f"api_ownership[{api_name}].capabilities[{capability_name}]"
                                        + f".endpoints[{endpoint_name}].request_config.stream_config"
                                        + ".event_configs[].kind"
                                    ),
                                ),
                                class_ref=_required_str_token(
                                    event_config.class_ref,
                                    field_name=(
                                        f"api_ownership[{api_name}].capabilities[{capability_name}]"
                                        + f".endpoints[{endpoint_name}].request_config.stream_config"
                                        + ".event_configs[].class_ref"
                                    ),
                                ),
                                class_config_id=event_config.class_config_id,
                                description=event_config.description,
                                source_path=_required_str_token(
                                    event_config.source_path,
                                    field_name=(
                                        f"api_ownership[{api_name}].capabilities[{capability_name}]"
                                        + f".endpoints[{endpoint_name}].request_config.stream_config"
                                        + ".event_configs[].source_path"
                                    ),
                                ),
                            )
                        )
                for endpoint_function in endpoint.functions:
                    capability_endpoint_function_rows.append(
                        APIOntologyCapabilityEndpointFunctionOperation(
                            api_name=api_name,
                            capability_name=capability_name,
                            endpoint_name=endpoint_name,
                            name=_required_str_token(
                                endpoint_function.name,
                                field_name=(
                                    f"api_ownership[{api_name}].capabilities[{capability_name}]"
                                    + f".endpoints[{endpoint_name}].functions[].name"
                                ),
                            ),
                            graph_target=_required_str_token(
                                endpoint_function.graph_target,
                                field_name=(
                                    f"api_ownership[{api_name}].capabilities[{capability_name}]"
                                    + f".endpoints[{endpoint_name}].functions[].graph_target"
                                ),
                            ),
                            graph_capability_function_name=_required_str_token(
                                endpoint_function.graph_capability_function_name,
                                field_name=(
                                    f"api_ownership[{api_name}].capabilities[{capability_name}]"
                                    + f".endpoints[{endpoint_name}].functions[].graph_capability_function_name"
                                ),
                            ),
                            source_path=_required_str_token(
                                endpoint_function.source_path,
                                field_name=(
                                    f"api_ownership[{api_name}].capabilities[{capability_name}]"
                                    + f".endpoints[{endpoint_name}].functions[].source_path"
                                ),
                            ),
                        )
                    )

        for graph in ownership.graphs:
            graph_target = _required_str_token(
                graph.target,
                field_name=f"api_ownership[{api_name}].graphs[].target",
            )
            graph_source_path = _required_str_token(
                graph.source_path,
                field_name=f"api_ownership[{api_name}].graphs[{graph_target}].source_path",
            )
            graph_rows.append(
                APIOntologyGraphOperation(
                    api_name=api_name,
                    target=graph_target,
                    description=None,
                    source_path=graph_source_path,
                )
            )

            for projection in graph.projections:
                projection_target = _required_str_token(
                    projection.target,
                    field_name=f"api_ownership[{api_name}].graphs[{graph_target}].projections[].target",
                )
                projection_source_path = _required_str_token(
                    projection.source_path,
                    field_name=(
                        f"api_ownership[{api_name}].graphs[{graph_target}].projections[{projection_target}].source_path"
                    ),
                )
                graph_projection_rows.append(
                    APIOntologyGraphProjectionOperation(
                        api_name=api_name,
                        graph_target=graph_target,
                        target=projection_target,
                        description=None,
                        source_path=projection_source_path,
                    )
                )

            for graph_capability in graph.capabilities:
                capability_name = _required_str_token(
                    graph_capability.capability_name,
                    field_name=f"api_ownership[{api_name}].graphs[{graph_target}].capabilities[].capability_name",
                )
                graph_capability_source_path = _required_str_token(
                    graph_capability.source_path,
                    field_name=(
                        f"api_ownership[{api_name}].graphs[{graph_target}].capabilities[{capability_name}].source_path"
                    ),
                )
                graph_capability_rows.append(
                    APIOntologyGraphCapabilityOperation(
                        api_name=api_name,
                        graph_target=graph_target,
                        capability_name=capability_name,
                        description=None,
                        source_path=graph_capability_source_path,
                    )
                )
                for function in graph_capability.functions:
                    function_target = _required_str_token(
                        function.target,
                        field_name=(
                            f"api_ownership[{api_name}].graphs[{graph_target}].capabilities[{capability_name}]"
                            + ".functions[].target"
                        ),
                    )
                    graph_function_key = (graph_target, function_target)
                    graph_function_rows_by_key.setdefault(
                        graph_function_key,
                        APIOntologyGraphFunctionOperation(
                            api_name=api_name,
                            graph_target=graph_target,
                            target=function_target,
                            source_path=_required_str_token(
                                function.source_path,
                                field_name=(
                                    f"api_ownership[{api_name}].graphs[{graph_target}].capabilities[{capability_name}]"
                                    + ".functions[].source_path"
                                ),
                            ),
                        ),
                    )
                    graph_capability_function_rows.append(
                        APIOntologyGraphCapabilityFunctionOperation(
                            api_name=api_name,
                            graph_target=graph_target,
                            capability_name=capability_name,
                            name=_required_str_token(
                                function.name,
                                field_name=(
                                    f"api_ownership[{api_name}].graphs[{graph_target}].capabilities[{capability_name}]"
                                    + ".functions[].name"
                                ),
                            ),
                            target=function_target,
                            source_path=_required_str_token(
                                function.source_path,
                                field_name=(
                                    f"api_ownership[{api_name}].graphs[{graph_target}].capabilities[{capability_name}]"
                                    + ".functions[].source_path"
                                ),
                            ),
                        )
                    )

        plans.append(
            APIOntologyPlan(
                api=APIOntologyApiOperation(
                    name=api_name,
                    description=None,
                    source_path=source_path,
                ),
                capabilities=tuple(
                    sorted(
                        capability_rows, key=lambda item: (item.name, item.source_path)
                    )
                ),
                capability_endpoints=tuple(
                    sorted(
                        capability_endpoint_rows,
                        key=lambda item: (
                            item.capability_name,
                            item.name,
                            item.source_path,
                        ),
                    )
                ),
                capability_endpoint_request_configs=tuple(
                    sorted(
                        capability_endpoint_request_config_rows,
                        key=lambda item: (
                            item.capability_name,
                            item.endpoint_name,
                            item.class_ref,
                            item.source_path,
                        ),
                    )
                ),
                capability_endpoint_response_configs=tuple(
                    sorted(
                        capability_endpoint_response_config_rows,
                        key=lambda item: (
                            item.capability_name,
                            item.endpoint_name,
                            item.class_ref,
                            item.source_path,
                        ),
                    )
                ),
                capability_endpoint_stream_configs=tuple(
                    sorted(
                        capability_endpoint_stream_config_rows,
                        key=lambda item: (
                            item.capability_name,
                            item.endpoint_name,
                            item.stream_mode,
                            item.source_path,
                        ),
                    )
                ),
                capability_endpoint_stream_event_configs=tuple(
                    sorted(
                        capability_endpoint_stream_event_config_rows,
                        key=lambda item: (
                            item.capability_name,
                            item.endpoint_name,
                            item.kind,
                            item.class_ref,
                            item.source_path,
                        ),
                    )
                ),
                capability_endpoint_functions=tuple(
                    sorted(
                        capability_endpoint_function_rows,
                        key=lambda item: (
                            item.capability_name,
                            item.endpoint_name,
                            item.name,
                            item.graph_target,
                            item.graph_capability_function_name,
                            item.source_path,
                        ),
                    )
                ),
                graphs=tuple(
                    sorted(graph_rows, key=lambda item: (item.target, item.source_path))
                ),
                graph_functions=tuple(
                    sorted(
                        graph_function_rows_by_key.values(),
                        key=lambda item: (
                            item.graph_target,
                            item.target,
                            item.source_path,
                        ),
                    )
                ),
                graph_projections=tuple(
                    sorted(
                        graph_projection_rows,
                        key=lambda item: (
                            item.graph_target,
                            item.target,
                            item.source_path,
                        ),
                    )
                ),
                graph_capabilities=tuple(
                    sorted(
                        graph_capability_rows,
                        key=lambda item: (
                            item.graph_target,
                            item.capability_name,
                            item.source_path,
                        ),
                    )
                ),
                graph_capability_functions=tuple(
                    sorted(
                        graph_capability_function_rows,
                        key=lambda item: (
                            item.graph_target,
                            item.capability_name,
                            item.name,
                            item.target,
                            item.source_path,
                        ),
                    )
                ),
            )
        )
    return tuple(sorted(plans, key=lambda item: (item.api.name, item.api.source_path)))


def encode_api_ontology_plan_payload(
    *,
    plans: tuple[APIOntologyPlan, ...],
) -> list[dict[str, object]]:
    return [
        {
            "api": {
                "name": plan.api.name,
                "description": plan.api.description,
                "source_path": plan.api.source_path,
            },
            "capabilities": [
                {
                    "api_name": row.api_name,
                    "name": row.name,
                    "description": row.description,
                    "source_path": row.source_path,
                }
                for row in plan.capabilities
            ],
            "capability_endpoints": [
                {
                    "api_name": row.api_name,
                    "capability_name": row.capability_name,
                    "name": row.name,
                    "description": row.description,
                    "source_path": row.source_path,
                }
                for row in plan.capability_endpoints
            ],
            "capability_endpoint_request_configs": [
                {
                    "api_name": row.api_name,
                    "capability_name": row.capability_name,
                    "endpoint_name": row.endpoint_name,
                    "class_ref": row.class_ref,
                    "class_config_id": (
                        str(row.class_config_id)
                        if row.class_config_id is not None
                        else None
                    ),
                    "description": row.description,
                    "source_path": row.source_path,
                }
                for row in plan.capability_endpoint_request_configs
            ],
            "capability_endpoint_response_configs": [
                {
                    "api_name": row.api_name,
                    "capability_name": row.capability_name,
                    "endpoint_name": row.endpoint_name,
                    "class_ref": row.class_ref,
                    "class_config_id": (
                        str(row.class_config_id)
                        if row.class_config_id is not None
                        else None
                    ),
                    "description": row.description,
                    "source_path": row.source_path,
                }
                for row in plan.capability_endpoint_response_configs
            ],
            "capability_endpoint_stream_configs": [
                {
                    "api_name": row.api_name,
                    "capability_name": row.capability_name,
                    "endpoint_name": row.endpoint_name,
                    "stream_mode": row.stream_mode,
                    "description": row.description,
                    "source_path": row.source_path,
                }
                for row in plan.capability_endpoint_stream_configs
            ],
            "capability_endpoint_stream_event_configs": [
                {
                    "api_name": row.api_name,
                    "capability_name": row.capability_name,
                    "endpoint_name": row.endpoint_name,
                    "kind": row.kind,
                    "class_ref": row.class_ref,
                    "class_config_id": (
                        str(row.class_config_id)
                        if row.class_config_id is not None
                        else None
                    ),
                    "description": row.description,
                    "source_path": row.source_path,
                }
                for row in plan.capability_endpoint_stream_event_configs
            ],
            "capability_endpoint_functions": [
                {
                    "api_name": row.api_name,
                    "capability_name": row.capability_name,
                    "endpoint_name": row.endpoint_name,
                    "name": row.name,
                    "graph_target": row.graph_target,
                    "graph_capability_function_name": row.graph_capability_function_name,
                    "source_path": row.source_path,
                }
                for row in plan.capability_endpoint_functions
            ],
            "graphs": [
                {
                    "api_name": row.api_name,
                    "target": row.target,
                    "description": row.description,
                    "source_path": row.source_path,
                }
                for row in plan.graphs
            ],
            "graph_functions": [
                {
                    "api_name": row.api_name,
                    "graph_target": row.graph_target,
                    "target": row.target,
                    "source_path": row.source_path,
                }
                for row in plan.graph_functions
            ],
            "graph_projections": [
                {
                    "api_name": row.api_name,
                    "graph_target": row.graph_target,
                    "target": row.target,
                    "description": row.description,
                    "source_path": row.source_path,
                }
                for row in plan.graph_projections
            ],
            "graph_capabilities": [
                {
                    "api_name": row.api_name,
                    "graph_target": row.graph_target,
                    "capability_name": row.capability_name,
                    "description": row.description,
                    "source_path": row.source_path,
                }
                for row in plan.graph_capabilities
            ],
            "graph_capability_functions": [
                {
                    "api_name": row.api_name,
                    "graph_target": row.graph_target,
                    "capability_name": row.capability_name,
                    "name": row.name,
                    "target": row.target,
                    "source_path": row.source_path,
                }
                for row in plan.graph_capability_functions
            ],
        }
        for plan in plans
    ]


def decode_api_ontology_plan_payload(
    *,
    payload: Sequence[object],
) -> tuple[APIOntologyPlan, ...]:
    plans: list[APIOntologyPlan] = []
    for index, plan_obj in enumerate(payload):
        row = _expect_mapping(plan_obj, field_name=f"api_ontology[{index}]")
        plans.append(_decode_api_ontology_plan_row(row=row, row_index=index))
    return tuple(plans)


def _decode_api_ontology_plan_row(
    *,
    row: Mapping[str, object],
    row_index: int,
) -> APIOntologyPlan:
    api_row = _expect_mapping(
        row.get("api"), field_name=f"api_ontology[{row_index}].api"
    )
    api_name = _required_str_token(
        api_row.get("name"), field_name=f"api_ontology[{row_index}].api.name"
    )
    api_source_path = _required_str_token(
        api_row.get("source_path"),
        field_name=f"api_ontology[{row_index}].api.source_path",
    )
    api_description = _optional_str_token(
        api_row.get("description"),
        field_name=f"api_ontology[{row_index}].api.description",
    )

    capabilities = tuple(
        _decode_capability_row(
            row_index=row_index, api_name=api_name, item=obj, item_index=index
        )
        for index, obj in enumerate(
            _expect_list(
                row.get("capabilities", []),
                field_name=f"api_ontology[{row_index}].capabilities",
            )
        )
    )
    capability_endpoints = tuple(
        _decode_capability_endpoint_row(
            row_index=row_index, api_name=api_name, item=obj, item_index=index
        )
        for index, obj in enumerate(
            _expect_list(
                row.get("capability_endpoints", []),
                field_name=f"api_ontology[{row_index}].capability_endpoints",
            )
        )
    )
    capability_endpoint_request_configs = tuple(
        _decode_capability_endpoint_request_config_row(
            row_index=row_index, api_name=api_name, item=obj, item_index=index
        )
        for index, obj in enumerate(
            _expect_list(
                row.get("capability_endpoint_request_configs", []),
                field_name=f"api_ontology[{row_index}].capability_endpoint_request_configs",
            )
        )
    )
    capability_endpoint_response_configs = tuple(
        _decode_capability_endpoint_response_config_row(
            row_index=row_index, api_name=api_name, item=obj, item_index=index
        )
        for index, obj in enumerate(
            _expect_list(
                row.get("capability_endpoint_response_configs", []),
                field_name=f"api_ontology[{row_index}].capability_endpoint_response_configs",
            )
        )
    )
    capability_endpoint_stream_configs = tuple(
        _decode_capability_endpoint_stream_config_row(
            row_index=row_index, api_name=api_name, item=obj, item_index=index
        )
        for index, obj in enumerate(
            _expect_list(
                row.get("capability_endpoint_stream_configs", []),
                field_name=f"api_ontology[{row_index}].capability_endpoint_stream_configs",
            )
        )
    )
    capability_endpoint_stream_event_configs = tuple(
        _decode_capability_endpoint_stream_event_config_row(
            row_index=row_index, api_name=api_name, item=obj, item_index=index
        )
        for index, obj in enumerate(
            _expect_list(
                row.get("capability_endpoint_stream_event_configs", []),
                field_name=f"api_ontology[{row_index}].capability_endpoint_stream_event_configs",
            )
        )
    )
    capability_endpoint_functions = tuple(
        _decode_capability_endpoint_function_row(
            row_index=row_index, api_name=api_name, item=obj, item_index=index
        )
        for index, obj in enumerate(
            _expect_list(
                row.get("capability_endpoint_functions", []),
                field_name=f"api_ontology[{row_index}].capability_endpoint_functions",
            )
        )
    )
    graphs = tuple(
        _decode_graph_row(
            row_index=row_index, api_name=api_name, item=obj, item_index=index
        )
        for index, obj in enumerate(
            _expect_list(
                row.get("graphs", []), field_name=f"api_ontology[{row_index}].graphs"
            )
        )
    )
    graph_functions = tuple(
        _decode_graph_function_row(
            row_index=row_index, api_name=api_name, item=obj, item_index=index
        )
        for index, obj in enumerate(
            _expect_list(
                row.get("graph_functions", []),
                field_name=f"api_ontology[{row_index}].graph_functions",
            )
        )
    )
    graph_projections = tuple(
        _decode_graph_projection_row(
            row_index=row_index, api_name=api_name, item=obj, item_index=index
        )
        for index, obj in enumerate(
            _expect_list(
                row.get("graph_projections", []),
                field_name=f"api_ontology[{row_index}].graph_projections",
            )
        )
    )
    graph_capabilities = tuple(
        _decode_graph_capability_row(
            row_index=row_index, api_name=api_name, item=obj, item_index=index
        )
        for index, obj in enumerate(
            _expect_list(
                row.get("graph_capabilities", []),
                field_name=f"api_ontology[{row_index}].graph_capabilities",
            )
        )
    )
    graph_capability_functions = tuple(
        _decode_graph_capability_function_row(
            row_index=row_index, api_name=api_name, item=obj, item_index=index
        )
        for index, obj in enumerate(
            _expect_list(
                row.get("graph_capability_functions", []),
                field_name=f"api_ontology[{row_index}].graph_capability_functions",
            )
        )
    )

    return APIOntologyPlan(
        api=APIOntologyApiOperation(
            name=api_name, description=api_description, source_path=api_source_path
        ),
        capabilities=capabilities,
        capability_endpoints=capability_endpoints,
        capability_endpoint_request_configs=capability_endpoint_request_configs,
        capability_endpoint_response_configs=capability_endpoint_response_configs,
        capability_endpoint_stream_configs=capability_endpoint_stream_configs,
        capability_endpoint_stream_event_configs=capability_endpoint_stream_event_configs,
        capability_endpoint_functions=capability_endpoint_functions,
        graphs=graphs,
        graph_functions=graph_functions,
        graph_projections=graph_projections,
        graph_capabilities=graph_capabilities,
        graph_capability_functions=graph_capability_functions,
    )


def _decode_capability_row(
    *,
    row_index: int,
    api_name: str,
    item: object,
    item_index: int,
) -> APIOntologyCapabilityOperation:
    row = _expect_mapping(
        item, field_name=f"api_ontology[{row_index}].capabilities[{item_index}]"
    )
    row_api_name = _required_str_token(
        row.get("api_name"),
        field_name=f"api_ontology[{row_index}].capabilities[{item_index}].api_name",
    )
    if row_api_name != api_name:
        raise ValueError(
            "Invalid api compile plan: capability.api_name must match api.name "
            + f"(api_ontology[{row_index}] api={api_name!r} capability.api_name={row_api_name!r})"
        )
    return APIOntologyCapabilityOperation(
        api_name=row_api_name,
        name=_required_str_token(
            row.get("name"),
            field_name=f"api_ontology[{row_index}].capabilities[{item_index}].name",
        ),
        description=_optional_str_token(
            row.get("description"),
            field_name=f"api_ontology[{row_index}].capabilities[{item_index}].description",
        ),
        source_path=_required_str_token(
            row.get("source_path"),
            field_name=f"api_ontology[{row_index}].capabilities[{item_index}].source_path",
        ),
    )


def _decode_capability_endpoint_row(
    *,
    row_index: int,
    api_name: str,
    item: object,
    item_index: int,
) -> APIOntologyCapabilityEndpointOperation:
    row = _expect_mapping(
        item, field_name=f"api_ontology[{row_index}].capability_endpoints[{item_index}]"
    )
    row_api_name = _required_str_token(
        row.get("api_name"),
        field_name=f"api_ontology[{row_index}].capability_endpoints[{item_index}].api_name",
    )
    if row_api_name != api_name:
        raise ValueError(
            "Invalid api compile plan: capability_endpoint.api_name must match api.name "
            + f"(api_ontology[{row_index}] api={api_name!r} capability_endpoint.api_name={row_api_name!r})"
        )
    return APIOntologyCapabilityEndpointOperation(
        api_name=row_api_name,
        capability_name=_required_str_token(
            row.get("capability_name"),
            field_name=f"api_ontology[{row_index}].capability_endpoints[{item_index}].capability_name",
        ),
        name=_required_str_token(
            row.get("name"),
            field_name=f"api_ontology[{row_index}].capability_endpoints[{item_index}].name",
        ),
        description=_optional_str_token(
            row.get("description"),
            field_name=f"api_ontology[{row_index}].capability_endpoints[{item_index}].description",
        ),
        source_path=_required_str_token(
            row.get("source_path"),
            field_name=f"api_ontology[{row_index}].capability_endpoints[{item_index}].source_path",
        ),
    )


def _decode_capability_endpoint_request_config_row(
    *,
    row_index: int,
    api_name: str,
    item: object,
    item_index: int,
) -> APIOntologyCapabilityEndpointRequestConfigOperation:
    row = _expect_mapping(
        item,
        field_name=f"api_ontology[{row_index}].capability_endpoint_request_configs[{item_index}]",
    )
    row_api_name = _required_str_token(
        row.get("api_name"),
        field_name=f"api_ontology[{row_index}].capability_endpoint_request_configs[{item_index}].api_name",
    )
    if row_api_name != api_name:
        raise ValueError(
            "Invalid api compile plan: capability_endpoint_request_config.api_name must match api.name "
            + f"(api_ontology[{row_index}] api={api_name!r} "
            + f"capability_endpoint_request_config.api_name={row_api_name!r})"
        )
    return APIOntologyCapabilityEndpointRequestConfigOperation(
        api_name=row_api_name,
        capability_name=_required_str_token(
            row.get("capability_name"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_request_configs[{item_index}].capability_name",
        ),
        endpoint_name=_required_str_token(
            row.get("endpoint_name"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_request_configs[{item_index}].endpoint_name",
        ),
        class_ref=_required_str_token(
            row.get("class_ref"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_request_configs[{item_index}].class_ref",
        ),
        class_config_id=_optional_uuid_token(
            row.get("class_config_id"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_request_configs[{item_index}].class_config_id",
        ),
        description=_optional_str_token(
            row.get("description"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_request_configs[{item_index}].description",
        ),
        source_path=_required_str_token(
            row.get("source_path"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_request_configs[{item_index}].source_path",
        ),
    )


def _decode_capability_endpoint_response_config_row(
    *,
    row_index: int,
    api_name: str,
    item: object,
    item_index: int,
) -> APIOntologyCapabilityEndpointResponseConfigOperation:
    row = _expect_mapping(
        item,
        field_name=f"api_ontology[{row_index}].capability_endpoint_response_configs[{item_index}]",
    )
    row_api_name = _required_str_token(
        row.get("api_name"),
        field_name=f"api_ontology[{row_index}].capability_endpoint_response_configs[{item_index}].api_name",
    )
    if row_api_name != api_name:
        raise ValueError(
            "Invalid api compile plan: capability_endpoint_response_config.api_name must match api.name "
            + f"(api_ontology[{row_index}] api={api_name!r} "
            + f"capability_endpoint_response_config.api_name={row_api_name!r})"
        )
    return APIOntologyCapabilityEndpointResponseConfigOperation(
        api_name=row_api_name,
        capability_name=_required_str_token(
            row.get("capability_name"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_response_configs[{item_index}].capability_name",
        ),
        endpoint_name=_required_str_token(
            row.get("endpoint_name"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_response_configs[{item_index}].endpoint_name",
        ),
        class_ref=_required_str_token(
            row.get("class_ref"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_response_configs[{item_index}].class_ref",
        ),
        class_config_id=_optional_uuid_token(
            row.get("class_config_id"),
            field_name=(
                f"api_ontology[{row_index}].capability_endpoint_response_configs[{item_index}].class_config_id"
            ),
        ),
        description=_optional_str_token(
            row.get("description"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_response_configs[{item_index}].description",
        ),
        source_path=_required_str_token(
            row.get("source_path"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_response_configs[{item_index}].source_path",
        ),
    )


def _decode_capability_endpoint_stream_config_row(
    *,
    row_index: int,
    api_name: str,
    item: object,
    item_index: int,
) -> APIOntologyCapabilityEndpointStreamConfigOperation:
    row = _expect_mapping(
        item,
        field_name=f"api_ontology[{row_index}].capability_endpoint_stream_configs[{item_index}]",
    )
    row_api_name = _required_str_token(
        row.get("api_name"),
        field_name=f"api_ontology[{row_index}].capability_endpoint_stream_configs[{item_index}].api_name",
    )
    if row_api_name != api_name:
        raise ValueError(
            "Invalid api compile plan: capability_endpoint_stream_config.api_name must match api.name "
            + f"(api_ontology[{row_index}] api={api_name!r} "
            + f"capability_endpoint_stream_config.api_name={row_api_name!r})"
        )
    return APIOntologyCapabilityEndpointStreamConfigOperation(
        api_name=row_api_name,
        capability_name=_required_str_token(
            row.get("capability_name"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_stream_configs[{item_index}].capability_name",
        ),
        endpoint_name=_required_str_token(
            row.get("endpoint_name"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_stream_configs[{item_index}].endpoint_name",
        ),
        stream_mode=_required_str_token(
            row.get("stream_mode"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_stream_configs[{item_index}].stream_mode",
        ),
        description=_optional_str_token(
            row.get("description"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_stream_configs[{item_index}].description",
        ),
        source_path=_required_str_token(
            row.get("source_path"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_stream_configs[{item_index}].source_path",
        ),
    )


def _decode_capability_endpoint_stream_event_config_row(
    *,
    row_index: int,
    api_name: str,
    item: object,
    item_index: int,
) -> APIOntologyCapabilityEndpointStreamEventConfigOperation:
    row = _expect_mapping(
        item,
        field_name=f"api_ontology[{row_index}].capability_endpoint_stream_event_configs[{item_index}]",
    )
    row_api_name = _required_str_token(
        row.get("api_name"),
        field_name=f"api_ontology[{row_index}].capability_endpoint_stream_event_configs[{item_index}].api_name",
    )
    if row_api_name != api_name:
        raise ValueError(
            "Invalid api compile plan: capability_endpoint_stream_event_config.api_name must match api.name "
            + f"(api_ontology[{row_index}] api={api_name!r} "
            + f"capability_endpoint_stream_event_config.api_name={row_api_name!r})"
        )
    return APIOntologyCapabilityEndpointStreamEventConfigOperation(
        api_name=row_api_name,
        capability_name=_required_str_token(
            row.get("capability_name"),
            field_name=(
                f"api_ontology[{row_index}].capability_endpoint_stream_event_configs[{item_index}].capability_name"
            ),
        ),
        endpoint_name=_required_str_token(
            row.get("endpoint_name"),
            field_name=(
                f"api_ontology[{row_index}].capability_endpoint_stream_event_configs[{item_index}].endpoint_name"
            ),
        ),
        kind=_required_str_token(
            row.get("kind"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_stream_event_configs[{item_index}].kind",
        ),
        class_ref=_required_str_token(
            row.get("class_ref"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_stream_event_configs[{item_index}].class_ref",
        ),
        class_config_id=_optional_uuid_token(
            row.get("class_config_id"),
            field_name=(
                f"api_ontology[{row_index}].capability_endpoint_stream_event_configs[{item_index}].class_config_id"
            ),
        ),
        description=_optional_str_token(
            row.get("description"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_stream_event_configs[{item_index}].description",
        ),
        source_path=_required_str_token(
            row.get("source_path"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_stream_event_configs[{item_index}].source_path",
        ),
    )


def _decode_capability_endpoint_function_row(
    *,
    row_index: int,
    api_name: str,
    item: object,
    item_index: int,
) -> APIOntologyCapabilityEndpointFunctionOperation:
    row = _expect_mapping(
        item,
        field_name=f"api_ontology[{row_index}].capability_endpoint_functions[{item_index}]",
    )
    row_api_name = _required_str_token(
        row.get("api_name"),
        field_name=f"api_ontology[{row_index}].capability_endpoint_functions[{item_index}].api_name",
    )
    if row_api_name != api_name:
        raise ValueError(
            "Invalid api compile plan: capability_endpoint_function.api_name must match api.name "
            + f"(api_ontology[{row_index}] api={api_name!r} "
            + f"capability_endpoint_function.api_name={row_api_name!r})"
        )
    return APIOntologyCapabilityEndpointFunctionOperation(
        api_name=row_api_name,
        capability_name=_required_str_token(
            row.get("capability_name"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_functions[{item_index}].capability_name",
        ),
        endpoint_name=_required_str_token(
            row.get("endpoint_name"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_functions[{item_index}].endpoint_name",
        ),
        name=_required_str_token(
            row.get("name"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_functions[{item_index}].name",
        ),
        graph_target=_required_str_token(
            row.get("graph_target"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_functions[{item_index}].graph_target",
        ),
        graph_capability_function_name=_required_str_token(
            row.get("graph_capability_function_name"),
            field_name=(
                f"api_ontology[{row_index}].capability_endpoint_functions[{item_index}]"
                + ".graph_capability_function_name"
            ),
        ),
        source_path=_required_str_token(
            row.get("source_path"),
            field_name=f"api_ontology[{row_index}].capability_endpoint_functions[{item_index}].source_path",
        ),
    )


def _decode_graph_row(
    *, row_index: int, api_name: str, item: object, item_index: int
) -> APIOntologyGraphOperation:
    row = _expect_mapping(
        item, field_name=f"api_ontology[{row_index}].graphs[{item_index}]"
    )
    row_api_name = _required_str_token(
        row.get("api_name"),
        field_name=f"api_ontology[{row_index}].graphs[{item_index}].api_name",
    )
    if row_api_name != api_name:
        raise ValueError(
            "Invalid api compile plan: graph.api_name must match api.name "
            + f"(api_ontology[{row_index}] api={api_name!r} graph.api_name={row_api_name!r})"
        )
    return APIOntologyGraphOperation(
        api_name=row_api_name,
        target=_required_str_token(
            row.get("target"),
            field_name=f"api_ontology[{row_index}].graphs[{item_index}].target",
        ),
        description=_optional_str_token(
            row.get("description"),
            field_name=f"api_ontology[{row_index}].graphs[{item_index}].description",
        ),
        source_path=_required_str_token(
            row.get("source_path"),
            field_name=f"api_ontology[{row_index}].graphs[{item_index}].source_path",
        ),
    )


def _decode_graph_function_row(
    *,
    row_index: int,
    api_name: str,
    item: object,
    item_index: int,
) -> APIOntologyGraphFunctionOperation:
    row = _expect_mapping(
        item, field_name=f"api_ontology[{row_index}].graph_functions[{item_index}]"
    )
    row_api_name = _required_str_token(
        row.get("api_name"),
        field_name=f"api_ontology[{row_index}].graph_functions[{item_index}].api_name",
    )
    if row_api_name != api_name:
        raise ValueError(
            "Invalid api compile plan: graph_function.api_name must match api.name "
            + f"(api_ontology[{row_index}] api={api_name!r} graph_function.api_name={row_api_name!r})"
        )
    return APIOntologyGraphFunctionOperation(
        api_name=row_api_name,
        graph_target=_required_str_token(
            row.get("graph_target"),
            field_name=f"api_ontology[{row_index}].graph_functions[{item_index}].graph_target",
        ),
        target=_required_str_token(
            row.get("target"),
            field_name=f"api_ontology[{row_index}].graph_functions[{item_index}].target",
        ),
        source_path=_required_str_token(
            row.get("source_path"),
            field_name=f"api_ontology[{row_index}].graph_functions[{item_index}].source_path",
        ),
    )


def _decode_graph_projection_row(
    *,
    row_index: int,
    api_name: str,
    item: object,
    item_index: int,
) -> APIOntologyGraphProjectionOperation:
    row = _expect_mapping(
        item, field_name=f"api_ontology[{row_index}].graph_projections[{item_index}]"
    )
    row_api_name = _required_str_token(
        row.get("api_name"),
        field_name=f"api_ontology[{row_index}].graph_projections[{item_index}].api_name",
    )
    if row_api_name != api_name:
        raise ValueError(
            "Invalid api compile plan: graph_projection.api_name must match api.name "
            + f"(api_ontology[{row_index}] api={api_name!r} graph_projection.api_name={row_api_name!r})"
        )
    return APIOntologyGraphProjectionOperation(
        api_name=row_api_name,
        graph_target=_required_str_token(
            row.get("graph_target"),
            field_name=f"api_ontology[{row_index}].graph_projections[{item_index}].graph_target",
        ),
        target=_required_str_token(
            row.get("target"),
            field_name=f"api_ontology[{row_index}].graph_projections[{item_index}].target",
        ),
        description=_optional_str_token(
            row.get("description"),
            field_name=f"api_ontology[{row_index}].graph_projections[{item_index}].description",
        ),
        source_path=_required_str_token(
            row.get("source_path"),
            field_name=f"api_ontology[{row_index}].graph_projections[{item_index}].source_path",
        ),
    )


def _decode_graph_capability_row(
    *,
    row_index: int,
    api_name: str,
    item: object,
    item_index: int,
) -> APIOntologyGraphCapabilityOperation:
    row = _expect_mapping(
        item, field_name=f"api_ontology[{row_index}].graph_capabilities[{item_index}]"
    )
    row_api_name = _required_str_token(
        row.get("api_name"),
        field_name=f"api_ontology[{row_index}].graph_capabilities[{item_index}].api_name",
    )
    if row_api_name != api_name:
        raise ValueError(
            "Invalid api compile plan: graph_capability.api_name must match api.name "
            + f"(api_ontology[{row_index}] api={api_name!r} graph_capability.api_name={row_api_name!r})"
        )
    return APIOntologyGraphCapabilityOperation(
        api_name=row_api_name,
        graph_target=_required_str_token(
            row.get("graph_target"),
            field_name=f"api_ontology[{row_index}].graph_capabilities[{item_index}].graph_target",
        ),
        capability_name=_required_str_token(
            row.get("capability_name"),
            field_name=f"api_ontology[{row_index}].graph_capabilities[{item_index}].capability_name",
        ),
        description=_optional_str_token(
            row.get("description"),
            field_name=f"api_ontology[{row_index}].graph_capabilities[{item_index}].description",
        ),
        source_path=_required_str_token(
            row.get("source_path"),
            field_name=f"api_ontology[{row_index}].graph_capabilities[{item_index}].source_path",
        ),
    )


def _decode_graph_capability_function_row(
    *,
    row_index: int,
    api_name: str,
    item: object,
    item_index: int,
) -> APIOntologyGraphCapabilityFunctionOperation:
    row = _expect_mapping(
        item,
        field_name=f"api_ontology[{row_index}].graph_capability_functions[{item_index}]",
    )
    row_api_name = _required_str_token(
        row.get("api_name"),
        field_name=f"api_ontology[{row_index}].graph_capability_functions[{item_index}].api_name",
    )
    if row_api_name != api_name:
        raise ValueError(
            "Invalid api compile plan: graph_capability_function.api_name must match api.name "
            + f"(api_ontology[{row_index}] api={api_name!r} graph_capability_function.api_name={row_api_name!r})"
        )
    return APIOntologyGraphCapabilityFunctionOperation(
        api_name=row_api_name,
        graph_target=_required_str_token(
            row.get("graph_target"),
            field_name=f"api_ontology[{row_index}].graph_capability_functions[{item_index}].graph_target",
        ),
        capability_name=_required_str_token(
            row.get("capability_name"),
            field_name=f"api_ontology[{row_index}].graph_capability_functions[{item_index}].capability_name",
        ),
        name=_required_str_token(
            row.get("name"),
            field_name=f"api_ontology[{row_index}].graph_capability_functions[{item_index}].name",
        ),
        target=_required_str_token(
            row.get("target"),
            field_name=f"api_ontology[{row_index}].graph_capability_functions[{item_index}].target",
        ),
        source_path=_required_str_token(
            row.get("source_path"),
            field_name=f"api_ontology[{row_index}].graph_capability_functions[{item_index}].source_path",
        ),
    )


def _expect_mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Invalid api compile plan: {field_name} must be an object")
    return cast(Mapping[str, object], value)


def _expect_list(value: object, *, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"Invalid api compile plan: {field_name} must be a list")
    return cast(list[object], value)


def _required_str_token(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Invalid api compile plan: {field_name} must be a string")
    token = value.strip()
    if not token:
        raise ValueError(f"Invalid api compile plan: {field_name} must be non-empty")
    return token


def _optional_str_token(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(
            f"Invalid api compile plan: {field_name} must be a string or null"
        )
    token = value.strip()
    return token or None


def _optional_uuid_token(value: object, *, field_name: str) -> UUID | None:
    token = _optional_str_token(value, field_name=field_name)
    if token is None:
        return None
    try:
        return UUID(token)
    except ValueError as exc:
        raise ValueError(
            f"Invalid api compile plan: {field_name} must be a UUID or null"
        ) from exc


__all__ = [
    "APIOntologyApiOperation",
    "APIOntologyCapabilityOperation",
    "APIOntologyCapabilityEndpointOperation",
    "APIOntologyCapabilityEndpointFunctionOperation",
    "APIOntologyGraphOperation",
    "APIOntologyGraphFunctionOperation",
    "APIOntologyGraphProjectionOperation",
    "APIOntologyGraphCapabilityOperation",
    "APIOntologyGraphCapabilityFunctionOperation",
    "APIOntologyPlan",
    "build_api_ontology_plans",
    "decode_api_ontology_plan_payload",
    "encode_api_ontology_plan_payload",
]
