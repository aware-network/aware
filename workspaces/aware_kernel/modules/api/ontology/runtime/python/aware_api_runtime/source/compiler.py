from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from tree_sitter import Node, Parser

from ..models import (
    APICapabilityEndpointOwnership,
    APICapabilityEndpointFunctionOwnership,
    APICapabilityEndpointRequestConfigOwnership,
    APICapabilityEndpointResponseConfigOwnership,
    APICapabilityEndpointStreamConfigOwnership,
    APICapabilityEndpointStreamEventConfigOwnership,
    APICapabilityOwnership,
    APIGraphCapabilityFunctionOwnership,
    APIGraphCapabilityOwnership,
    APIGraphOwnership,
    APIGraphProjectionOwnership,
    APIOwnership,
    BindingMapTruth,
    ProjectionOwnedClassTruth,
)
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

_VALID_STREAM_MODES = frozenset({"server", "client", "bidirectional"})
_VALID_STREAM_EVENT_KINDS = frozenset(
    {"snapshot", "delta", "notice", "complete", "error"}
)


def load_api_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    projection_truth_by_name: (
        dict[str, dict[str, ProjectionOwnedClassTruth]] | None
    ) = None,
    binding_truth_by_ref: dict[tuple[str, str], BindingMapTruth] | None = None,
) -> tuple[APIOwnership, ...]:
    source_texts: dict[Path, str] = {}
    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="api source")
        source_texts[relpath] = source_path.read_text(encoding="utf-8")
    return load_api_ownership_from_source_texts(
        package_root=package_root,
        source_texts=source_texts,
        projection_truth_by_name=projection_truth_by_name,
        binding_truth_by_ref=binding_truth_by_ref,
    )


def load_api_graph_targets_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
) -> tuple[str, ...]:
    source_texts: dict[Path, str] = {}
    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="api source")
        source_texts[relpath] = source_path.read_text(encoding="utf-8")
    return load_api_graph_targets_from_source_texts(
        package_root=package_root,
        source_texts=source_texts,
    )


def load_api_graph_targets_from_source_texts(
    *,
    package_root: Path,
    source_texts: Mapping[Path, str],
) -> tuple[str, ...]:
    parser = Parser(language=AWARE_LANGUAGE)
    targets: set[str] = set()
    for relpath, source_text in source_texts.items():
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="api source")
        tree = parser.parse(source_text.encode("utf-8"))
        for node in tree.root_node.named_children:
            if node.type != "api_def":
                continue
            for child in _iter_api_children(node=node):
                if child.type != "api_graph_def":
                    continue
                graph_target = _qualified_text(child.child_by_field_name("graph"))
                if graph_target:
                    targets.add(graph_target)
    return tuple(sorted(targets, key=str.casefold))


def load_api_ownership_from_source_texts(
    *,
    package_root: Path,
    source_texts: Mapping[Path, str],
    projection_truth_by_name: (
        dict[str, dict[str, ProjectionOwnedClassTruth]] | None
    ) = None,
    binding_truth_by_ref: dict[tuple[str, str], BindingMapTruth] | None = None,
) -> tuple[APIOwnership, ...]:
    parser = Parser(language=AWARE_LANGUAGE)
    api_by_name: dict[str, APIOwnership] = {}

    for relpath, source_text in source_texts.items():
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="api source")
        source_rel = relpath.as_posix()
        tree = parser.parse(source_text.encode("utf-8"))

        for node in tree.root_node.named_children:
            if node.type != "api_def":
                continue
            api_name = _symbol_key(_field_text(node, "name"))
            if not api_name:
                continue
            if api_name in api_by_name:
                raise ValueError(
                    f"Duplicate api declaration {api_name!r} across api sources"
                )

            capabilities_by_name: dict[str, APICapabilityOwnership] = {}
            graphs_by_target: dict[str, APIGraphOwnership] = {}

            for child in _iter_api_children(node=node):
                if child.type == "api_capability_def":
                    capability = _load_api_capability_definition(
                        node=child,
                        api_name=api_name,
                        source_path=source_path,
                        source_rel=source_rel,
                    )
                    capability_key = capability.name.casefold()
                    if capability_key in capabilities_by_name:
                        raise ValueError(
                            f"API declaration {api_name!r} has duplicate capability {capability.name!r} "
                            + f"in {source_path}"
                        )
                    capabilities_by_name[capability_key] = capability
                    continue

                if child.type == "api_graph_def":
                    graph = _load_api_graph_definition(
                        node=child,
                        api_name=api_name,
                        source_path=source_path,
                        source_rel=source_rel,
                        declared_capability_names=frozenset(capabilities_by_name),
                        projection_truth_by_name=projection_truth_by_name,
                        binding_truth_by_ref=binding_truth_by_ref,
                    )
                    graph_key = graph.target.casefold()
                    if graph_key in graphs_by_target:
                        raise ValueError(
                            f"API declaration {api_name!r} has duplicate graph target {graph.target!r} "
                            + f"in {source_path}"
                        )
                    graphs_by_target[graph_key] = graph

            if not capabilities_by_name:
                raise ValueError(
                    f"API declaration {api_name!r} must include at least one capability in {source_path}"
                )

            capabilities_by_name = _bind_default_endpoint_functions(
                api_name=api_name,
                source_path=source_path,
                capabilities_by_name=capabilities_by_name,
                graphs_by_target=graphs_by_target,
            )

            api_by_name[api_name] = APIOwnership(
                name=api_name,
                source_path=source_rel,
                capabilities=tuple(
                    sorted(
                        capabilities_by_name.values(),
                        key=lambda item: (item.name, item.source_path),
                    )
                ),
                graphs=tuple(
                    sorted(
                        graphs_by_target.values(),
                        key=lambda item: (item.target, item.source_path),
                    )
                ),
            )

    return tuple(
        sorted(api_by_name.values(), key=lambda item: (item.name, item.source_path))
    )


def _load_api_capability_definition(
    *,
    node: Node,
    api_name: str,
    source_path: Path,
    source_rel: str,
) -> APICapabilityOwnership:
    capability_name = _symbol_key(_field_text(node, "capability_name"))
    if not capability_name:
        raise ValueError(
            f"API declaration {api_name!r} has capability with empty name in {source_path}"
        )
    endpoints_by_name: dict[str, APICapabilityEndpointOwnership] = {}
    for child in _iter_api_capability_children(node=node):
        if child.type != "api_capability_endpoint_def":
            continue
        endpoint = _load_api_capability_endpoint_definition(
            node=child,
            api_name=api_name,
            capability_name=capability_name,
            source_path=source_path,
            source_rel=source_rel,
        )
        endpoint_key = endpoint.name.casefold()
        if endpoint_key in endpoints_by_name:
            raise ValueError(
                f"API declaration {api_name!r} capability {capability_name!r} has duplicate endpoint "
                + f"{endpoint.name!r} in {source_path}"
            )
        endpoints_by_name[endpoint_key] = endpoint
    if not endpoints_by_name:
        raise ValueError(
            f"API declaration {api_name!r} capability {capability_name!r} must include at least one endpoint in {source_path}"
        )
    return APICapabilityOwnership(
        name=capability_name,
        source_path=source_rel,
        endpoints=tuple(
            sorted(
                endpoints_by_name.values(),
                key=lambda item: (item.name, item.source_path),
            )
        ),
        description=_extract_block_description(node.child_by_field_name("body")),
    )


def _load_api_capability_endpoint_definition(
    *,
    node: Node,
    api_name: str,
    capability_name: str,
    source_path: Path,
    source_rel: str,
) -> APICapabilityEndpointOwnership:
    endpoint_name = _symbol_key(_field_text(node, "endpoint_name"))
    request_class_ref = _qualified_text(node.child_by_field_name("request"))
    if not endpoint_name:
        raise ValueError(
            f"API declaration {api_name!r} capability {capability_name!r} has endpoint with empty name in {source_path}"
        )
    if not request_class_ref:
        raise ValueError(
            f"API declaration {api_name!r} capability {capability_name!r} endpoint {endpoint_name!r} has empty request "
            + f"class reference in {source_path}"
        )

    body = node.child_by_field_name("body")
    response_config: APICapabilityEndpointResponseConfigOwnership | None = None
    stream_config: APICapabilityEndpointStreamConfigOwnership | None = None
    for child in _iter_api_capability_endpoint_children(node=node):
        if child.type == "api_capability_endpoint_response_def":
            if response_config is not None:
                raise ValueError(
                    f"API declaration {api_name!r} capability {capability_name!r} endpoint {endpoint_name!r} has "
                    + f"multiple response declarations in {source_path}"
                )
            response_config = _load_api_capability_endpoint_response_definition(
                node=child,
                api_name=api_name,
                capability_name=capability_name,
                endpoint_name=endpoint_name,
                source_path=source_path,
                source_rel=source_rel,
            )
            continue
        if child.type == "api_capability_endpoint_stream_def":
            if stream_config is not None:
                raise ValueError(
                    f"API declaration {api_name!r} capability {capability_name!r} endpoint {endpoint_name!r} has "
                    + f"multiple stream declarations in {source_path}"
                )
            stream_config = _load_api_capability_endpoint_stream_definition(
                node=child,
                api_name=api_name,
                capability_name=capability_name,
                endpoint_name=endpoint_name,
                source_path=source_path,
                source_rel=source_rel,
            )

    return APICapabilityEndpointOwnership(
        name=endpoint_name,
        source_path=source_rel,
        request_config=APICapabilityEndpointRequestConfigOwnership(
            class_ref=request_class_ref,
            source_path=source_rel,
            response_config=response_config,
            stream_config=stream_config,
        ),
        functions=(),
        description=_extract_block_description(body),
    )


def _load_api_capability_endpoint_response_definition(
    *,
    node: Node,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
    source_path: Path,
    source_rel: str,
) -> APICapabilityEndpointResponseConfigOwnership:
    class_ref = _qualified_text(node.child_by_field_name("response"))
    if not class_ref:
        raise ValueError(
            f"API declaration {api_name!r} capability {capability_name!r} endpoint {endpoint_name!r} has response "
            + f"with empty class reference in {source_path}"
        )
    return APICapabilityEndpointResponseConfigOwnership(
        class_ref=class_ref,
        source_path=source_rel,
    )


def _load_api_capability_endpoint_stream_definition(
    *,
    node: Node,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
    source_path: Path,
    source_rel: str,
) -> APICapabilityEndpointStreamConfigOwnership:
    stream_mode = _normalize_member_token(_field_text(node, "stream_mode"))
    if stream_mode not in _VALID_STREAM_MODES:
        raise ValueError(
            f"API declaration {api_name!r} capability {capability_name!r} endpoint {endpoint_name!r} has invalid "
            + f"stream mode {stream_mode!r} in {source_path}"
        )

    event_configs_by_kind: dict[
        str, APICapabilityEndpointStreamEventConfigOwnership
    ] = {}
    for child in _iter_api_capability_endpoint_stream_children(node=node):
        if child.type != "api_capability_endpoint_stream_event_def":
            continue
        event_config = _load_api_capability_endpoint_stream_event_definition(
            node=child,
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
            source_path=source_path,
            source_rel=source_rel,
        )
        event_kind = event_config.kind.casefold()
        if event_kind in event_configs_by_kind:
            raise ValueError(
                f"API declaration {api_name!r} capability {capability_name!r} endpoint {endpoint_name!r} has duplicate "
                + f"stream event kind {event_config.kind!r} in {source_path}"
            )
        event_configs_by_kind[event_kind] = event_config

    return APICapabilityEndpointStreamConfigOwnership(
        stream_mode=stream_mode,
        source_path=source_rel,
        event_configs=tuple(
            sorted(
                event_configs_by_kind.values(),
                key=lambda item: (item.kind, item.class_ref, item.source_path),
            )
        ),
        description=_extract_block_description(node.child_by_field_name("body")),
    )


def _load_api_capability_endpoint_stream_event_definition(
    *,
    node: Node,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
    source_path: Path,
    source_rel: str,
) -> APICapabilityEndpointStreamEventConfigOwnership:
    kind = _normalize_member_token(_field_text(node, "kind"))
    class_ref = _qualified_text(node.child_by_field_name("class"))
    if kind not in _VALID_STREAM_EVENT_KINDS:
        raise ValueError(
            f"API declaration {api_name!r} capability {capability_name!r} endpoint {endpoint_name!r} has invalid "
            + f"stream event kind {kind!r} in {source_path}"
        )
    if not class_ref:
        raise ValueError(
            f"API declaration {api_name!r} capability {capability_name!r} endpoint {endpoint_name!r} stream event "
            + f"{kind!r} has empty class reference in {source_path}"
        )
    return APICapabilityEndpointStreamEventConfigOwnership(
        kind=kind,
        class_ref=class_ref,
        source_path=source_rel,
    )


def _load_api_graph_definition(
    *,
    node: Node,
    api_name: str,
    source_path: Path,
    source_rel: str,
    declared_capability_names: frozenset[str],
    projection_truth_by_name: dict[str, dict[str, ProjectionOwnedClassTruth]] | None,
    binding_truth_by_ref: dict[tuple[str, str], BindingMapTruth] | None,
) -> APIGraphOwnership:
    graph_target = _qualified_text(node.child_by_field_name("graph"))
    if not graph_target:
        raise ValueError(
            f"API declaration {api_name!r} has graph with empty target in {source_path}"
        )

    projections_by_target: dict[str, APIGraphProjectionOwnership] = {}
    capabilities_by_name: dict[str, APIGraphCapabilityOwnership] = {}

    for child in _iter_api_graph_children(node=node):
        if child.type == "api_graph_projection_def":
            projection = _load_api_graph_projection_definition(
                node=child,
                api_name=api_name,
                graph_target=graph_target,
                source_path=source_path,
                source_rel=source_rel,
                projection_truth_by_name=projection_truth_by_name,
                binding_truth_by_ref=binding_truth_by_ref,
            )
            projection_key = projection.target.casefold()
            if projection_key in projections_by_target:
                raise ValueError(
                    f"API declaration {api_name!r} graph {graph_target!r} has duplicate projection {projection.target!r} "
                    + f"in {source_path}"
                )
            projections_by_target[projection_key] = projection
            continue

        if child.type == "api_graph_capability_def":
            binding = _load_api_graph_capability_definition(
                node=child,
                api_name=api_name,
                graph_target=graph_target,
                source_path=source_path,
                source_rel=source_rel,
                declared_capability_names=declared_capability_names,
            )
            binding_key = binding.capability_name.casefold()
            if binding_key in capabilities_by_name:
                raise ValueError(
                    f"API declaration {api_name!r} graph {graph_target!r} has duplicate capability binding "
                    + f"{binding.capability_name!r} in {source_path}"
                )
            capabilities_by_name[binding_key] = binding

    if not projections_by_target and not capabilities_by_name:
        raise ValueError(
            f"API declaration {api_name!r} graph {graph_target!r} must include at least one projection or capability "
            + f"binding in {source_path}"
        )

    return APIGraphOwnership(
        target=graph_target,
        source_path=source_rel,
        projections=tuple(
            sorted(
                projections_by_target.values(),
                key=lambda item: (item.target, item.source_path),
            )
        ),
        capabilities=tuple(
            sorted(
                capabilities_by_name.values(),
                key=lambda item: (item.capability_name, item.source_path),
            )
        ),
    )


def _load_api_graph_projection_definition(
    *,
    node: Node,
    api_name: str,
    graph_target: str,
    source_path: Path,
    source_rel: str,
    projection_truth_by_name: dict[str, dict[str, ProjectionOwnedClassTruth]] | None,
    binding_truth_by_ref: dict[tuple[str, str], BindingMapTruth] | None,
) -> APIGraphProjectionOwnership:
    projection_target = _qualified_text(node.child_by_field_name("projection"))
    if not projection_target:
        raise ValueError(
            f"API declaration {api_name!r} graph {graph_target!r} has projection with empty target in {source_path}"
        )
    _validate_scoped_target(
        scope_label="projection",
        scope_target=projection_target,
        graph_target=graph_target,
        api_name=api_name,
        source_path=source_path,
    )

    for child in _iter_api_graph_projection_children(node=node):
        if child.type != "api_graph_projection_binding_def":
            continue
        raise ValueError(
            f"API declaration {api_name!r} graph {graph_target!r} projection {projection_target!r} declares "
            + f"a projection node-key binding in {source_path}. Projection node-key bindings are Experience-owned; "
            + "API may only declare graph projection roots and endpoint/function contracts."
        )

    return APIGraphProjectionOwnership(
        target=projection_target,
        source_path=source_rel,
    )


def _load_api_graph_capability_definition(
    *,
    node: Node,
    api_name: str,
    graph_target: str,
    source_path: Path,
    source_rel: str,
    declared_capability_names: frozenset[str],
) -> APIGraphCapabilityOwnership:
    capability_name = _symbol_key(_field_text(node, "capability_name"))
    if not capability_name:
        raise ValueError(
            f"API declaration {api_name!r} graph {graph_target!r} has capability binding with empty name in {source_path}"
        )
    if capability_name.casefold() not in declared_capability_names:
        raise ValueError(
            f"API declaration {api_name!r} graph {graph_target!r} references unknown capability "
            + f"{capability_name!r} in {source_path}"
        )

    functions_by_name: dict[str, APIGraphCapabilityFunctionOwnership] = {}
    for child in _iter_api_graph_capability_children(node=node):
        if child.type != "api_graph_capability_function_def":
            continue
        function_name = _symbol_key(_field_text(child, "name"))
        target = _qualified_text(child.child_by_field_name("target"))
        if not function_name:
            raise ValueError(
                f"API declaration {api_name!r} graph {graph_target!r} capability {capability_name!r} has function "
                + f"with empty name in {source_path}"
            )
        if not target:
            raise ValueError(
                f"API declaration {api_name!r} graph {graph_target!r} capability {capability_name!r} function "
                + f"{function_name!r} has empty graph function target in {source_path}"
            )
        _validate_scoped_target(
            scope_label="graph function",
            scope_target=target,
            graph_target=graph_target,
            api_name=api_name,
            source_path=source_path,
        )
        function_key = function_name.casefold()
        if function_key in functions_by_name:
            raise ValueError(
                f"API declaration {api_name!r} graph {graph_target!r} capability {capability_name!r} has duplicate "
                + f"function {function_name!r} in {source_path}"
            )
        functions_by_name[function_key] = APIGraphCapabilityFunctionOwnership(
            name=function_name,
            target=target,
            source_path=source_rel,
        )

    if not functions_by_name:
        raise ValueError(
            f"API declaration {api_name!r} graph {graph_target!r} capability {capability_name!r} must include at "
            + f"least one function in {source_path}"
        )

    return APIGraphCapabilityOwnership(
        capability_name=capability_name,
        source_path=source_rel,
        functions=tuple(
            sorted(
                functions_by_name.values(),
                key=lambda item: (item.name, item.target, item.source_path),
            )
        ),
    )


def _bind_default_endpoint_functions(
    *,
    api_name: str,
    source_path: Path,
    capabilities_by_name: dict[str, APICapabilityOwnership],
    graphs_by_target: dict[str, APIGraphOwnership],
) -> dict[str, APICapabilityOwnership]:
    updated_capabilities: dict[str, APICapabilityOwnership] = {}
    graph_capabilities_by_key: dict[tuple[str, str], APIGraphCapabilityOwnership] = {}
    for graph in graphs_by_target.values():
        for graph_capability in graph.capabilities:
            graph_capabilities_by_key[
                (graph.target.casefold(), graph_capability.capability_name.casefold())
            ] = graph_capability

    for capability_key, capability in capabilities_by_name.items():
        updated_endpoints: list[APICapabilityEndpointOwnership] = []
        for endpoint in capability.endpoints:
            endpoint_functions = _build_default_endpoint_functions(
                api_name=api_name,
                capability_name=capability.name,
                endpoint_name=endpoint.name,
                source_path=source_path,
                graphs_by_target=graphs_by_target,
                graph_capabilities_by_key=graph_capabilities_by_key,
            )
            updated_endpoints.append(
                APICapabilityEndpointOwnership(
                    name=endpoint.name,
                    source_path=endpoint.source_path,
                    request_config=endpoint.request_config,
                    functions=endpoint_functions,
                    description=endpoint.description,
                )
            )
        updated_capabilities[capability_key] = APICapabilityOwnership(
            name=capability.name,
            source_path=capability.source_path,
            endpoints=tuple(updated_endpoints),
            description=capability.description,
        )
    return updated_capabilities


def _build_default_endpoint_functions(
    *,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
    source_path: Path,
    graphs_by_target: dict[str, APIGraphOwnership],
    graph_capabilities_by_key: dict[tuple[str, str], APIGraphCapabilityOwnership],
) -> tuple[APICapabilityEndpointFunctionOwnership, ...]:
    endpoint_functions_by_name: dict[str, APICapabilityEndpointFunctionOwnership] = {}
    capability_key = capability_name.casefold()
    for graph in graphs_by_target.values():
        graph_capability = graph_capabilities_by_key.get(
            (graph.target.casefold(), capability_key)
        )
        if graph_capability is None:
            continue
        for function in graph_capability.functions:
            function_key = function.name.casefold()
            existing = endpoint_functions_by_name.get(function_key)
            if existing is not None:
                raise ValueError(
                    f"API declaration {api_name!r} endpoint {endpoint_name!r} capability {capability_name!r} has "
                    + f"ambiguous default function {function.name!r} across graphs {existing.graph_target!r} and "
                    + f"{graph.target!r} in {source_path}"
                )
            endpoint_functions_by_name[function_key] = (
                APICapabilityEndpointFunctionOwnership(
                    name=function.name,
                    graph_target=graph.target,
                    graph_capability_function_name=function.name,
                    source_path=function.source_path,
                )
            )
    return tuple(
        sorted(
            endpoint_functions_by_name.values(),
            key=lambda item: (
                item.name,
                item.graph_target,
                item.graph_capability_function_name,
                item.source_path,
            ),
        )
    )


def _resolve_projection_truth(
    *,
    projection_target: str,
    projection_truth_by_name: dict[str, dict[str, ProjectionOwnedClassTruth]],
    api_name: str,
    source_path: Path,
) -> dict[str, ProjectionOwnedClassTruth]:
    for candidate in _projection_truth_candidates(projection_target=projection_target):
        projection_truth = projection_truth_by_name.get(candidate)
        if projection_truth is not None:
            return projection_truth
    raise ValueError(
        f"API declaration {api_name!r} references unknown projection {projection_target!r} "
        + f"(source={source_path})"
    )


def _projection_truth_candidates(*, projection_target: str) -> tuple[str, ...]:
    raw = (projection_target or "").strip()
    if not raw:
        return ()
    candidates: list[str] = [raw]
    candidates_casefolded: set[str] = {raw.casefold()}
    last = raw.rsplit(".", 1)[-1]
    if last:
        folded = last.casefold()
        if folded not in candidates_casefolded:
            candidates_casefolded.add(folded)
            candidates.append(last)
    return tuple(candidates)


def _validate_scoped_target(
    *,
    scope_label: str,
    scope_target: str,
    graph_target: str,
    api_name: str,
    source_path: Path,
) -> None:
    scope_norm = scope_target.casefold()
    graph_norm = graph_target.casefold()
    if scope_norm == graph_norm or scope_norm.startswith(graph_norm + "."):
        return
    raise ValueError(
        f"API declaration {api_name!r} graph {graph_target!r} has {scope_label} target {scope_target!r} outside "
        + f"graph scope (source={source_path})"
    )


def _resolve_binding_truth(
    *,
    binding_ref: str,
    target_graph: str,
    binding_truth_by_ref: dict[tuple[str, str], BindingMapTruth] | None,
    api_name: str,
    projection_target: str,
    source_path: Path,
) -> BindingMapTruth:
    if binding_truth_by_ref is None:
        raise ValueError(
            f"API declaration {api_name!r} graph {target_graph!r} projection {projection_target!r} uses binding "
            + f"{binding_ref!r} but no binding registry was supplied (source={source_path})"
        )
    binding_truth = binding_truth_by_ref.get(
        (binding_ref.casefold(), target_graph.casefold())
    )
    if binding_truth is None:
        raise ValueError(
            f"API declaration {api_name!r} graph {target_graph!r} projection {projection_target!r} references "
            + f"unknown binding {binding_ref!r} for target graph {target_graph!r} (source={source_path})"
        )
    return binding_truth


def _validate_binding_anchor(
    *,
    api_name: str,
    binding_ref: str,
    projection_target: str,
    projection_truth: dict[str, ProjectionOwnedClassTruth],
    parent_class: str,
    relationship_attribute: str,
    binding_truth: BindingMapTruth,
    source_path: Path,
) -> None:
    parent_truth = projection_truth.get(parent_class)
    if parent_truth is None:
        raise ValueError(
            f"API declaration {api_name!r} binding {binding_ref!r} references unknown parent class "
            + f"{parent_class!r} for projection {projection_target!r} (source={source_path})"
        )
    if relationship_attribute not in parent_truth.attributes:
        raise ValueError(
            f"API declaration {api_name!r} binding {binding_ref!r} references unknown relationship "
            + f"{parent_class}::{relationship_attribute} for projection {projection_target!r} (source={source_path})"
        )

    relationship_targets = {
        attribute: target for attribute, target in parent_truth.relationship_targets
    }
    target_class = relationship_targets.get(relationship_attribute)
    if target_class is None:
        raise ValueError(
            f"API declaration {api_name!r} binding {binding_ref!r} cannot resolve relationship target for anchor "
            + f"{parent_class}::{relationship_attribute} (source={source_path})"
        )
    if _normalize_member_token(target_class) != _normalize_member_token(
        binding_truth.target_class
    ):
        raise ValueError(
            f"API declaration {api_name!r} binding {binding_ref!r} targets class {binding_truth.target_class!r} but "
            + f"projection anchor {parent_class}::{relationship_attribute} resolves to {target_class!r} "
            + f"(source={source_path})"
        )

    target_truth = projection_truth.get(target_class)
    if target_truth is None:
        raise ValueError(
            f"API declaration {api_name!r} binding {binding_ref!r} target class {target_class!r} is not "
            + f"owned by projection {projection_target!r} (source={source_path})"
        )
    if binding_truth.target_attribute not in target_truth.identity_key_attributes:
        raise ValueError(
            f"API declaration {api_name!r} binding {binding_ref!r} target attribute "
            + f"{binding_truth.target_attribute!r} is not an identity key on class {target_class!r} "
            + f"(source={source_path})"
        )


def _iter_api_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type != "api_item":
            continue
        children.extend(child.named_children)
    return tuple(children)


def _iter_api_graph_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type != "api_graph_item":
            continue
        children.extend(child.named_children)
    return tuple(children)


def _iter_api_capability_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type == "api_capability_item":
            children.extend(child.named_children)
            continue
        if child.type == "api_capability_endpoint_def":
            children.append(child)
    return tuple(children)


def _iter_api_capability_endpoint_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type == "api_capability_endpoint_item":
            children.extend(child.named_children)
            continue
        if child.type in {
            "api_capability_endpoint_response_def",
            "api_capability_endpoint_stream_def",
        }:
            children.append(child)
    return tuple(children)


def _iter_api_capability_endpoint_stream_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type == "api_capability_endpoint_stream_item":
            children.extend(child.named_children)
            continue
        if child.type == "api_capability_endpoint_stream_event_def":
            children.append(child)
    return tuple(children)


def _iter_api_graph_projection_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type != "api_graph_projection_item":
            continue
        children.extend(child.named_children)
    return tuple(children)


def _iter_api_graph_capability_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type != "api_graph_capability_item":
            continue
        children.extend(child.named_children)
    return tuple(children)


def _extract_block_description(node: Node | None) -> str | None:
    if node is None:
        return None
    for child in node.named_children:
        if child.type == "triple_string_literal":
            raw = _qualified_text(child)
            if raw.startswith('"""') and raw.endswith('"""') and len(raw) >= 6:
                text = raw[3:-3].strip()
                if text:
                    return text
                continue
        if child.type == "string_literal":
            raw = _qualified_text(child)
            if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
                text = raw[1:-1].strip()
                if text:
                    return text
                continue
    return None


def _field_text(node: Node, field: str) -> str:
    target = node.child_by_field_name(field)
    return _qualified_text(target)


def _qualified_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8").strip()


def _symbol_key(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _normalize_member_token(raw: str) -> str:
    return (raw or "").strip()


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} path must stay within package root: {candidate_resolved}"
    )


__all__ = [
    "load_api_graph_targets_from_sources",
    "load_api_graph_targets_from_source_texts",
    "load_api_ownership_from_sources",
    "load_api_ownership_from_source_texts",
]
