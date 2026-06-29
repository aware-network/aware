from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar
from uuid import UUID

from aware_api_ontology.api.api import Api
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_request_config import (
    ApiCapabilityEndpointRequestConfig,
)
from aware_api_ontology.api.api_capability_endpoint_stream_config import (
    ApiCapabilityEndpointStreamConfig,
)
from aware_api_ontology.api.api_capability_endpoint_stream_event_config import (
    ApiCapabilityEndpointStreamEventConfig,
)
from aware_api_ontology.api.api_graph_capability_function import (
    ApiGraphCapabilityFunction,
)
from aware_api_ontology.api.api_package import ApiPackage
from aware_api_ontology.stable_ids import stable_api_package_id
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_orm.models.orm_model import ORMModel

from .invocation.spec import (
    ApiInvocationApiSpec,
    ApiInvocationCapabilitySpec,
    ApiInvocationEndpointSpec,
    ApiInvocationFulfillmentBindingSpec,
    ApiInvocationManifest,
    ApiInvocationRequestSpec,
    ApiInvocationResponseSpec,
    ApiInvocationStreamEventSpec,
    ApiInvocationStreamSpec,
)
from .invocation.resolution import ApiInvocationSourceCommit

_TRoot = TypeVar("_TRoot", bound=ORMModel)


@dataclass(frozen=True, slots=True)
class ApiRuntimePackageRef:
    """Runtime ref for a Workspace-selected ApiPackage semantic package."""

    family_key: str
    package_kind: str
    package_name: str
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_branch_id: str | None = None
    semantic_projection_name: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    source_code_package_id: str | None = None
    manifest_path: str | None = None
    manifest_toml_path: str | None = None

    @property
    def has_semantic_identity(self) -> bool:
        return bool(_clean(self.semantic_package_id) or _clean(self.semantic_root_id))


@dataclass(frozen=True, slots=True)
class ResolvedApiRuntimePackageRef:
    """Resolved ApiPackage semantic coordinates plus invocation runtime view."""

    package_ref: ApiRuntimePackageRef
    api_package_id: UUID
    api_id: UUID
    package_name: str
    api_name: str
    fqn_prefix: str | None
    invocation_manifest: ApiInvocationManifest
    semantic_branch_id: UUID | None = None
    semantic_head_commit_id: UUID | None = None
    semantic_projection_hash: str | None = None
    api_projection_hash: str | None = None
    api_domain_commit_id: UUID | None = None
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_projection_name: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    api_object_instance_graph_commit_id: UUID | None = None
    source_code_package_id: str | None = None
    manifest_path: str | None = None
    manifest_toml_path: str | None = None


async def resolve_api_runtime_package_ref(
    *,
    index: MetaGraphRuntimeIndex,
    package_ref: ApiRuntimePackageRef,
) -> ResolvedApiRuntimePackageRef:
    """Resolve one committed Workspace ApiPackage ref into API invocation metadata."""

    validate_api_runtime_package_ref(package_ref)
    package_commit_ref_label = "semantic_object_instance_graph_commit_id"
    package_commit_ref_value = _clean(
        package_ref.semantic_object_instance_graph_commit_id
    )
    if package_commit_ref_value is None:
        package_commit_ref_label = "semantic_head_commit_id"
        package_commit_ref_value = _clean(package_ref.semantic_head_commit_id)
    package_commit_ref_id = _required_uuid(
        package_commit_ref_value,
        label=package_commit_ref_label,
    )
    api_package_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ApiPackage",
    )
    api_package_id = _optional_uuid(
        package_ref.semantic_package_id
    ) or stable_api_package_id(
        name=package_ref.package_name,
    )
    store = FSCommitStore()
    branch_id = _optional_uuid(package_ref.semantic_branch_id)
    if branch_id is None:
        if _clean(package_ref.semantic_object_instance_graph_commit_id) is None:
            raise RuntimeError(
                "Branchless API runtime package refs require "
                "semantic_object_instance_graph_commit_id; legacy "
                "semantic_head_commit_id refs must also provide semantic_branch_id."
            )
        package_commit_refs = (
            await store.domain_commit_refs_for_object_instance_graph_commit_id(
                projection_hash=api_package_projection_hash,
                object_instance_graph_commit_id=package_commit_ref_id,
            )
        )
        if not package_commit_refs:
            raise RuntimeError(
                "API runtime package ref semantic_object_instance_graph_commit_id "
                "did not resolve to any indexed ApiPackage branch: "
                f"semantic_object_instance_graph_commit_id={package_commit_ref_id} "
                f"projection_hash={api_package_projection_hash}"
            )
        if len(package_commit_refs) != 1:
            raise RuntimeError(
                "API runtime package ref semantic_object_instance_graph_commit_id "
                "resolved to multiple ApiPackage branches: "
                f"semantic_object_instance_graph_commit_id={package_commit_ref_id} "
                f"projection_hash={api_package_projection_hash} "
                f"branches={[str(ref.branch_id) for ref in package_commit_refs]!r}"
            )
        package_commit_ref = package_commit_refs[0]
        branch_id = package_commit_ref.branch_id
        api_package_domain_commit_id = package_commit_ref.domain_commit_id
    else:
        api_package_domain_commit_id = (
            await store.domain_commit_id_for_object_instance_graph_commit_id(
                branch_id=branch_id,
                projection_hash=api_package_projection_hash,
                object_instance_graph_commit_id=package_commit_ref_id,
            )
        )
        if api_package_domain_commit_id is None:
            legacy_domain_commit = await store.get_commit(
                branch_id=branch_id,
                projection_hash=api_package_projection_hash,
                commit_id=package_commit_ref_id,
            )
            if legacy_domain_commit is None:
                raise RuntimeError(
                    f"API runtime package ref {package_commit_ref_label} is neither "
                    "an indexed ObjectInstanceGraphCommit id nor a domain commit id: "
                    f"{package_commit_ref_label}={package_commit_ref_id} "
                    f"branch_id={branch_id} projection_hash={api_package_projection_hash}"
                )
            api_package_domain_commit_id = package_commit_ref_id
    api_package = await _hydrate_root_from_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=api_package_projection_hash,
        commit_id=api_package_domain_commit_id,
        root_id=api_package_id,
        root_type=ApiPackage,
        hydrate_portal_targets=True,
    )
    if api_package is None:
        raise RuntimeError(
            "API runtime package ref could not hydrate ApiPackage from semantic "
            f"commit: package_name={package_ref.package_name!r} "
            f"semantic_package_id={api_package_id}"
        )

    api_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="Api",
    )
    api_domain_commit_ref = await _api_domain_commit_ref_from_package(
        index=index,
        store=store,
        api_package=api_package,
        branch_id=branch_id,
        preferred_projection_hash=api_projection_hash,
    )
    api_domain_commit_id = (
        api_domain_commit_ref[1] if api_domain_commit_ref is not None else None
    )
    if api_domain_commit_ref is not None:
        api_projection_hash = api_domain_commit_ref[0]
    if (
        api_package.api_object_instance_graph_commit_id is not None
        and api_domain_commit_id is None
    ):
        raise RuntimeError(
            "API runtime package ref resolved ApiPackage with a pinned "
            "api_object_instance_graph_commit_id, but the commit store could not "
            "resolve its domain commit id: "
            f"api_package={api_package.id} "
            f"api_object_instance_graph_commit_id={api_package.api_object_instance_graph_commit_id}"
        )
    api = api_package.api if _api_has_invocation_surface(api_package.api) else None
    if api is None:
        api_id = _expected_api_id_from_ref(
            package_ref=package_ref,
            api_package=api_package,
        )
        api = (
            await _hydrate_root_from_commit(
                index=index,
                branch_id=branch_id,
                projection_hash=api_projection_hash,
                commit_id=api_domain_commit_id,
                root_id=api_id,
                root_type=Api,
                hydrate_portal_targets=True,
            )
            if api_domain_commit_id is not None
            else await _hydrate_root_from_head(
                index=index,
                branch_id=branch_id,
                projection_hash=api_projection_hash,
                root_id=api_id,
                root_type=Api,
                hydrate_portal_targets=True,
            )
        )
    if api is None:
        raise RuntimeError(
            "API runtime package ref could not hydrate Api graph truth for "
            f"package_name={package_ref.package_name!r} api_id={api_package.api_id}"
        )

    return build_api_runtime_package_binding_from_objects(
        index=index,
        package_ref=package_ref,
        api_package=api_package,
        api=api,
        semantic_branch_id=branch_id,
        semantic_projection_hash=api_package_projection_hash,
        api_projection_hash=api_projection_hash,
        api_domain_commit_id=api_domain_commit_id,
    )


def build_api_runtime_package_binding_from_objects(
    *,
    index: MetaGraphRuntimeIndex,
    package_ref: ApiRuntimePackageRef,
    api_package: ApiPackage,
    api: Api,
    semantic_branch_id: UUID | None = None,
    semantic_head_commit_id: UUID | None = None,
    semantic_projection_hash: str | None = None,
    api_projection_hash: str | None = None,
    api_domain_commit_id: UUID | None = None,
) -> ResolvedApiRuntimePackageRef:
    """Build the API runtime binding from already-hydrated ontology objects."""

    validate_api_runtime_package_ref(package_ref)
    _validate_package_objects(
        package_ref=package_ref,
        api_package=api_package,
        api=api,
    )
    invocation_manifest = build_api_invocation_manifest_from_api_package(
        index=index,
        api_package=api_package,
        api=api,
    )
    return ResolvedApiRuntimePackageRef(
        package_ref=package_ref,
        api_package_id=api_package.id,
        api_id=api.id,
        package_name=api_package.name,
        api_name=api.name,
        fqn_prefix=_clean(api_package.fqn_prefix),
        invocation_manifest=invocation_manifest,
        semantic_branch_id=semantic_branch_id
        or _optional_uuid(package_ref.semantic_branch_id),
        semantic_head_commit_id=semantic_head_commit_id
        or _optional_uuid(package_ref.semantic_head_commit_id),
        semantic_projection_hash=semantic_projection_hash,
        api_projection_hash=api_projection_hash
        or find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="Api",
        ),
        api_domain_commit_id=api_domain_commit_id
        or _api_domain_commit_id_from_package(api_package),
        workspace_package_id=_clean(package_ref.workspace_package_id),
        semantic_package_id=_clean(package_ref.semantic_package_id),
        semantic_object_instance_graph_commit_id=_clean(
            package_ref.semantic_object_instance_graph_commit_id
        ),
        semantic_projection_name=_clean(package_ref.semantic_projection_name),
        semantic_root_kind=_clean(package_ref.semantic_root_kind),
        semantic_root_id=_clean(package_ref.semantic_root_id),
        api_object_instance_graph_commit_id=api_package.api_object_instance_graph_commit_id,
        source_code_package_id=_clean(package_ref.source_code_package_id),
        manifest_path=_clean(package_ref.manifest_path),
        manifest_toml_path=_clean(package_ref.manifest_toml_path),
    )


def build_api_invocation_source_commit_from_package_ref(
    binding: ResolvedApiRuntimePackageRef,
) -> ApiInvocationSourceCommit:
    """Build explicit API source commit authority for package-ref dispatch."""

    if binding.semantic_branch_id is None:
        raise RuntimeError("API package-ref dispatch requires semantic_branch_id.")
    api_projection_hash = (binding.api_projection_hash or "").strip()
    if not api_projection_hash:
        raise RuntimeError("API package-ref dispatch requires api_projection_hash.")
    if binding.api_domain_commit_id is None:
        raise RuntimeError(
            "API package-ref dispatch requires pinned api_domain_commit_id. "
            "Package refs without ApiPackage.api_object_instance_graph_commit are migration-only."
        )
    return ApiInvocationSourceCommit(
        branch_id=binding.semantic_branch_id,
        projection_hash=api_projection_hash,
        commit_id=binding.api_domain_commit_id,
        object_instance_graph_commit_id=binding.api_object_instance_graph_commit_id,
    )


def build_api_invocation_manifest_from_api_package(
    *,
    index: MetaGraphRuntimeIndex,
    api_package: ApiPackage,
    api: Api,
) -> ApiInvocationManifest:
    """Create the invocation runtime view from committed ApiPackage ontology truth."""

    _validate_api_package_api_pair(api_package=api_package, api=api)
    source_path = _api_package_source_path(api_package)
    return ApiInvocationManifest(
        schema_version=1,
        package_name=_required_token("api_package.name", api_package.name),
        fqn_prefix=_clean(api_package.fqn_prefix) or "",
        apis=[
            ApiInvocationApiSpec(
                name=_required_token("api.name", api.name),
                source_path=source_path,
                capabilities=[
                    ApiInvocationCapabilitySpec(
                        name=_required_token("api_capability.name", capability.name),
                        source_path=source_path,
                        endpoints=[
                            _endpoint_spec_from_ontology(
                                index=index,
                                api=api,
                                capability_name=capability.name,
                                endpoint=endpoint,
                                source_path=source_path,
                            )
                            for endpoint in capability.api_capability_endpoints
                        ],
                        description=capability.description,
                    )
                    for capability in api.api_capabilities
                ],
            )
        ],
    )


def validate_api_runtime_package_ref(package_ref: ApiRuntimePackageRef) -> None:
    if _clean(package_ref.family_key) != "api":
        raise RuntimeError(
            "API runtime package ref requires family_key='api': "
            f"{package_ref.family_key!r}"
        )
    if _clean(package_ref.package_kind) != "api":
        raise RuntimeError(
            "API runtime package ref requires package_kind='api': "
            f"{package_ref.package_kind!r}"
        )
    if not _clean(package_ref.package_name):
        raise RuntimeError("API runtime package ref requires a package_name.")

    semantic_projection_name = _clean(package_ref.semantic_projection_name)
    if (
        semantic_projection_name is not None
        and semantic_projection_name != "ApiPackage"
    ):
        raise RuntimeError(
            "API runtime package ref requires semantic_projection_name='ApiPackage' "
            f"when provided: {semantic_projection_name!r}"
        )

    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    if semantic_root_kind is not None and semantic_root_kind not in {
        "api",
        "api_package",
    }:
        raise RuntimeError(
            "API runtime package ref semantic_root_kind must be 'api' or "
            f"'api_package' when provided: {semantic_root_kind!r}"
        )


def _endpoint_spec_from_ontology(
    *,
    index: MetaGraphRuntimeIndex,
    api: Api,
    capability_name: str,
    endpoint: ApiCapabilityEndpoint,
    source_path: str,
) -> ApiInvocationEndpointSpec:
    request_config = endpoint.request_config
    if request_config is None:
        raise RuntimeError(
            "API invocation metadata requires endpoint request_config: "
            f"endpoint={endpoint.name!r}"
        )
    endpoint_name = _required_token("api_capability_endpoint.name", endpoint.name)
    normalized_capability_name = _required_token(
        "api_capability.name",
        capability_name,
    )
    api_name = _required_token("api.name", api.name)
    endpoint_ref = ".".join((api_name, normalized_capability_name, endpoint_name))
    return ApiInvocationEndpointSpec(
        name=endpoint_name,
        source_path=source_path,
        endpoint_ref=endpoint_ref,
        discriminant=endpoint_ref,
        invocation_kind="shared_client_endpoint",
        client_backend="aware_api.invoker.AwareApiEndpointInvoker",
        client_operation="invoke_api_endpoint",
        addressing_strategy="session_bound",
        request=_request_spec_from_ontology(
            index=index,
            request_config=request_config,
            source_path=source_path,
        ),
        response=_response_spec_from_ontology(
            index=index,
            request_config=request_config,
            source_path=source_path,
        ),
        stream=_stream_spec_from_ontology(
            index=index,
            request_config=request_config,
            source_path=source_path,
        ),
        fulfillment_bindings=_fulfillment_bindings_from_ontology(
            api=api,
            endpoint=endpoint,
            source_path=source_path,
        ),
        description=endpoint.description,
    )


def _request_spec_from_ontology(
    *,
    index: MetaGraphRuntimeIndex,
    request_config: ApiCapabilityEndpointRequestConfig,
    source_path: str,
) -> ApiInvocationRequestSpec:
    return ApiInvocationRequestSpec(
        class_ref=_class_ref_for_config_id(
            index=index,
            class_config_id=request_config.class_config_id,
            class_config=request_config.class_config,
            label="request_config.class_config_id",
        ),
        source_path=source_path,
        description=request_config.description,
    )


def _response_spec_from_ontology(
    *,
    index: MetaGraphRuntimeIndex,
    request_config: ApiCapabilityEndpointRequestConfig,
    source_path: str,
) -> ApiInvocationResponseSpec | None:
    response_config = request_config.response_config
    if response_config is None:
        return None
    return ApiInvocationResponseSpec(
        class_ref=_class_ref_for_config_id(
            index=index,
            class_config_id=response_config.class_config_id,
            class_config=response_config.class_config,
            label="response_config.class_config_id",
        ),
        source_path=source_path,
        description=response_config.description,
    )


def _stream_spec_from_ontology(
    *,
    index: MetaGraphRuntimeIndex,
    request_config: ApiCapabilityEndpointRequestConfig,
    source_path: str,
) -> ApiInvocationStreamSpec | None:
    stream_config = request_config.stream_config
    if stream_config is None:
        return None
    return ApiInvocationStreamSpec(
        stream_mode=_enum_text(stream_config.stream_mode),
        source_path=source_path,
        events=[
            _stream_event_spec_from_ontology(
                index=index,
                stream_config=stream_config,
                event_config=event_config,
                source_path=source_path,
            )
            for event_config in stream_config.api_capability_endpoint_stream_event_configs
        ],
        description=stream_config.description,
    )


def _stream_event_spec_from_ontology(
    *,
    index: MetaGraphRuntimeIndex,
    stream_config: ApiCapabilityEndpointStreamConfig,
    event_config: ApiCapabilityEndpointStreamEventConfig,
    source_path: str,
) -> ApiInvocationStreamEventSpec:
    del stream_config
    return ApiInvocationStreamEventSpec(
        kind=_enum_text(event_config.kind),
        class_ref=_class_ref_for_config_id(
            index=index,
            class_config_id=event_config.class_config_id,
            class_config=event_config.class_config,
            label="stream_event_config.class_config_id",
        ),
        source_path=source_path,
        description=event_config.description,
    )


def _fulfillment_bindings_from_ontology(
    *,
    api: Api,
    endpoint: ApiCapabilityEndpoint,
    source_path: str,
) -> list[ApiInvocationFulfillmentBindingSpec]:
    graph_functions_by_id, graph_targets_by_function_id = _api_graph_function_indexes(
        api
    )
    bindings: list[ApiInvocationFulfillmentBindingSpec] = []
    for endpoint_function in endpoint.api_capability_endpoint_functions:
        graph_function = (
            endpoint_function.api_graph_capability_function
            or graph_functions_by_id.get(
                endpoint_function.api_graph_capability_function_id
            )
        )
        if graph_function is None:
            raise RuntimeError(
                "API endpoint function cannot resolve graph capability function: "
                f"endpoint_function={endpoint_function.name!r} "
                f"api_graph_capability_function_id={endpoint_function.api_graph_capability_function_id}"
            )
        graph_target = graph_targets_by_function_id.get(graph_function.id)
        if graph_target is None:
            raise RuntimeError(
                "API endpoint function cannot resolve graph target for graph "
                f"capability function: endpoint_function={endpoint_function.name!r} "
                f"api_graph_capability_function_id={graph_function.id}"
            )
        bindings.append(
            ApiInvocationFulfillmentBindingSpec(
                name=_required_token(
                    "endpoint_function.name",
                    endpoint_function.name,
                ),
                graph_target=graph_target,
                graph_capability_function_name=_required_token(
                    "api_graph_capability_function.name",
                    graph_function.name,
                ),
                source_path=source_path,
            )
        )
    return bindings


def _api_graph_function_indexes(
    api: Api,
) -> tuple[dict[UUID, ApiGraphCapabilityFunction], dict[UUID, str]]:
    functions_by_id: dict[UUID, ApiGraphCapabilityFunction] = {}
    targets_by_function_id: dict[UUID, str] = {}
    for api_graph in api.api_graphs:
        graph_target = _api_graph_target_name(api_graph)
        for graph_capability in api_graph.api_graph_capabilities:
            for graph_function in graph_capability.api_graph_capability_functions:
                functions_by_id[graph_function.id] = graph_function
                targets_by_function_id[graph_function.id] = graph_target
    return functions_by_id, targets_by_function_id


def _api_graph_target_name(api_graph: object) -> str:
    object_config_graph = getattr(api_graph, "object_config_graph", None)
    object_config_graph_name = _clean(getattr(object_config_graph, "name", None))
    if object_config_graph_name is not None:
        return object_config_graph_name
    object_config_graph_id = getattr(api_graph, "object_config_graph_id", None)
    if object_config_graph_id is not None:
        return str(object_config_graph_id)
    raise RuntimeError("API graph target requires object_config_graph_id or name.")


def _class_ref_for_config_id(
    *,
    index: MetaGraphRuntimeIndex,
    class_config_id: UUID,
    class_config: object | None,
    label: str,
) -> str:
    class_fqn = _clean(getattr(class_config, "class_fqn", None))
    if class_fqn is not None:
        return class_fqn

    indexed_class_config = index.class_configs_by_id.get(class_config_id)
    class_fqn = _clean(getattr(indexed_class_config, "class_fqn", None))
    if class_fqn is not None:
        return class_fqn

    raise RuntimeError(
        "API invocation metadata cannot resolve ClassConfig FQN: "
        f"{label}={class_config_id}"
    )


def _validate_package_objects(
    *,
    package_ref: ApiRuntimePackageRef,
    api_package: ApiPackage,
    api: Api,
) -> None:
    _validate_api_package_api_pair(api_package=api_package, api=api)
    if api_package.name != package_ref.package_name:
        raise RuntimeError(
            "API runtime package ref package_name does not match ApiPackage: "
            f"ref={package_ref.package_name!r} api_package={api_package.name!r}"
        )
    semantic_package_id = _optional_uuid(package_ref.semantic_package_id)
    if semantic_package_id is not None and semantic_package_id != api_package.id:
        raise RuntimeError(
            "API runtime package ref semantic_package_id does not match "
            f"ApiPackage: ref={semantic_package_id} api_package={api_package.id}"
        )
    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    semantic_root_id = _optional_uuid(package_ref.semantic_root_id)
    if semantic_root_id is not None:
        expected_root_id = (
            api.id if semantic_root_kind != "api_package" else api_package.id
        )
        if semantic_root_id != expected_root_id:
            raise RuntimeError(
                "API runtime package ref semantic_root_id does not match "
                f"{semantic_root_kind or 'api'} root: ref={semantic_root_id} "
                f"expected={expected_root_id}"
            )


def _validate_api_package_api_pair(*, api_package: ApiPackage, api: Api) -> None:
    if api_package.api_id != api.id:
        raise RuntimeError(
            "ApiPackage points at a different Api than the hydrated API graph: "
            f"api_package={api_package.id} api_package.api_id={api_package.api_id} api={api.id}"
        )


def _expected_api_id_from_ref(
    *,
    package_ref: ApiRuntimePackageRef,
    api_package: ApiPackage,
) -> UUID:
    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    semantic_root_id = _optional_uuid(package_ref.semantic_root_id)
    if semantic_root_kind == "api" and semantic_root_id is not None:
        return semantic_root_id
    return api_package.api_id


def _api_has_invocation_surface(api: Api | None) -> bool:
    return api is not None and bool(api.api_capabilities or api.api_graphs)


def _api_domain_commit_id_from_package(api_package: ApiPackage) -> UUID | None:
    api_commit = api_package.api_object_instance_graph_commit
    if api_commit is None:
        return None
    return api_commit.commit_id


async def _api_domain_commit_ref_from_package(
    *,
    index: MetaGraphRuntimeIndex,
    store: FSCommitStore,
    api_package: ApiPackage,
    branch_id: UUID,
    preferred_projection_hash: str,
) -> tuple[str, UUID] | None:
    pinned_commit_id = api_package.api_object_instance_graph_commit_id
    if pinned_commit_id is not None:
        matches: list[tuple[str, UUID]] = []
        for projection_hash in _candidate_projection_hashes_by_name(
            index=index,
            projection_name="Api",
            preferred_projection_hash=preferred_projection_hash,
        ):
            domain_commit_id = (
                await store.domain_commit_id_for_object_instance_graph_commit_id(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    object_instance_graph_commit_id=pinned_commit_id,
                )
            )
            if domain_commit_id is not None:
                matches.append((projection_hash, domain_commit_id))
        if len(matches) > 1:
            raise RuntimeError(
                "API runtime package ref api_object_instance_graph_commit_id "
                "resolved to multiple Api projections: "
                f"api_package={api_package.id} "
                f"api_object_instance_graph_commit_id={pinned_commit_id} "
                f"matches={matches!r}"
            )
        if matches:
            return matches[0]

    api_commit = api_package.api_object_instance_graph_commit
    if api_commit is not None and api_commit.commit_id is not None:
        return preferred_projection_hash, api_commit.commit_id
    return None


def _candidate_projection_hashes_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
    preferred_projection_hash: str,
) -> tuple[str, ...]:
    projection_token = projection_name.strip()
    candidates: list[str] = [preferred_projection_hash]
    candidates.extend(
        projection_hash
        for projection_hash, opg in sorted(
            index.opg_by_hash.items(),
            key=lambda item: item[0],
        )
        if (opg.name or "").strip() == projection_token
    )
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        deduped.append(candidate)
        seen.add(candidate)
    return tuple(deduped)


async def _hydrate_root_from_head(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    root_id: UUID,
    root_type: type[_TRoot],
    hydrate_portal_targets: bool,
) -> _TRoot | None:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None
    return await _hydrate_root_from_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=None,
        root_id=root_id,
        root_type=root_type,
        hydrate_portal_targets=hydrate_portal_targets,
    )


async def _hydrate_root_from_commit(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID | None,
    root_id: UUID,
    root_type: type[_TRoot],
    hydrate_portal_targets: bool,
) -> _TRoot | None:
    del hydrate_portal_targets
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"API runtime package ref missing projection hash: {projection_hash}"
        )
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=commit_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_root_model(
        index=index,
        opg=opg,
        oig=oig,
        model_type=root_type,
        root_id=root_id,
        branch_id=branch_id,
    )


def _api_package_source_path(api_package: ApiPackage) -> str:
    return (
        _clean(api_package.manifest_relative_path)
        or f"ApiPackage:{_required_token('api_package.name', api_package.name)}"
    )


def _enum_text(value: object) -> str:
    enum_value = getattr(value, "value", value)
    return _required_token("enum.value", str(enum_value))


def _required_uuid(value: str | None, *, label: str) -> UUID:
    parsed = _optional_uuid(value)
    if parsed is None:
        raise RuntimeError(f"API runtime package ref requires {label}.")
    return parsed


def _optional_uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    stripped = value.strip()
    if not stripped:
        return None
    return UUID(stripped)


def _required_token(label: str, value: str | None) -> str:
    normalized = _clean(value)
    if normalized is None:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "ApiRuntimePackageRef",
    "ResolvedApiRuntimePackageRef",
    "build_api_invocation_manifest_from_api_package",
    "build_api_invocation_source_commit_from_package_ref",
    "build_api_runtime_package_binding_from_objects",
    "resolve_api_runtime_package_ref",
    "validate_api_runtime_package_ref",
]
