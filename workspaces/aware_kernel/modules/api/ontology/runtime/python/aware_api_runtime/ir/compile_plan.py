from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
from uuid import UUID

from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_utils.logging import logger
from ..ontology_graph.ontology import (
    APIOntologyPlan,
    build_api_ontology_plans,
    decode_api_ontology_plan_payload,
    encode_api_ontology_plan_payload,
)
from ..interface.builder import (
    ApiInterfaceSpecArtifact,
    build_api_interface_spec,
    emit_api_interface_spec_artifact,
)
from ..invocation.builder import (
    ApiInvocationManifestArtifact,
    build_api_invocation_manifest,
    emit_api_invocation_manifest_artifact,
)
from ..models import APIOwnership, BindingMapTruth, ProjectionOwnedClassTruth
from ..models import (
    APICapabilityEndpointFunctionOwnership,
    APICapabilityEndpointOwnership,
    APICapabilityEndpointRequestConfigOwnership,
    APICapabilityEndpointResponseConfigOwnership,
    APICapabilityEndpointStreamConfigOwnership,
    APICapabilityEndpointStreamEventConfigOwnership,
    APICapabilityOwnership,
    APIGraphCapabilityFunctionOwnership,
    APIGraphCapabilityOwnership,
    APIGraphOwnership,
    APIGraphProjectionOwnership,
)
from ..packages import (
    ApiPublicPackagePlanArtifact,
    ApiServiceProtocolPlanArtifact,
    build_api_public_package_plan,
    build_api_service_protocol_plan,
    emit_api_public_package_plan_artifact,
    emit_api_service_protocol_plan_artifact,
)
from ..dependencies.runtime_resolution import (
    load_api_dependency_binding_truths,
    load_api_dependency_class_config_ids,
)
from ..source.semantic_analysis import analyze_api_sources
from ..workspace import APIWorkspaceSnapshot


def _round_duration_s(duration_s: float) -> float:
    return round(max(duration_s, 0.0), 6)


@contextmanager
def _record_optional_phase(
    phase_timings_s: dict[str, float] | None,
    phase_name: str,
) -> Iterator[None]:
    if phase_timings_s is None:
        yield
        return
    started_at = perf_counter()
    logger.info("API compile plan phase started: %s", phase_name)
    try:
        yield
    finally:
        duration_s = _round_duration_s(perf_counter() - started_at)
        phase_timings_s[phase_name] = duration_s
        logger.info(
            "API compile plan phase finished: %s (%.6fs)",
            phase_name,
            duration_s,
        )


@dataclass(frozen=True, slots=True)
class APICompilePlanNamespaceRoot:
    path: str
    namespace: str


@dataclass(frozen=True, slots=True)
class APICompilePlan:
    schema_version: int
    package_name: str
    fqn_prefix: str
    source_files: tuple[str, ...]
    api_ownership: tuple[APIOwnership, ...]
    api_ontology: tuple[APIOntologyPlan, ...]
    generated_dto_namespace_roots: tuple[APICompilePlanNamespaceRoot, ...] = ()


@dataclass(frozen=True, slots=True)
class APICompilePlanArtifact:
    path: Path
    relpath: str
    hash_sha256: str


@dataclass(frozen=True, slots=True)
class APIRuntimeArtifacts:
    compile_plan: APICompilePlanArtifact
    interface_spec: ApiInterfaceSpecArtifact
    invocation_manifest: ApiInvocationManifestArtifact
    public_package_plan: ApiPublicPackagePlanArtifact
    service_protocol_plan: ApiServiceProtocolPlanArtifact


def build_api_compile_plan(
    *,
    snapshot: APIWorkspaceSnapshot,
    projection_truth_by_name: (
        dict[str, dict[str, ProjectionOwnedClassTruth]] | None
    ) = None,
    binding_truth_by_ref: dict[tuple[str, str], BindingMapTruth] | None = None,
    dependency_class_config_ids: dict[str, UUID] | None = None,
    phase_timings_s: dict[str, float] | None = None,
    dependency_repo_roots: Sequence[str | Path] = (),
) -> APICompilePlan:
    with _record_optional_phase(phase_timings_s, "build_api_compile_plan.source_files"):
        source_files = tuple(path.as_posix() for path in snapshot.source_files)
    with _record_optional_phase(
        phase_timings_s,
        "build_api_compile_plan.load_api_dependency_binding_truths",
    ):
        resolved_binding_truth_by_ref = (
            binding_truth_by_ref
            if binding_truth_by_ref is not None
            else (
                load_api_dependency_binding_truths(
                    snapshot=snapshot,
                    phase_timings_s=phase_timings_s,
                    dependency_repo_roots=dependency_repo_roots,
                )
                if snapshot.spec.dependencies
                else {}
            )
        )
    with _record_optional_phase(
        phase_timings_s,
        "build_api_compile_plan.analyze_api_sources",
    ):
        semantic_analysis = analyze_api_sources(
            package_root=snapshot.package_root,
            source_files=snapshot.source_files,
            projection_truth_by_name=projection_truth_by_name,
            binding_truth_by_ref=resolved_binding_truth_by_ref,
        )
        api_ownership = semantic_analysis.api_ownership
    with _record_optional_phase(
        phase_timings_s,
        "build_api_compile_plan.load_api_dependency_class_config_ids",
    ):
        dependency_class_config_ids = (
            dependency_class_config_ids
            if dependency_class_config_ids is not None
            else (
                load_api_dependency_class_config_ids(
                    snapshot=snapshot,
                    phase_timings_s=phase_timings_s,
                    dependency_repo_roots=dependency_repo_roots,
                )
                if snapshot.spec.dependencies
                else {}
            )
        )
    with _record_optional_phase(
        phase_timings_s,
        "build_api_compile_plan.bind_endpoint_class_config_ids",
    ):
        api_ownership = bind_api_endpoint_class_config_ids(
            api_ownership=api_ownership,
            class_config_id_by_ref=dependency_class_config_ids,
        )
    with _record_optional_phase(
        phase_timings_s,
        "build_api_compile_plan.build_api_ontology_plans",
    ):
        api_ontology = build_api_ontology_plans(api_ownership=api_ownership)
    return APICompilePlan(
        schema_version=9,
        package_name=(snapshot.spec.api.package_name or "").strip(),
        fqn_prefix=(snapshot.spec.api.fqn_prefix or "").strip(),
        source_files=source_files,
        api_ownership=api_ownership,
        api_ontology=api_ontology,
    )


def emit_api_compile_plan_artifact(
    *,
    plan: APICompilePlan,
    runtime_package_dir: Path,
    repo_root: Path,
) -> APICompilePlanArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    payload = _encode_plan(plan=plan)
    digest = api_compile_plan_artifact_hash(plan=plan)

    artifact_path = (runtime_package_dir / "api.compile_plan.json").resolve()
    _ = artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return APICompilePlanArtifact(
        path=artifact_path, relpath=relpath, hash_sha256=digest
    )


def decode_api_compile_plan_payload(
    *,
    payload: Mapping[str, object],
) -> APICompilePlan:
    schema_version = _required_int(
        payload.get("schema_version"),
        field_name="schema_version",
    )
    raw_api_ownership = _required_list(
        payload.get("api_ownership"),
        field_name="api_ownership",
    )
    raw_api_ontology = _required_list(
        payload.get("api_ontology"),
        field_name="api_ontology",
    )
    return APICompilePlan(
        schema_version=schema_version,
        package_name=_required_text(
            payload.get("package_name"),
            field_name="package_name",
        ),
        fqn_prefix=_required_text(
            payload.get("fqn_prefix"),
            field_name="fqn_prefix",
        ),
        source_files=tuple(
            _required_text(item, field_name="source_files[]")
            for item in _optional_list(payload.get("source_files"))
        ),
        api_ownership=tuple(
            _decode_api_ownership(item=item, index=index)
            for index, item in enumerate(raw_api_ownership)
        ),
        api_ontology=decode_api_ontology_plan_payload(payload=raw_api_ontology),
        generated_dto_namespace_roots=_decode_namespace_roots(
            value=payload.get("generated_dto_namespace_roots"),
        ),
    )


def emit_api_runtime_artifacts(
    *,
    plan: APICompilePlan,
    runtime_package_dir: Path,
    repo_root: Path,
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
) -> APIRuntimeArtifacts:
    compile_plan = emit_api_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
    )
    interface_spec = build_api_interface_spec(
        package_name=plan.package_name,
        fqn_prefix=plan.fqn_prefix,
        api_ownership=plan.api_ownership,
    )
    interface_spec_artifact = emit_api_interface_spec_artifact(
        spec=interface_spec,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
    )
    invocation_manifest = build_api_invocation_manifest(
        package_name=plan.package_name,
        fqn_prefix=plan.fqn_prefix,
        api_ownership=plan.api_ownership,
    )
    invocation_manifest_artifact = emit_api_invocation_manifest_artifact(
        manifest=invocation_manifest,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
    )
    public_package_plan = build_api_public_package_plan(
        package_name=plan.package_name,
        fqn_prefix=plan.fqn_prefix,
        api_ontology=plan.api_ontology,
    )
    public_package_plan_artifact = emit_api_public_package_plan_artifact(
        plan=public_package_plan,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
    )
    service_protocol_plan = build_api_service_protocol_plan(
        package_name=plan.package_name,
        fqn_prefix=plan.fqn_prefix,
        api_ontology=plan.api_ontology,
        accessible_graphs=accessible_graphs,
    )
    service_protocol_plan_artifact = emit_api_service_protocol_plan_artifact(
        plan=service_protocol_plan,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
    )
    return APIRuntimeArtifacts(
        compile_plan=compile_plan,
        interface_spec=interface_spec_artifact,
        invocation_manifest=invocation_manifest_artifact,
        public_package_plan=public_package_plan_artifact,
        service_protocol_plan=service_protocol_plan_artifact,
    )


def _decode_api_ownership(*, item: object, index: int) -> APIOwnership:
    row = _required_mapping(item, field_name=f"api_ownership[{index}]")
    api_name = _required_text(
        row.get("name"), field_name=f"api_ownership[{index}].name"
    )
    return APIOwnership(
        name=api_name,
        source_path=_required_text(
            row.get("source_path"),
            field_name=f"api_ownership[{api_name}].source_path",
        ),
        capabilities=tuple(
            _decode_api_capability(
                item=capability,
                api_name=api_name,
                index=capability_index,
            )
            for capability_index, capability in enumerate(
                _optional_list(row.get("capabilities"))
            )
        ),
        graphs=tuple(
            _decode_api_graph(
                item=graph,
                api_name=api_name,
                index=graph_index,
            )
            for graph_index, graph in enumerate(_optional_list(row.get("graphs")))
        ),
    )


def _decode_api_capability(
    *,
    item: object,
    api_name: str,
    index: int,
) -> APICapabilityOwnership:
    row = _required_mapping(
        item,
        field_name=f"api_ownership[{api_name}].capabilities[{index}]",
    )
    capability_name = _required_text(
        row.get("name"),
        field_name=f"api_ownership[{api_name}].capabilities[{index}].name",
    )
    return APICapabilityOwnership(
        name=capability_name,
        description=_optional_text(row.get("description")),
        source_path=_required_text(
            row.get("source_path"),
            field_name=(
                f"api_ownership[{api_name}].capabilities[{capability_name}].source_path"
            ),
        ),
        endpoints=tuple(
            _decode_api_endpoint(
                item=endpoint,
                api_name=api_name,
                capability_name=capability_name,
                index=endpoint_index,
            )
            for endpoint_index, endpoint in enumerate(
                _optional_list(row.get("endpoints"))
            )
        ),
    )


def _decode_api_endpoint(
    *,
    item: object,
    api_name: str,
    capability_name: str,
    index: int,
) -> APICapabilityEndpointOwnership:
    row = _required_mapping(
        item,
        field_name=(
            f"api_ownership[{api_name}].capabilities[{capability_name}]"
            f".endpoints[{index}]"
        ),
    )
    endpoint_name = _required_text(
        row.get("name"),
        field_name=(
            f"api_ownership[{api_name}].capabilities[{capability_name}]"
            f".endpoints[{index}].name"
        ),
    )
    return APICapabilityEndpointOwnership(
        name=endpoint_name,
        description=_optional_text(row.get("description")),
        source_path=_required_text(
            row.get("source_path"),
            field_name=(
                f"api_ownership[{api_name}].capabilities[{capability_name}]"
                f".endpoints[{endpoint_name}].source_path"
            ),
        ),
        request_config=_decode_request_config(
            item=row.get("request_config"),
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
        ),
        functions=tuple(
            _decode_endpoint_function(
                item=function,
                api_name=api_name,
                capability_name=capability_name,
                endpoint_name=endpoint_name,
                index=function_index,
            )
            for function_index, function in enumerate(
                _optional_list(row.get("functions"))
            )
        ),
    )


def _decode_request_config(
    *,
    item: object,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
) -> APICapabilityEndpointRequestConfigOwnership:
    row = _required_mapping(
        item,
        field_name=(
            f"api_ownership[{api_name}].capabilities[{capability_name}]"
            f".endpoints[{endpoint_name}].request_config"
        ),
    )
    response_config = row.get("response_config")
    stream_config = row.get("stream_config")
    return APICapabilityEndpointRequestConfigOwnership(
        class_ref=_required_text(
            row.get("class_ref"),
            field_name=(
                f"api_ownership[{api_name}].capabilities[{capability_name}]"
                f".endpoints[{endpoint_name}].request_config.class_ref"
            ),
        ),
        class_config_id=_optional_uuid(row.get("class_config_id")),
        description=_optional_text(row.get("description")),
        source_path=_required_text(
            row.get("source_path"),
            field_name=(
                f"api_ownership[{api_name}].capabilities[{capability_name}]"
                f".endpoints[{endpoint_name}].request_config.source_path"
            ),
        ),
        response_config=(
            _decode_response_config(
                item=response_config,
                api_name=api_name,
                capability_name=capability_name,
                endpoint_name=endpoint_name,
            )
            if response_config is not None
            else None
        ),
        stream_config=(
            _decode_stream_config(
                item=stream_config,
                api_name=api_name,
                capability_name=capability_name,
                endpoint_name=endpoint_name,
            )
            if stream_config is not None
            else None
        ),
    )


def _decode_response_config(
    *,
    item: object,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
) -> APICapabilityEndpointResponseConfigOwnership:
    row = _required_mapping(
        item,
        field_name=(
            f"api_ownership[{api_name}].capabilities[{capability_name}]"
            f".endpoints[{endpoint_name}].request_config.response_config"
        ),
    )
    return APICapabilityEndpointResponseConfigOwnership(
        class_ref=_required_text(
            row.get("class_ref"),
            field_name=(
                f"api_ownership[{api_name}].capabilities[{capability_name}]"
                f".endpoints[{endpoint_name}].response_config.class_ref"
            ),
        ),
        class_config_id=_optional_uuid(row.get("class_config_id")),
        description=_optional_text(row.get("description")),
        source_path=_required_text(
            row.get("source_path"),
            field_name=(
                f"api_ownership[{api_name}].capabilities[{capability_name}]"
                f".endpoints[{endpoint_name}].response_config.source_path"
            ),
        ),
    )


def _decode_stream_config(
    *,
    item: object,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
) -> APICapabilityEndpointStreamConfigOwnership:
    row = _required_mapping(
        item,
        field_name=(
            f"api_ownership[{api_name}].capabilities[{capability_name}]"
            f".endpoints[{endpoint_name}].request_config.stream_config"
        ),
    )
    return APICapabilityEndpointStreamConfigOwnership(
        stream_mode=_required_text(
            row.get("stream_mode"),
            field_name=(
                f"api_ownership[{api_name}].capabilities[{capability_name}]"
                f".endpoints[{endpoint_name}].stream_config.stream_mode"
            ),
        ),
        description=_optional_text(row.get("description")),
        source_path=_required_text(
            row.get("source_path"),
            field_name=(
                f"api_ownership[{api_name}].capabilities[{capability_name}]"
                f".endpoints[{endpoint_name}].stream_config.source_path"
            ),
        ),
        event_configs=tuple(
            _decode_stream_event_config(
                item=event,
                api_name=api_name,
                capability_name=capability_name,
                endpoint_name=endpoint_name,
                index=event_index,
            )
            for event_index, event in enumerate(
                _optional_list(row.get("event_configs"))
            )
        ),
    )


def _decode_stream_event_config(
    *,
    item: object,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
    index: int,
) -> APICapabilityEndpointStreamEventConfigOwnership:
    row = _required_mapping(
        item,
        field_name=(
            f"api_ownership[{api_name}].capabilities[{capability_name}]"
            f".endpoints[{endpoint_name}].stream_config.event_configs[{index}]"
        ),
    )
    return APICapabilityEndpointStreamEventConfigOwnership(
        kind=_required_text(row.get("kind"), field_name="stream_event.kind"),
        class_ref=_required_text(
            row.get("class_ref"),
            field_name="stream_event.class_ref",
        ),
        class_config_id=_optional_uuid(row.get("class_config_id")),
        description=_optional_text(row.get("description")),
        source_path=_required_text(
            row.get("source_path"),
            field_name="stream_event.source_path",
        ),
    )


def _decode_endpoint_function(
    *,
    item: object,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
    index: int,
) -> APICapabilityEndpointFunctionOwnership:
    row = _required_mapping(
        item,
        field_name=(
            f"api_ownership[{api_name}].capabilities[{capability_name}]"
            f".endpoints[{endpoint_name}].functions[{index}]"
        ),
    )
    return APICapabilityEndpointFunctionOwnership(
        name=_required_text(row.get("name"), field_name="endpoint_function.name"),
        graph_target=_required_text(
            row.get("graph_target"),
            field_name="endpoint_function.graph_target",
        ),
        graph_capability_function_name=_required_text(
            row.get("graph_capability_function_name"),
            field_name="endpoint_function.graph_capability_function_name",
        ),
        source_path=_required_text(
            row.get("source_path"),
            field_name="endpoint_function.source_path",
        ),
    )


def _decode_api_graph(
    *,
    item: object,
    api_name: str,
    index: int,
) -> APIGraphOwnership:
    row = _required_mapping(
        item,
        field_name=f"api_ownership[{api_name}].graphs[{index}]",
    )
    graph_target = _required_text(
        row.get("target"),
        field_name=f"api_ownership[{api_name}].graphs[{index}].target",
    )
    return APIGraphOwnership(
        target=graph_target,
        source_path=_required_text(
            row.get("source_path"),
            field_name=f"api_ownership[{api_name}].graphs[{graph_target}].source_path",
        ),
        projections=tuple(
            _decode_graph_projection(item=projection, index=projection_index)
            for projection_index, projection in enumerate(
                _optional_list(row.get("projections"))
            )
        ),
        capabilities=tuple(
            _decode_graph_capability(item=capability, index=capability_index)
            for capability_index, capability in enumerate(
                _optional_list(row.get("capabilities"))
            )
        ),
    )


def _decode_graph_projection(
    *,
    item: object,
    index: int,
) -> APIGraphProjectionOwnership:
    row = _required_mapping(item, field_name=f"graph.projections[{index}]")
    return APIGraphProjectionOwnership(
        target=_required_text(row.get("target"), field_name="graph_projection.target"),
        source_path=_required_text(
            row.get("source_path"),
            field_name="graph_projection.source_path",
        ),
    )


def _decode_graph_capability(
    *,
    item: object,
    index: int,
) -> APIGraphCapabilityOwnership:
    row = _required_mapping(item, field_name=f"graph.capabilities[{index}]")
    return APIGraphCapabilityOwnership(
        capability_name=_required_text(
            row.get("capability_name"),
            field_name="graph_capability.capability_name",
        ),
        source_path=_required_text(
            row.get("source_path"),
            field_name="graph_capability.source_path",
        ),
        functions=tuple(
            _decode_graph_capability_function(item=function, index=function_index)
            for function_index, function in enumerate(
                _optional_list(row.get("functions"))
            )
        ),
    )


def _decode_graph_capability_function(
    *,
    item: object,
    index: int,
) -> APIGraphCapabilityFunctionOwnership:
    row = _required_mapping(item, field_name=f"graph_capability.functions[{index}]")
    return APIGraphCapabilityFunctionOwnership(
        name=_required_text(
            row.get("name"), field_name="graph_capability_function.name"
        ),
        target=_required_text(
            row.get("target"),
            field_name="graph_capability_function.target",
        ),
        source_path=_required_text(
            row.get("source_path"),
            field_name="graph_capability_function.source_path",
        ),
    )


def _encode_plan(*, plan: APICompilePlan) -> dict[str, object]:
    return {
        "schema_version": plan.schema_version,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "source_files": list(plan.source_files),
        "generated_dto_namespace_roots": [
            {
                "path": root.path,
                "namespace": root.namespace,
            }
            for root in plan.generated_dto_namespace_roots
        ],
        "api_ownership": [
            {
                "name": api.name,
                "source_path": api.source_path,
                "capabilities": [
                    {
                        "name": capability.name,
                        "description": capability.description,
                        "source_path": capability.source_path,
                        "endpoints": [
                            {
                                "name": endpoint.name,
                                "description": endpoint.description,
                                "source_path": endpoint.source_path,
                                "request_config": {
                                    "class_ref": endpoint.request_config.class_ref,
                                    "class_config_id": (
                                        str(endpoint.request_config.class_config_id)
                                        if endpoint.request_config.class_config_id
                                        is not None
                                        else None
                                    ),
                                    "description": endpoint.request_config.description,
                                    "source_path": endpoint.request_config.source_path,
                                    "response_config": (
                                        {
                                            "class_ref": endpoint.request_config.response_config.class_ref,
                                            "description": endpoint.request_config.response_config.description,
                                            "source_path": endpoint.request_config.response_config.source_path,
                                        }
                                        if endpoint.request_config.response_config
                                        is not None
                                        else None
                                    ),
                                    "stream_config": (
                                        {
                                            "stream_mode": endpoint.request_config.stream_config.stream_mode,
                                            "description": endpoint.request_config.stream_config.description,
                                            "source_path": endpoint.request_config.stream_config.source_path,
                                            "event_configs": [
                                                {
                                                    "kind": event_config.kind,
                                                    "class_ref": event_config.class_ref,
                                                    "description": event_config.description,
                                                    "source_path": event_config.source_path,
                                                }
                                                for event_config in endpoint.request_config.stream_config.event_configs
                                            ],
                                        }
                                        if endpoint.request_config.stream_config
                                        is not None
                                        else None
                                    ),
                                },
                                "functions": [
                                    {
                                        "name": function.name,
                                        "graph_target": function.graph_target,
                                        "graph_capability_function_name": function.graph_capability_function_name,
                                        "source_path": function.source_path,
                                    }
                                    for function in endpoint.functions
                                ],
                            }
                            for endpoint in capability.endpoints
                        ],
                    }
                    for capability in api.capabilities
                ],
                "graphs": [
                    {
                        "target": graph.target,
                        "source_path": graph.source_path,
                        "projections": [
                            {
                                "target": projection.target,
                                "source_path": projection.source_path,
                            }
                            for projection in graph.projections
                        ],
                        "capabilities": [
                            {
                                "capability_name": capability.capability_name,
                                "source_path": capability.source_path,
                                "functions": [
                                    {
                                        "name": function.name,
                                        "target": function.target,
                                        "source_path": function.source_path,
                                    }
                                    for function in capability.functions
                                ],
                            }
                            for capability in graph.capabilities
                        ],
                    }
                    for graph in api.graphs
                ],
            }
            for api in plan.api_ownership
        ],
        "api_ontology": encode_api_ontology_plan_payload(plans=plan.api_ontology),
    }


def encode_api_compile_plan_payload(*, plan: APICompilePlan) -> dict[str, object]:
    return _encode_plan(plan=plan)


def _decode_namespace_roots(
    *,
    value: object,
) -> tuple[APICompilePlanNamespaceRoot, ...]:
    roots: list[APICompilePlanNamespaceRoot] = []
    for index, item in enumerate(_optional_list(value)):
        row = _required_mapping(
            item,
            field_name=f"generated_dto_namespace_roots[{index}]",
        )
        roots.append(
            APICompilePlanNamespaceRoot(
                path=_required_text(
                    row.get("path"),
                    field_name=f"generated_dto_namespace_roots[{index}].path",
                ),
                namespace=_required_text(
                    row.get("namespace"),
                    field_name=f"generated_dto_namespace_roots[{index}].namespace",
                ),
            )
        )
    return tuple(roots)


def api_compile_plan_artifact_hash(*, plan: APICompilePlan) -> str:
    payload = _encode_plan(plan=plan)
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def bind_api_endpoint_class_config_ids(
    *,
    api_ownership: tuple[APIOwnership, ...],
    class_config_id_by_ref: dict[str, UUID],
) -> tuple[APIOwnership, ...]:
    if not class_config_id_by_ref:
        return api_ownership

    bound_apis: list[APIOwnership] = []
    for api in api_ownership:
        bound_capabilities = []
        for capability in api.capabilities:
            bound_endpoints = []
            for endpoint in capability.endpoints:
                request_config = endpoint.request_config
                response_config = request_config.response_config
                stream_config = request_config.stream_config
                bound_endpoints.append(
                    replace(
                        endpoint,
                        request_config=replace(
                            request_config,
                            class_config_id=class_config_id_by_ref.get(
                                request_config.class_ref.strip()
                            ),
                            response_config=(
                                replace(
                                    response_config,
                                    class_config_id=class_config_id_by_ref.get(
                                        response_config.class_ref.strip()
                                    ),
                                )
                                if response_config is not None
                                else None
                            ),
                            stream_config=(
                                replace(
                                    stream_config,
                                    event_configs=tuple(
                                        replace(
                                            event_config,
                                            class_config_id=class_config_id_by_ref.get(
                                                event_config.class_ref.strip()
                                            ),
                                        )
                                        for event_config in stream_config.event_configs
                                    ),
                                )
                                if stream_config is not None
                                else None
                            ),
                        ),
                    )
                )
            bound_capabilities.append(
                replace(capability, endpoints=tuple(bound_endpoints))
            )
        bound_apis.append(replace(api, capabilities=tuple(bound_capabilities)))
    return tuple(bound_apis)


def _required_mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    raise RuntimeError(f"API compile plan payload requires object {field_name}")


def _required_list(value: object, *, field_name: str) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    raise RuntimeError(f"API compile plan payload requires list {field_name}")


def _optional_list(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    raise RuntimeError("API compile plan payload expected list value")


def _required_text(value: object, *, field_name: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise RuntimeError(f"API compile plan payload requires non-empty {field_name}")


def _optional_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _required_int(value: object, *, field_name: str) -> int:
    if isinstance(value, bool):
        raise RuntimeError(f"API compile plan payload requires integer {field_name}")
    if isinstance(value, int):
        return value
    raise RuntimeError(f"API compile plan payload requires integer {field_name}")


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value.strip())
    raise RuntimeError("API compile plan payload expected UUID string")


__all__ = [
    "APICompilePlan",
    "APICompilePlanArtifact",
    "APICompilePlanNamespaceRoot",
    "APIRuntimeArtifacts",
    "api_compile_plan_artifact_hash",
    "bind_api_endpoint_class_config_ids",
    "build_api_compile_plan",
    "decode_api_compile_plan_payload",
    "encode_api_compile_plan_payload",
    "emit_api_compile_plan_artifact",
    "emit_api_runtime_artifacts",
]
