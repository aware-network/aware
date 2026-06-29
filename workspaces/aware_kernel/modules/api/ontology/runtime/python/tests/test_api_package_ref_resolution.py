from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_api_ontology.api.api import Api
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_function import (
    ApiCapabilityEndpointFunction,
)
from aware_api_ontology.api.api_capability_endpoint_request_config import (
    ApiCapabilityEndpointRequestConfig,
)
from aware_api_ontology.api.api_capability_endpoint_response_config import (
    ApiCapabilityEndpointResponseConfig,
)
from aware_api_ontology.api.api_capability_endpoint_stream_config import (
    ApiCapabilityEndpointStreamConfig,
)
from aware_api_ontology.api.api_capability_endpoint_stream_enums import (
    ApiCapabilityEndpointStreamEventKind,
    ApiCapabilityEndpointStreamMode,
)
from aware_api_ontology.api.api_capability_endpoint_stream_event_config import (
    ApiCapabilityEndpointStreamEventConfig,
)
from aware_api_ontology.api.api_graph import ApiGraph
from aware_api_ontology.api.api_graph_capability import ApiGraphCapability
from aware_api_ontology.api.api_graph_capability_function import (
    ApiGraphCapabilityFunction,
)
from aware_api_ontology.api.api_graph_function import ApiGraphFunction
from aware_api_ontology.api.api_package import ApiPackage
from aware_api_runtime.package_ref_resolution import (
    ApiRuntimePackageRef,
    build_api_invocation_source_commit_from_package_ref,
    build_api_runtime_package_binding_from_objects,
    resolve_api_runtime_package_ref,
    validate_api_runtime_package_ref,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.instance.commit.fs_store import ObjectInstanceGraphCommitRef
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)


def _class_config(*, id: UUID, class_fqn: str, name: str) -> ClassConfig:
    return ClassConfig.model_construct(
        id=id,
        class_fqn=class_fqn,
        name=name,
    )


def _index(*, class_configs: list[ClassConfig]) -> MetaGraphRuntimeIndex:
    return cast(
        MetaGraphRuntimeIndex,
        cast(
            object,
            SimpleNamespace(
                class_configs_by_id={
                    class_config.id: class_config for class_config in class_configs
                },
                opg_by_hash={
                    "sha256:Api": SimpleNamespace(
                        name="api",
                        projection_hash="sha256:Api",
                    ),
                    "sha256:ApiPackage": SimpleNamespace(
                        name="api_package",
                        projection_hash="sha256:ApiPackage",
                    ),
                },
                ocg=SimpleNamespace(
                    object_projection_graphs=[
                        SimpleNamespace(name="Api", projection_hash="sha256:Api")
                    ]
                ),
            ),
        ),
    )


def _api_fixture() -> tuple[ApiPackage, Api, MetaGraphRuntimeIndex]:
    api_id = uuid4()
    package_id = uuid4()
    capability_id = uuid4()
    endpoint_id = uuid4()
    request_config_id = uuid4()
    request_class_config_id = uuid4()
    response_class_config_id = uuid4()
    stream_config_id = uuid4()
    stream_event_class_config_id = uuid4()
    api_graph_id = uuid4()
    api_graph_capability_id = uuid4()
    api_graph_function_id = uuid4()
    api_graph_capability_function_id = uuid4()
    api_object_instance_graph_commit_id = uuid4()
    api_domain_commit_id = uuid4()

    request_class_config = _class_config(
        id=request_class_config_id,
        class_fqn="aware_home_api.door.LockDoorRequest",
        name="LockDoorRequest",
    )
    response_class_config = _class_config(
        id=response_class_config_id,
        class_fqn="aware_home_api.door.LockDoorResult",
        name="LockDoorResult",
    )
    stream_event_class_config = _class_config(
        id=stream_event_class_config_id,
        class_fqn="aware_home_api.door.LockDoorNotice",
        name="LockDoorNotice",
    )
    response_config = ApiCapabilityEndpointResponseConfig.model_construct(
        id=uuid4(),
        api_capability_endpoint_request_config_id=request_config_id,
        class_config_id=response_class_config_id,
        description="Terminal lock result.",
    )
    event_config = ApiCapabilityEndpointStreamEventConfig.model_construct(
        id=uuid4(),
        api_capability_endpoint_stream_config_id=stream_config_id,
        kind=ApiCapabilityEndpointStreamEventKind.notice,
        class_config_id=stream_event_class_config_id,
        description="Door lock notice.",
    )
    stream_config = ApiCapabilityEndpointStreamConfig.model_construct(
        id=stream_config_id,
        api_capability_endpoint_request_config_id=request_config_id,
        stream_mode=ApiCapabilityEndpointStreamMode.server,
        api_capability_endpoint_stream_event_configs=[event_config],
        description="Server notices.",
    )
    request_config = ApiCapabilityEndpointRequestConfig.model_construct(
        id=request_config_id,
        api_capability_endpoint_id=endpoint_id,
        class_config_id=request_class_config_id,
        response_config=response_config,
        stream_config=stream_config,
        description="Lock request.",
    )
    graph_function = ApiGraphFunction.model_construct(
        id=api_graph_function_id,
        api_graph_id=api_graph_id,
        class_config_function_config_id=uuid4(),
    )
    graph_capability_function = ApiGraphCapabilityFunction.model_construct(
        id=api_graph_capability_function_id,
        api_graph_capability_id=api_graph_capability_id,
        api_graph_function_id=api_graph_function_id,
        api_graph_function=graph_function,
        name="lock",
    )
    endpoint_function = ApiCapabilityEndpointFunction.model_construct(
        id=uuid4(),
        api_capability_endpoint_id=endpoint_id,
        api_graph_capability_function_id=api_graph_capability_function_id,
        api_graph_capability_function=graph_capability_function,
        name="lock",
    )
    endpoint = ApiCapabilityEndpoint.model_construct(
        id=endpoint_id,
        api_capability_id=capability_id,
        name="lock_door",
        request_config=request_config,
        api_capability_endpoint_functions=[endpoint_function],
        description="Lock one door.",
    )
    capability = ApiCapability.model_construct(
        id=capability_id,
        api_id=api_id,
        name="door",
        api_capability_endpoints=[endpoint],
        description="Door operations.",
    )
    graph_capability = ApiGraphCapability.model_construct(
        id=api_graph_capability_id,
        api_graph_id=api_graph_id,
        api_capability_id=capability_id,
        api_capability=capability,
        api_graph_capability_functions=[graph_capability_function],
    )
    object_config_graph = ObjectConfigGraph.model_construct(
        id=uuid4(),
        name="aware_home",
        hash="sha256:home",
        fqn_prefix="aware_home",
        language=CodeLanguage.aware,
    )
    api_graph = ApiGraph.model_construct(
        id=api_graph_id,
        api_id=api_id,
        object_config_graph_id=object_config_graph.id,
        object_config_graph=object_config_graph,
        api_graph_capabilities=[graph_capability],
    )
    api = Api.model_construct(
        id=api_id,
        name="home_devices",
        api_capabilities=[capability],
        api_graphs=[api_graph],
    )
    api_object_instance_graph_commit = ObjectInstanceGraphCommit.model_construct(
        id=api_object_instance_graph_commit_id,
        commit_id=api_domain_commit_id,
    )
    api_package = ApiPackage.model_construct(
        id=package_id,
        name="home-story-api",
        api_id=api_id,
        api=api,
        fqn_prefix="aware_home_story_api",
        manifest_relative_path="apis/home/aware.api.toml",
        api_object_instance_graph_commit=api_object_instance_graph_commit,
        api_object_instance_graph_commit_id=api_object_instance_graph_commit_id,
    )
    index = _index(
        class_configs=[
            request_class_config,
            response_class_config,
            stream_event_class_config,
        ]
    )
    return api_package, api, index


def _package_ref(
    *,
    api_package: ApiPackage,
    api: Api,
) -> ApiRuntimePackageRef:
    return ApiRuntimePackageRef(
        family_key="api",
        package_kind="api",
        package_name=api_package.name,
        semantic_package_id=str(api_package.id),
        semantic_object_instance_graph_commit_id=str(uuid4()),
        semantic_head_commit_id=str(uuid4()),
        semantic_branch_id=str(uuid4()),
        semantic_projection_name="ApiPackage",
        semantic_root_kind="api",
        semantic_root_id=str(api.id),
        source_code_package_id=str(uuid4()),
        manifest_path="apis/home/aware.api.toml",
    )


def test_build_api_runtime_package_binding_from_objects_uses_api_package_truth() -> (
    None
):
    api_package, api, index = _api_fixture()

    resolved = build_api_runtime_package_binding_from_objects(
        index=index,
        package_ref=_package_ref(api_package=api_package, api=api),
        api_package=api_package,
        api=api,
    )

    manifest = resolved.invocation_manifest
    endpoint = manifest.apis[0].capabilities[0].endpoints[0]
    assert resolved.package_name == "home-story-api"
    assert resolved.api_name == "home_devices"
    assert (
        resolved.api_object_instance_graph_commit_id
        == api_package.api_object_instance_graph_commit_id
    )
    assert resolved.api_projection_hash == "sha256:Api"
    assert api_package.api_object_instance_graph_commit is not None
    assert (
        resolved.api_domain_commit_id
        == api_package.api_object_instance_graph_commit.commit_id
    )
    source_commit = build_api_invocation_source_commit_from_package_ref(resolved)
    assert resolved.semantic_branch_id is not None
    assert source_commit.branch_id == resolved.semantic_branch_id
    assert source_commit.projection_hash == "sha256:Api"
    assert source_commit.commit_id == resolved.api_domain_commit_id
    assert (
        source_commit.object_instance_graph_commit_id
        == api_package.api_object_instance_graph_commit_id
    )
    assert manifest.package_name == "home-story-api"
    assert manifest.fqn_prefix == "aware_home_story_api"
    assert manifest.apis[0].source_path == "apis/home/aware.api.toml"
    assert endpoint.endpoint_ref == "home_devices.door.lock_door"
    assert endpoint.discriminant == "home_devices.door.lock_door"
    assert endpoint.client_backend == "aware_api.invoker.AwareApiEndpointInvoker"
    assert endpoint.request.class_ref == "aware_home_api.door.LockDoorRequest"
    assert endpoint.response is not None
    assert endpoint.response.class_ref == "aware_home_api.door.LockDoorResult"
    assert endpoint.stream is not None
    assert endpoint.stream.stream_mode == "server"
    assert endpoint.stream.events[0].kind == "notice"
    assert endpoint.stream.events[0].class_ref == "aware_home_api.door.LockDoorNotice"
    assert endpoint.fulfillment_bindings[0].name == "lock"
    assert endpoint.fulfillment_bindings[0].graph_target == "aware_home"
    assert endpoint.fulfillment_bindings[0].graph_capability_function_name == "lock"


def test_validate_api_runtime_package_ref_rejects_non_api_kind() -> None:
    with pytest.raises(RuntimeError, match="family_key='api'"):
        validate_api_runtime_package_ref(
            ApiRuntimePackageRef(
                family_key="service",
                package_kind="api",
                package_name="home-story-api",
            )
        )


def test_build_api_runtime_package_binding_rejects_semantic_package_mismatch() -> None:
    api_package, api, index = _api_fixture()
    package_ref = ApiRuntimePackageRef(
        family_key="api",
        package_kind="api",
        package_name=api_package.name,
        semantic_package_id=str(uuid4()),
        semantic_root_kind="api",
        semantic_root_id=str(api.id),
    )

    with pytest.raises(RuntimeError, match="semantic_package_id"):
        build_api_runtime_package_binding_from_objects(
            index=index,
            package_ref=package_ref,
            api_package=api_package,
            api=api,
        )


@pytest.mark.asyncio
async def test_resolve_api_runtime_package_ref_hydrates_package_then_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path / "aware-root"))
    api_package, api, index = _api_fixture()
    assert api_package.api_object_instance_graph_commit is not None
    api_domain_commit_id = api_package.api_object_instance_graph_commit.commit_id
    api_package_without_portal = api_package.model_copy(
        update={
            "api": None,
            "api_object_instance_graph_commit": ObjectInstanceGraphCommit.model_construct(
                id=api_package.api_object_instance_graph_commit_id,
                commit_id=uuid4(),
            ),
        }
    )
    package_ref = _package_ref(api_package=api_package, api=api)
    hydrated: list[str] = []

    def _fake_projection_hash(
        *, index: MetaGraphRuntimeIndex, projection_name: str
    ) -> str:
        del index
        return f"sha256:{projection_name}"

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        hydrated.append(cast(str, kwargs["projection_hash"]))
        if kwargs["root_type"] is ApiPackage:
            assert kwargs["commit_id"] == UUID(
                cast(str, package_ref.semantic_object_instance_graph_commit_id)
            )
            return api_package_without_portal
        assert kwargs["root_type"] is Api
        assert kwargs["commit_id"] == api_domain_commit_id
        return api

    async def _fake_hydrate_root_from_head(**kwargs: Any) -> object:
        raise AssertionError(f"unexpected head fallback: {kwargs!r}")

    async def _fake_domain_commit_id_for_oig_commit_id(
        self: object,
        **kwargs: Any,
    ) -> UUID:
        del self
        if kwargs["projection_hash"] == "sha256:ApiPackage":
            assert kwargs["object_instance_graph_commit_id"] == UUID(
                cast(str, package_ref.semantic_object_instance_graph_commit_id)
            )
            return UUID(cast(str, package_ref.semantic_object_instance_graph_commit_id))
        assert kwargs["projection_hash"] == "sha256:Api"
        assert kwargs["object_instance_graph_commit_id"] == (
            api_package.api_object_instance_graph_commit_id
        )
        assert api_domain_commit_id is not None
        return api_domain_commit_id

    monkeypatch.setattr(
        "aware_api_runtime.package_ref_resolution.find_meta_graph_projection_hash_by_name",
        _fake_projection_hash,
    )
    monkeypatch.setattr(
        "aware_api_runtime.package_ref_resolution._hydrate_root_from_commit",
        _fake_hydrate_root_from_commit,
    )
    monkeypatch.setattr(
        "aware_api_runtime.package_ref_resolution._hydrate_root_from_head",
        _fake_hydrate_root_from_head,
    )
    monkeypatch.setattr(
        "aware_api_runtime.package_ref_resolution.FSCommitStore."
        "domain_commit_id_for_object_instance_graph_commit_id",
        _fake_domain_commit_id_for_oig_commit_id,
    )

    resolved = await resolve_api_runtime_package_ref(
        index=index,
        package_ref=package_ref,
    )

    assert hydrated == ["sha256:ApiPackage", "sha256:Api"]
    assert resolved.api_package_id == api_package.id
    assert resolved.api_id == api.id
    assert resolved.semantic_projection_hash == "sha256:ApiPackage"
    assert (
        resolved.api_object_instance_graph_commit_id
        == api_package.api_object_instance_graph_commit_id
    )
    assert resolved.invocation_manifest.apis[0].name == "home_devices"


@pytest.mark.asyncio
async def test_resolve_api_runtime_package_ref_resolves_branch_from_oig_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path / "aware-root"))
    api_package, api, index = _api_fixture()
    assert api_package.api_object_instance_graph_commit is not None
    api_domain_commit_id = api_package.api_object_instance_graph_commit.commit_id
    api_package_without_portal = api_package.model_copy(
        update={
            "api": None,
            "api_object_instance_graph_commit": ObjectInstanceGraphCommit.model_construct(
                id=api_package.api_object_instance_graph_commit_id,
                commit_id=uuid4(),
            ),
        }
    )
    branch_id = uuid4()
    package_oig_commit_id = uuid4()
    package_domain_commit_id = uuid4()
    package_ref = ApiRuntimePackageRef(
        family_key="api",
        package_kind="api",
        package_name=api_package.name,
        semantic_package_id=str(api_package.id),
        semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
        semantic_projection_name="ApiPackage",
        semantic_root_kind="api",
        semantic_root_id=str(api.id),
    )
    hydrated: list[str] = []

    def _fake_projection_hash(
        *, index: MetaGraphRuntimeIndex, projection_name: str
    ) -> str:
        del index
        return f"sha256:{projection_name}"

    async def _fake_domain_commit_refs_for_oig_commit_id(
        self: object,
        **kwargs: Any,
    ) -> tuple[ObjectInstanceGraphCommitRef, ...]:
        del self
        assert kwargs["projection_hash"] == "sha256:ApiPackage"
        assert kwargs["object_instance_graph_commit_id"] == package_oig_commit_id
        return (
            ObjectInstanceGraphCommitRef(
                branch_id=branch_id,
                projection_hash="sha256:ApiPackage",
                object_instance_graph_commit_id=package_oig_commit_id,
                domain_commit_id=package_domain_commit_id,
            ),
        )

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        hydrated.append(cast(str, kwargs["projection_hash"]))
        if kwargs["root_type"] is ApiPackage:
            assert kwargs["branch_id"] == branch_id
            assert kwargs["commit_id"] == package_domain_commit_id
            return api_package_without_portal
        assert kwargs["root_type"] is Api
        assert kwargs["branch_id"] == branch_id
        assert kwargs["commit_id"] == api_domain_commit_id
        return api

    async def _fake_domain_commit_id_for_oig_commit_id(
        self: object,
        **kwargs: Any,
    ) -> UUID:
        del self
        assert kwargs["branch_id"] == branch_id
        assert kwargs["projection_hash"] == "sha256:Api"
        assert kwargs["object_instance_graph_commit_id"] == (
            api_package.api_object_instance_graph_commit_id
        )
        assert api_domain_commit_id is not None
        return api_domain_commit_id

    monkeypatch.setattr(
        "aware_api_runtime.package_ref_resolution.find_meta_graph_projection_hash_by_name",
        _fake_projection_hash,
    )
    monkeypatch.setattr(
        "aware_api_runtime.package_ref_resolution._hydrate_root_from_commit",
        _fake_hydrate_root_from_commit,
    )
    monkeypatch.setattr(
        "aware_api_runtime.package_ref_resolution.FSCommitStore."
        "domain_commit_refs_for_object_instance_graph_commit_id",
        _fake_domain_commit_refs_for_oig_commit_id,
    )
    monkeypatch.setattr(
        "aware_api_runtime.package_ref_resolution.FSCommitStore."
        "domain_commit_id_for_object_instance_graph_commit_id",
        _fake_domain_commit_id_for_oig_commit_id,
    )

    resolved = await resolve_api_runtime_package_ref(
        index=index,
        package_ref=package_ref,
    )

    assert hydrated == ["sha256:ApiPackage", "sha256:Api"]
    assert resolved.semantic_branch_id == branch_id
    assert resolved.semantic_object_instance_graph_commit_id == str(
        package_oig_commit_id
    )
    assert resolved.api_package_id == api_package.id
    assert resolved.api_id == api.id
