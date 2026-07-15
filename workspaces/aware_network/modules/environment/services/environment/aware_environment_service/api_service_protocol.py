from __future__ import annotations

# pyright: reportMissingImports=false

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence, TypeVar, cast
from uuid import UUID

from pydantic import BaseModel

from aware_environment_ontology.stable_ids import (
    stable_environment_session_attention_session_id,
)
from aware_types import JsonArray, JsonObject

from aware_environment_service_dto.environment import environment as environment_dto
from aware_environment_service_dto.environment.environment import (
    AdmitEnvironmentActorRequest,
    AdmitEnvironmentActorResponse,
    AttachEnvironmentOntologyRequest,
    ConfigureServiceApiDependencyRoutesRequest,
    ConfigureServiceApiDependencyRoutesResponse,
    DescribeEnvironmentConfigRequest,
    DescribeEnvironmentConfigResponse,
    DescribeEnvironmentRequest,
    DescribeEnvironmentResponse,
    DescribeEnvironmentSessionResponse,
    DescribeEnvironmentStatusRequest,
    DescribeEnvironmentStatusResponse,
    DescribeEnvironmentTopologyRequest,
    DescribeEnvironmentTopologyResponse,
    EnsureEnvironmentOntologyRuntimeRequest,
    EnsureReadyRequest,
    EnsureReadyResponse,
    EnvironmentOperationResponse,
    FetchCapabilitiesRequest,
    FetchCapabilitiesResponse,
    GetLaneHeadRequest,
    GetLaneHeadResponse,
    GetObjectInstanceGraphCommitRequest,
    GetObjectInstanceGraphCommitResponse,
    InvokeFunctionRequest,
    InvokeFunctionResponse,
    JoinEnvironmentSessionResponse,
    ListEnvironmentOntologiesRequest,
    MaterializeCommittedProjectionDtoRequest,
    MaterializeCommittedProjectionDtoResponse,
    ResolveEnvironmentSessionAttentionResponse,
    ResolveRuntimeRefsRequest,
    ResolveRuntimeRefsResponse,
    StartEnvironmentSessionResponse,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphGetLaneHeadRequest,
    MetaGraphGetLaneHeadResponse,
    MetaGraphGetObjectInstanceGraphCommitRequest,
    MetaGraphGetObjectInstanceGraphCommitResponse,
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
    MetaGraphResolveProjectionRequest,
    MetaGraphResolveProjectionResponse,
)
from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget,
)
from aware_meta_sdk.stable_ids import stable_object_instance_graph_branch_id
from aware_ontology_service_dto.persistence.readiness import (
    OntologyDatabaseArtifactRef,
    OntologyDatabaseArtifactReceipt,
    OntologyPersistenceEnsureReadyRequest,
    OntologyPersistenceEnsureReadyResponse,
)
from aware_ontology_service_dto.runtime.artifact_set import (
    OntologyRuntimeArtifactSetResolveRequest,
    OntologyRuntimeArtifactSetResolveResponse,
)
from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphGetObjectInstanceGraphCommitRequest,
    OntologyGraphGetObjectInstanceGraphCommitResponse,
    OntologyGraphGetLaneHeadRequest,
    OntologyGraphGetLaneHeadResponse,
    OntologyGraphInvokeFunctionRequest,
    OntologyGraphInvokeFunctionResponse,
    OntologyGraphResolveProjectionRequest,
    OntologyGraphResolveProjectionResponse,
)
from aware_ontology_service_dto.graph.instance.function_call_target import (
    OntologyGraphFunctionCallTarget,
)
from aware_environment.environment.readiness import (
    EnvironmentReadinessHostState,
    EnvironmentReadinessService,
)
from aware_environment.environment.committed_projection_dto import (
    materialize_committed_projection_dto as materialize_committed_projection_dto_via_environment_runtime,
)
from aware_environment.branching import stable_environment_thread_branch_id
from aware_environment.stable_ids import stable_boot_process_id, stable_boot_thread_id
from aware_service_runtime.api_ingress.host_context import (
    ServiceApiHostContext,
    current_service_api_host_context,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    ServiceApiDependencyRouteKind,
)
from aware_service_runtime.contracts import (
    MetaTemporalGraphRoute,
    ServiceGraphGateway,
    ServiceHostTransport,
    ServiceOperationRequest,
    ServiceOperationResponse,
)
from aware_environment_service.ontology_service_api_route import (
    OntologyServiceApiRouteSelector,
    select_ontology_service_api_route,
)
from aware_environment_service.actor_admission_service import (
    AdmitEnvironmentActorRequestSpec,
    EnvironmentActorAdmissionBackend,
    IdentityRoleAssignmentApiClient,
    admit_environment_actor,
)
from aware_environment_service.session_service import (
    AttentionEnvironmentSessionApiClient,
    DescribeEnvironmentSessionRequestSpec,
    EnvironmentSessionAttentionBackend,
    EnvironmentSessionBackend,
    IdentityEnvironmentSessionApiClient,
    JoinEnvironmentSessionRequestSpec,
    ResolveEnvironmentSessionAttentionRequestSpec,
    StartEnvironmentSessionRequestSpec,
    describe_environment_session,
    join_environment_session,
    resolve_environment_session_attention,
    start_environment_session,
)
from aware_environment_service.navigation_service import (
    CreateEnvironmentNavigationContextRequestSpec,
    DescribeEnvironmentNavigationContextRequestSpec,
    EnvironmentNavigationBackend,
    ListEnvironmentNavigationContextsRequestSpec,
    SelectEnvironmentNavigationTargetRequestSpec,
    create_environment_navigation_context,
    describe_environment_navigation_context,
    list_environment_navigation_contexts,
    select_environment_navigation_target,
)

_ResponseT = TypeVar("_ResponseT", bound=EnvironmentOperationResponse)
EnvironmentServiceBackend: type[Any] | None = None
OntologyApiClientProvider = Callable[[], object | None]
_LOCAL_FUNCTION_INVOCATION_FALLBACK_ENV = (
    "AWARE_ENVIRONMENT_TEST_ONLY_LOCAL_FUNCTION_INVOCATION_FALLBACK"
)
_ENVIRONMENT_ATTACH_ONTOLOGY_FUNCTION_REF = (
    "aware_environment.default.environment.Environment.attach_ontology"
)


class _EnvironmentRuntimeResolverLike(Protocol):
    async def get_manifest(self) -> tuple[object, object]: ...

    def get_workspace_revision_materialized_root(self) -> str | Path | None: ...

    def get_runtime_artifact_refs(self) -> Sequence[object]: ...


class _MetaGraphInvokeClient(Protocol):
    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse: ...


class _MetaGraphReadinessClient(_MetaGraphInvokeClient, Protocol):
    async def resolve_projection(
        self,
        request: MetaGraphResolveProjectionRequest,
    ) -> MetaGraphResolveProjectionResponse: ...

    async def get_lane_head(
        self,
        request: MetaGraphGetLaneHeadRequest,
    ) -> MetaGraphGetLaneHeadResponse: ...

    async def get_object_instance_graph_commit(
        self,
        request: MetaGraphGetObjectInstanceGraphCommitRequest,
    ) -> MetaGraphGetObjectInstanceGraphCommitResponse: ...


class _MetaGraphCommitReadClient(_MetaGraphInvokeClient, Protocol):
    async def get_object_instance_graph_commit(
        self,
        request: MetaGraphGetObjectInstanceGraphCommitRequest,
    ) -> MetaGraphGetObjectInstanceGraphCommitResponse: ...


class _OntologyPersistenceReadinessClient(Protocol):
    async def ensure_ready(
        self,
        request: OntologyPersistenceEnsureReadyRequest,
    ) -> OntologyPersistenceEnsureReadyResponse: ...


class _OntologyRuntimeArtifactSetClient(Protocol):
    async def resolve_runtime_artifact_set(
        self,
        request: OntologyRuntimeArtifactSetResolveRequest,
    ) -> OntologyRuntimeArtifactSetResolveResponse: ...


class _OntologyGraphReadinessClient(Protocol):
    async def resolve_projection(
        self,
        request: OntologyGraphResolveProjectionRequest,
    ) -> OntologyGraphResolveProjectionResponse: ...

    async def get_lane_head(
        self,
        request: OntologyGraphGetLaneHeadRequest,
    ) -> OntologyGraphGetLaneHeadResponse: ...

    async def get_object_instance_graph_commit(
        self,
        request: OntologyGraphGetObjectInstanceGraphCommitRequest,
    ) -> OntologyGraphGetObjectInstanceGraphCommitResponse: ...

    async def invoke_function(
        self,
        request: OntologyGraphInvokeFunctionRequest,
    ) -> OntologyGraphInvokeFunctionResponse: ...


class EnvironmentProfileBackend(Protocol):
    async def upsert_environment_profile(
        self,
        *,
        request: environment_dto.UpsertEnvironmentProfileRequest,
        host_context: ServiceApiHostContext,
    ) -> environment_dto.UpsertEnvironmentProfileResponse: ...

    async def provision_environment_profile(
        self,
        *,
        request: environment_dto.ProvisionEnvironmentProfileRequest,
        host_context: ServiceApiHostContext,
    ) -> environment_dto.ProvisionEnvironmentProfileResponse: ...


class _DescribeSupport:
    def build_describe_environment_opgs(
        self,
        *,
        index: object,
    ) -> list[environment_dto.DescribeEnvironmentOPG]:
        """Build Environment OPG descriptors from a runtime index-like object."""

        edge_to_function_id: dict[UUID, UUID] = {}
        ocg = getattr(index, "ocg", None)
        for node in getattr(ocg, "object_config_graph_nodes", ()) or ():
            class_config = getattr(node, "class_config", None)
            if class_config is None:
                continue
            for link in (
                getattr(class_config, "class_config_function_configs", ()) or ()
            ):
                function_config = getattr(link, "function_config", None)
                function_id = getattr(function_config, "id", None)
                if function_id is not None:
                    edge_to_function_id[getattr(link, "id")] = function_id

        opg_values = getattr(index, "opg_by_id", None)
        if isinstance(opg_values, dict):
            opgs = tuple(opg_values.values())
        else:
            opgs = tuple(getattr(ocg, "object_projection_graphs", ()) or ())

        descriptors: list[environment_dto.DescribeEnvironmentOPG] = []
        for opg in opgs:
            constructors: list[environment_dto.DescribeEnvironmentOPGConstructor] = []
            for constructor in (
                getattr(opg, "object_projection_graph_constructors", ()) or ()
            ):
                function_edge_id = getattr(constructor, "function_constructor_id", None)
                function_id = (
                    edge_to_function_id.get(function_edge_id)
                    if function_edge_id is not None
                    else None
                )
                if function_id is None:
                    continue

                root_class_config_id = None
                root_node_id = getattr(constructor, "root_node_id", None)
                if root_node_id is not None:
                    for node in getattr(opg, "object_projection_graph_nodes", ()) or ():
                        if getattr(node, "id", None) == root_node_id:
                            root_class_config_id = getattr(
                                node,
                                "class_config_id",
                                None,
                            )
                            break

                constructors.append(
                    environment_dto.DescribeEnvironmentOPGConstructor(
                        function_id=function_id,
                        root_class_config_id=root_class_config_id,
                    )
                )

            descriptors.append(
                environment_dto.DescribeEnvironmentOPG(
                    id=getattr(opg, "id", None),
                    projection_hash=getattr(opg, "projection_hash", None),
                    name=getattr(opg, "name", None),
                    description=getattr(opg, "description", None),
                    supports_virtual_build=getattr(
                        opg,
                        "supports_virtual_build",
                        None,
                    ),
                    constructors=constructors,
                )
            )

        descriptors.sort(key=lambda item: item.projection_hash or "")
        return descriptors


describe_support = _DescribeSupport()


@dataclass(frozen=True, slots=True)
class _EnvironmentReadinessArtifactSetDescriptor:
    ocg_id: UUID | None
    opg_hashes: tuple[str, ...]
    environment_projection_hash: str | None
    environment_object_projection_graph_id: UUID | None
    environment_constructor_function_id: UUID | None


@dataclass(frozen=True, slots=True)
class _EnvironmentDescribeArtifactSetDescriptor:
    ocg_id: UUID | None
    opg_hashes: tuple[str, ...]
    opgs: tuple[environment_dto.DescribeEnvironmentOPG, ...]


def _read_environment_readiness_artifact_set_descriptor(
    *,
    artifact_refs: Sequence[object],
    projection_name: str = "Environment",
) -> _EnvironmentReadinessArtifactSetDescriptor | None:
    saw_artifact_set_ref = False
    for artifact_ref in artifact_refs:
        artifact_family = _artifact_ref_text(artifact_ref, "artifact_family")
        artifact_role = _artifact_ref_text(artifact_ref, "artifact_role")
        if artifact_family == "ontology_runtime_artifact_set":
            saw_artifact_set_ref = True
        elif artifact_role != "runtime_artifact_set":
            continue

        artifact_set = _ontology_runtime_artifact_set_from_ref(artifact_ref)
        if artifact_set is None:
            continue
        descriptor = _readiness_descriptor_from_ontology_runtime_artifact_set(
            artifact_set=artifact_set,
            projection_name=projection_name,
        )
        if descriptor is not None:
            return descriptor

    if saw_artifact_set_ref:
        raise RuntimeError(
            "Environment readiness received ontology runtime artifact-set refs "
            "without an Environment runtime projection descriptor."
        )
    return None


def _read_environment_describe_artifact_set_descriptor(
    *,
    artifact_refs: Sequence[object],
) -> _EnvironmentDescribeArtifactSetDescriptor | None:
    saw_artifact_set_ref = False
    descriptors: list[_EnvironmentDescribeArtifactSetDescriptor] = []
    for artifact_ref in artifact_refs:
        artifact_family = _artifact_ref_text(artifact_ref, "artifact_family")
        artifact_role = _artifact_ref_text(artifact_ref, "artifact_role")
        if artifact_family == "ontology_runtime_artifact_set":
            saw_artifact_set_ref = True
        elif artifact_role != "runtime_artifact_set":
            continue

        artifact_set = _ontology_runtime_artifact_set_from_ref(artifact_ref)
        if artifact_set is None:
            continue
        descriptor = _describe_descriptor_from_ontology_runtime_artifact_set(
            artifact_set=artifact_set,
        )
        if descriptor is not None:
            descriptors.append(descriptor)

    if descriptors:
        opgs_by_key: dict[
            tuple[str | None, str | None, str | None],
            environment_dto.DescribeEnvironmentOPG,
        ] = {}
        opg_hashes: list[str] = []
        for descriptor in descriptors:
            opg_hashes.extend(descriptor.opg_hashes)
            for opg in descriptor.opgs:
                key = (
                    str(opg.id) if opg.id is not None else None,
                    opg.projection_hash,
                    opg.name,
                )
                opgs_by_key.setdefault(key, opg)
        return _EnvironmentDescribeArtifactSetDescriptor(
            ocg_id=next(
                (
                    descriptor.ocg_id
                    for descriptor in descriptors
                    if descriptor.ocg_id is not None
                ),
                None,
            ),
            opg_hashes=tuple(dict.fromkeys(opg_hashes)),
            opgs=tuple(
                sorted(
                    opgs_by_key.values(),
                    key=lambda opg: (opg.name or "", opg.projection_hash or ""),
                )
            ),
        )

    if saw_artifact_set_ref:
        raise RuntimeError(
            "Environment describe_config received ontology runtime artifact-set refs "
            "without runtime projection descriptors."
        )
    return None


def _runtime_artifact_refs_from_resolver(
    resolver: object,
) -> tuple[object, ...]:
    get_refs = getattr(resolver, "get_runtime_artifact_refs", None)
    if not callable(get_refs):
        return ()
    refs = get_refs()
    if isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)):
        return tuple(refs)
    return ()


def _ontology_runtime_artifact_set_from_ref(
    artifact_ref: object,
) -> Mapping[str, object] | None:
    receipt = _artifact_ref_mapping(artifact_ref, "receipt")
    artifact_set = receipt.get("ontology_runtime_artifact_set")
    if isinstance(artifact_set, Mapping):
        return artifact_set
    provider_payload = _artifact_ref_mapping(artifact_ref, "provider_payload")
    artifact_set = provider_payload.get("ontology_runtime_artifact_set")
    if isinstance(artifact_set, Mapping):
        return artifact_set
    return None


def _readiness_descriptor_from_ontology_runtime_artifact_set(
    *,
    artifact_set: Mapping[str, object],
    projection_name: str,
) -> _EnvironmentReadinessArtifactSetDescriptor | None:
    descriptors = _mapping_sequence(artifact_set.get("runtime_projection_descriptors"))
    selected = next(
        (
            descriptor
            for descriptor in descriptors
            if str(descriptor.get("projection_name") or "").strip() == projection_name
        ),
        None,
    )
    if selected is None:
        return None
    provenance = _mapping_payload(artifact_set.get("provenance"))
    projection_hash = _optional_text(selected.get("projection_hash"))
    return _EnvironmentReadinessArtifactSetDescriptor(
        ocg_id=_optional_uuid(
            selected.get("object_config_graph_id")
            or provenance.get("object_config_graph_id")
        ),
        opg_hashes=(
            _text_tuple(selected.get("opg_hashes"))
            or tuple(
                item
                for item in (
                    _optional_text(descriptor.get("projection_hash"))
                    for descriptor in descriptors
                )
                if item is not None
            )
            or ((projection_hash,) if projection_hash is not None else ())
        ),
        environment_projection_hash=projection_hash,
        environment_object_projection_graph_id=_optional_uuid(
            selected.get("object_projection_graph_id")
        ),
        environment_constructor_function_id=_optional_uuid(
            selected.get("constructor_function_id")
        ),
    )


def _describe_descriptor_from_ontology_runtime_artifact_set(
    *,
    artifact_set: Mapping[str, object],
) -> _EnvironmentDescribeArtifactSetDescriptor | None:
    descriptors = _mapping_sequence(artifact_set.get("runtime_projection_descriptors"))
    if not descriptors:
        return None
    provenance = _mapping_payload(artifact_set.get("provenance"))
    opgs = tuple(
        opg
        for opg in (
            _describe_opg_from_runtime_projection_descriptor(descriptor)
            for descriptor in descriptors
        )
        if opg is not None
    )
    if not opgs:
        return None
    return _EnvironmentDescribeArtifactSetDescriptor(
        ocg_id=_optional_uuid(provenance.get("object_config_graph_id")),
        opg_hashes=tuple(
            item
            for item in (
                _optional_text(descriptor.get("projection_hash"))
                for descriptor in descriptors
            )
            if item is not None
        ),
        opgs=opgs,
    )


def _describe_opg_from_runtime_projection_descriptor(
    descriptor: Mapping[str, object],
) -> environment_dto.DescribeEnvironmentOPG | None:
    opg_id = _optional_uuid(descriptor.get("object_projection_graph_id"))
    projection_hash = _optional_text(descriptor.get("projection_hash"))
    projection_name = _optional_text(descriptor.get("projection_name"))
    if opg_id is None and projection_hash is None and projection_name is None:
        return None
    constructor_function_id = _optional_uuid(descriptor.get("constructor_function_id"))
    metadata = _mapping_payload(descriptor.get("metadata"))
    constructors = (
        [
            environment_dto.DescribeEnvironmentOPGConstructor(
                function_id=constructor_function_id,
                root_class_config_id=_optional_uuid(
                    metadata.get("root_class_config_id")
                ),
            )
        ]
        if constructor_function_id is not None
        else []
    )
    return environment_dto.DescribeEnvironmentOPG(
        id=opg_id,
        projection_hash=projection_hash,
        name=projection_name,
        description=_optional_text(descriptor.get("description")),
        supports_virtual_build=bool(metadata.get("supports_virtual_build")),
        constructors=constructors,
    )


def _capability_catalog_from_ontology_runtime_artifact_refs(
    *,
    artifact_refs: Sequence[object],
) -> tuple[
    tuple[environment_dto.CapabilityObject, ...],
    tuple[environment_dto.CapabilityFunction, ...],
]:
    objects_by_key: dict[
        tuple[str, str],
        environment_dto.CapabilityObject,
    ] = {}
    functions_by_id: dict[UUID, environment_dto.CapabilityFunction] = {}
    for artifact_ref in artifact_refs:
        artifact_family = _artifact_ref_text(artifact_ref, "artifact_family")
        artifact_role = _artifact_ref_text(artifact_ref, "artifact_role")
        if artifact_family != "ontology_runtime_artifact_set" and (
            artifact_role != "runtime_artifact_set"
        ):
            continue

        artifact_set = _ontology_runtime_artifact_set_from_ref(artifact_ref)
        if artifact_set is None:
            continue
        for descriptor in _mapping_sequence(
            artifact_set.get("runtime_projection_descriptors")
        ):
            projection_name = _optional_text(descriptor.get("projection_name"))
            if projection_name is None:
                continue
            metadata = _mapping_payload(descriptor.get("metadata"))
            function_entries = _mapping_sequence(metadata.get("capability_functions"))
            if not function_entries:
                continue
            object_id = _optional_uuid(
                metadata.get("root_class_config_id")
                or descriptor.get("object_projection_graph_id")
            )
            if object_id is None:
                continue

            object_functions: list[environment_dto.CapabilityFunction] = []
            for function_entry in function_entries:
                function_id = _optional_uuid(function_entry.get("id"))
                function_name = _optional_text(function_entry.get("name"))
                if function_id is None or function_name is None:
                    continue
                function = environment_dto.CapabilityFunction(
                    id=function_id,
                    name=function_name,
                    summary=_optional_text(function_entry.get("summary")),
                    is_constructor=bool(function_entry.get("is_constructor")),
                )
                functions_by_id.setdefault(function_id, function)
                object_functions.append(function)
            if not object_functions:
                continue
            objects_by_key.setdefault(
                (str(object_id), projection_name),
                environment_dto.CapabilityObject(
                    id=object_id,
                    name=projection_name,
                    description=_optional_text(descriptor.get("description")),
                    functions=sorted(
                        object_functions,
                        key=lambda function: function.name,
                    ),
                ),
            )

    return (
        tuple(
            sorted(
                objects_by_key.values(),
                key=lambda item: item.name,
            )
        ),
        tuple(
            sorted(
                functions_by_id.values(),
                key=lambda item: item.name,
            )
        ),
    )


def _artifact_ref_text(artifact_ref: object, key: str) -> str | None:
    return _optional_text(_artifact_ref_value(artifact_ref, key))


def _artifact_ref_mapping(artifact_ref: object, key: str) -> Mapping[str, object]:
    return _mapping_payload(_artifact_ref_value(artifact_ref, key))


def _artifact_ref_value(artifact_ref: object, key: str) -> object | None:
    if isinstance(artifact_ref, Mapping):
        return artifact_ref.get(key)
    return getattr(artifact_ref, key, None)


def _mapping_payload(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return {str(key): item for key, item in dumped.items()}
    return {}


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(_mapping_payload(item) for item in value if _mapping_payload(item))


def _text_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        token = value.strip()
        return (token,) if token else ()
    if not isinstance(value, Sequence):
        return ()
    return tuple(
        dict.fromkeys(
            token
            for item in value
            for token in (_optional_text(item),)
            if token is not None
        )
    )


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


async def dispatch_environment_operation(
    *,
    resolver: _EnvironmentRuntimeResolverLike,
    request: environment_dto.EnvironmentOperationRequest,
) -> environment_dto.EnvironmentOperationResponse | None:
    _ = (resolver, request)
    raise RuntimeError(
        "Legacy local Environment runtime dispatch is retired from the Meta SDK "
        "boundary. Configure a canonical Environment API/SDK backend for this "
        "operation."
    )


class _ResolverEnvironmentReadinessHostPort:
    def __init__(
        self,
        *,
        resolver: _EnvironmentRuntimeResolverLike,
        host_context: ServiceApiHostContext,
        ontology_service_route_selector: OntologyServiceApiRouteSelector | None = None,
    ) -> None:
        self._resolver = resolver
        self._host_context = host_context
        self._ontology_service_route_selector = ontology_service_route_selector

    async def resolve_environment_readiness_state(
        self,
        *,
        request: environment_dto.EnsureReadyRequest,
    ) -> EnvironmentReadinessHostState:
        _ = request
        manifest_path, manifest = await self._resolver.get_manifest()
        descriptor = _read_environment_readiness_artifact_set_descriptor(
            artifact_refs=_runtime_artifact_refs_from_resolver(self._resolver),
        )
        if descriptor is None:
            raise RuntimeError(
                "Environment readiness requires ontology runtime artifact-set "
                "refs with an Environment runtime projection descriptor; "
                "hosted runtime index fallback is retired."
            )
        persistence_backend = _persistence_backend_for_manifest(
            manifest=manifest,
            configured_backend=_persistence_backend_name(),
        )
        database_url_ref = _database_url_ref_for_backend(persistence_backend)

        return EnvironmentReadinessHostState(
            manifest_path=str(manifest_path),
            environment_title=manifest.environment.title or None,
            ocg_id=descriptor.ocg_id,
            opg_hashes=descriptor.opg_hashes,
            environment_projection_hash=descriptor.environment_projection_hash,
            environment_object_projection_graph_id=(
                descriptor.environment_object_projection_graph_id
            ),
            environment_constructor_function_id=(
                descriptor.environment_constructor_function_id
            ),
            persistence_backend=persistence_backend,
            database_url_ref=database_url_ref,
            database_connection_ref=(
                _database_connection_ref_for_ontology_persistence(
                    backend=persistence_backend,
                    host_context=self._host_context,
                    ontology_service_route_selector=(
                        self._ontology_service_route_selector
                    ),
                    fallback_ref=database_url_ref,
                )
            ),
            environment_key=(os.environ.get("AWARE_ENVIRONMENT_KEY") or "").strip()
            or None,
        )


class _ResolverOntologyDatabaseArtifactPort:
    def __init__(self, *, resolver: _EnvironmentRuntimeResolverLike) -> None:
        self._resolver = resolver

    async def resolve_environment_database_artifacts(
        self,
        *,
        request: environment_dto.EnsureReadyRequest,
        host_state: EnvironmentReadinessHostState,
    ) -> OntologyDatabaseArtifactReceipt:
        artifact_refs = _runtime_artifact_refs_from_resolver(self._resolver)
        artifact_set = _environment_ontology_runtime_artifact_set_from_refs(
            artifact_refs
        )
        if artifact_set is None:
            raise RuntimeError(
                "Environment readiness DB artifacts require ontology runtime "
                "artifact-set refs with an Environment projection descriptor."
            )
        descriptor = _readiness_descriptor_from_ontology_runtime_artifact_set(
            artifact_set=artifact_set,
            projection_name="Environment",
        )
        if descriptor is None:
            raise RuntimeError(
                "Environment readiness DB artifacts require an Environment "
                "runtime projection descriptor."
            )
        return _ontology_database_artifact_receipt_from_artifact_set(
            artifact_set=artifact_set,
            descriptor=descriptor,
            environment_id=request.environment_id,
            backend_target=_db_backend_target_from_persistence_backend(
                host_state.persistence_backend
            ),
        )


def build_aware_environment_service_protocol_handler(
    *,
    resolver: _EnvironmentRuntimeResolverLike | None = None,
    ontology_api_client_provider: OntologyApiClientProvider | None = None,
    ontology_service_route_selector: OntologyServiceApiRouteSelector | None = None,
    actor_admission_backend: EnvironmentActorAdmissionBackend | None = None,
    environment_profile_backend: EnvironmentProfileBackend | None = None,
    environment_session_backend: EnvironmentSessionBackend | None = None,
    environment_session_attention_backend: (
        EnvironmentSessionAttentionBackend | None
    ) = None,
    environment_navigation_backend: EnvironmentNavigationBackend | None = None,
    identity_api_client: IdentityRoleAssignmentApiClient | None = None,
    attention_api_client: AttentionEnvironmentSessionApiClient | None = None,
    host_environment_id_observer: Callable[[UUID], None] | None = None,
    allow_local_function_invocation_fallback: bool = False,
) -> AwareEnvironmentServiceProtocolHandler:
    return AwareEnvironmentServiceProtocolHandler(
        resolver=resolver,
        ontology_api_client_provider=ontology_api_client_provider,
        ontology_service_route_selector=ontology_service_route_selector,
        actor_admission_backend=actor_admission_backend,
        environment_profile_backend=environment_profile_backend,
        environment_session_backend=environment_session_backend,
        environment_session_attention_backend=environment_session_attention_backend,
        environment_navigation_backend=environment_navigation_backend,
        identity_api_client=identity_api_client,
        attention_api_client=attention_api_client,
        host_environment_id_observer=host_environment_id_observer,
        allow_local_function_invocation_fallback=(
            allow_local_function_invocation_fallback
        ),
    )


class _HostContextTransport(ServiceHostTransport):
    def __init__(self, *, host_context: ServiceApiHostContext) -> None:
        self._host_context = host_context

    async def send_service_response(
        self,
        *,
        request: ServiceOperationRequest,
        response: ServiceOperationResponse,
    ) -> None:
        _ = (request, response)
        return

    async def close_service_stream(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> None:
        _ = request
        return

    async def get_graph_gateway(self) -> ServiceGraphGateway:
        graph_gateway = self._host_context.graph_gateway
        if graph_gateway is None:
            raise RuntimeError(
                "Environment service protocol requires a Service graph gateway."
            )
        return graph_gateway

    async def get_meta_temporal_graph_route(self) -> MetaTemporalGraphRoute:
        route = self._host_context.meta_temporal_graph_route
        if route is None:
            raise RuntimeError(
                "Environment service protocol requires a Meta temporal graph route."
            )
        return route


class _RuntimeEnvironmentServiceBackend:
    def __init__(
        self,
        *,
        transport: ServiceHostTransport,
        resolver: _EnvironmentRuntimeResolverLike | None = None,
    ) -> None:
        _ = transport
        self._resolver = resolver

    async def handle_request(
        self, *, request: environment_dto.EnvironmentOperationRequest
    ) -> environment_dto.EnvironmentOperationResponse:
        if self._resolver is None:
            raise RuntimeError(
                "Environment service protocol operation requires a configured "
                "Environment backend; no local runtime resolver fallback is "
                "available at the Meta SDK boundary."
            )
        dispatched = await dispatch_environment_operation(
            resolver=self._resolver,
            request=request,
        )
        if dispatched is None or dispatched.response is None:
            raise RuntimeError(
                "Unsupported Environment service protocol operation "
                f"{getattr(request, 'operation', 'unknown')!r}."
            )
        return cast(environment_dto.EnvironmentOperationResponse, dispatched.response)


@dataclass(slots=True)
class _EnvironmentProtocolSupport:
    _resolver: _EnvironmentRuntimeResolverLike | None = None
    _ontology_api_client_provider: OntologyApiClientProvider | None = None
    _ontology_service_route_selector: OntologyServiceApiRouteSelector | None = None
    _actor_admission_backend: EnvironmentActorAdmissionBackend | None = None
    _environment_profile_backend: EnvironmentProfileBackend | None = None
    _environment_session_backend: EnvironmentSessionBackend | None = None
    _environment_session_attention_backend: (
        EnvironmentSessionAttentionBackend | None
    ) = None
    _environment_navigation_backend: EnvironmentNavigationBackend | None = None
    _identity_api_client: IdentityRoleAssignmentApiClient | None = None
    _attention_api_client: AttentionEnvironmentSessionApiClient | None = None
    _host_environment_id_observer: Callable[[UUID], None] | None = None
    _allow_local_function_invocation_fallback: bool = False
    _backend: object | None = None

    def host_context(self) -> ServiceApiHostContext:
        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "Environment service protocol requires an active Service API host context."
            )
        return host_context

    def backend(self) -> object:
        backend_type = EnvironmentServiceBackend or _RuntimeEnvironmentServiceBackend
        if self._backend is None:
            transport = _HostContextTransport(host_context=self.host_context())
            if backend_type is _RuntimeEnvironmentServiceBackend:
                self._backend = backend_type(
                    transport=transport,
                    resolver=self._resolver,
                )
            else:
                self._backend = backend_type(transport=transport)
        return self._backend

    async def describe_environment_config_via_artifact_set(
        self,
        *,
        request: environment_dto.DescribeEnvironmentConfigRequest,
    ) -> environment_dto.DescribeEnvironmentConfigResponse:
        resolver = self._resolver
        if resolver is None:
            raise RuntimeError(
                "Environment describe_config requires a configured Environment "
                "host resolver."
            )
        manifest_path, manifest = await resolver.get_manifest()
        descriptor = _read_environment_describe_artifact_set_descriptor(
            artifact_refs=_runtime_artifact_refs_from_resolver(resolver),
        )
        if descriptor is None:
            raise RuntimeError(
                "Environment describe_config requires ontology runtime "
                "artifact-set refs with runtime projection descriptors; "
                "hosted runtime index fallback is retired."
            )
        manifest_environment = getattr(manifest, "environment", None)
        environment_config_id = getattr(manifest_environment, "id", None)
        return environment_dto.DescribeEnvironmentConfigResponse(
            operation="describe_environment_config",
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            title=getattr(manifest_environment, "title", None),
            environment_config_id=(
                _optional_uuid(environment_config_id)
                if environment_config_id is not None
                else None
            ),
            environment_config_title=getattr(manifest_environment, "title", None),
            canonical_language=getattr(
                manifest_environment,
                "canonical_language",
                None,
            ),
            bundle_manifest_path=str(manifest_path),
            ocg_id=descriptor.ocg_id,
            opg_hashes=list(descriptor.opg_hashes),
            opgs=list(descriptor.opgs),
        )

    async def fetch_capabilities_via_artifact_catalog(
        self,
        *,
        request: environment_dto.FetchCapabilitiesRequest,
    ) -> environment_dto.FetchCapabilitiesResponse:
        resolver = self._resolver
        if resolver is None:
            raise RuntimeError(
                "Environment fetch_capabilities requires a configured Environment "
                "host resolver."
            )
        objects, functions = _capability_catalog_from_ontology_runtime_artifact_refs(
            artifact_refs=_runtime_artifact_refs_from_resolver(resolver),
        )
        if not objects and not functions:
            raise RuntimeError(
                "Environment fetch_capabilities requires an ontology-owned "
                "capability catalog; hosted runtime index fallback is retired."
            )
        return environment_dto.FetchCapabilitiesResponse(
            operation="fetch_capabilities",
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            roles=[],
            functions=list(functions),
            objects=list(objects),
        )

    async def describe_environment_via_artifact_set(
        self,
        *,
        request: environment_dto.DescribeEnvironmentRequest,
    ) -> environment_dto.DescribeEnvironmentResponse:
        config = await self.describe_environment_config_via_artifact_set(
            request=environment_dto.DescribeEnvironmentConfigRequest(
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
            ),
        )
        lane_head: environment_dto.GetLaneHeadResponse | None = None
        if request.branch_id is not None and request.projection_hash is not None:
            lane_head = await self.get_lane_head_via_ontology_api(
                request=environment_dto.GetLaneHeadRequest(
                    actor_id=request.actor_id,
                    environment_id=request.environment_id,
                    process_id=request.process_id,
                    thread_id=request.thread_id,
                    branch_id=request.branch_id,
                    projection_hash=request.projection_hash,
                )
            )

        boot_process_id = request.process_id or stable_boot_process_id(
            environment_id=request.environment_id,
        )
        boot_thread_id = request.thread_id or stable_boot_thread_id(
            environment_id=request.environment_id,
        )
        boot_branch_id = stable_environment_thread_branch_id(
            environment_id=request.environment_id,
            thread_id=boot_thread_id,
        )

        return environment_dto.DescribeEnvironmentResponse(
            operation="describe_environment",
            actor_id=request.actor_id or self.host_context().operation_context.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status="succeeded",
            error=None,
            environment_config_id=config.environment_config_id,
            environment_config_title=config.environment_config_title,
            bundle_manifest_path=config.bundle_manifest_path,
            bundle_manifest_http_path=config.bundle_manifest_http_path,
            bundle_artifact_http_path_prefix=config.bundle_artifact_http_path_prefix,
            bundle_descriptor_http_path=config.bundle_descriptor_http_path,
            bundle_head_id=config.bundle_head_id,
            bundle_release_identity=config.bundle_release_identity,
            ocg_id=config.ocg_id,
            environment_title=config.environment_config_title or config.title,
            boot_process_id=boot_process_id,
            boot_thread_id=boot_thread_id,
            boot_branch_id=boot_branch_id,
            head_commit_id=lane_head.commit_id if lane_head is not None else None,
            head_graph_hash_post=(
                lane_head.graph_hash_post if lane_head is not None else None
            ),
            head_object_instance_graph_id=(
                lane_head.object_instance_graph_id if lane_head is not None else None
            ),
            head_root_object_id=(
                lane_head.root_object_id if lane_head is not None else None
            ),
            head_version=lane_head.head_version if lane_head is not None else None,
        )

    async def describe_environment_status_via_artifact_set(
        self,
        *,
        request: environment_dto.DescribeEnvironmentStatusRequest,
    ) -> environment_dto.DescribeEnvironmentStatusResponse:
        config = await self.describe_environment_config_via_artifact_set(
            request=environment_dto.DescribeEnvironmentConfigRequest(
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
            ),
        )
        include_blocks = {
            str(block).strip() for block in request.include_blocks if str(block).strip()
        }
        include_all = not include_blocks
        blocks: list[environment_dto.EnvironmentStatusBlock] = []
        if include_all or "runtime" in include_blocks:
            blocks.append(
                environment_dto.EnvironmentStatusBlock(
                    name="runtime",
                    authority=environment_dto.EnvironmentStatusAuthority(
                        kind=(
                            environment_dto.EnvironmentStatusAuthorityKind.local_fs_view
                        ),
                        source_artifact=config.bundle_manifest_path,
                    ),
                    payload={
                        "environment_config_id": (
                            str(config.environment_config_id)
                            if config.environment_config_id is not None
                            else None
                        ),
                        "ocg_id": str(config.ocg_id) if config.ocg_id else None,
                        "opg_hashes": list(config.opg_hashes),
                        "opg_count": len(config.opgs),
                    },
                )
            )

        refusals: list[dict[str, object]] = []
        if (
            include_all
            or "commit_truth" in include_blocks
            or request.strict_commit_truth
        ):
            commit_block = await self._commit_truth_status_block(request=request)
            blocks.append(commit_block)
            if request.strict_commit_truth and not commit_block.available:
                refusals.append(
                    {
                        "reason": "commit_truth_unavailable",
                        "details": commit_block.unavailable_reason,
                    }
                )

        return environment_dto.DescribeEnvironmentStatusResponse(
            operation="describe_environment_status",
            actor_id=request.actor_id or self.host_context().operation_context.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status="blocked" if refusals else "succeeded",
            error=(
                "commit truth unavailable"
                if refusals and request.strict_commit_truth
                else None
            ),
            status_version="environment.status.v1",
            blocks=blocks,
            refusals=cast(Any, refusals),
        )

    async def _commit_truth_status_block(
        self,
        *,
        request: environment_dto.DescribeEnvironmentStatusRequest,
    ) -> environment_dto.EnvironmentStatusBlock:
        if request.branch_id is None or request.projection_hash is None:
            return environment_dto.EnvironmentStatusBlock(
                name="commit_truth",
                authority=environment_dto.EnvironmentStatusAuthority(
                    kind=environment_dto.EnvironmentStatusAuthorityKind.commit_truth,
                    source_artifact=None,
                ),
                available=False,
                unavailable_reason="branch_id and projection_hash are required",
            )
        lane_head = await self.get_lane_head_via_ontology_api(
            request=environment_dto.GetLaneHeadRequest(
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
            )
        )
        available = lane_head.status == "succeeded" and lane_head.commit_id is not None
        return environment_dto.EnvironmentStatusBlock(
            name="commit_truth",
            authority=environment_dto.EnvironmentStatusAuthority(
                kind=environment_dto.EnvironmentStatusAuthorityKind.commit_truth,
                source_artifact="ontology-service-api",
            ),
            available=available,
            unavailable_reason=(
                None
                if available
                else lane_head.error or f"lane_head_status={lane_head.status}"
            ),
            payload={
                "branch_id": str(request.branch_id),
                "projection_hash": request.projection_hash,
                "commit_id": str(lane_head.commit_id) if lane_head.commit_id else None,
                "graph_hash_post": lane_head.graph_hash_post,
                "object_instance_graph_id": (
                    str(lane_head.object_instance_graph_id)
                    if lane_head.object_instance_graph_id is not None
                    else None
                ),
                "root_object_id": (
                    str(lane_head.root_object_id)
                    if lane_head.root_object_id is not None
                    else None
                ),
                "head_version": lane_head.head_version,
            },
        )

    async def describe_environment_topology_via_artifact_set(
        self,
        *,
        request: environment_dto.DescribeEnvironmentTopologyRequest,
    ) -> environment_dto.DescribeEnvironmentTopologyResponse:
        process_id = request.process_id or stable_boot_process_id(
            environment_id=request.environment_id
        )
        thread_id = request.thread_id or stable_boot_thread_id(
            environment_id=request.environment_id
        )
        process_key = "boot"
        thread_key = "boot"
        if request.process_key is not None and request.process_key != "boot":
            processes: list[environment_dto.DescribeEnvironmentTopologyProcess] = []
        elif request.thread_key is not None and request.thread_key != "boot":
            processes = []
        else:
            processes = [
                environment_dto.DescribeEnvironmentTopologyProcess(
                    process_id=process_id,
                    process_key=process_key,
                    title="Boot Process",
                    description="Deterministic boot process for the Environment.",
                    threads=[
                        environment_dto.DescribeEnvironmentTopologyThread(
                            thread_id=thread_id,
                            thread_key=thread_key,
                            title="Boot Thread",
                            description=(
                                "Deterministic boot thread for Environment SDK "
                                "topology discovery."
                            ),
                            layouts=[],
                            attachments=[],
                        )
                    ],
                )
            ]
        return environment_dto.DescribeEnvironmentTopologyResponse(
            operation="describe_environment_topology",
            actor_id=request.actor_id or self.host_context().operation_context.actor_id,
            environment_id=request.environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=request.branch_id
            or stable_environment_thread_branch_id(
                environment_id=request.environment_id,
                thread_id=thread_id,
            ),
            projection_hash=request.projection_hash,
            status="succeeded",
            error=None,
            processes=processes,
        )

    async def get_lane_head_via_ontology_api(
        self,
        *,
        request: environment_dto.GetLaneHeadRequest,
    ) -> environment_dto.GetLaneHeadResponse:
        actor_id = request.actor_id or self.host_context().operation_context.actor_id
        graph_client, error = self._resolve_graph_readiness_client()
        if graph_client is None:
            return environment_dto.GetLaneHeadResponse(
                operation="get_lane_head",
                actor_id=actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="failed",
                error=(
                    error
                    or "Environment lane-head read requires a configured Ontology "
                    "graph API route."
                ),
            )
        if request.branch_id is None or request.projection_hash is None:
            return environment_dto.GetLaneHeadResponse(
                operation="get_lane_head",
                actor_id=actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="failed",
                error="get_lane_head requires branch_id and projection_hash.",
            )
        response = await graph_client.get_lane_head(
            MetaGraphGetLaneHeadRequest(
                actor_id=actor_id,
                domain_branch_id=request.branch_id,
                domain_projection_hash=request.projection_hash,
            )
        )
        return environment_dto.GetLaneHeadResponse(
            operation="get_lane_head",
            actor_id=response.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=response.domain_branch_id,
            projection_hash=response.domain_projection_hash,
            status=response.status,
            error=response.error,
            commit_id=response.domain_commit_id,
            graph_hash_post=response.graph_hash_post,
            object_instance_graph_id=response.object_instance_graph_id,
            object_instance_graph_identity_id=_optional_uuid(
                getattr(response, "object_instance_graph_identity_id", None)
            ),
            object_instance_graph_branch_id=_environment_oig_branch_id(
                object_instance_graph_identity_id=_optional_uuid(
                    getattr(response, "object_instance_graph_identity_id", None)
                ),
                branch_id=response.domain_branch_id,
            ),
            object_projection_graph_id=_optional_uuid(
                getattr(response, "object_projection_graph_id", None)
            ),
            object_projection_graph_identity_id=_optional_uuid(
                getattr(response, "object_projection_graph_identity_id", None)
            ),
            root_object_id=response.root_object_id,
            head_version=response.head_version,
        )

    async def get_object_instance_graph_commit_via_ontology_api(
        self,
        *,
        request: environment_dto.GetObjectInstanceGraphCommitRequest,
    ) -> environment_dto.GetObjectInstanceGraphCommitResponse:
        graph_client: _MetaGraphCommitReadClient | None = None
        error: str | None = None
        ontology_client = (
            self._ontology_api_client_provider()
            if self._ontology_api_client_provider is not None
            else None
        )
        if ontology_client is not None:
            try:
                graph_client = _ontology_graph_meta_commit_read_client(ontology_client)
            except RuntimeError as exc:
                error = str(exc)
        elif self._ontology_api_client_provider is not None:
            error = (
                "Environment OIG commit read requires the configured Ontology graph "
                "API route to be available."
            )
        if graph_client is None:
            raise RuntimeError(
                error
                or "Environment OIG commit read requires a configured Ontology "
                "graph API route."
            )
        if request.branch_id is None or request.projection_hash is None:
            raise ValueError(
                "get_object_instance_graph_commit requires branch_id and projection_hash."
            )
        actor_id = request.actor_id or self.host_context().operation_context.actor_id
        response = await graph_client.get_object_instance_graph_commit(
            MetaGraphGetObjectInstanceGraphCommitRequest(
                actor_id=actor_id,
                domain_branch_id=request.branch_id,
                domain_projection_hash=request.projection_hash,
                domain_commit_id=request.commit_id,
            )
        )
        if response.object_instance_graph_commit_id is None:
            raise RuntimeError(
                "Ontology service did not return an ObjectInstanceGraphCommit id "
                f"for Environment commit readback: {response.error or response.status}"
            )
        return environment_dto.GetObjectInstanceGraphCommitResponse(
            operation="get_object_instance_graph_commit",
            actor_id=response.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=response.domain_branch_id,
            projection_hash=response.domain_projection_hash,
            status=response.status,
            error=response.error,
            commit_id=response.domain_commit_id,
            object_instance_graph_commit_id=response.object_instance_graph_commit_id,
            object_instance_graph_id=response.object_instance_graph_id,
            object_instance_graph_identity_id=(
                response.object_instance_graph_identity_id
            ),
            object_instance_graph_branch_id=_environment_oig_branch_id(
                object_instance_graph_identity_id=(
                    response.object_instance_graph_identity_id
                ),
                branch_id=response.domain_branch_id,
            ),
            object_projection_graph_id=_optional_uuid(
                getattr(response, "object_projection_graph_id", None)
            ),
            object_projection_graph_identity_id=_optional_uuid(
                getattr(response, "object_projection_graph_identity_id", None)
            ),
            root_object_id=response.root_object_id,
            graph_hash_pre=response.graph_hash_pre,
            graph_hash_post=response.graph_hash_post,
            commit=response.commit,
        )

    def _resolve_graph_readiness_client(
        self,
    ) -> tuple[_MetaGraphReadinessClient | None, str | None]:
        ontology_client = (
            self._ontology_api_client_provider()
            if self._ontology_api_client_provider is not None
            else None
        )
        if ontology_client is not None:
            try:
                return _ontology_graph_meta_readiness_client(ontology_client), None
            except RuntimeError as exc:
                return None, str(exc)
        if self._ontology_api_client_provider is not None:
            return (
                None,
                "Environment graph read requires the configured Ontology graph API "
                "route to be available.",
            )

        return (
            None,
            "Environment graph read requires a configured Ontology graph API route.",
        )

    async def attach_environment_ontology_via_graph(
        self,
        *,
        request: environment_dto.AttachEnvironmentOntologyRequest,
    ) -> environment_dto.AttachEnvironmentOntologyResponse:
        actor_id = request.actor_id or self.host_context().operation_context.actor_id
        if actor_id is None:
            return _failed_attach_environment_ontology_response(
                request=request,
                error="attach_environment_ontology requires actor_id.",
            )
        if request.branch_id is None or request.projection_hash is None:
            return _failed_attach_environment_ontology_response(
                request=request,
                actor_id=actor_id,
                error=(
                    "attach_environment_ontology requires branch_id and "
                    "projection_hash for an Environment instance lane."
                ),
            )

        try:
            refs_response = await self.invoke_backend(
                request=environment_dto.ResolveRuntimeRefsRequest(
                    actor_id=actor_id,
                    environment_id=request.environment_id,
                    process_id=request.process_id,
                    thread_id=request.thread_id,
                    branch_id=request.branch_id,
                    projection_hash=request.projection_hash,
                    function_targets=[
                        environment_dto.ResolveRuntimeFunctionTargetQuery(
                            query_key="environment_attach_ontology",
                            function_ref=_ENVIRONMENT_ATTACH_ONTOLOGY_FUNCTION_REF,
                            call_target=environment_dto.InvokeFunctionCallTarget.instance,
                            projection_hash_hint=request.projection_hash,
                        )
                    ],
                ),
                response_model=environment_dto.ResolveRuntimeRefsResponse,
            )
        except Exception as exc:
            return _failed_attach_environment_ontology_response(
                request=request,
                actor_id=actor_id,
                error=f"attach_environment_ontology target resolution failed: {exc}",
            )
        target = _resolved_runtime_function_target(
            response=refs_response,
            query_key="environment_attach_ontology",
        )
        if target is None or target.status != "resolved" or target.function_id is None:
            return _failed_attach_environment_ontology_response(
                request=request,
                actor_id=actor_id,
                error=(
                    "attach_environment_ontology target resolution failed: "
                    f"{getattr(target, 'error', None) or getattr(target, 'status', None) or refs_response.error}"
                ),
                evidence={
                    "runtime_ref": refs_response.model_dump(
                        mode="json",
                        exclude_none=True,
                    )
                },
            )

        invoke_response = await invoke_environment_function_via_ontology_api(
            request=environment_dto.InvokeFunctionRequest(
                actor_id=actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=target.projection_hash or request.projection_hash,
                call_target=environment_dto.InvokeFunctionCallTarget.instance,
                object_id=request.environment_id,
                function_id=target.function_id,
                args=[
                    str(request.ontology_id),
                    request.role,
                    request.status,
                    request.title,
                    request.description,
                ],
                kwargs={},
                expected_graph_hash_pre=request.expected_graph_hash_pre,
                expected_head_commit_id=request.expected_head_commit_id,
                commit=request.commit,
                publish=request.publish,
            ),
            ontology_api_client_provider=self._ontology_api_client_provider,
            missing_route_error=(
                "attach_environment_ontology requires a configured Ontology graph API route."
            ),
        )
        if invoke_response is None:
            return _failed_attach_environment_ontology_response(
                request=request,
                actor_id=actor_id,
                error=(
                    "attach_environment_ontology requires a configured graph "
                    "invocation route."
                ),
            )

        membership = _environment_ontology_membership_from_payload(
            payload=invoke_response.payload,
            ontology_id=request.ontology_id,
            role=request.role,
            status=request.status,
            title=request.title,
            description=request.description,
            commit_id=invoke_response.commit_id,
            graph_hash_post=invoke_response.graph_hash_post,
        )
        return environment_dto.AttachEnvironmentOntologyResponse(
            operation="attach_environment_ontology",
            actor_id=invoke_response.actor_id or actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=invoke_response.branch_id,
            projection_hash=invoke_response.projection_hash,
            status=invoke_response.status,
            error=invoke_response.error,
            membership=membership,
            commit_id=invoke_response.commit_id,
            object_instance_graph_commit_id=(
                invoke_response.object_instance_graph_commit_id
            ),
            graph_hash_pre=invoke_response.graph_hash_pre,
            graph_hash_post=invoke_response.graph_hash_post,
            evidence={
                "authority": "environment.ontology.graph.invoke_function",
                "function_ref": _ENVIRONMENT_ATTACH_ONTOLOGY_FUNCTION_REF,
                "runtime_ref": target.model_dump(mode="json", exclude_none=True),
            },
        )

    async def list_environment_ontologies_via_committed_projection(
        self,
        *,
        request: environment_dto.ListEnvironmentOntologiesRequest,
    ) -> environment_dto.ListEnvironmentOntologiesResponse:
        actor_id = request.actor_id or self.host_context().operation_context.actor_id
        if request.commit_id is None and (
            request.branch_id is None or request.projection_hash is None
        ):
            return environment_dto.ListEnvironmentOntologiesResponse(
                operation="list_environment_ontologies",
                actor_id=actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="failed",
                error=(
                    "list_environment_ontologies requires commit_id or "
                    "branch_id and projection_hash."
                ),
                memberships=[],
                evidence={"authority": "environment.committed_projection_dto"},
            )

        commit_id = request.commit_id
        lane_head: environment_dto.GetLaneHeadResponse | None = None
        if commit_id is None:
            lane_head = await self.get_lane_head_via_ontology_api(
                request=environment_dto.GetLaneHeadRequest(
                    actor_id=actor_id,
                    environment_id=request.environment_id,
                    process_id=request.process_id,
                    thread_id=request.thread_id,
                    branch_id=request.branch_id,
                    projection_hash=request.projection_hash,
                )
            )
            if lane_head.status != "succeeded" or lane_head.commit_id is None:
                return environment_dto.ListEnvironmentOntologiesResponse(
                    operation="list_environment_ontologies",
                    actor_id=actor_id,
                    environment_id=request.environment_id,
                    process_id=request.process_id,
                    thread_id=request.thread_id,
                    branch_id=request.branch_id,
                    projection_hash=request.projection_hash,
                    status="failed",
                    error=lane_head.error or "Environment lane head unavailable.",
                    memberships=[],
                    evidence={
                        "authority": "environment.lane_head",
                        "lane_head": lane_head.model_dump(
                            mode="json",
                            exclude_none=True,
                        ),
                    },
                )
            commit_id = lane_head.commit_id

        dto_response = await self.invoke_backend(
            request=environment_dto.MaterializeCommittedProjectionDtoRequest(
                actor_id=actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                commit_id=commit_id,
                expected_graph_hash_post=request.expected_graph_hash_post,
                root_object_id=request.root_object_id,
                use_commit_root=True,
                dto_class_ref=request.dto_class_ref,
                dto_package_name=request.dto_package_name,
                dto_import_root=request.dto_import_root,
                include_relationships=True,
                max_depth=2,
            ),
            response_model=environment_dto.MaterializeCommittedProjectionDtoResponse,
        )
        if dto_response.status != "succeeded" or dto_response.dto_payload is None:
            return environment_dto.ListEnvironmentOntologiesResponse(
                operation="list_environment_ontologies",
                actor_id=actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status=dto_response.status,
                error=dto_response.error
                or dto_response.refusal_code
                or "Environment committed DTO unavailable.",
                memberships=[],
                commit_id=dto_response.commit_id or commit_id,
                object_instance_graph_commit_id=(
                    dto_response.object_instance_graph_commit_id
                ),
                graph_hash_post=dto_response.graph_hash_post,
                evidence={
                    "authority": "environment.committed_projection_dto",
                    "dto_response": dto_response.model_dump(
                        mode="json",
                        exclude_none=True,
                    ),
                    **(
                        {
                            "lane_head": lane_head.model_dump(
                                mode="json",
                                exclude_none=True,
                            )
                        }
                        if lane_head is not None
                        else {}
                    ),
                },
            )

        return environment_dto.ListEnvironmentOntologiesResponse(
            operation="list_environment_ontologies",
            actor_id=actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status="succeeded",
            error=None,
            memberships=_environment_ontology_memberships_from_environment_payload(
                dto_response.dto_payload,
                commit_id=dto_response.commit_id or commit_id,
                graph_hash_post=dto_response.graph_hash_post,
            ),
            commit_id=dto_response.commit_id or commit_id,
            object_instance_graph_commit_id=dto_response.object_instance_graph_commit_id,
            graph_hash_post=dto_response.graph_hash_post,
            evidence={
                "authority": "environment.committed_projection_dto",
                "dto_class_ref": dto_response.dto_class_ref,
                "dto_package_name": dto_response.dto_package_name,
                **(
                    {
                        "lane_head": lane_head.model_dump(
                            mode="json",
                            exclude_none=True,
                        )
                    }
                    if lane_head is not None
                    else {}
                ),
            },
        )

    async def ensure_environment_ontology_runtime_via_ontology_api(
        self,
        *,
        request: environment_dto.EnsureEnvironmentOntologyRuntimeRequest,
    ) -> environment_dto.EnsureEnvironmentOntologyRuntimeResponse:
        actor_id = request.actor_id or self.host_context().operation_context.actor_id
        ontology_client = (
            self._ontology_api_client_provider()
            if self._ontology_api_client_provider is not None
            else None
        )
        if ontology_client is None:
            return _failed_ensure_environment_ontology_runtime_response(
                request=request,
                actor_id=actor_id,
                error=(
                    "ensure_environment_ontology_runtime requires a configured "
                    "Ontology API route."
                ),
            )

        try:
            runtime_client = _ontology_runtime_artifact_set_client(ontology_client)
        except RuntimeError as exc:
            return _failed_ensure_environment_ontology_runtime_response(
                request=request,
                actor_id=actor_id,
                error=str(exc),
            )

        runtime_response = await runtime_client.resolve_runtime_artifact_set(
            OntologyRuntimeArtifactSetResolveRequest(
                actor_id=actor_id,
                package_name=request.package_name,
                fqn_prefix=request.fqn_prefix,
                artifact_set_id=request.artifact_set_id,
                workspace_revision_id=request.workspace_revision_id,
                materialization_ref=request.materialization_ref,
                include_artifacts=request.include_artifacts,
                source_payload=request.source_payload,
            )
        )
        if (
            runtime_response.status not in {"resolved", "succeeded"}
            or runtime_response.artifact_set is None
        ):
            return _failed_ensure_environment_ontology_runtime_response(
                request=request,
                actor_id=runtime_response.actor_id or actor_id,
                error=(
                    runtime_response.error
                    or "Ontology runtime artifact-set resolution failed."
                ),
                evidence={
                    "authority": "ontology.runtime.resolve_runtime_artifact_set",
                    "ontology_runtime_response": runtime_response.model_dump(
                        mode="json",
                        exclude_none=True,
                    ),
                },
            )

        resolver = self._resolver
        register = getattr(resolver, "register_runtime_artifact_set", None)
        if resolver is None or not callable(register):
            return _failed_ensure_environment_ontology_runtime_response(
                request=request,
                actor_id=runtime_response.actor_id or actor_id,
                error=(
                    "Environment host resolver does not expose a runtime artifact "
                    "registry."
                ),
            )

        try:
            registration = register(
                artifact_set=runtime_response.artifact_set,
                ontology_id=request.ontology_id,
                membership_commit_id=request.membership_commit_id,
            )
        except Exception as exc:
            return _failed_ensure_environment_ontology_runtime_response(
                request=request,
                actor_id=runtime_response.actor_id or actor_id,
                error=f"Environment runtime artifact registration failed: {exc}",
            )

        return environment_dto.EnsureEnvironmentOntologyRuntimeResponse(
            operation="ensure_environment_ontology_runtime",
            actor_id=runtime_response.actor_id or actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status="succeeded",
            error=None,
            ontology_id=request.ontology_id,
            package_name=registration.package_name,
            fqn_prefix=registration.fqn_prefix,
            artifact_set_id=registration.artifact_set_id,
            runtime_projection_descriptor_count=(
                registration.runtime_projection_descriptor_count
            ),
            capability_object_count=registration.capability_object_count,
            capability_function_count=registration.capability_function_count,
            registered_artifact_ref_count=registration.registered_artifact_ref_count,
            registry_artifact_ref_count=registration.registry_artifact_ref_count,
            membership_commit_id=request.membership_commit_id,
            evidence={
                "authority": "environment.runtime_artifact_registry",
                "source_authority": "ontology.runtime.resolve_runtime_artifact_set",
                "ontology_runtime_response": runtime_response.model_dump(
                    mode="json",
                    exclude_none=True,
                ),
                "registration": {
                    "artifact_set_id": registration.artifact_set_id,
                    "package_name": registration.package_name,
                    "fqn_prefix": registration.fqn_prefix,
                    "registry_artifact_ref_count": (
                        registration.registry_artifact_ref_count
                    ),
                },
            },
        )

    async def ensure_ready_via_environment_runtime(
        self,
        *,
        request: environment_dto.EnsureReadyRequest,
    ) -> environment_dto.EnsureReadyResponse:
        actor_id = request.actor_id or self.host_context().operation_context.actor_id
        ontology_client = (
            self._ontology_api_client_provider()
            if self._ontology_api_client_provider is not None
            else None
        )
        ontology_provider_configured = self._ontology_api_client_provider is not None
        if ontology_provider_configured and ontology_client is None:
            return environment_dto.EnsureReadyResponse(
                actor_id=actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="failed",
                error=(
                    "Environment readiness requires the configured Ontology "
                    "graph API route to be available."
                ),
                readiness_receipt=environment_dto.EnvironmentReadinessReceipt(
                    status="failed",
                    actor_id=actor_id,
                    environment_id=request.environment_id,
                    process_id=request.process_id,
                    thread_id=request.thread_id,
                    branch_id=request.branch_id,
                    projection_hash=request.projection_hash,
                ),
            )
        if ontology_client is None:
            return environment_dto.EnsureReadyResponse(
                actor_id=actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="failed",
                error=(
                    "Environment readiness requires a configured Ontology graph API route."
                ),
                readiness_receipt=environment_dto.EnvironmentReadinessReceipt(
                    status="failed",
                    actor_id=actor_id,
                    environment_id=request.environment_id,
                    process_id=request.process_id,
                    thread_id=request.thread_id,
                    branch_id=request.branch_id,
                    projection_hash=request.projection_hash,
                ),
            )
        graph_client_error: str | None = None
        graph_client: _MetaGraphReadinessClient | None = None
        if ontology_client is not None:
            try:
                graph_client = _ontology_graph_meta_readiness_client(ontology_client)
            except RuntimeError as exc:
                graph_client_error = str(exc)
                if ontology_provider_configured:
                    return environment_dto.EnsureReadyResponse(
                        actor_id=actor_id,
                        environment_id=request.environment_id,
                        process_id=request.process_id,
                        thread_id=request.thread_id,
                        branch_id=request.branch_id,
                        projection_hash=request.projection_hash,
                        status="failed",
                        error=graph_client_error,
                        readiness_receipt=(
                            environment_dto.EnvironmentReadinessReceipt(
                                status="failed",
                                actor_id=actor_id,
                                environment_id=request.environment_id,
                                process_id=request.process_id,
                                thread_id=request.thread_id,
                                branch_id=request.branch_id,
                                projection_hash=request.projection_hash,
                            )
                        ),
                    )
        if graph_client is None:
            return environment_dto.EnsureReadyResponse(
                actor_id=actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="failed",
                error=(
                    graph_client_error
                    or "Environment readiness requires a graph invocation route."
                ),
                readiness_receipt=environment_dto.EnvironmentReadinessReceipt(
                    status="failed",
                    actor_id=actor_id,
                    environment_id=request.environment_id,
                    process_id=request.process_id,
                    thread_id=request.thread_id,
                    branch_id=request.branch_id,
                    projection_hash=request.projection_hash,
                ),
            )
        if actor_id is None:
            return environment_dto.EnsureReadyResponse(
                actor_id=None,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="failed",
                error="Environment readiness requires actor_id.",
                readiness_receipt=environment_dto.EnvironmentReadinessReceipt(
                    status="failed",
                    actor_id=None,
                    environment_id=request.environment_id,
                    process_id=request.process_id,
                    thread_id=request.thread_id,
                    branch_id=request.branch_id,
                    projection_hash=request.projection_hash,
                ),
            )
        try:
            ontology_persistence = _ontology_persistence_readiness_client(
                ontology_client
            )
        except RuntimeError:
            ontology_persistence = None
        if self._resolver is None:
            return environment_dto.EnsureReadyResponse(
                actor_id=actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="failed",
                error=(
                    "Environment readiness requires a configured Environment "
                    "host resolver."
                ),
                readiness_receipt=environment_dto.EnvironmentReadinessReceipt(
                    status="failed",
                    actor_id=actor_id,
                    environment_id=request.environment_id,
                    process_id=request.process_id,
                    thread_id=request.thread_id,
                    branch_id=request.branch_id,
                    projection_hash=request.projection_hash,
                ),
            )
        service = EnvironmentReadinessService(
            host=_ResolverEnvironmentReadinessHostPort(
                resolver=self._resolver,
                host_context=self.host_context(),
                ontology_service_route_selector=(self._ontology_service_route_selector),
            ),
            meta_graph=graph_client,
            structure_artifacts=_ResolverOntologyDatabaseArtifactPort(
                resolver=self._resolver,
            ),
            ontology_persistence=ontology_persistence,
        )
        return await service.ensure_ready(request=request, actor_id=actor_id)

    async def invoke_backend(
        self,
        *,
        request: environment_dto.EnvironmentOperationRequest,
        response_model: type[_ResponseT],
    ) -> _ResponseT:
        if isinstance(
            request,
            environment_dto.MountEnvironmentSessionAttentionRequest,
        ):
            mount_response = await self.mount_environment_session_attention(
                request=request
            )
            return cast(
                _ResponseT,
                response_model.model_validate(mount_response.model_dump(mode="json")),
            )

        if isinstance(request, environment_dto.DescribeEnvironmentConfigRequest):
            describe_response = await self.describe_environment_config_via_artifact_set(
                request=request,
            )
            return cast(
                _ResponseT,
                response_model.model_validate(
                    describe_response.model_dump(mode="json")
                ),
            )

        if isinstance(request, environment_dto.FetchCapabilitiesRequest):
            capabilities_response = await self.fetch_capabilities_via_artifact_catalog(
                request=request,
            )
            return cast(
                _ResponseT,
                response_model.model_validate(
                    capabilities_response.model_dump(mode="json")
                ),
            )

        if isinstance(request, environment_dto.DescribeEnvironmentRequest):
            describe_response = await self.describe_environment_via_artifact_set(
                request=request,
            )
            return cast(
                _ResponseT,
                response_model.model_validate(
                    describe_response.model_dump(mode="json")
                ),
            )

        if isinstance(request, environment_dto.DescribeEnvironmentStatusRequest):
            status_response = await self.describe_environment_status_via_artifact_set(
                request=request,
            )
            return cast(
                _ResponseT,
                response_model.model_validate(status_response.model_dump(mode="json")),
            )

        if isinstance(request, environment_dto.DescribeEnvironmentTopologyRequest):
            topology_response = (
                await self.describe_environment_topology_via_artifact_set(
                    request=request,
                )
            )
            return cast(
                _ResponseT,
                response_model.model_validate(
                    topology_response.model_dump(mode="json")
                ),
            )

        if isinstance(request, environment_dto.GetLaneHeadRequest):
            head_response = await self.get_lane_head_via_ontology_api(request=request)
            return cast(
                _ResponseT,
                response_model.model_validate(head_response.model_dump(mode="json")),
            )

        if isinstance(request, environment_dto.GetObjectInstanceGraphCommitRequest):
            commit_response = (
                await self.get_object_instance_graph_commit_via_ontology_api(
                    request=request,
                )
            )
            return cast(
                _ResponseT,
                response_model.model_validate(commit_response.model_dump(mode="json")),
            )

        if isinstance(request, environment_dto.ResolveRuntimeRefsRequest):
            resolver = self._resolver
            artifact_refs = (
                _runtime_artifact_refs_from_resolver(resolver)
                if resolver is not None
                else ()
            )
            if artifact_refs:
                from aware_environment_service.runtime_ref import (
                    resolve_runtime_refs_from_artifact_refs,
                )

                refs_response = resolve_runtime_refs_from_artifact_refs(
                    artifact_refs=artifact_refs,
                    request=request,
                )
                return cast(
                    _ResponseT,
                    response_model.model_validate(
                        refs_response.model_dump(mode="json")
                    ),
                )

        if isinstance(
            request,
            environment_dto.EnsureEnvironmentOntologyRuntimeRequest,
        ):
            ensure_response = (
                await self.ensure_environment_ontology_runtime_via_ontology_api(
                    request=request,
                )
            )
            return cast(
                _ResponseT,
                response_model.model_validate(ensure_response.model_dump(mode="json")),
            )

        if isinstance(request, environment_dto.AttachEnvironmentOntologyRequest):
            attach_response = await self.attach_environment_ontology_via_graph(
                request=request,
            )
            return cast(
                _ResponseT,
                response_model.model_validate(attach_response.model_dump(mode="json")),
            )

        if isinstance(request, environment_dto.ListEnvironmentOntologiesRequest):
            list_response = (
                await self.list_environment_ontologies_via_committed_projection(
                    request=request,
                )
            )
            return cast(
                _ResponseT,
                response_model.model_validate(list_response.model_dump(mode="json")),
            )

        if isinstance(request, environment_dto.EnsureReadyRequest):
            ready_response = await self.ensure_ready_via_environment_runtime(
                request=request,
            )
            self._observe_host_environment_ready(
                request=request,
                response=ready_response,
            )
            return cast(
                _ResponseT,
                response_model.model_validate(ready_response.model_dump(mode="json")),
            )

        if isinstance(request, environment_dto.AdmitEnvironmentActorRequest):
            admission_response = await admit_environment_actor(
                request=_convert_model(
                    request,
                    model_cls=AdmitEnvironmentActorRequestSpec,
                ),
                host_context=self.host_context(),
                admission_backend=self._actor_admission_backend,
                identity_api_client=self._identity_api_client,
            )
            return cast(
                _ResponseT,
                response_model.model_validate(
                    admission_response.model_dump(mode="json")
                ),
            )

        if isinstance(request, environment_dto.UpsertEnvironmentProfileRequest):
            if self._environment_profile_backend is None:
                profile_key = getattr(request.profile, "key", None)
                return cast(
                    _ResponseT,
                    response_model.model_validate(
                        environment_dto.UpsertEnvironmentProfileResponse(
                            operation="upsert_environment_profile",
                            actor_id=request.actor_id,
                            environment_id=request.environment_id,
                            process_id=request.process_id,
                            thread_id=request.thread_id,
                            branch_id=request.branch_id,
                            projection_hash=request.projection_hash,
                            status="unavailable",
                            error=(
                                "environment_profile_backend_unavailable:"
                                f"{profile_key or 'unknown'}"
                            ),
                        ).model_dump(mode="json")
                    ),
                )
            profile_response = (
                await self._environment_profile_backend.upsert_environment_profile(
                    request=request,
                    host_context=self.host_context(),
                )
            )
            return cast(
                _ResponseT,
                response_model.model_validate(profile_response.model_dump(mode="json")),
            )

        if isinstance(request, environment_dto.ProvisionEnvironmentProfileRequest):
            if self._environment_profile_backend is None:
                return cast(
                    _ResponseT,
                    response_model.model_validate(
                        environment_dto.ProvisionEnvironmentProfileResponse(
                            operation="provision_environment_profile",
                            actor_id=request.actor_id,
                            environment_id=request.environment_id,
                            process_id=request.process_id,
                            thread_id=request.thread_id,
                            branch_id=request.branch_id,
                            projection_hash=request.projection_hash,
                            status="unavailable",
                            error=(
                                "environment_profile_backend_unavailable:"
                                f"{request.topology_seed_key}"
                            ),
                            environment_profile_id=request.environment_profile_id,
                        ).model_dump(mode="json")
                    ),
                )
            profile_response = (
                await self._environment_profile_backend.provision_environment_profile(
                    request=request,
                    host_context=self.host_context(),
                )
            )
            return cast(
                _ResponseT,
                response_model.model_validate(profile_response.model_dump(mode="json")),
            )

        if isinstance(request, environment_dto.StartEnvironmentSessionRequest):
            session_response = await start_environment_session(
                request=_convert_model(
                    request,
                    model_cls=StartEnvironmentSessionRequestSpec,
                ),
                host_context=self.host_context(),
                session_backend=self._environment_session_backend,
                identity_api_client=cast(
                    IdentityEnvironmentSessionApiClient | None,
                    self._identity_api_client,
                ),
            )
            return cast(
                _ResponseT,
                response_model.model_validate(session_response.model_dump(mode="json")),
            )

        if isinstance(request, environment_dto.JoinEnvironmentSessionRequest):
            session_response = await join_environment_session(
                request=_convert_model(
                    request,
                    model_cls=JoinEnvironmentSessionRequestSpec,
                ),
                host_context=self.host_context(),
                session_backend=self._environment_session_backend,
                identity_api_client=cast(
                    IdentityEnvironmentSessionApiClient | None,
                    self._identity_api_client,
                ),
            )
            return cast(
                _ResponseT,
                response_model.model_validate(session_response.model_dump(mode="json")),
            )

        if isinstance(request, environment_dto.DescribeEnvironmentSessionRequest):
            session_response = await describe_environment_session(
                request=_convert_model(
                    request,
                    model_cls=DescribeEnvironmentSessionRequestSpec,
                ),
                session_backend=self._environment_session_backend,
            )
            return cast(
                _ResponseT,
                response_model.model_validate(session_response.model_dump(mode="json")),
            )

        if isinstance(
            request,
            environment_dto.ResolveEnvironmentSessionAttentionRequest,
        ):
            session_response = await resolve_environment_session_attention(
                request=_convert_model(
                    request,
                    model_cls=ResolveEnvironmentSessionAttentionRequestSpec,
                ),
                host_context=self.host_context(),
                session_backend=self._environment_session_backend,
                attention_resolution_backend=(
                    self._environment_session_attention_backend
                ),
                attention_api_client=self._attention_api_client,
            )
            return cast(
                _ResponseT,
                response_model.model_validate(session_response.model_dump(mode="json")),
            )

        if isinstance(
            request,
            environment_dto.CreateEnvironmentNavigationContextRequest,
        ):
            navigation_response = await create_environment_navigation_context(
                request=_convert_model(
                    request,
                    model_cls=CreateEnvironmentNavigationContextRequestSpec,
                ),
                host_context=self.host_context(),
                navigation_backend=self._environment_navigation_backend,
            )
            return cast(
                _ResponseT,
                response_model.model_validate(
                    navigation_response.model_dump(mode="json")
                ),
            )

        if isinstance(
            request,
            environment_dto.SelectEnvironmentNavigationTargetRequest,
        ):
            navigation_response = await select_environment_navigation_target(
                request=_convert_model(
                    request,
                    model_cls=SelectEnvironmentNavigationTargetRequestSpec,
                ),
                host_context=self.host_context(),
                navigation_backend=self._environment_navigation_backend,
            )
            return cast(
                _ResponseT,
                response_model.model_validate(
                    navigation_response.model_dump(mode="json")
                ),
            )

        if isinstance(
            request,
            environment_dto.DescribeEnvironmentNavigationContextRequest,
        ):
            navigation_response = await describe_environment_navigation_context(
                request=_convert_model(
                    request,
                    model_cls=DescribeEnvironmentNavigationContextRequestSpec,
                ),
                host_context=self.host_context(),
                navigation_backend=self._environment_navigation_backend,
            )
            return cast(
                _ResponseT,
                response_model.model_validate(
                    navigation_response.model_dump(mode="json")
                ),
            )

        if isinstance(
            request,
            environment_dto.ListEnvironmentNavigationContextsRequest,
        ):
            navigation_response = await list_environment_navigation_contexts(
                request=_convert_model(
                    request,
                    model_cls=ListEnvironmentNavigationContextsRequestSpec,
                ),
                host_context=self.host_context(),
                navigation_backend=self._environment_navigation_backend,
            )
            return cast(
                _ResponseT,
                response_model.model_validate(
                    navigation_response.model_dump(mode="json")
                ),
            )

        if isinstance(request, environment_dto.InvokeFunctionRequest):
            meta_response = await invoke_environment_function_via_ontology_api(
                request=request,
                ontology_api_client_provider=self._ontology_api_client_provider,
                missing_route_error=(
                    None
                    if _local_function_invocation_fallback_enabled(
                        requested=self._allow_local_function_invocation_fallback
                    )
                    else (
                        "Environment function-call mutation requires a configured "
                        "Ontology graph API route."
                    )
                ),
            )
            if meta_response is not None:
                return cast(
                    _ResponseT,
                    response_model.model_validate(
                        meta_response.model_dump(mode="json")
                    ),
                )

        if isinstance(
            request,
            environment_dto.MaterializeCommittedProjectionDtoRequest,
        ):
            resolver = self._resolver
            dto_response = (
                await materialize_committed_projection_dto_via_environment_runtime(
                    request=request,
                    workspace_revision_materialized_root=(
                        resolver.get_workspace_revision_materialized_root()
                        if resolver is not None
                        else None
                    ),
                    runtime_artifact_refs=(
                        resolver.get_runtime_artifact_refs()
                        if resolver is not None
                        else ()
                    ),
                    ontology_api_client_provider=self._ontology_api_client_provider,
                )
            )
            return cast(
                _ResponseT,
                response_model.model_validate(dto_response.model_dump(mode="json")),
            )

        response = await cast(Any, self.backend()).handle_request(request=request)
        response_payload = (
            response.model_dump(mode="json")
            if isinstance(response, BaseModel)
            else response
        )
        return cast(_ResponseT, response_model.model_validate(response_payload))

    async def mount_environment_session_attention(
        self,
        *,
        request: environment_dto.MountEnvironmentSessionAttentionRequest,
    ) -> environment_dto.MountEnvironmentSessionAttentionResponse:
        status = request.status.strip().lower()
        if not status:
            raise ValueError("Environment Attention portal status must not be blank.")
        host_context = self.host_context()
        graph_gateway = host_context.graph_gateway
        if graph_gateway is None:
            raise RuntimeError(
                "Environment Attention portal mount requires a Service graph gateway."
            )
        actor_id = host_context.operation_context.actor_id
        if actor_id is None:
            raise RuntimeError(
                "Environment Attention portal mount requires an admitted actor id."
            )
        if host_context.materialization is not None:
            graph_context = host_context.materialization.graph_context
        elif host_context.graph_context_provider is not None:
            graph_context = (
                await host_context.graph_context_provider.resolve_graph_context()
            )
        else:
            resolve_graph_context = getattr(
                graph_gateway, "resolve_graph_context", None
            )
            if not callable(resolve_graph_context):
                raise RuntimeError(
                    "Environment graph gateway cannot resolve graph context."
                )
            graph_context = await resolve_graph_context()
        runtime_index_value = getattr(graph_context, "index", graph_context)
        if not hasattr(runtime_index_value, "class_configs_by_id") or not hasattr(
            runtime_index_value, "opg_by_hash"
        ):
            raise RuntimeError(
                "Environment Attention portal graph context has no Meta runtime index."
            )
        runtime_index = runtime_index_value
        projection, class_config = _resolve_environment_attention_portal_projection(
            runtime_index
        )
        portal_id = stable_environment_session_attention_session_id(
            environment_session_id=request.environment_session_id,
            attention_session_id=request.attention_session_id,
        )
        response = await graph_gateway.invoke_function(
            request=MetaGraphInvokeFunctionRequest(
                actor_id=actor_id,
                domain_branch_id=portal_id,
                domain_projection_hash=str(projection.projection_hash),
                call_target=MetaGraphFunctionCallTarget.opg_constructor,
                object_projection_graph_id=UUID(str(projection.id)),
                function_id=_resolve_environment_attention_portal_constructor_id(
                    class_config
                ),
                args=cast(JsonArray, []),
                kwargs=cast(
                    JsonObject,
                    {
                        "environment_session_id": str(request.environment_session_id),
                        "attention_session_id": str(request.attention_session_id),
                        "key": request.key,
                        "title": request.title,
                        "status": status,
                        "metadata_json": dict(request.metadata or {}),
                    },
                ),
                commit=True,
                publish=False,
            ),
            graph_context=runtime_index,
        )
        result = MetaGraphInvokeFunctionResponse.model_validate(response)
        if result.status.strip().lower() != "succeeded":
            raise RuntimeError(
                "Environment Attention portal constructor failed: "
                f"{result.error or result.status}"
            )
        if result.root_object_id != portal_id:
            raise RuntimeError(
                "Environment Attention portal constructor returned a non-canonical "
                "root id."
            )
        if result.object_instance_graph_commit_id is None:
            raise RuntimeError(
                "Environment Attention portal constructor returned no graph commit."
            )
        if not result.graph_hash_post:
            raise RuntimeError(
                "Environment Attention portal constructor returned no graph hash."
            )
        return environment_dto.MountEnvironmentSessionAttentionResponse(
            request_id=request.request_id,
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status=status,
            environment_session_attention_session_id=portal_id,
            environment_session_id=request.environment_session_id,
            attention_session_id=request.attention_session_id,
            key=request.key,
            title=request.title,
            metadata=cast(JsonObject, dict(request.metadata or {})),
            domain_commit_id=result.domain_commit_id,
            object_instance_graph_commit_id=result.object_instance_graph_commit_id,
            graph_hash_post=result.graph_hash_post,
        )

    def _observe_host_environment_ready(
        self,
        *,
        request: environment_dto.EnsureReadyRequest,
        response: environment_dto.EnsureReadyResponse,
    ) -> None:
        observer = self._host_environment_id_observer
        if observer is None:
            return
        status = str(response.status or "").strip().casefold()
        if status != "ready":
            return
        environment_id = response.environment_id or request.environment_id
        if isinstance(environment_id, UUID):
            observer(environment_id)


def _resolve_environment_attention_portal_projection(
    runtime_index: Any,
) -> tuple[Any, Any]:
    class_configs_by_id = cast(Any, runtime_index.class_configs_by_id)
    projections = list(cast(Any, runtime_index.opg_by_hash).values())
    matches: list[tuple[Any, Any]] = []
    for projection in projections:
        if (
            getattr(projection, "name", "") or ""
        ).strip() != "EnvironmentSessionAttentionSession":
            continue
        for node in projection.object_projection_graph_nodes or []:
            if not node.is_root:
                continue
            class_config = class_configs_by_id.get(node.class_config_id)
            if class_config is not None and (
                (getattr(class_config, "name", "") or "").strip()
                == "EnvironmentSessionAttentionSession"
            ):
                matches.append((projection, class_config))
    if len(matches) != 1:
        raise RuntimeError(
            "EnvironmentSessionAttentionSession projection root is missing or "
            f"ambiguous: matches={len(matches)}"
        )
    return matches[0]


def _resolve_environment_attention_portal_constructor_id(
    class_config: Any,
) -> UUID:
    matches = [
        function_config.id
        for link in class_config.class_config_function_configs or []
        for function_config in [link.function_config]
        if function_config is not None
        and (function_config.name or "").strip() == "build_via_environment_session"
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "EnvironmentSessionAttentionSession build_via_environment_session "
            f"constructor is missing or ambiguous: matches={len(matches)}"
        )
    return UUID(str(matches[0]))


class _EnvironmentCapabilityHandler:
    def __init__(
        self,
        *,
        support: _EnvironmentProtocolSupport,
    ) -> None:
        self._support = support

    def bind_endpoint(
        self,
        *,
        endpoint_name: str,
        request_model: type[BaseModel],
        response_model: type[_ResponseT],
    ) -> None:
        async def _invoke(request: BaseModel) -> BaseModel:
            payload = (
                request.model_dump(mode="json")
                if isinstance(request, BaseModel)
                else request
            )
            environment_request = request_model.model_validate(payload)
            return await self._support.invoke_backend(
                request=cast(
                    environment_dto.EnvironmentOperationRequest,
                    environment_request,
                ),
                response_model=response_model,
            )

        setattr(self, endpoint_name, _invoke)


def _single_endpoint_capability(
    *,
    support: _EnvironmentProtocolSupport,
    endpoint_name: str,
    request_model: type[BaseModel],
    response_model: type[_ResponseT],
) -> _EnvironmentCapabilityHandler:
    handler = _EnvironmentCapabilityHandler(support=support)
    handler.bind_endpoint(
        endpoint_name=endpoint_name,
        request_model=request_model,
        response_model=response_model,
    )
    return handler


def _convert_model(value: object, *, model_cls: type[BaseModel]) -> Any:
    payload = value
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude_none=True)
    return model_cls.model_validate(payload)


def _bind_endpoint(
    *,
    handler: _EnvironmentCapabilityHandler,
    endpoint_name: str,
    request_model: type[BaseModel],
    response_model: type[_ResponseT],
) -> None:
    handler.bind_endpoint(
        endpoint_name=endpoint_name,
        request_model=request_model,
        response_model=response_model,
    )


class EnvironmentApiServiceProtocolHandler:
    def __init__(self, *, support: _EnvironmentProtocolSupport) -> None:
        self.capabilities = _single_endpoint_capability(
            support=support,
            endpoint_name="fetch_capabilities",
            request_model=environment_dto.FetchCapabilitiesRequest,
            response_model=FetchCapabilitiesResponse,
        )
        self.describe_config = _single_endpoint_capability(
            support=support,
            endpoint_name="describe_environment_config",
            request_model=environment_dto.DescribeEnvironmentConfigRequest,
            response_model=DescribeEnvironmentConfigResponse,
        )
        self.describe = _single_endpoint_capability(
            support=support,
            endpoint_name="describe_environment",
            request_model=environment_dto.DescribeEnvironmentRequest,
            response_model=DescribeEnvironmentResponse,
        )
        self.topology = _single_endpoint_capability(
            support=support,
            endpoint_name="describe_environment_topology",
            request_model=environment_dto.DescribeEnvironmentTopologyRequest,
            response_model=DescribeEnvironmentTopologyResponse,
        )
        self.status = _single_endpoint_capability(
            support=support,
            endpoint_name="describe_environment_status",
            request_model=environment_dto.DescribeEnvironmentStatusRequest,
            response_model=DescribeEnvironmentStatusResponse,
        )
        self.ready = _single_endpoint_capability(
            support=support,
            endpoint_name="ensure_ready",
            request_model=environment_dto.EnsureReadyRequest,
            response_model=EnsureReadyResponse,
        )
        self.lane_head = _single_endpoint_capability(
            support=support,
            endpoint_name="get_lane_head",
            request_model=environment_dto.GetLaneHeadRequest,
            response_model=GetLaneHeadResponse,
        )
        self.object_instance_graph_commit = _single_endpoint_capability(
            support=support,
            endpoint_name="get_object_instance_graph_commit",
            request_model=environment_dto.GetObjectInstanceGraphCommitRequest,
            response_model=GetObjectInstanceGraphCommitResponse,
        )
        self.committed_projection_dto = _single_endpoint_capability(
            support=support,
            endpoint_name="materialize_committed_projection_dto",
            request_model=environment_dto.MaterializeCommittedProjectionDtoRequest,
            response_model=MaterializeCommittedProjectionDtoResponse,
        )
        self.runtime_ref = _single_endpoint_capability(
            support=support,
            endpoint_name="resolve_runtime_refs",
            request_model=environment_dto.ResolveRuntimeRefsRequest,
            response_model=ResolveRuntimeRefsResponse,
        )
        self.service_routes = _single_endpoint_capability(
            support=support,
            endpoint_name="configure_service_api_dependency_routes",
            request_model=environment_dto.ConfigureServiceApiDependencyRoutesRequest,
            response_model=ConfigureServiceApiDependencyRoutesResponse,
        )
        self.actor_admission = _single_endpoint_capability(
            support=support,
            endpoint_name="admit_actor",
            request_model=environment_dto.AdmitEnvironmentActorRequest,
            response_model=AdmitEnvironmentActorResponse,
        )
        self.profile = _EnvironmentCapabilityHandler(support=support)
        _bind_endpoint(
            handler=self.profile,
            endpoint_name="upsert_environment_profile",
            request_model=environment_dto.UpsertEnvironmentProfileRequest,
            response_model=environment_dto.UpsertEnvironmentProfileResponse,
        )
        _bind_endpoint(
            handler=self.profile,
            endpoint_name="provision_environment_profile",
            request_model=environment_dto.ProvisionEnvironmentProfileRequest,
            response_model=environment_dto.ProvisionEnvironmentProfileResponse,
        )
        self.ontology = _EnvironmentCapabilityHandler(support=support)
        _bind_endpoint(
            handler=self.ontology,
            endpoint_name="attach_environment_ontology",
            request_model=environment_dto.AttachEnvironmentOntologyRequest,
            response_model=environment_dto.AttachEnvironmentOntologyResponse,
        )
        _bind_endpoint(
            handler=self.ontology,
            endpoint_name="ensure_environment_ontology_runtime",
            request_model=environment_dto.EnsureEnvironmentOntologyRuntimeRequest,
            response_model=environment_dto.EnsureEnvironmentOntologyRuntimeResponse,
        )
        _bind_endpoint(
            handler=self.ontology,
            endpoint_name="list_environment_ontologies",
            request_model=environment_dto.ListEnvironmentOntologiesRequest,
            response_model=environment_dto.ListEnvironmentOntologiesResponse,
        )
        self.session = _EnvironmentCapabilityHandler(support=support)
        _bind_endpoint(
            handler=self.session,
            endpoint_name="start_session",
            request_model=environment_dto.StartEnvironmentSessionRequest,
            response_model=StartEnvironmentSessionResponse,
        )
        _bind_endpoint(
            handler=self.session,
            endpoint_name="join_session",
            request_model=environment_dto.JoinEnvironmentSessionRequest,
            response_model=JoinEnvironmentSessionResponse,
        )
        _bind_endpoint(
            handler=self.session,
            endpoint_name="describe_session",
            request_model=environment_dto.DescribeEnvironmentSessionRequest,
            response_model=DescribeEnvironmentSessionResponse,
        )
        _bind_endpoint(
            handler=self.session,
            endpoint_name="resolve_attention",
            request_model=environment_dto.ResolveEnvironmentSessionAttentionRequest,
            response_model=ResolveEnvironmentSessionAttentionResponse,
        )
        _bind_endpoint(
            handler=self.session,
            endpoint_name="mount_attention_session",
            request_model=environment_dto.MountEnvironmentSessionAttentionRequest,
            response_model=environment_dto.MountEnvironmentSessionAttentionResponse,
        )
        self.navigation = _EnvironmentCapabilityHandler(support=support)
        _bind_endpoint(
            handler=self.navigation,
            endpoint_name="create_navigation_context",
            request_model=environment_dto.CreateEnvironmentNavigationContextRequest,
            response_model=(environment_dto.CreateEnvironmentNavigationContextResponse),
        )
        _bind_endpoint(
            handler=self.navigation,
            endpoint_name="select_navigation_target",
            request_model=environment_dto.SelectEnvironmentNavigationTargetRequest,
            response_model=(environment_dto.SelectEnvironmentNavigationTargetResponse),
        )
        _bind_endpoint(
            handler=self.navigation,
            endpoint_name="describe_navigation_context",
            request_model=environment_dto.DescribeEnvironmentNavigationContextRequest,
            response_model=(
                environment_dto.DescribeEnvironmentNavigationContextResponse
            ),
        )
        _bind_endpoint(
            handler=self.navigation,
            endpoint_name="list_navigation_contexts",
            request_model=environment_dto.ListEnvironmentNavigationContextsRequest,
            response_model=(environment_dto.ListEnvironmentNavigationContextsResponse),
        )
        self.function_call = _single_endpoint_capability(
            support=support,
            endpoint_name="invoke_function",
            request_model=environment_dto.InvokeFunctionRequest,
            response_model=InvokeFunctionResponse,
        )


class AwareEnvironmentServiceProtocolHandler:
    def __init__(
        self,
        *,
        resolver: _EnvironmentRuntimeResolverLike | None = None,
        ontology_api_client_provider: OntologyApiClientProvider | None = None,
        ontology_service_route_selector: OntologyServiceApiRouteSelector | None = None,
        actor_admission_backend: EnvironmentActorAdmissionBackend | None = None,
        environment_profile_backend: EnvironmentProfileBackend | None = None,
        environment_session_backend: EnvironmentSessionBackend | None = None,
        environment_session_attention_backend: (
            EnvironmentSessionAttentionBackend | None
        ) = None,
        environment_navigation_backend: EnvironmentNavigationBackend | None = None,
        identity_api_client: IdentityRoleAssignmentApiClient | None = None,
        attention_api_client: AttentionEnvironmentSessionApiClient | None = None,
        host_environment_id_observer: Callable[[UUID], None] | None = None,
        allow_local_function_invocation_fallback: bool = False,
    ) -> None:
        support = _EnvironmentProtocolSupport(
            _resolver=resolver,
            _ontology_api_client_provider=ontology_api_client_provider,
            _ontology_service_route_selector=ontology_service_route_selector,
            _actor_admission_backend=actor_admission_backend,
            _environment_profile_backend=environment_profile_backend,
            _environment_session_backend=environment_session_backend,
            _environment_session_attention_backend=(
                environment_session_attention_backend
            ),
            _environment_navigation_backend=environment_navigation_backend,
            _identity_api_client=identity_api_client,
            _attention_api_client=attention_api_client,
            _host_environment_id_observer=host_environment_id_observer,
            _allow_local_function_invocation_fallback=(
                allow_local_function_invocation_fallback
            ),
        )
        self.environment = EnvironmentApiServiceProtocolHandler(support=support)


def _persistence_backend_name() -> str:
    backend = (os.environ.get("AWARE_PERSISTENCE_BACKEND") or "").strip()
    return backend or "noop"


def _persistence_backend_for_manifest(
    *,
    manifest: object,
    configured_backend: str,
) -> str:
    _ = manifest
    return configured_backend


def _database_url_ref_for_backend(backend: str) -> str | None:
    if backend.strip().casefold() in {"db", "postgres", "postgresql"}:
        return "env:DATABASE_URL"
    return None


def _database_connection_ref_for_ontology_persistence(
    *,
    backend: str,
    host_context: ServiceApiHostContext,
    ontology_service_route_selector: OntologyServiceApiRouteSelector | None = None,
    fallback_ref: str | None,
) -> str | None:
    if backend.strip().casefold() not in {"db", "postgres", "postgresql"}:
        return None
    route = _select_ontology_persistence_route(
        host_context,
        selector=ontology_service_route_selector,
    )
    if route is None:
        return fallback_ref
    if route.route_kind is not ServiceApiDependencyRouteKind.REMOTE_NODE_API_ENDPOINT:
        return fallback_ref
    database_url = (os.environ.get("DATABASE_URL") or "").strip()
    if not database_url:
        raise RuntimeError(
            "Remote Ontology persistence DB readiness requires DATABASE_URL in "
            "the Environment host process so the consumer DB can be passed as a "
            "transportable connection reference."
        )
    return database_url


def _select_ontology_persistence_route(
    host_context: ServiceApiHostContext,
    *,
    selector: OntologyServiceApiRouteSelector | None = None,
) -> ServiceApiDependencyRouteDescriptor | None:
    return select_ontology_service_api_route(
        host_context.service_api_dependency_routes,
        selector=selector,
    )


def _db_backend_target_from_persistence_backend(backend: str) -> str:
    if backend.strip().casefold() in {"db", "postgresql"}:
        return "postgres"
    return backend.strip() or "postgres"


def _environment_ontology_runtime_artifact_set_from_refs(
    artifact_refs: Sequence[object],
) -> Mapping[str, object] | None:
    saw_artifact_set_ref = False
    for artifact_ref in artifact_refs:
        artifact_family = _artifact_ref_text(artifact_ref, "artifact_family")
        artifact_role = _artifact_ref_text(artifact_ref, "artifact_role")
        if artifact_family == "ontology_runtime_artifact_set":
            saw_artifact_set_ref = True
        elif artifact_role != "runtime_artifact_set":
            continue
        artifact_set = _ontology_runtime_artifact_set_from_ref(artifact_ref)
        if artifact_set is None:
            continue
        descriptor = _readiness_descriptor_from_ontology_runtime_artifact_set(
            artifact_set=artifact_set,
            projection_name="Environment",
        )
        if descriptor is not None:
            return artifact_set
    if saw_artifact_set_ref:
        raise RuntimeError(
            "Environment readiness DB artifacts received ontology runtime "
            "artifact-set refs without an Environment runtime projection descriptor."
        )
    return None


def _ontology_database_artifact_receipt_from_artifact_set(
    *,
    artifact_set: Mapping[str, object],
    descriptor: _EnvironmentReadinessArtifactSetDescriptor,
    environment_id: UUID,
    backend_target: str,
) -> OntologyDatabaseArtifactReceipt:
    provenance = _mapping_payload(artifact_set.get("provenance"))
    metadata = _mapping_payload(artifact_set.get("metadata"))
    runtime_bundle_artifact = _required_runtime_artifact_ref(
        artifact_set=artifact_set,
        artifact_role="runtime_bundle_manifest",
    )
    db_schema_registry_artifact = _required_runtime_artifact_ref(
        artifact_set=artifact_set,
        artifact_role="db_schema_registry",
    )
    db_schema_registry_ref = _ontology_database_artifact_ref_from_runtime_artifact(
        db_schema_registry_artifact,
        field_name="db_schema_registry",
    )
    return OntologyDatabaseArtifactReceipt(
        environment_id=environment_id,
        ontology_package_id=_required_uuid_field(
            provenance.get("ontology_package_id"),
            "artifact_set.provenance.ontology_package_id",
        ),
        ontology_manifest_ref=_ontology_database_artifact_ref_from_runtime_artifact(
            runtime_bundle_artifact,
            field_name="runtime_bundle_manifest",
        ),
        ocg_id=descriptor.ocg_id
        or _required_uuid_field(
            provenance.get("object_config_graph_id"),
            "artifact_set.provenance.object_config_graph_id",
        ),
        ocg_hash=_required_text_field(
            metadata.get("object_config_graph_hash"),
            "artifact_set.metadata.object_config_graph_hash",
        ),
        ocg_head_commit_id=_optional_uuid(
            provenance.get("object_config_graph_commit_id")
        ),
        ocg_lane_branch_id=_optional_uuid(provenance.get("ontology_package_id")),
        ocg_lane_projection_hash=descriptor.environment_projection_hash,
        db_schema_registry_ref=db_schema_registry_ref,
        db_schema_hash=db_schema_registry_ref.hash,
        db_backend_target=backend_target,
        db_package_kind=_runtime_artifact_provider_text(
            db_schema_registry_artifact,
            "package_kind",
            default="ontology",
        ),
        sql_roots=list(
            _sql_roots_from_db_schema_registry_artifact(db_schema_registry_artifact)
        ),
        ontology_lock_ref=None,
        ocg_lane_index_ref=None,
    )


def _required_runtime_artifact_ref(
    *,
    artifact_set: Mapping[str, object],
    artifact_role: str,
) -> Mapping[str, object]:
    artifacts = _mapping_sequence(artifact_set.get("artifacts"))
    for artifact in artifacts:
        if _optional_text(artifact.get("artifact_role")) == artifact_role:
            return artifact
    package_name = _optional_text(artifact_set.get("package_name")) or "<unknown>"
    raise RuntimeError(
        f"OntologyRuntimeArtifactSet {package_name!r} does not expose "
        f"artifact_role={artifact_role!r}."
    )


def _ontology_database_artifact_ref_from_runtime_artifact(
    artifact_ref: Mapping[str, object],
    *,
    field_name: str,
) -> OntologyDatabaseArtifactRef:
    path = (
        _optional_text(artifact_ref.get("manifest_path"))
        or _optional_text(artifact_ref.get("workspace_relative_path"))
        or _optional_text(artifact_ref.get("uri"))
    )
    if path is None:
        raise RuntimeError(f"Ontology runtime artifact {field_name} is missing path.")
    digest = _optional_text(artifact_ref.get("digest")) or _optional_text(
        _mapping_payload(artifact_ref.get("receipt")).get("hash")
    )
    if digest is None:
        raise RuntimeError(f"Ontology runtime artifact {field_name} is missing digest.")
    return OntologyDatabaseArtifactRef(
        path=Path(path).as_posix(),
        hash=digest,
    )


def _sql_roots_from_db_schema_registry_artifact(
    artifact_ref: Mapping[str, object],
) -> tuple[str, ...]:
    provider_payload = _mapping_payload(artifact_ref.get("provider_payload"))
    receipt = _mapping_payload(artifact_ref.get("receipt"))
    sql_roots = _text_tuple(provider_payload.get("sql_roots")) or _text_tuple(
        receipt.get("sql_roots")
    )
    if not sql_roots:
        raise RuntimeError(
            "Ontology db_schema_registry artifact is missing provider_payload.sql_roots."
        )
    return tuple(Path(path).as_posix() for path in sql_roots)


def _runtime_artifact_provider_text(
    artifact_ref: Mapping[str, object],
    key: str,
    *,
    default: str,
) -> str:
    provider_payload = _mapping_payload(artifact_ref.get("provider_payload"))
    value = _optional_text(provider_payload.get(key))
    return value or default


def _required_uuid_field(value: object, field_name: str) -> UUID:
    if value is None or not str(value).strip():
        raise RuntimeError(f"{field_name} is required.")
    return _required_uuid(value)


def _required_text_field(value: object, field_name: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise RuntimeError(f"{field_name} is required.")
    return text


def _required_uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _optional_uuid(value: object | None) -> UUID | None:
    if value is None:
        return None
    return _required_uuid(value)


class _OntologyGraphMetaReadinessClient:
    """Meta-readiness-shaped port backed by the selected Ontology authority."""

    def __init__(self, *, graph: _OntologyGraphReadinessClient) -> None:
        self._graph = graph

    async def resolve_projection(
        self,
        request: MetaGraphResolveProjectionRequest,
    ) -> MetaGraphResolveProjectionResponse:
        response = await self._graph.resolve_projection(
            OntologyGraphResolveProjectionRequest(
                actor_id=request.actor_id,
                projection_name=request.projection_name,
                projection_hash=request.projection_hash,
                object_projection_graph_id=request.object_projection_graph_id,
                include_available=request.include_available,
            )
        )
        return MetaGraphResolveProjectionResponse.model_validate(
            response.model_dump(mode="python")
            if isinstance(response, BaseModel)
            else response
        )

    async def get_lane_head(
        self,
        request: MetaGraphGetLaneHeadRequest,
    ) -> MetaGraphGetLaneHeadResponse:
        response = await self._graph.get_lane_head(
            OntologyGraphGetLaneHeadRequest(
                actor_id=request.actor_id,
                domain_branch_id=request.domain_branch_id,
                domain_projection_hash=request.domain_projection_hash,
            )
        )
        return MetaGraphGetLaneHeadResponse.model_validate(
            response.model_dump(mode="python")
            if isinstance(response, BaseModel)
            else response
        )

    async def get_object_instance_graph_commit(
        self,
        request: MetaGraphGetObjectInstanceGraphCommitRequest,
    ) -> MetaGraphGetObjectInstanceGraphCommitResponse:
        response = await self._graph.get_object_instance_graph_commit(
            OntologyGraphGetObjectInstanceGraphCommitRequest(
                actor_id=request.actor_id,
                domain_branch_id=request.domain_branch_id,
                domain_projection_hash=request.domain_projection_hash,
                domain_commit_id=request.domain_commit_id,
            )
        )
        return MetaGraphGetObjectInstanceGraphCommitResponse.model_validate(
            response.model_dump(mode="python")
            if isinstance(response, BaseModel)
            else response
        )

    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse:
        response = await self._graph.invoke_function(
            OntologyGraphInvokeFunctionRequest(
                actor_id=request.actor_id,
                domain_branch_id=request.domain_branch_id,
                domain_projection_hash=request.domain_projection_hash,
                call_target=OntologyGraphFunctionCallTarget(request.call_target.value),
                target_object_id=request.target_object_id,
                object_projection_graph_id=request.object_projection_graph_id,
                function_id=request.function_id,
                args=request.args,
                kwargs=request.kwargs,
                expected_graph_hash_pre=request.expected_graph_hash_pre,
                expected_head_commit_id=request.expected_head_commit_id,
                commit=request.commit,
                publish=request.publish,
            )
        )
        return MetaGraphInvokeFunctionResponse.model_validate(
            _meta_graph_invoke_payload_from_ontology_response(response)
        )


def _meta_graph_invoke_payload_from_ontology_response(
    response: object,
) -> dict[str, object]:
    payload = _payload_dict(response)
    if "required_reactions" in payload:
        payload["required_meta_reactions"] = payload.pop("required_reactions")
    commit_event = payload.get("commit_event")
    if commit_event is not None:
        payload["commit_event"] = _meta_commit_event_payload_from_ontology(commit_event)
    return payload


def _meta_commit_event_payload_from_ontology(event: object) -> dict[str, object]:
    payload = _payload_dict(event)
    payload["event_family"] = "meta.oig_commit"
    payload["meta_authority_id"] = payload.pop(
        "ontology_authority_id",
        "aware_ontology",
    )
    if "required_reactions" in payload:
        payload["required_meta_reactions"] = payload.pop("required_reactions")

    commit_action = payload.get("commit_action")
    if commit_action is not None:
        action_payload = _payload_dict(commit_action)
        call_target = action_payload.get("call_target")
        if call_target is not None:
            raw_call_target = getattr(call_target, "value", call_target)
            action_payload["call_target"] = MetaGraphFunctionCallTarget(
                raw_call_target
            ).value
        payload["commit_action"] = action_payload
    return payload


def _payload_dict(value: object) -> dict[str, object]:
    if isinstance(value, BaseModel):
        return dict(cast(dict[str, object], value.model_dump(mode="python")))
    if isinstance(value, dict):
        return dict(cast(dict[str, object], value))
    raise TypeError(f"Expected pydantic-compatible payload, got {type(value).__name__}")


def _ontology_graph_meta_readiness_client(
    client: object,
) -> _MetaGraphReadinessClient:
    graph = _ontology_graph_port(client)
    if (
        not hasattr(graph, "resolve_projection")
        or not hasattr(graph, "get_lane_head")
        or not hasattr(graph, "invoke_function")
    ):
        raise RuntimeError(
            "Configured Ontology API client does not expose ontology.graph "
            "resolve_projection/get_lane_head/invoke_function."
        )
    return cast(
        _MetaGraphReadinessClient,
        _OntologyGraphMetaReadinessClient(
            graph=cast(_OntologyGraphReadinessClient, graph)
        ),
    )


def _ontology_graph_meta_invoke_client(client: object) -> _MetaGraphInvokeClient:
    graph = _ontology_graph_port(client)
    if not hasattr(graph, "invoke_function"):
        raise RuntimeError(
            "Configured Ontology API client does not expose "
            "ontology.graph.invoke_function."
        )
    return cast(
        _MetaGraphInvokeClient,
        _OntologyGraphMetaReadinessClient(
            graph=cast(_OntologyGraphReadinessClient, graph)
        ),
    )


def _ontology_graph_meta_commit_read_client(
    client: object,
) -> _MetaGraphCommitReadClient:
    graph = _ontology_graph_port(client)
    if not hasattr(graph, "get_object_instance_graph_commit"):
        raise RuntimeError(
            "Configured Ontology API client does not expose "
            "ontology.graph.get_object_instance_graph_commit."
        )
    return cast(
        _MetaGraphCommitReadClient,
        _OntologyGraphMetaReadinessClient(
            graph=cast(_OntologyGraphReadinessClient, graph)
        ),
    )


def _ontology_graph_port(client: object) -> object:
    graph = getattr(client, "graph", None)
    if graph is None:
        ontology = getattr(client, "ontology", None)
        graph = getattr(ontology, "graph", None) if ontology is not None else None
    if graph is None:
        raise RuntimeError(
            "Configured Ontology API client does not expose ontology.graph."
        )
    return graph


def _ontology_persistence_readiness_client(
    client: object,
) -> _OntologyPersistenceReadinessClient:
    persistence = getattr(client, "persistence", None)
    if persistence is None:
        ontology = getattr(client, "ontology", None)
        persistence = (
            getattr(ontology, "persistence", None) if ontology is not None else None
        )
    if persistence is None or not hasattr(persistence, "ensure_ready"):
        raise RuntimeError(
            "Configured Ontology API client does not expose "
            "ontology.persistence.ensure_ready."
        )
    return cast(_OntologyPersistenceReadinessClient, persistence)


def _ontology_runtime_artifact_set_client(
    client: object,
) -> _OntologyRuntimeArtifactSetClient:
    runtime = getattr(client, "runtime", None)
    if runtime is None:
        ontology = getattr(client, "ontology", None)
        runtime = getattr(ontology, "runtime", None) if ontology is not None else None
    if runtime is None or not hasattr(runtime, "resolve_runtime_artifact_set"):
        raise RuntimeError(
            "Configured Ontology API client does not expose "
            "ontology.runtime.resolve_runtime_artifact_set."
        )
    return cast(_OntologyRuntimeArtifactSetClient, runtime)


def _local_function_invocation_fallback_enabled(*, requested: bool) -> bool:
    if not requested:
        return False
    value = os.environ.get(_LOCAL_FUNCTION_INVOCATION_FALLBACK_ENV, "")
    return value.strip().casefold() in {"1", "true", "yes", "on"}


async def invoke_environment_function_via_ontology_api(
    *,
    request: environment_dto.InvokeFunctionRequest,
    ontology_api_client_provider: OntologyApiClientProvider | None,
    missing_route_error: str | None = None,
) -> environment_dto.InvokeFunctionResponse | None:
    actor_id = request.actor_id
    if actor_id is None:
        return _failed_invoke_function_response(
            request=request,
            error="Environment function-call mutation requires actor_id.",
        )

    ontology_provider_configured = ontology_api_client_provider is not None
    ontology_client = (
        ontology_api_client_provider()
        if ontology_api_client_provider is not None
        else None
    )
    graph_client: _MetaGraphInvokeClient | None = None
    if ontology_client is not None:
        try:
            graph_client = _ontology_graph_meta_invoke_client(ontology_client)
        except RuntimeError as exc:
            return _failed_invoke_function_response(
                request=request,
                error=str(exc),
            )
    elif ontology_provider_configured:
        return _failed_invoke_function_response(
            request=request,
            error=(
                "Environment function-call mutation requires the configured "
                "Ontology graph API route to be available."
            ),
        )

    if graph_client is None:
        if missing_route_error is None:
            return None
        return _failed_invoke_function_response(
            request=request,
            error=missing_route_error,
        )

    response = await graph_client.invoke_function(
        _meta_invoke_function_request_from_environment(
            request=request,
            actor_id=actor_id,
        )
    )
    return _environment_invoke_function_response_from_meta(
        request=request,
        response=response,
    )


def _meta_invoke_function_request_from_environment(
    *,
    request: environment_dto.InvokeFunctionRequest,
    actor_id: Any,
) -> MetaGraphInvokeFunctionRequest:
    return MetaGraphInvokeFunctionRequest(
        actor_id=actor_id,
        domain_branch_id=request.branch_id,
        domain_projection_hash=request.projection_hash,
        call_target=MetaGraphFunctionCallTarget(request.call_target.value),
        target_object_id=request.object_id,
        object_projection_graph_id=request.object_projection_graph_id,
        function_id=request.function_id,
        args=request.args,
        kwargs=request.kwargs,
        expected_graph_hash_pre=request.expected_graph_hash_pre,
        expected_head_commit_id=request.expected_head_commit_id,
        commit=request.commit,
        publish=request.publish,
    )


def _environment_invoke_function_response_from_meta(
    *,
    request: environment_dto.InvokeFunctionRequest,
    response: MetaGraphInvokeFunctionResponse,
) -> environment_dto.InvokeFunctionResponse:
    commit_event = response.commit_event
    object_instance_graph_identity_id = (
        commit_event.object_instance_graph_identity_id
        if commit_event is not None
        else None
    )
    object_instance_graph_id = (
        commit_event.object_instance_graph_id if commit_event is not None else None
    )
    return environment_dto.InvokeFunctionResponse(
        actor_id=response.actor_id,
        environment_id=request.environment_id,
        process_id=request.process_id,
        thread_id=request.thread_id,
        branch_id=response.domain_branch_id,
        projection_hash=response.domain_projection_hash,
        status=response.status,
        payload=response.payload,
        error=response.error,
        logs=response.logs,
        execution_time_ms=response.execution_time_ms,
        root_object_id=response.root_object_id,
        graph_hash_pre=response.graph_hash_pre,
        graph_hash_post=response.graph_hash_post,
        function_call_id=response.function_call_id,
        function_call_response_id=response.function_call_response_id,
        changes=response.changes,
        commit_id=response.domain_commit_id,
        object_instance_graph_commit_id=response.object_instance_graph_commit_id,
        object_projection_graph_id=request.object_projection_graph_id,
        object_projection_graph_identity_id=request.object_projection_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_branch_id=_environment_oig_branch_id(
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            branch_id=response.domain_branch_id,
        ),
    )


def _environment_oig_branch_id(
    *,
    object_instance_graph_identity_id: UUID | None,
    branch_id: UUID | None,
) -> UUID | None:
    if object_instance_graph_identity_id is None or branch_id is None:
        return None
    return stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        branch_id=branch_id,
    )


def _failed_invoke_function_response(
    *,
    request: environment_dto.InvokeFunctionRequest,
    error: str,
) -> environment_dto.InvokeFunctionResponse:
    return environment_dto.InvokeFunctionResponse(
        actor_id=request.actor_id,
        environment_id=request.environment_id,
        process_id=request.process_id,
        thread_id=request.thread_id,
        branch_id=request.branch_id,
        projection_hash=request.projection_hash,
        status="failed",
        error=error,
    )


def _failed_attach_environment_ontology_response(
    *,
    request: environment_dto.AttachEnvironmentOntologyRequest,
    error: str,
    actor_id: UUID | None = None,
    evidence: Mapping[str, object] | None = None,
) -> environment_dto.AttachEnvironmentOntologyResponse:
    return environment_dto.AttachEnvironmentOntologyResponse(
        operation="attach_environment_ontology",
        actor_id=actor_id or request.actor_id,
        environment_id=request.environment_id,
        process_id=request.process_id,
        thread_id=request.thread_id,
        branch_id=request.branch_id,
        projection_hash=request.projection_hash,
        status="failed",
        error=error,
        evidence=dict(evidence or {}),
    )


def _failed_ensure_environment_ontology_runtime_response(
    *,
    request: environment_dto.EnsureEnvironmentOntologyRuntimeRequest,
    error: str,
    actor_id: UUID | None = None,
    evidence: Mapping[str, object] | None = None,
) -> environment_dto.EnsureEnvironmentOntologyRuntimeResponse:
    return environment_dto.EnsureEnvironmentOntologyRuntimeResponse(
        operation="ensure_environment_ontology_runtime",
        actor_id=actor_id or request.actor_id,
        environment_id=request.environment_id,
        process_id=request.process_id,
        thread_id=request.thread_id,
        branch_id=request.branch_id,
        projection_hash=request.projection_hash,
        status="failed",
        error=error,
        ontology_id=request.ontology_id,
        package_name=request.package_name,
        fqn_prefix=request.fqn_prefix,
        artifact_set_id=request.artifact_set_id,
        membership_commit_id=request.membership_commit_id,
        evidence=dict(evidence or {}),
    )


def _resolved_runtime_function_target(
    *,
    response: environment_dto.ResolveRuntimeRefsResponse,
    query_key: str,
) -> environment_dto.ResolvedRuntimeFunctionTarget | None:
    for target in response.function_targets:
        if target.query_key == query_key:
            return target
    return response.function_targets[0] if response.function_targets else None


def _environment_ontology_memberships_from_environment_payload(
    payload: object,
    *,
    commit_id: UUID | None,
    graph_hash_post: str | None,
) -> list[environment_dto.EnvironmentOntologyMembership]:
    environment_payload = _payload_mapping(payload)
    raw_memberships = (
        environment_payload.get("ontologies")
        or environment_payload.get("environment_ontologies")
        or []
    )
    if not isinstance(raw_memberships, Sequence) or isinstance(
        raw_memberships,
        (str, bytes),
    ):
        return []
    memberships: list[environment_dto.EnvironmentOntologyMembership] = []
    for raw_membership in raw_memberships:
        try:
            membership = _environment_ontology_membership_from_payload(
                payload=raw_membership,
                ontology_id=None,
                role="runtime",
                status="active",
                title=None,
                description=None,
                commit_id=commit_id,
                graph_hash_post=graph_hash_post,
            )
            memberships.append(membership)
        except RuntimeError:
            continue
    return memberships


def _environment_ontology_membership_from_payload(
    *,
    payload: object,
    ontology_id: UUID | None,
    role: str,
    status: str,
    title: str | None,
    description: str | None,
    commit_id: UUID | None,
    graph_hash_post: str | None,
) -> environment_dto.EnvironmentOntologyMembership:
    value = _unwrap_invocation_value(payload)
    mapping = _payload_mapping(value)
    ontology_payload = _payload_mapping(mapping.get("ontology"))
    resolved_ontology_id = (
        _optional_uuid(mapping.get("ontology_id"))
        or _optional_uuid(ontology_payload.get("id"))
        or ontology_id
    )
    if resolved_ontology_id is None:
        raise RuntimeError(
            "EnvironmentOntology membership payload did not expose ontology_id."
        )
    return environment_dto.EnvironmentOntologyMembership(
        environment_ontology_id=(
            _optional_uuid(mapping.get("environment_ontology_id"))
            or _optional_uuid(mapping.get("id"))
        ),
        ontology_id=resolved_ontology_id,
        role=_optional_text(mapping.get("role")) or role,
        status=_optional_text(mapping.get("status")) or status,
        title=_optional_text(mapping.get("title")) or title,
        description=_optional_text(mapping.get("description")) or description,
        commit_id=commit_id,
        graph_hash_post=graph_hash_post,
        evidence={
            "source": "environment_ontology_membership_pointer",
            "payload_keys": sorted(str(key) for key in mapping.keys()),
        },
    )


def _unwrap_invocation_value(payload: object) -> object:
    mapping = _payload_mapping(payload)
    if set(mapping.keys()) == {"value"}:
        return mapping["value"]
    return payload


def _payload_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json", exclude_none=True)
        if isinstance(dumped, Mapping):
            return {str(key): item for key, item in dumped.items()}
    return {}


__all__ = [
    "EnvironmentServiceBackend",
    "EnvironmentProfileBackend",
    "invoke_environment_function_via_ontology_api",
    "AwareEnvironmentServiceProtocolHandler",
    "EnvironmentApiServiceProtocolHandler",
    "build_aware_environment_service_protocol_handler",
    "AdmitEnvironmentActorRequest",
    "ConfigureServiceApiDependencyRoutesRequest",
    "DescribeEnvironmentConfigRequest",
    "DescribeEnvironmentRequest",
    "DescribeEnvironmentStatusRequest",
    "DescribeEnvironmentTopologyRequest",
    "EnsureEnvironmentOntologyRuntimeRequest",
    "EnsureReadyRequest",
    "AttachEnvironmentOntologyRequest",
    "FetchCapabilitiesRequest",
    "GetLaneHeadRequest",
    "GetObjectInstanceGraphCommitRequest",
    "InvokeFunctionRequest",
    "ListEnvironmentOntologiesRequest",
    "MaterializeCommittedProjectionDtoRequest",
    "ResolveRuntimeRefsRequest",
]
