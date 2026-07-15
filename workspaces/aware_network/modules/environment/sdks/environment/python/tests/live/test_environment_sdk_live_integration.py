from __future__ import annotations

# pyright: reportMissingImports=false

from dataclasses import dataclass
import os
from uuid import UUID

import pytest
import pytest_asyncio

from aware_environment_sdk import (
    EnvironmentReadinessClient,
    EnvironmentReadinessContext,
)
from aware_environment_service_api import AwareEnvironmentServiceApiClient
from aware_environment_service_api._bindings import ENDPOINT_REF_BY_NAME
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentConfigRequest,
    DescribeEnvironmentRequest,
    DescribeEnvironmentTopologyRequest,
    FetchCapabilitiesRequest,
    GetLaneHeadRequest,
    InvokeFunctionCallTarget,
    ResolveRuntimeFunctionTargetQuery,
    ResolveRuntimeRefsRequest,
)
from aware_sdk_network.testing.live import (
    LiveSdkEndpointProofRow,
    build_live_api_client_for_package,
    close_live_api_client,
    endpoint_refs_for_api_package,
)


pytest_plugins = ("aware_sdk_network.testing.pytest_plugin",)


ENVIRONMENT_API_PACKAGE_NAME = "environment-service-api"


@dataclass(frozen=True, slots=True)
class EnvironmentLiveSdk:
    api: AwareEnvironmentServiceApiClient
    readiness: EnvironmentReadinessClient
    context: EnvironmentReadinessContext


ENVIRONMENT_ENDPOINT_MATRIX: tuple[LiveSdkEndpointProofRow, ...] = (
    LiveSdkEndpointProofRow(
        "environment.actor_admission.admit_actor",
        "EnvironmentActorAdmissionClient.admit_actor",
        3,
        "fixture_pending",
        "requires accepted Identity role/admission fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.capabilities.fetch_capabilities",
        "api.environment.capabilities.fetch_capabilities",
        1,
        "blocked",
        "awaits ontology-owned capability catalog; runtime-index fallback is retired",
    ),
    LiveSdkEndpointProofRow(
        "environment.committed_projection_dto.materialize_committed_projection_dto",
        "api.environment.committed_projection_dto.materialize_committed_projection_dto",
        1,
        "fixture_pending",
        "requires committed projection DTO fixture and deploy artifact selector",
    ),
    LiveSdkEndpointProofRow(
        "environment.describe.describe_environment",
        "api.environment.describe.describe_environment",
        1,
        "green",
        "artifact-set backed Environment description plus optional lane head",
    ),
    LiveSdkEndpointProofRow(
        "environment.describe_config.describe_environment_config",
        "api.environment.describe_config.describe_environment_config",
        1,
        "green",
        "artifact-set backed EnvironmentConfig description",
    ),
    LiveSdkEndpointProofRow(
        "environment.function_call.invoke_function",
        "EnvironmentGraphClient.invoke_function_ref",
        3,
        "fixture_pending",
        "requires runtime-ref target resolution and isolated graph mutation fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.lane_head.get_lane_head",
        "api.environment.lane_head.get_lane_head",
        1,
        "green",
        "typed lane-head read through Meta route; empty lanes are valid reads",
    ),
    LiveSdkEndpointProofRow(
        "environment.navigation.create_navigation_context",
        "EnvironmentNavigationClient.create_navigation_context",
        3,
        "fixture_pending",
        "requires joined EnvironmentSession fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.navigation.describe_navigation_context",
        "EnvironmentNavigationClient.describe_navigation_context",
        1,
        "fixture_pending",
        "requires existing EnvironmentNavigationContext fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.navigation.list_navigation_contexts",
        "EnvironmentNavigationClient.list_navigation_contexts",
        1,
        "fixture_pending",
        "requires joined EnvironmentSession fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.navigation.select_navigation_target",
        "EnvironmentNavigationClient.select_navigation_target",
        3,
        "fixture_pending",
        "requires joined EnvironmentSession and target topology fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.object_instance_graph_commit.get_object_instance_graph_commit",
        "EnvironmentReadinessClient.get_object_instance_graph_commit",
        1,
        "fixture_pending",
        "requires a committed Environment lane head",
    ),
    LiveSdkEndpointProofRow(
        "environment.ontology.attach_environment_ontology",
        "EnvironmentOntologyClient.attach_ontology",
        3,
        "fixture_pending",
        "requires stable Environment lane plus Ontology id fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.ontology.ensure_environment_ontology_runtime",
        "api.environment.ontology.ensure_environment_ontology_runtime",
        3,
        "fixture_pending",
        "requires ontology runtime artifact fixture and deploy selector",
    ),
    LiveSdkEndpointProofRow(
        "environment.ontology.list_environment_ontologies",
        "EnvironmentOntologyClient.list_ontologies",
        1,
        "fixture_pending",
        "requires committed Environment DTO fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.profile.provision_environment_profile",
        "api.environment.profile.provision_environment_profile",
        3,
        "fixture_pending",
        "requires isolated profile seed/provision fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.profile.upsert_environment_profile",
        "api.environment.profile.upsert_environment_profile",
        3,
        "fixture_pending",
        "requires isolated profile topology fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.ready.ensure_ready",
        "EnvironmentReadinessClient.ensure_ready",
        2,
        "green",
        "idempotent readiness over live Environment API provider refs",
    ),
    LiveSdkEndpointProofRow(
        "environment.runtime_ref.resolve_runtime_refs",
        "EnvironmentGraphClient.resolve_function_target",
        1,
        "blocked",
        "awaits canonical Environment runtime descriptor lookup without legacy dispatch",
    ),
    LiveSdkEndpointProofRow(
        "environment.service_routes.configure_service_api_dependency_routes",
        "EnvironmentReadinessClient.configure_service_api_dependency_routes",
        3,
        "fixture_pending",
        "node boot owns route installation; SDK mutation needs isolated route fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.session.describe_session",
        "EnvironmentSessionClient.describe_session",
        1,
        "fixture_pending",
        "requires started EnvironmentSession fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.session.join_session",
        "EnvironmentSessionClient.join_session",
        3,
        "fixture_pending",
        "requires accepted Environment admission/session fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.session.start_session",
        "EnvironmentSessionClient.start_session",
        3,
        "fixture_pending",
        "requires accepted Environment admission fixture",
    ),
    LiveSdkEndpointProofRow(
        "environment.status.describe_environment_status",
        "EnvironmentReadinessClient.describe_environment_status",
        1,
        "green",
        "runtime and commit-truth authority block read",
    ),
    LiveSdkEndpointProofRow(
        "environment.topology.describe_environment_topology",
        "api.environment.topology.describe_environment_topology",
        1,
        "green",
        "deterministic boot process/thread topology read",
    ),
)


def test_environment_endpoint_matrix_accounts_for_generated_sdk_surface() -> None:
    generated_endpoint_refs = set(ENDPOINT_REF_BY_NAME.values())
    matrix_endpoint_refs = {row.endpoint_ref for row in ENVIRONMENT_ENDPOINT_MATRIX}
    assert matrix_endpoint_refs == generated_endpoint_refs
    assert len(ENVIRONMENT_ENDPOINT_MATRIX) == 25
    assert {row.status for row in ENVIRONMENT_ENDPOINT_MATRIX} == {
        "blocked",
        "fixture_pending",
        "green",
    }


def test_live_environment_advertises_generated_environment_endpoint_surface(
    live_sdk_api_dependency_routes,
) -> None:
    advertised_refs = endpoint_refs_for_api_package(
        live_sdk_api_dependency_routes,
        api_package_name=ENVIRONMENT_API_PACKAGE_NAME,
    )
    assert advertised_refs == set(ENDPOINT_REF_BY_NAME.values())


@pytest.fixture(scope="session")
def live_environment_context(live_sdk_actor_id) -> EnvironmentReadinessContext:
    if live_sdk_actor_id is None:
        pytest.fail(
            "Environment live SDK calls require Service admission actor context; "
            "set AWARE_SDK_LIVE_ACTOR_ID",
            pytrace=False,
        )
    environment_id = _required_uuid_env("AWARE_SDK_LIVE_ENVIRONMENT_ID")
    return EnvironmentReadinessContext(
        actor_id=live_sdk_actor_id,
        environment_id=environment_id,
        process_id=_optional_uuid_env("AWARE_SDK_LIVE_PROCESS_ID"),
        thread_id=_optional_uuid_env("AWARE_SDK_LIVE_THREAD_ID"),
        branch_id=_optional_uuid_env("AWARE_SDK_LIVE_BRANCH_ID"),
        projection_hash=_optional_text_env("AWARE_SDK_LIVE_PROJECTION_HASH"),
    )


@pytest_asyncio.fixture()
async def environment_sdk(
    live_sdk_api_dependency_routes,
    live_environment_context: EnvironmentReadinessContext,
):
    api_invoker = build_live_api_client_for_package(
        live_sdk_api_dependency_routes,
        api_package_name=ENVIRONMENT_API_PACKAGE_NAME,
        actor_id=live_environment_context.actor_id,
    )
    api_client = AwareEnvironmentServiceApiClient(api_invoker)
    try:
        yield EnvironmentLiveSdk(
            api=api_client,
            readiness=EnvironmentReadinessClient(
                api_client=api_client,
                context=live_environment_context,
            ),
            context=live_environment_context,
        )
    finally:
        await close_live_api_client(api_invoker)


@pytest.mark.asyncio
async def test_environment_read_surfaces_live_sdk(
    environment_sdk: EnvironmentLiveSdk,
) -> None:
    ready = await environment_sdk.readiness.ensure_ready()
    ready_context = environment_sdk.context.with_ready_receipt(ready)
    ready_readiness = EnvironmentReadinessClient(
        api_client=environment_sdk.api,
        context=ready_context,
    )

    describe_config = await environment_sdk.api.environment.describe_config.describe_environment_config(
        DescribeEnvironmentConfigRequest(
            actor_id=ready_context.actor_id,
            environment_id=ready_context.environment_id,
            process_id=ready_context.process_id,
            thread_id=ready_context.thread_id,
            branch_id=ready_context.branch_id,
            projection_hash=ready_context.projection_hash,
        )
    )
    assert describe_config.environment_id == ready_context.environment_id
    assert describe_config.environment_config_id is not None
    assert describe_config.title
    assert describe_config.opgs

    describe = await environment_sdk.api.environment.describe.describe_environment(
        DescribeEnvironmentRequest(
            actor_id=ready_context.actor_id,
            environment_id=ready_context.environment_id,
            process_id=ready_context.process_id,
            thread_id=ready_context.thread_id,
            branch_id=ready_context.branch_id,
            projection_hash=ready_context.projection_hash,
        )
    )
    assert describe.status == "succeeded"
    assert describe.environment_config_id == describe_config.environment_config_id
    assert describe.boot_process_id is not None
    assert describe.boot_thread_id is not None
    assert describe.boot_branch_id is not None

    status = await ready_readiness.describe_environment_status(
        include_blocks=("runtime", "commit_truth"),
        strict_commit_truth=False,
    )
    assert status.status == "succeeded"
    assert status.status_version == "environment.status.v1"
    block_names = {block.name for block in status.raw_response.blocks}
    assert {"runtime", "commit_truth"}.issubset(block_names)

    topology = (
        await environment_sdk.api.environment.topology.describe_environment_topology(
            DescribeEnvironmentTopologyRequest(
                actor_id=ready_context.actor_id,
                environment_id=ready_context.environment_id,
                process_id=ready_context.process_id,
                thread_id=ready_context.thread_id,
                branch_id=ready_context.branch_id,
                projection_hash=ready_context.projection_hash,
                process_key="boot",
                thread_key="boot",
            )
        )
    )
    assert topology.status == "succeeded"
    assert topology.processes
    assert topology.processes[0].threads

    if ready_context.branch_id is None or ready_context.projection_hash is None:
        pytest.fail(
            "Environment live lane-head proof requires branch/projection context; "
            "set AWARE_SDK_LIVE_BRANCH_ID and AWARE_SDK_LIVE_PROJECTION_HASH",
            pytrace=False,
        )
    lane_head = await environment_sdk.api.environment.lane_head.get_lane_head(
        GetLaneHeadRequest(
            actor_id=ready_context.actor_id,
            environment_id=ready_context.environment_id,
            process_id=ready_context.process_id,
            thread_id=ready_context.thread_id,
            branch_id=ready_context.branch_id,
            projection_hash=ready_context.projection_hash,
        )
    )
    assert lane_head.status in {"empty", "succeeded"}
    assert lane_head.branch_id == ready_context.branch_id
    assert lane_head.projection_hash == ready_context.projection_hash


@pytest.mark.asyncio
async def test_environment_catalog_and_runtime_ref_blockers_fail_closed_live_sdk(
    environment_sdk: EnvironmentLiveSdk,
) -> None:
    context = environment_sdk.context
    with pytest.raises(RuntimeError) as capability_error:
        await environment_sdk.api.environment.capabilities.fetch_capabilities(
            FetchCapabilitiesRequest(
                actor_id=context.actor_id,
                environment_id=context.environment_id,
                process_id=context.process_id,
                thread_id=context.thread_id,
                branch_id=context.branch_id,
                projection_hash=context.projection_hash,
            )
        )
    assert "ontology-owned capability catalog" in str(capability_error.value)

    with pytest.raises(RuntimeError) as runtime_ref_error:
        await environment_sdk.api.environment.runtime_ref.resolve_runtime_refs(
            ResolveRuntimeRefsRequest(
                actor_id=context.actor_id,
                environment_id=context.environment_id,
                process_id=context.process_id,
                thread_id=context.thread_id,
                branch_id=context.branch_id,
                projection_hash=context.projection_hash,
                function_targets=[
                    ResolveRuntimeFunctionTargetQuery(
                        query_key="live-sdk-environment-runtime-ref",
                        function_ref="aware_environment.Environment.create",
                        call_target=InvokeFunctionCallTarget.opg_constructor,
                    )
                ],
                class_refs=[],
            )
        )
    runtime_error_text = str(runtime_ref_error.value).lower()
    assert "runtime" in runtime_error_text
    assert "legacy" in runtime_error_text or "retired" in runtime_error_text


def _required_uuid_env(name: str) -> UUID:
    value = _optional_uuid_env(name)
    if value is None:
        pytest.fail(f"Environment live SDK proof requires {name}.", pytrace=False)
    return value


def _optional_uuid_env(name: str) -> UUID | None:
    raw_value = _optional_text_env(name)
    return UUID(raw_value) if raw_value is not None else None


def _optional_text_env(name: str) -> str | None:
    value = (os.environ.get(name) or "").strip()
    return value or None
