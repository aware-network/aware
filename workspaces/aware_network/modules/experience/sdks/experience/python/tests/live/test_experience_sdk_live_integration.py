from __future__ import annotations

import pytest
import pytest_asyncio

from aware_experience_sdk import build_experience_sdk_client
from aware_experience_service_api import AwareExperienceServiceApiClient
from aware_experience_service_api._bindings import ENDPOINT_REF_BY_NAME
from aware_sdk_network.testing.live import (
    LiveSdkEndpointProofRow,
    build_live_api_client_for_package,
    close_live_api_client,
    endpoint_refs_for_api_package,
)


pytest_plugins = ("aware_sdk_network.testing.pytest_plugin",)


EXPERIENCE_API_PACKAGE_NAME = "experience-service-api"


EXPERIENCE_ENDPOINT_MATRIX: tuple[LiveSdkEndpointProofRow, ...] = (
    LiveSdkEndpointProofRow(
        "experience.activate_experience_section_graph_binding.activate_experience_section_graph_binding",
        "sdk.activate_section_graph_binding",
        3,
        "fixture_pending",
        "requires an existing section graph binding fixture with activation scope",
    ),
    LiveSdkEndpointProofRow(
        "experience.actor_admission.admit_experience_actor_config",
        "sdk.admit_actor_config",
        3,
        "fixture_pending",
        "requires Identity actor-config fixture and admission read-back",
    ),
    LiveSdkEndpointProofRow(
        "experience.apply_experience_view_event_transition.apply_experience_view_event_transition",
        "sdk.apply_view_event_transition",
        3,
        "fixture_pending",
        "requires a view-event transition fixture owned by an Experience package",
    ),
    LiveSdkEndpointProofRow(
        "experience.environment_profile.apply_experience_environment_profile_programs",
        "sdk.apply_environment_profile_programs",
        2,
        "fixture_pending",
        "requires isolated EnvironmentExperience profile program fixture",
    ),
    LiveSdkEndpointProofRow(
        "experience.environment_profile.provision_experience_environment_profile",
        "sdk.provision_environment_profile",
        2,
        "fixture_pending",
        "requires isolated EnvironmentExperience topology seed fixture",
    ),
    LiveSdkEndpointProofRow(
        "experience.environment_profile.upsert_experience_environment_profile",
        "sdk.upsert_environment_profile",
        2,
        "fixture_pending",
        "requires isolated EnvironmentExperience profile fixture",
    ),
    LiveSdkEndpointProofRow(
        "experience.get_experience_section_graph_binding_catalog.get_experience_section_graph_binding_catalog",
        "sdk.get_section_graph_binding_catalog",
        1,
        "green",
        "read-only catalog call over live Services provider refs",
    ),
    LiveSdkEndpointProofRow(
        "experience.get_experience_section_graph_binding_state.get_experience_section_graph_binding_state",
        "sdk.get_section_graph_binding_state",
        1,
        "fixture_pending",
        "requires an activated binding state fixture",
    ),
    LiveSdkEndpointProofRow(
        "experience.invoke_experience_view_invocation_action.invoke_experience_view_invocation_action",
        "sdk.invoke_view_invocation_action",
        3,
        "fixture_pending",
        "requires API-backed view action fixture and downstream receipt assertion",
    ),
    LiveSdkEndpointProofRow(
        "experience.package_materialization.resolve_experience_package_projection_ownership",
        "sdk.resolve_package_projection_ownership",
        1,
        "green",
        "read-only package ownership resolver over identity-default source",
    ),
    LiveSdkEndpointProofRow(
        "experience.program.apply_program_ref",
        "sdk.api_client.experience.program.apply_program_ref",
        3,
        "fixture_pending",
        "requires deterministic program ref fixture and turn read-back",
    ),
    LiveSdkEndpointProofRow(
        "experience.program.get_turn_execution",
        "sdk.api_client.experience.program.get_turn_execution",
        1,
        "fixture_pending",
        "requires an existing turn execution fixture",
    ),
    LiveSdkEndpointProofRow(
        "experience.program.run_program",
        "sdk.api_client.experience.program.run_program",
        3,
        "fixture_pending",
        "requires isolated program execution fixture",
    ),
    LiveSdkEndpointProofRow(
        "experience.program.submit_program_turn",
        "sdk.api_client.experience.program.submit_program_turn",
        3,
        "fixture_pending",
        "requires active program turn fixture",
    ),
    LiveSdkEndpointProofRow(
        "experience.record_experience_view_invocation_action.record_experience_view_invocation_action",
        "sdk.record_view_invocation_action",
        2,
        "fixture_pending",
        "requires idempotent view invocation action fixture",
    ),
    LiveSdkEndpointProofRow(
        "experience.request_experience_layout_transition.request_experience_layout_transition",
        "sdk.request_layout_transition",
        3,
        "fixture_pending",
        "requires Identity actor/session and layout transition fixture",
    ),
    LiveSdkEndpointProofRow(
        "experience.resolve_experience_invocation_action_role_policy.resolve_experience_invocation_action_role_policy",
        "sdk.api_client.experience.resolve_experience_invocation_action_role_policy.resolve_experience_invocation_action_role_policy",
        1,
        "fixture_pending",
        "requires view action role policy fixture",
    ),
    LiveSdkEndpointProofRow(
        "experience.resolve_experience_thread_layout_intent.resolve_experience_thread_layout_intent",
        "sdk.resolve_thread_layout_intent",
        1,
        "fixture_pending",
        "requires declared thread layout intent fixture",
    ),
    LiveSdkEndpointProofRow(
        "experience.session_handoff.ensure_experience_session_handoff",
        "sdk.ensure_session_handoff",
        2,
        "fixture_pending",
        "requires Interface/Environment/Identity session handoff fixture",
    ),
    LiveSdkEndpointProofRow(
        "experience.session_handoff.get_experience_session_handoff_status",
        "sdk.get_session_handoff_status",
        1,
        "fixture_pending",
        "requires session handoff scope fixture",
    ),
    LiveSdkEndpointProofRow(
        "experience.watch_experience_section_graph_bindings.watch_experience_section_graph_bindings",
        "sdk.watch_section_graph_bindings / generated stream method",
        4,
        "stream_contract",
        "requires explicit stream fixture once bindings exist",
    ),
    LiveSdkEndpointProofRow(
        "experience.watch_experience_view_state.watch_experience_view_state",
        "sdk.api_client.experience.watch_experience_view_state.watch_experience_view_state",
        4,
        "stream_contract",
        "requires explicit stream fixture once view-state providers exist",
    ),
)


def test_experience_endpoint_matrix_accounts_for_generated_sdk_surface() -> None:
    generated_endpoint_refs = set(ENDPOINT_REF_BY_NAME.values())
    matrix_endpoint_refs = {row.endpoint_ref for row in EXPERIENCE_ENDPOINT_MATRIX}
    assert matrix_endpoint_refs == generated_endpoint_refs
    assert len(EXPERIENCE_ENDPOINT_MATRIX) == 22


def test_live_services_advertise_generated_experience_endpoint_surface(
    live_sdk_api_dependency_routes,
) -> None:
    advertised_refs = endpoint_refs_for_api_package(
        live_sdk_api_dependency_routes,
        api_package_name=EXPERIENCE_API_PACKAGE_NAME,
    )
    assert advertised_refs == set(ENDPOINT_REF_BY_NAME.values())


@pytest_asyncio.fixture()
async def experience_sdk(live_sdk_api_dependency_routes, live_sdk_actor_id):
    if live_sdk_actor_id is None:
        pytest.fail(
            "Experience live SDK calls require Service admission actor context; "
            "set AWARE_SDK_LIVE_ACTOR_ID",
            pytrace=False,
        )
    api_invoker = build_live_api_client_for_package(
        live_sdk_api_dependency_routes,
        api_package_name=EXPERIENCE_API_PACKAGE_NAME,
        actor_id=live_sdk_actor_id,
    )
    try:
        yield build_experience_sdk_client(AwareExperienceServiceApiClient(api_invoker))
    finally:
        await close_live_api_client(api_invoker)


@pytest.mark.asyncio
async def test_experience_package_projection_ownership_live_sdk(
    experience_sdk,
) -> None:
    response = await experience_sdk.resolve_package_projection_ownership(
        workspace_root="/home/luis/aware",
        experience_toml_path="modules/identity/experience/default/aware.experience.toml",
        package_name="identity-default",
        validate_only=True,
    )
    catalog = response.catalog
    assert catalog.status == "resolved"
    assert catalog.package_name == "identity-default"
    assert catalog.fqn_prefix == "identity"
    assert catalog.evidence.get("projection_experience_count") == 7
    assert catalog.missing_required_projection_refs == []
    assert len(catalog.entries) == 7
    program_port_refs = {
        consumer.ref
        for entry in catalog.entries
        for consumer in entry.consumers
        if consumer.kind == "program_port"
    }
    assert program_port_refs == {
        "actor_role",
        "actor_subscription",
        "event_config_condition_config_scope",
        "identity",
        "organization",
        "role",
        "role_config",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "experience_name",
    (
        "identity",
        "actor_role",
        "actor_subscription",
        "event_config_condition_config_scope",
    ),
)
async def test_experience_section_graph_binding_catalog_live_sdk(
    experience_sdk,
    experience_name: str,
) -> None:
    response = await experience_sdk.get_section_graph_binding_catalog(
        experience_name=experience_name
    )
    assert response.experience_name == experience_name
    assert response.catalog_revision
    assert response.bindings == []
