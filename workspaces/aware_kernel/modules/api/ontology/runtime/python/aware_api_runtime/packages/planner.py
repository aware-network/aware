from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from importlib import import_module
from uuid import UUID

from aware_meta.materialization.schemas import (
    API_PUBLIC_PACKAGE_KIND,
    API_PUBLIC_PACKAGE_RENDERER_PROFILE,
    API_SERVICE_PROTOCOL_KIND,
    API_SERVICE_PROTOCOL_RENDERER_PROFILE,
    MaterializationSource,
)
from aware_meta.attribute.config.type_descriptor_helpers import (
    resolve_type_class_config_id,
    resolve_type_info,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_orm.registry import ORMModelRegistry

from ..ontology_graph.ontology import (
    APIOntologyCapabilityEndpointFunctionOperation,
    APIOntologyCapabilityEndpointOperation,
    APIOntologyCapabilityEndpointRequestConfigOperation,
    APIOntologyCapabilityEndpointResponseConfigOperation,
    APIOntologyCapabilityEndpointStreamConfigOperation,
    APIOntologyCapabilityEndpointStreamEventConfigOperation,
    APIOntologyPlan,
)
from .models import (
    ApiProductBackendHandoff,
    ApiPublicPackageApiPlan,
    ApiPublicPackageCapabilityPlan,
    ApiPublicPackageEndpointPlan,
    ApiPublicPackagePlan,
    ApiPublicPackageRequestPlan,
    ApiPublicPackageResponsePlan,
    ApiPublicPackageStreamEventPlan,
    ApiPublicPackageStreamPlan,
    ApiServiceProtocolApiPlan,
    ApiServiceProtocolCapabilityPlan,
    ApiServiceProtocolEndpointFunctionPlan,
    ApiServiceProtocolEndpointPlan,
    ApiServiceProtocolPlan,
)

_API_PUBLIC_PACKAGE_SCHEMA_VERSION = 1
_API_SERVICE_PROTOCOL_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class _EndpointContractPlan:
    request: ApiPublicPackageRequestPlan
    response: ApiPublicPackageResponsePlan | None
    stream: ApiPublicPackageStreamPlan | None


def build_api_public_package_plan(
    *,
    package_name: str,
    fqn_prefix: str,
    api_ontology: Sequence[APIOntologyPlan],
) -> ApiPublicPackagePlan:
    api_plans = tuple(
        _build_api_plan(plan=plan)
        for plan in sorted(
            api_ontology,
            key=lambda item: (item.api.name.casefold(), item.api.source_path),
        )
    )
    return ApiPublicPackagePlan(
        schema_version=_API_PUBLIC_PACKAGE_SCHEMA_VERSION,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        backend_handoff=ApiProductBackendHandoff(
            materialization_source=MaterializationSource.api,
            aware_package_kind=API_PUBLIC_PACKAGE_KIND,
            expected_renderer_profile=API_PUBLIC_PACKAGE_RENDERER_PROFILE,
        ),
        apis=api_plans,
    )


def build_api_service_protocol_plan(
    *,
    package_name: str,
    fqn_prefix: str,
    api_ontology: Sequence[APIOntologyPlan],
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
) -> ApiServiceProtocolPlan:
    class_nodes_by_id = _index_service_protocol_accessible_class_nodes(
        accessible_graphs=accessible_graphs
    )
    api_plans = tuple(
        _build_service_protocol_api_plan(
            plan=plan,
            class_nodes_by_id=class_nodes_by_id,
        )
        for plan in sorted(
            api_ontology,
            key=lambda item: (item.api.name.casefold(), item.api.source_path),
        )
    )
    return ApiServiceProtocolPlan(
        schema_version=_API_SERVICE_PROTOCOL_SCHEMA_VERSION,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        backend_handoff=ApiProductBackendHandoff(
            materialization_source=MaterializationSource.api,
            aware_package_kind=API_SERVICE_PROTOCOL_KIND,
            expected_renderer_profile=API_SERVICE_PROTOCOL_RENDERER_PROFILE,
        ),
        apis=api_plans,
    )


def _build_api_plan(*, plan: APIOntologyPlan) -> ApiPublicPackageApiPlan:
    endpoint_rows_by_key = {
        (row.capability_name, row.name): row for row in plan.capability_endpoints
    }
    request_rows_by_key = {
        (row.capability_name, row.endpoint_name): row
        for row in plan.capability_endpoint_request_configs
    }
    response_rows_by_key = {
        (row.capability_name, row.endpoint_name): row
        for row in plan.capability_endpoint_response_configs
    }
    stream_rows_by_key = {
        (row.capability_name, row.endpoint_name): row
        for row in plan.capability_endpoint_stream_configs
    }
    stream_event_rows_by_key: dict[
        tuple[str, str], list[APIOntologyCapabilityEndpointStreamEventConfigOperation]
    ] = defaultdict(list)
    for row in plan.capability_endpoint_stream_event_configs:
        stream_event_rows_by_key[(row.capability_name, row.endpoint_name)].append(row)

    endpoint_keys_by_capability: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for key in endpoint_rows_by_key:
        endpoint_keys_by_capability[key[0]].append(key)

    capability_plans: list[ApiPublicPackageCapabilityPlan] = []
    for capability in sorted(
        plan.capabilities,
        key=lambda item: (item.name.casefold(), item.source_path),
    ):
        endpoint_plans: list[ApiPublicPackageEndpointPlan] = []
        for endpoint_key in sorted(
            endpoint_keys_by_capability.get(capability.name, ()),
            key=lambda item: item[1].casefold(),
        ):
            endpoint = endpoint_rows_by_key[endpoint_key]
            request = request_rows_by_key.get(endpoint_key)
            if request is None:
                raise RuntimeError(
                    "Invalid public package plan input: endpoint is missing request config "
                    + (
                        f"(api={plan.api.name!r}, capability={endpoint.capability_name!r}, "
                        + f"endpoint={endpoint.name!r})"
                    )
                )

            response = response_rows_by_key.get(endpoint_key)
            stream = stream_rows_by_key.get(endpoint_key)
            contract = _build_endpoint_contract_plan(
                api_name=plan.api.name,
                endpoint=endpoint,
                request=request,
                response=response,
                stream=stream,
                stream_event_rows=stream_event_rows_by_key.get(endpoint_key, ()),
            )

            endpoint_plans.append(
                ApiPublicPackageEndpointPlan(
                    api_name=plan.api.name,
                    capability_name=endpoint.capability_name,
                    name=endpoint.name,
                    discriminant=_build_endpoint_discriminant(
                        api_name=plan.api.name,
                        capability_name=endpoint.capability_name,
                        endpoint_name=endpoint.name,
                    ),
                    description=endpoint.description,
                    source_path=endpoint.source_path,
                    request=contract.request,
                    response=contract.response,
                    stream=contract.stream,
                )
            )

        capability_plans.append(
            ApiPublicPackageCapabilityPlan(
                api_name=plan.api.name,
                name=capability.name,
                description=capability.description,
                source_path=capability.source_path,
                endpoints=tuple(endpoint_plans),
            )
        )

    return ApiPublicPackageApiPlan(
        name=plan.api.name,
        description=plan.api.description,
        source_path=plan.api.source_path,
        capabilities=tuple(capability_plans),
    )


def _build_service_protocol_api_plan(
    *,
    plan: APIOntologyPlan,
    class_nodes_by_id: dict[UUID, ObjectConfigGraphNode],
) -> ApiServiceProtocolApiPlan:
    endpoint_rows_by_key = {
        (row.capability_name, row.name): row for row in plan.capability_endpoints
    }
    request_rows_by_key = {
        (row.capability_name, row.endpoint_name): row
        for row in plan.capability_endpoint_request_configs
    }
    response_rows_by_key = {
        (row.capability_name, row.endpoint_name): row
        for row in plan.capability_endpoint_response_configs
    }
    stream_rows_by_key = {
        (row.capability_name, row.endpoint_name): row
        for row in plan.capability_endpoint_stream_configs
    }
    stream_event_rows_by_key: dict[
        tuple[str, str], list[APIOntologyCapabilityEndpointStreamEventConfigOperation]
    ] = defaultdict(list)
    for row in plan.capability_endpoint_stream_event_configs:
        stream_event_rows_by_key[(row.capability_name, row.endpoint_name)].append(row)
    function_rows_by_key: dict[
        tuple[str, str], list[APIOntologyCapabilityEndpointFunctionOperation]
    ] = defaultdict(list)
    for row in plan.capability_endpoint_functions:
        function_rows_by_key[(row.capability_name, row.endpoint_name)].append(row)
    graph_capability_function_python_ref_by_key: dict[tuple[str, str], str] = {}
    for row in plan.graph_capability_functions:
        key = (row.graph_target, row.name)
        existing_target = graph_capability_function_python_ref_by_key.get(key)
        if existing_target is not None and existing_target != row.target:
            raise RuntimeError(
                "Invalid service protocol plan input: graph capability function name is ambiguous "
                "within one graph target "
                + (
                    f"(api={plan.api.name!r}, graph_target={row.graph_target!r}, "
                    f"graph_capability_function_name={row.name!r}, "
                    f"targets={existing_target!r}/{row.target!r})"
                )
            )
        graph_capability_function_python_ref_by_key[key] = row.target

    endpoint_keys_by_capability: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for key in endpoint_rows_by_key:
        endpoint_keys_by_capability[key[0]].append(key)

    capability_plans: list[ApiServiceProtocolCapabilityPlan] = []
    for capability in sorted(
        plan.capabilities,
        key=lambda item: (item.name.casefold(), item.source_path),
    ):
        endpoint_plans: list[ApiServiceProtocolEndpointPlan] = []
        for endpoint_key in sorted(
            endpoint_keys_by_capability.get(capability.name, ()),
            key=lambda item: item[1].casefold(),
        ):
            endpoint = endpoint_rows_by_key[endpoint_key]
            request = request_rows_by_key.get(endpoint_key)
            if request is None:
                raise RuntimeError(
                    "Invalid service protocol plan input: endpoint is missing request config "
                    + (
                        f"(api={plan.api.name!r}, capability={endpoint.capability_name!r}, "
                        + f"endpoint={endpoint.name!r})"
                    )
                )

            response = response_rows_by_key.get(endpoint_key)
            stream = stream_rows_by_key.get(endpoint_key)
            contract = _build_endpoint_contract_plan(
                api_name=plan.api.name,
                endpoint=endpoint,
                request=request,
                response=response,
                stream=stream,
                stream_event_rows=stream_event_rows_by_key.get(endpoint_key, ()),
            )
            endpoint_ref = _build_endpoint_discriminant(
                api_name=plan.api.name,
                capability_name=endpoint.capability_name,
                endpoint_name=endpoint.name,
            )
            endpoint_plans.append(
                ApiServiceProtocolEndpointPlan(
                    api_name=plan.api.name,
                    capability_name=endpoint.capability_name,
                    name=endpoint.name,
                    endpoint_ref=endpoint_ref,
                    discriminant=endpoint_ref,
                    description=endpoint.description,
                    source_path=endpoint.source_path,
                    request=contract.request,
                    response=contract.response,
                    stream=contract.stream,
                    fulfillment_bindings=tuple(
                        ApiServiceProtocolEndpointFunctionPlan(
                            name=row.name,
                            graph_target=row.graph_target,
                            graph_capability_function_name=row.graph_capability_function_name,
                            graph_function_python_ref=graph_function_python_ref,
                            graph_function_runtime_target=(
                                _resolve_graph_function_runtime_target(
                                    graph_function_python_ref=graph_function_python_ref,
                                    class_nodes_by_id=class_nodes_by_id,
                                )
                                if class_nodes_by_id
                                else None
                            ),
                            call_target_kind=(
                                _resolve_graph_function_call_target_kind(
                                    graph_function_python_ref=graph_function_python_ref,
                                    class_nodes_by_id=class_nodes_by_id,
                                )
                                if class_nodes_by_id
                                else None
                            ),
                            exact_output_field_name=(
                                _resolve_graph_function_exact_output_field_name(
                                    graph_function_python_ref=graph_function_python_ref,
                                    class_nodes_by_id=class_nodes_by_id,
                                )
                                if class_nodes_by_id
                                else None
                            ),
                            source_path=row.source_path,
                        )
                        for row, graph_function_python_ref in (
                            (
                                row,
                                _resolve_graph_function_python_ref(
                                    api_name=plan.api.name,
                                    graph_target=row.graph_target,
                                    graph_capability_function_name=row.graph_capability_function_name,
                                    graph_capability_function_python_ref_by_key=(
                                        graph_capability_function_python_ref_by_key
                                    ),
                                ),
                            )
                            for row in sorted(
                                function_rows_by_key.get(endpoint_key, ()),
                                key=lambda item: (
                                    item.name.casefold(),
                                    item.graph_target,
                                    item.graph_capability_function_name,
                                    item.source_path,
                                ),
                            )
                        )
                    ),
                )
            )

        capability_plans.append(
            ApiServiceProtocolCapabilityPlan(
                api_name=plan.api.name,
                name=capability.name,
                description=capability.description,
                source_path=capability.source_path,
                endpoints=tuple(endpoint_plans),
            )
        )

    return ApiServiceProtocolApiPlan(
        name=plan.api.name,
        description=plan.api.description,
        source_path=plan.api.source_path,
        capabilities=tuple(capability_plans),
    )


def _resolve_graph_function_python_ref(
    *,
    api_name: str,
    graph_target: str,
    graph_capability_function_name: str,
    graph_capability_function_python_ref_by_key: dict[tuple[str, str], str],
) -> str:
    target = graph_capability_function_python_ref_by_key.get(
        (graph_target, graph_capability_function_name)
    )
    if target is None:
        raise RuntimeError(
            "Invalid service protocol plan input: endpoint-function graph callable target "
            "could not be resolved from API graph truth "
            + (
                f"(api={api_name!r}, graph_target={graph_target!r}, "
                f"graph_capability_function_name={graph_capability_function_name!r})"
            )
        )
    return target


def _index_service_protocol_accessible_class_nodes(
    *,
    accessible_graphs: Sequence[ObjectConfigGraph],
) -> dict[UUID, ObjectConfigGraphNode]:
    class_nodes_by_id: dict[UUID, ObjectConfigGraphNode] = {}
    for graph in accessible_graphs:
        for node in graph.object_config_graph_nodes:
            if (
                node.type == ObjectConfigGraphNodeType.class_
                and node.class_config is not None
            ):
                class_nodes_by_id[node.class_config.id] = node
    return class_nodes_by_id


def _resolve_graph_function_runtime_target(
    *,
    graph_function_python_ref: str,
    class_nodes_by_id: dict[UUID, ObjectConfigGraphNode],
) -> str:
    target = graph_function_python_ref.strip()
    class_ref, separator, function_name = target.rpartition(".")
    if not class_ref or not separator or not function_name:
        raise RuntimeError(
            "Invalid service protocol plan input: graph_function_python_ref must include a function path "
            + f"(got {graph_function_python_ref!r})"
        )

    class_config = _resolve_graph_function_runtime_class_config(
        class_ref=class_ref,
        class_nodes_by_id=class_nodes_by_id,
        graph_function_python_ref=graph_function_python_ref,
    )
    function_config = _resolve_graph_function_runtime_function_config(
        class_config=class_config,
        function_name=function_name,
        graph_function_python_ref=graph_function_python_ref,
    )
    class_fqn = (class_config.class_fqn or "").strip()
    if not class_fqn:
        raise RuntimeError(
            "Invalid service protocol plan input: resolved ClassConfig is missing class_fqn "
            + f"(graph_function_python_ref={graph_function_python_ref!r})"
        )
    return f"{class_fqn}.{function_config.name}"


def _resolve_graph_function_call_target_kind(
    *,
    graph_function_python_ref: str,
    class_nodes_by_id: dict[UUID, ObjectConfigGraphNode],
) -> str:
    target = graph_function_python_ref.strip()
    class_ref, separator, function_name = target.rpartition(".")
    if not class_ref or not separator or not function_name:
        raise RuntimeError(
            "Invalid service protocol plan input: graph_function_python_ref must include a function path "
            + f"(got {graph_function_python_ref!r})"
        )
    class_config = _resolve_graph_function_runtime_class_config(
        class_ref=class_ref,
        class_nodes_by_id=class_nodes_by_id,
        graph_function_python_ref=graph_function_python_ref,
    )
    function_config = _resolve_graph_function_runtime_function_config(
        class_config=class_config,
        function_name=function_name,
        graph_function_python_ref=graph_function_python_ref,
    )
    if (function_config.verb or "").strip().casefold() == "read":
        raise RuntimeError(
            "Ontology read functions are retired; expose reads through service-owned views instead: "
            + f"graph_function_python_ref={graph_function_python_ref!r}"
        )
    if _function_is_constructor(
        class_config=class_config,
        function_name=function_name,
    ):
        return "constructor"
    return "instance"


def _resolve_graph_function_exact_output_field_name(
    *,
    graph_function_python_ref: str,
    class_nodes_by_id: dict[UUID, ObjectConfigGraphNode],
) -> str | None:
    target = graph_function_python_ref.strip()
    class_ref, separator, function_name = target.rpartition(".")
    if not class_ref or not separator or not function_name:
        raise RuntimeError(
            "Invalid service protocol plan input: graph_function_python_ref must include a function path "
            + f"(got {graph_function_python_ref!r})"
        )
    class_config = _resolve_graph_function_runtime_class_config(
        class_ref=class_ref,
        class_nodes_by_id=class_nodes_by_id,
        graph_function_python_ref=graph_function_python_ref,
    )
    function_config = _resolve_graph_function_runtime_function_config(
        class_config=class_config,
        function_name=function_name,
        graph_function_python_ref=graph_function_python_ref,
    )
    output_edges = sorted(
        (
            edge
            for edge in function_config.function_config_attribute_configs
            if edge.type == FunctionAttributeType.output
            and edge.attribute_config is not None
        ),
        key=lambda item: (item.position, str(item.id)),
    )
    if len(output_edges) != 1:
        return None
    output_attr = output_edges[0].attribute_config
    if output_attr is None or not (output_attr.name or "").strip():
        return None
    type_info = resolve_type_info(output_attr)
    if type_info.is_collection:
        return None
    output_class_config_id = resolve_type_class_config_id(output_attr)
    if output_class_config_id is None or output_class_config_id != class_config.id:
        return None
    return str(output_attr.name).strip()


def _resolve_graph_function_runtime_class_config(
    *,
    class_ref: str,
    class_nodes_by_id: dict[UUID, ObjectConfigGraphNode],
    graph_function_python_ref: str,
) -> ClassConfig:
    matches = tuple(
        node.class_config
        for node in class_nodes_by_id.values()
        if node.class_config is not None
        and _service_protocol_graph_class_matches(
            class_config=node.class_config, target=class_ref
        )
    )
    unique_matches = _unique_class_configs(matches=matches)
    if not unique_matches:
        raise RuntimeError(
            "Invalid service protocol plan input: could not resolve runtime ClassConfig from graph_function_python_ref "
            + f"(graph_function_python_ref={graph_function_python_ref!r})"
        )
    if len(unique_matches) != 1:
        raise RuntimeError(
            "Invalid service protocol plan input: ambiguous runtime ClassConfig matches for graph_function_python_ref "
            + f"(graph_function_python_ref={graph_function_python_ref!r})"
        )
    return unique_matches[0]


def _resolve_graph_function_runtime_function_config(
    *,
    class_config: ClassConfig,
    function_name: str,
    graph_function_python_ref: str,
) -> FunctionConfig:
    matches = tuple(
        link.function_config
        for link in class_config.class_config_function_configs
        if link.function_config is not None
        and (link.function_config.name or "").strip() == function_name
    )
    unique_matches = _unique_function_configs(matches=matches)
    if not unique_matches:
        raise RuntimeError(
            "Invalid service protocol plan input: could not resolve runtime FunctionConfig "
            "from graph_function_python_ref "
            + f"(graph_function_python_ref={graph_function_python_ref!r})"
        )
    if len(unique_matches) != 1:
        raise RuntimeError(
            "Invalid service protocol plan input: ambiguous runtime FunctionConfig matches "
            "for graph_function_python_ref "
            + f"(graph_function_python_ref={graph_function_python_ref!r})"
        )
    return unique_matches[0]


def _function_is_constructor(
    *,
    class_config: ClassConfig,
    function_name: str,
) -> bool:
    link_matches = [
        link
        for link in class_config.class_config_function_configs
        if link.function_config is not None
        and (link.function_config.name or "").strip() == function_name
    ]
    if any(bool(link.is_constructor) for link in link_matches):
        return True
    orm_class = ORMModelRegistry.get_class_by_class_config_id(class_config.id)
    if orm_class is None:
        return False
    module = import_module(orm_class.__module__)
    functions = getattr(module, "FUNCTIONS", None)
    if not isinstance(functions, dict):
        return False
    class_functions = functions.get(orm_class.__name__)
    if not isinstance(class_functions, dict):
        return False
    function_payload = class_functions.get(function_name)
    if not isinstance(function_payload, dict):
        return False
    canonical = function_payload.get("canonical")
    if not isinstance(canonical, dict):
        return False
    return bool(canonical.get("is_constructor"))


def _unique_class_configs(
    *, matches: Sequence[ClassConfig | None]
) -> tuple[ClassConfig, ...]:
    unique_by_id: dict[UUID, ClassConfig] = {}
    for class_config in matches:
        if class_config is None:
            continue
        unique_by_id[class_config.id] = class_config
    return tuple(unique_by_id[key] for key in sorted(unique_by_id))


def _unique_function_configs(
    *, matches: Sequence[FunctionConfig | None]
) -> tuple[FunctionConfig, ...]:
    unique_by_id: dict[UUID, FunctionConfig] = {}
    for function_config in matches:
        if function_config is None:
            continue
        unique_by_id[function_config.id] = function_config
    return tuple(unique_by_id[key] for key in sorted(unique_by_id))


def _service_protocol_graph_class_matches(
    *, class_config: ClassConfig, target: str
) -> bool:
    target_variants = _normalized_variants(target)
    actual_variants = _normalized_variants(class_config.class_fqn)
    actual_variants.add(_normalize_token(class_config.name))
    actual_variants.add(_leaf_token(class_config.class_fqn))
    actual_variants.add(_leaf_token(class_config.name))

    for target_variant in target_variants:
        if target_variant in actual_variants:
            return True
        if any(actual.endswith(f".{target_variant}") for actual in actual_variants):
            return True
    return False


def _normalize_token(value: str | None) -> str:
    return (value or "").strip().casefold()


def _leaf_token(value: str | None) -> str:
    normalized = _normalize_token(value)
    if "." not in normalized:
        return normalized
    return normalized.rsplit(".", 1)[-1]


def _normalized_variants(value: str | None) -> set[str]:
    normalized = _normalize_token(value)
    if not normalized:
        return set()

    variants = {normalized}
    parts = [part for part in normalized.split(".") if part]
    if "default" in parts[1:-1]:
        variants.add(".".join(part for part in parts if part != "default"))
    return {variant for variant in variants if variant}


def _build_endpoint_contract_plan(
    *,
    api_name: str,
    endpoint: APIOntologyCapabilityEndpointOperation,
    request: APIOntologyCapabilityEndpointRequestConfigOperation,
    response: APIOntologyCapabilityEndpointResponseConfigOperation | None,
    stream: APIOntologyCapabilityEndpointStreamConfigOperation | None,
    stream_event_rows: Sequence[
        APIOntologyCapabilityEndpointStreamEventConfigOperation
    ],
) -> _EndpointContractPlan:
    stream_plan = None
    if stream is not None:
        event_plans = tuple(
            ApiPublicPackageStreamEventPlan(
                kind=row.kind,
                class_ref=row.class_ref,
                description=row.description,
                source_path=row.source_path,
            )
            for row in sorted(
                stream_event_rows,
                key=lambda item: (
                    item.kind.casefold(),
                    item.class_ref,
                    item.source_path,
                ),
            )
        )
        stream_plan = ApiPublicPackageStreamPlan(
            stream_mode=stream.stream_mode,
            description=stream.description,
            source_path=stream.source_path,
            events=event_plans,
        )
    return _EndpointContractPlan(
        request=ApiPublicPackageRequestPlan(
            class_ref=request.class_ref,
            description=request.description,
            source_path=request.source_path,
        ),
        response=(
            ApiPublicPackageResponsePlan(
                class_ref=response.class_ref,
                description=response.description,
                source_path=response.source_path,
            )
            if response is not None
            else None
        ),
        stream=stream_plan,
    )


def _build_endpoint_discriminant(
    *,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
) -> str:
    return ".".join((api_name, capability_name, endpoint_name))


__all__ = ["build_api_public_package_plan", "build_api_service_protocol_plan"]
