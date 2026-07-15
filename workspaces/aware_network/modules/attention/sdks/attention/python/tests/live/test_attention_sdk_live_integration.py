from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import os
from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from aware_environment_sdk import EnvironmentGraphClient, EnvironmentGraphContext
from aware_environment_service_api import AwareEnvironmentServiceApiClient
from aware_attention_sdk import AttentionSdkClient, build_attention_sdk_client
from aware_attention_service_api import AwareAttentionServiceApiClient
from aware_attention_service_api._bindings import ENDPOINT_REF_BY_NAME
from aware_attention_service_dto.attention.section.models import (
    AttentionSectionFocusTarget,
    AttentionRuntimeMountLayoutRequest,
    AttentionRuntimeMountSnapshotEvent,
    AttentionRuntimeMountSectionRequest,
)
from aware_attention_service_dto.attention.section.service_operation import (
    ActivateAttentionSectionObservableRequest,
    AttentionSectionActivationScope,
    GetAttentionFocusScopeCommitsRequest,
    GetAttentionRuntimeMountRequest,
    GetAttentionSectionStateRequest,
    WatchAttentionRuntimeMountRequest,
)
from aware_sdk_network.testing.live import (
    build_live_api_client_for_package,
    close_live_api_client,
    endpoint_refs_for_api_package,
)
from attention_endpoint_matrix import (
    ATTENTION_API_PACKAGE_NAME,
    ENVIRONMENT_API_PACKAGE_NAME,
)


pytest_plugins = ("aware_sdk_network.testing.pytest_plugin",)


@dataclass(frozen=True, slots=True)
class AttentionLiveSdk:
    api: AwareAttentionServiceApiClient
    sdk: AttentionSdkClient


@dataclass(frozen=True, slots=True)
class AttentionEnvironmentLiveSdk:
    attention: AttentionLiveSdk
    environment_api: AwareEnvironmentServiceApiClient
    environment_context: EnvironmentGraphContext


def test_live_services_advertise_generated_attention_endpoint_surface(
    live_sdk_api_dependency_routes,
) -> None:
    advertised_refs = endpoint_refs_for_api_package(
        live_sdk_api_dependency_routes,
        api_package_name=ATTENTION_API_PACKAGE_NAME,
    )
    assert advertised_refs == set(ENDPOINT_REF_BY_NAME.values())


@pytest_asyncio.fixture()
async def attention_sdk(live_sdk_api_dependency_routes):
    api_invoker = build_live_api_client_for_package(
        live_sdk_api_dependency_routes,
        api_package_name=ATTENTION_API_PACKAGE_NAME,
        actor_id=uuid4(),
    )
    api_client = AwareAttentionServiceApiClient(api_invoker)
    try:
        yield AttentionLiveSdk(
            api=api_client,
            sdk=build_attention_sdk_client(api_client),
        )
    finally:
        await close_live_api_client(api_invoker)


@pytest_asyncio.fixture()
async def attention_environment_sdk(
    live_sdk_api_dependency_routes,
    live_sdk_actor_id,
):
    if live_sdk_actor_id is None:
        pytest.fail(
            "Environment -> Attention live proof requires Service admission "
            "actor context; set AWARE_SDK_LIVE_ACTOR_ID"
        )
    environment_id = _required_uuid_env("AWARE_SDK_LIVE_ENVIRONMENT_ID")
    environment_invoker = build_live_api_client_for_package(
        live_sdk_api_dependency_routes,
        api_package_name=ENVIRONMENT_API_PACKAGE_NAME,
        actor_id=live_sdk_actor_id,
    )
    attention_invoker = build_live_api_client_for_package(
        live_sdk_api_dependency_routes,
        api_package_name=ATTENTION_API_PACKAGE_NAME,
        actor_id=live_sdk_actor_id,
    )
    try:
        attention_api = AwareAttentionServiceApiClient(attention_invoker)
        yield AttentionEnvironmentLiveSdk(
            attention=AttentionLiveSdk(
                api=attention_api,
                sdk=build_attention_sdk_client(attention_api),
            ),
            environment_api=AwareEnvironmentServiceApiClient(environment_invoker),
            environment_context=EnvironmentGraphContext(
                actor_id=live_sdk_actor_id,
                environment_id=environment_id,
                process_id=_optional_uuid_env("AWARE_SDK_LIVE_PROCESS_ID"),
                thread_id=_optional_uuid_env("AWARE_SDK_LIVE_THREAD_ID"),
            ),
        )
    finally:
        await close_live_api_client(attention_invoker)
        await close_live_api_client(environment_invoker)


@pytest.mark.asyncio
async def test_attention_layout_section_observable_live_sdk(
    attention_sdk: AttentionLiveSdk,
) -> None:
    suffix = uuid4().hex[:10]
    section_key = f"live-sdk-{suffix}"
    layout_key = f"live-layout-{suffix}"
    window_key = f"live-window-{suffix}"
    observable_id = uuid4()

    empty_state = await attention_sdk.sdk.get_section_state(
        GetAttentionSectionStateRequest(section_key=section_key)
    )
    assert empty_state.snapshot.section_key == section_key
    assert empty_state.snapshot.observable_id is None

    activation = await attention_sdk.sdk.activate_section_observable(
        ActivateAttentionSectionObservableRequest(
            section_key=section_key,
            observable_id=observable_id,
            rationale="attention_sdk_live_readiness",
            section_title="Live SDK Section",
            section_description="Attention SDK live readiness section",
            focus_scope_title="Live SDK Focus",
            focus_scope_description="Attention SDK live readiness focus scope",
        )
    )
    assert activation.snapshot.section_key == section_key
    assert activation.snapshot.exists is True
    assert activation.snapshot.observable_id == observable_id
    assert activation.snapshot.focus_scope_id is not None
    assert activation.snapshot.is_active is True

    readback = await attention_sdk.sdk.get_section_state(
        GetAttentionSectionStateRequest(section_key=section_key)
    )
    assert readback.snapshot.section_id == activation.snapshot.section_id
    assert readback.snapshot.observable_id == observable_id
    assert readback.snapshot.focus_scope_id == activation.snapshot.focus_scope_id
    assert activation.snapshot.focus_scope_id is not None

    commits = await attention_sdk.sdk.get_focus_scope_commits(
        GetAttentionFocusScopeCommitsRequest(
            focus_scope_id=activation.snapshot.focus_scope_id,
        )
    )
    assert commits.focus_scope_id == activation.snapshot.focus_scope_id
    assert commits.exists is True
    assert isinstance(commits.commits, list)

    mount = await attention_sdk.sdk.get_runtime_mount(
        _runtime_mount_request(
            window_key=window_key,
            layout_key=layout_key,
            section_key=section_key,
            observable_id=observable_id,
        )
    )
    assert mount.runtime_mount.window_key == window_key
    assert mount.runtime_mount.layout_key == layout_key
    assert mount.runtime_mount.active_section_key == section_key
    assert mount.runtime_mount.active_observable_id == observable_id
    assert [state.section_key for state in mount.runtime_mount.layout_sections] == [
        section_key
    ]
    assert [
        snapshot.section_key for snapshot in mount.runtime_mount.section_snapshots
    ] == [section_key]
    assert mount.runtime_mount.section_snapshots[0].observable_id == observable_id


@pytest.mark.asyncio
async def test_attention_focus_scope_commit_from_environment_graph_live_sdk(
    attention_environment_sdk: AttentionEnvironmentLiveSdk,
) -> None:
    constructor_ref = _required_first_text_env(
        "AWARE_SDK_LIVE_ENV_GRAPH_CONSTRUCTOR_REF",
        "AWARE_SDK_LIVE_CONSTRUCTOR_FUNCTION_REF",
    )
    mutation_ref = _required_first_text_env(
        "AWARE_SDK_LIVE_ENV_GRAPH_MUTATION_REF",
        "AWARE_SDK_LIVE_MUTATION_FUNCTION_REF",
    )
    constructor_args = _json_list_env(
        "AWARE_SDK_LIVE_ENV_GRAPH_CONSTRUCTOR_ARGS_JSON",
        "AWARE_SDK_LIVE_CONSTRUCTOR_ARGS_JSON",
    )
    constructor_kwargs = _json_object_env(
        "AWARE_SDK_LIVE_ENV_GRAPH_CONSTRUCTOR_KWARGS_JSON",
        "AWARE_SDK_LIVE_CONSTRUCTOR_KWARGS_JSON",
    )
    mutation_args = _json_list_env(
        "AWARE_SDK_LIVE_ENV_GRAPH_MUTATION_ARGS_JSON",
        "AWARE_SDK_LIVE_MUTATION_ARGS_JSON",
    )
    mutation_kwargs = _json_object_env(
        "AWARE_SDK_LIVE_ENV_GRAPH_MUTATION_KWARGS_JSON",
        "AWARE_SDK_LIVE_MUTATION_KWARGS_JSON",
    )

    graph_client = EnvironmentGraphClient(
        api_client=attention_environment_sdk.environment_api,
        context=attention_environment_sdk.environment_context,
        commit=True,
        publish=True,
    )
    constructor_target = await graph_client.resolve_function_target(
        function_ref=constructor_ref,
        call_target="constructor",
    )
    assert constructor_target.object_projection_graph_identity_id is not None
    constructor_receipt = await graph_client.invoke_resolved_target(
        target=constructor_target,
        args=constructor_args,
        kwargs=constructor_kwargs,
    )
    constructor_object_id = _required_receipt_uuid(
        constructor_receipt,
        "object_id",
    )
    branch_id = _required_receipt_uuid(constructor_receipt, "branch_id")
    projection_hash = _required_receipt_text(
        constructor_receipt,
        "projection_hash",
    )
    object_projection_graph_identity_id = _required_receipt_uuid(
        constructor_receipt,
        "object_projection_graph_identity_id",
    )
    object_instance_graph_branch_id = _required_receipt_uuid(
        constructor_receipt,
        "object_instance_graph_branch_id",
    )

    suffix = uuid4().hex[:10]
    section_key = f"live-env-provenance-{suffix}"
    observable_id = uuid4()
    activation = (
        await attention_environment_sdk.attention.sdk.activate_section_observable(
            ActivateAttentionSectionObservableRequest(
                section_key=section_key,
                observable_id=observable_id,
                activation_scope=AttentionSectionActivationScope(
                    branch_id=branch_id,
                    state_projection_hash=projection_hash,
                    focus_target=AttentionSectionFocusTarget(
                        kind="materialized",
                        object_projection_graph_identity_id=(
                            object_projection_graph_identity_id
                        ),
                        object_instance_graph_branch_id=(
                            object_instance_graph_branch_id
                        ),
                        projection_hash=projection_hash,
                        target_type="oigb",
                        target_id=object_instance_graph_branch_id,
                        description=(
                            "Environment SDK live graph provenance focus " f"{suffix}"
                        ),
                    ),
                ),
                rationale="environment_sdk_live_graph_provenance",
                section_title="Live Environment Provenance",
                focus_scope_title="Live Environment Provenance Focus",
            )
        )
    )
    assert activation.snapshot.focus_scope_id is not None
    assert activation.snapshot.focus_id is not None
    assert activation.snapshot.focus_target is not None
    assert (
        activation.snapshot.focus_target.object_instance_graph_branch_id
        == object_instance_graph_branch_id
    )

    mutation_client = EnvironmentGraphClient(
        api_client=attention_environment_sdk.environment_api,
        context=EnvironmentGraphContext(
            actor_id=attention_environment_sdk.environment_context.actor_id,
            environment_id=attention_environment_sdk.environment_context.environment_id,
            process_id=attention_environment_sdk.environment_context.process_id,
            thread_id=attention_environment_sdk.environment_context.thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
        ),
        commit=True,
        publish=True,
    )
    mutation_receipt = await mutation_client.invoke_function_ref(
        function_ref=mutation_ref,
        call_target="instance",
        receiver_object_id=constructor_object_id,
        args=mutation_args,
        kwargs=mutation_kwargs,
        projection_hash_hint=projection_hash,
    )
    object_instance_graph_commit_id = _required_receipt_uuid(
        mutation_receipt,
        "object_instance_graph_commit_id",
    )
    assert (
        _required_receipt_uuid(
            mutation_receipt,
            "object_instance_graph_branch_id",
        )
        == object_instance_graph_branch_id
    )

    pin = await _poll_focus_scope_commit(
        attention_environment_sdk.attention.sdk,
        focus_scope_id=activation.snapshot.focus_scope_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )
    assert pin.focus_id == activation.snapshot.focus_id
    assert pin.object_instance_graph_commit_id == object_instance_graph_commit_id


@pytest.mark.asyncio
async def test_attention_watch_runtime_mount_stream_live_sdk(
    attention_sdk: AttentionLiveSdk,
) -> None:
    suffix = uuid4().hex[:10]
    layout_key = f"live-stream-layout-{suffix}"
    section_key = f"live-stream-section-{suffix}"
    observable_id = uuid4()
    await attention_sdk.sdk.activate_section_observable(
        ActivateAttentionSectionObservableRequest(
            section_key=section_key,
            observable_id=observable_id,
            rationale="attention_sdk_live_stream_readiness",
            section_title="Live SDK Stream Section",
            section_description="Attention SDK live stream readiness section",
            focus_scope_title="Live SDK Stream Focus",
            focus_scope_description="Attention SDK live stream readiness focus scope",
        )
    )
    request = WatchAttentionRuntimeMountRequest(
        poll_interval_ms=250,
        layouts=[
            AttentionRuntimeMountLayoutRequest(
                layout_key=layout_key,
                is_default=True,
                sections=[
                    AttentionRuntimeMountSectionRequest(
                        section_key=section_key,
                        default_observable_id=observable_id,
                        default_rationale="attention_sdk_live_stream_mount",
                    )
                ],
            )
        ],
    )

    stream = attention_sdk.api.attention.watch_runtime_mount.stream_watch_runtime_mount(
        request
    )
    try:
        event = await anext(stream)
    finally:
        await stream.aclose()

    assert isinstance(event, AttentionRuntimeMountSnapshotEvent)
    assert event.kind == "snapshot"
    assert event.runtime_mount.layout_key == layout_key
    assert event.runtime_mount.active_section_key == section_key
    assert event.runtime_mount.active_observable_id == observable_id
    assert [
        snapshot.section_key for snapshot in event.runtime_mount.section_snapshots
    ] == [section_key]
    assert event.runtime_mount.section_snapshots[0].observable_id == observable_id


def _runtime_mount_request(
    *,
    window_key: str,
    layout_key: str,
    section_key: str,
    observable_id: UUID,
) -> GetAttentionRuntimeMountRequest:
    return GetAttentionRuntimeMountRequest(
        window_key=window_key,
        preferred_layout_key=layout_key,
        preferred_section_key=section_key,
        preferred_observable_id=observable_id,
        layouts=[
            AttentionRuntimeMountLayoutRequest(
                layout_key=layout_key,
                is_default=True,
                sections=[
                    AttentionRuntimeMountSectionRequest(
                        section_key=section_key,
                        title="Live SDK Section",
                        description="Attention SDK live readiness section",
                        order=0,
                        flex=1.0,
                        is_visible=True,
                        default_observable_id=observable_id,
                        default_rationale="attention_sdk_live_runtime_mount",
                    )
                ],
            )
        ],
    )


async def _poll_focus_scope_commit(
    sdk: AttentionSdkClient,
    *,
    focus_scope_id: UUID,
    object_instance_graph_commit_id: UUID,
) -> object:
    timeout_s = _poll_timeout_s()
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    while True:
        response = await sdk.get_focus_scope_commits(
            GetAttentionFocusScopeCommitsRequest(
                focus_scope_id=focus_scope_id,
                object_instance_graph_commit_id=object_instance_graph_commit_id,
            )
        )
        for pin in response.commits:
            if pin.object_instance_graph_commit_id == object_instance_graph_commit_id:
                return pin
        if loop.time() >= deadline:
            raise AssertionError(
                "Attention live SDK did not observe Environment OIG commit "
                f"{object_instance_graph_commit_id} for focus_scope "
                f"{focus_scope_id} within {timeout_s:.1f}s."
            )
        await asyncio.sleep(0.5)


def _required_uuid_env(name: str) -> UUID:
    value = _optional_uuid_env(name)
    if value is None:
        pytest.fail(f"live Environment -> Attention proof requires {name}")
    return value


def _optional_uuid_env(name: str) -> UUID | None:
    value = _optional_text_env(name)
    return UUID(value) if value is not None else None


def _optional_text_env(name: str) -> str | None:
    value = (os.environ.get(name) or "").strip()
    return value or None


def _required_first_text_env(*names: str) -> str:
    for name in names:
        value = _optional_text_env(name)
        if value is not None:
            return value
    pytest.fail(
        "live Environment -> Attention graph proof requires one of " + ", ".join(names)
    )


def _json_list_env(*names: str) -> list[object]:
    value = _json_env(*names, default=[])
    if not isinstance(value, list):
        raise AssertionError(f"{names[0]} must decode to a JSON array.")
    return value


def _json_object_env(*names: str) -> dict[str, object]:
    value = _json_env(*names, default={})
    if not isinstance(value, dict):
        raise AssertionError(f"{names[0]} must decode to a JSON object.")
    return value


def _json_env(*names: str, default: object) -> object:
    for name in names:
        raw_value = _optional_text_env(name)
        if raw_value is not None:
            return json.loads(raw_value)
    return default


def _required_receipt_uuid(receipt: object, field_name: str) -> UUID:
    value = getattr(receipt, field_name)
    if value is None:
        raise AssertionError(f"Environment graph live receipt is missing {field_name}.")
    return UUID(str(value))


def _required_receipt_text(receipt: object, field_name: str) -> str:
    raw_value = getattr(receipt, field_name)
    value = str(raw_value).strip() if raw_value is not None else ""
    if not value:
        raise AssertionError(f"Environment graph live receipt is missing {field_name}.")
    return value


def _poll_timeout_s() -> float:
    value = _optional_text_env("AWARE_SDK_LIVE_ATTENTION_COMMIT_TIMEOUT_S")
    if value is not None:
        timeout_s = float(value)
        if timeout_s <= 0:
            raise AssertionError(
                "AWARE_SDK_LIVE_ATTENTION_COMMIT_TIMEOUT_S must be positive."
            )
        return timeout_s
    return 30.0
