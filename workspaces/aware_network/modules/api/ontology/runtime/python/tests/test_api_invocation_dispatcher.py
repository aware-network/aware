from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_meta.materialization import MaterializationLaneContext

from aware_api_runtime.invocation import (
    ApiInvocationApiSpec,
    ApiInvocationCapabilitySpec,
    ApiInvocationEndpointSpec,
    ApiInvocationFulfillmentBindingSpec,
    ApiInvocationIR,
    ApiInvocationManifest,
    ApiInvocationRequestSpec,
    ApiInvocationResponseSpec,
    ApiInvocationSourceCommit,
    ApiInvocationStreamEventSpec,
    ApiInvocationStreamSpec,
    MaterializedApiCallBinding,
    dispatch_api_invocation_from_package_ref,
    dispatch_api_invocation_from_manifest,
    dispatch_api_invocation,
    resolve_api_invocation_ir_from_manifest,
    resolve_api_invocation_manifest_endpoint,
)
from aware_api_runtime.package_ref_resolution import ApiRuntimePackageRef


def _lane(*, projection_hash: str = "sha256:api") -> MaterializationLaneContext:
    return MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash=projection_hash,
    )


def _ir() -> ApiInvocationIR:
    return ApiInvocationIR(
        api_name="home_devices",
        capability_name="open_door",
        endpoint_name="open_door",
        endpoint_ref="home_devices.open_door.open_door",
        discriminant="home_devices.open_door.open_door",
        source_path="runtime-proof",
        request_payload={"label": "Front Door"},
        request_class_ref="aware_home_api.door.OpenDoor",
        request_class_config_id=uuid4(),
        request_source_path="runtime-proof",
        response_class_ref="aware_home_api.door.OpenDoorResult",
        response_source_path="runtime-proof",
        stream=None,
        fulfillment_bindings=(),
        description="Open one door.",
    )


def _index(*, request_class_config_id: UUID | None = None) -> object:
    effective_id = request_class_config_id or uuid4()
    return SimpleNamespace(
        class_configs_by_id={
            effective_id: SimpleNamespace(
                id=effective_id,
                class_fqn="aware_home_api.door.OpenDoor",
            )
        }
    )


def _manifest() -> ApiInvocationManifest:
    return ApiInvocationManifest(
        schema_version=1,
        package_name="home-devices-api",
        fqn_prefix="aware_home_api",
        apis=[
            ApiInvocationApiSpec(
                name="home_devices",
                source_path="modules/home/structure/api/aware/home_devices.aware",
                capabilities=[
                    ApiInvocationCapabilitySpec(
                        name="door",
                        source_path="modules/home/structure/api/aware/home_devices.aware",
                        endpoints=[
                            ApiInvocationEndpointSpec(
                                name="open_door",
                                source_path="modules/home/structure/api/aware/home_devices.aware",
                                endpoint_ref="home_devices.door.open_door",
                                discriminant="home_devices.door.open_door",
                                invocation_kind="shared_client_endpoint",
                                client_backend="aware_api.invoker.AwareApiEndpointInvoker",
                                client_operation="invoke_api_endpoint",
                                addressing_strategy="session_bound",
                                request=ApiInvocationRequestSpec(
                                    class_ref="aware_home_api.door.OpenDoor",
                                    source_path="modules/home/structure/api/aware/home_devices.aware",
                                ),
                                response=ApiInvocationResponseSpec(
                                    class_ref="aware_home_api.door.OpenDoorResult",
                                    source_path="modules/home/structure/api/aware/home_devices.aware",
                                ),
                                stream=ApiInvocationStreamSpec(
                                    stream_mode="events",
                                    source_path="modules/home/structure/api/aware/home_devices.aware",
                                    events=[
                                        ApiInvocationStreamEventSpec(
                                            kind="progress",
                                            class_ref="aware_home_api.door.OpenDoorProgress",
                                            source_path="modules/home/structure/api/aware/home_devices.aware",
                                        )
                                    ],
                                ),
                                fulfillment_bindings=[
                                    ApiInvocationFulfillmentBindingSpec(
                                        name="open",
                                        graph_target="door",
                                        graph_capability_function_name="open",
                                        source_path="modules/home/structure/api/aware/home_devices.aware",
                                    )
                                ],
                                description="Open one door.",
                            )
                        ],
                    )
                ],
            )
        ],
    )


def test_resolve_api_invocation_manifest_endpoint_accepts_ref_and_discriminant() -> (
    None
):
    manifest = _manifest()

    by_ref = resolve_api_invocation_manifest_endpoint(
        manifest=manifest,
        endpoint_ref="home_devices.door.open_door",
        discriminant="home_devices.door.open_door",
    )
    by_discriminant = resolve_api_invocation_manifest_endpoint(
        manifest=manifest,
        discriminant="home_devices.door.open_door",
    )

    assert by_ref.endpoint.name == "open_door"
    assert by_discriminant.endpoint is by_ref.endpoint


def test_resolve_api_invocation_ir_from_manifest_lowers_endpoint_payload_and_contract() -> (
    None
):
    request_class_config_id = uuid4()

    ir = resolve_api_invocation_ir_from_manifest(
        index=cast(Any, _index(request_class_config_id=request_class_config_id)),
        manifest=_manifest(),
        endpoint_ref="home_devices.door.open_door",
        request_payload={"label": "Front Door"},
    )

    assert ir.api_name == "home_devices"
    assert ir.capability_name == "door"
    assert ir.endpoint_name == "open_door"
    assert ir.endpoint_ref == "home_devices.door.open_door"
    assert ir.discriminant == "home_devices.door.open_door"
    assert ir.request_payload == {"label": "Front Door"}
    assert ir.request_class_ref == "aware_home_api.door.OpenDoor"
    assert ir.request_class_config_id == request_class_config_id
    assert ir.response_class_ref == "aware_home_api.door.OpenDoorResult"
    assert ir.stream is not None
    assert ir.stream.stream_mode == "events"
    assert ir.stream.events[0].kind == "progress"
    assert ir.fulfillment_bindings[0].graph_target == "door"


@pytest.mark.asyncio
async def test_dispatch_api_invocation_from_manifest_lowers_then_dispatches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def _fake_dispatch_api_invocation(**kwargs: object) -> object:
        captured.update(kwargs)
        return SimpleNamespace(ir=kwargs["ir"])

    monkeypatch.setattr(
        "aware_api_runtime.invocation.ingress.dispatch_api_invocation",
        _fake_dispatch_api_invocation,
    )

    result = await dispatch_api_invocation_from_manifest(
        runtime=cast(Any, object()),
        index=cast(Any, _index()),
        actor_id=uuid4(),
        source_lane=_lane(projection_hash="sha256:api"),
        target_lane=_lane(projection_hash="sha256:api-call"),
        manifest=_manifest(),
        discriminant="home_devices.door.open_door",
        request_payload={"label": "Front Door"},
        call_key=uuid4(),
        commit=False,
        publish=True,
    )

    ir = cast(ApiInvocationIR, captured["ir"])
    assert ir.endpoint_ref == "home_devices.door.open_door"
    assert ir.request_payload == {"label": "Front Door"}
    assert captured["commit"] is False
    assert captured["publish"] is True
    assert result.ir is ir


@pytest.mark.asyncio
async def test_dispatch_api_invocation_from_package_ref_uses_pinned_source_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_ref = ApiRuntimePackageRef(
        family_key="api",
        package_kind="api",
        package_name="home-devices-api",
        semantic_branch_id=str(uuid4()),
        semantic_head_commit_id=str(uuid4()),
    )
    package_binding = SimpleNamespace(invocation_manifest=_manifest())
    source_commit = ApiInvocationSourceCommit(
        branch_id=uuid4(),
        projection_hash="sha256:pinned-api",
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
    )
    target_lane = _lane(projection_hash="sha256:api-call")
    captured: dict[str, object] = {}

    async def _fake_resolve_api_runtime_package_ref(**kwargs: object) -> object:
        captured["resolved_package_ref"] = kwargs["package_ref"]
        return package_binding

    def _fake_source_commit_from_package_ref(
        binding: object,
    ) -> ApiInvocationSourceCommit:
        captured["source_binding"] = binding
        return source_commit

    async def _fake_dispatch_api_invocation(**kwargs: object) -> object:
        captured.update(kwargs)
        return SimpleNamespace(ir=kwargs["ir"], envelope=object())

    monkeypatch.setattr(
        "aware_api_runtime.package_ref_resolution.resolve_api_runtime_package_ref",
        _fake_resolve_api_runtime_package_ref,
    )
    monkeypatch.setattr(
        "aware_api_runtime.package_ref_resolution."
        "build_api_invocation_source_commit_from_package_ref",
        _fake_source_commit_from_package_ref,
    )
    monkeypatch.setattr(
        "aware_api_runtime.invocation.ingress.dispatch_api_invocation",
        _fake_dispatch_api_invocation,
    )

    result = await dispatch_api_invocation_from_package_ref(
        runtime=cast(Any, object()),
        index=cast(Any, _index()),
        actor_id=uuid4(),
        target_lane=target_lane,
        package_ref=package_ref,
        endpoint_ref="home_devices.door.open_door",
        request_payload={"label": "Front Door"},
        call_key=uuid4(),
        commit=False,
        publish=True,
    )

    assert captured["resolved_package_ref"] is package_ref
    assert captured["source_binding"] is package_binding
    assert captured["source_commit"] == source_commit
    source_lane = cast(MaterializationLaneContext, captured["source_lane"])
    assert source_lane.branch_id == source_commit.branch_id
    assert source_lane.projection_hash == source_commit.projection_hash
    assert captured["target_lane"] is target_lane
    assert captured["commit"] is False
    assert captured["publish"] is True
    assert result.package_binding is package_binding
    assert result.source_commit == source_commit


@pytest.mark.asyncio
async def test_dispatch_api_invocation_materializes_call_and_builds_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ir = _ir()
    call_key = uuid4()
    binding = MaterializedApiCallBinding(
        api_call_id=uuid4(),
        api_capability_endpoint_id=uuid4(),
        call_key=call_key,
        request_hash="sha256:dispatcher-proof",
        request_model_id=uuid4(),
        request_class_config_id=cast(Any, ir.request_class_config_id),
        commit_id=uuid4(),
        head_commit_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sha256:api-call",
    )
    captured: dict[str, object] = {}

    async def _fake_materialize_api_call(**kwargs: object) -> object:
        captured.update(kwargs)
        return SimpleNamespace(
            binding=binding,
            api_call=object(),
            last_commit_id=binding.commit_id,
            last_head_commit_id=binding.head_commit_id,
        )

    monkeypatch.setattr(
        "aware_api_runtime.invocation.dispatcher._materialize_api_call",
        _fake_materialize_api_call,
    )

    result = await dispatch_api_invocation(
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        source_lane=_lane(projection_hash="sha256:api"),
        target_lane=_lane(projection_hash="sha256:api-call"),
        ir=ir,
        call_key=call_key,
        commit=False,
        publish=True,
    )

    assert captured["ir"] is ir
    assert captured["call_key"] == call_key
    assert captured["commit"] is False
    assert captured["publish"] is True
    assert result.ir is ir
    assert result.materialized_call.binding is binding
    assert result.envelope.api_call_id == binding.api_call_id
    assert (
        result.envelope.api_capability_endpoint_id == binding.api_capability_endpoint_id
    )
    assert result.envelope.call_key == call_key
    assert result.envelope.endpoint_ref == "home_devices.open_door.open_door"
    assert result.envelope.commit_id == binding.commit_id
    assert result.envelope.head_commit_id == binding.head_commit_id
    assert result.envelope.branch_id == binding.branch_id
    assert result.envelope.projection_hash == "sha256:api-call"
