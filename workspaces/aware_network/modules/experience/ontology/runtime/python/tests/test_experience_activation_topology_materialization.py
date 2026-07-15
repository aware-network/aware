from __future__ import annotations

import pytest
from uuid import uuid4

from aware_experience.materialization import service as materialization_service
from aware_experience.materialization import activation_topology_materialization


def _projection_spec(
    name: str,
) -> materialization_service.ProjectionExperienceMaterializationSpec:
    return materialization_service.ProjectionExperienceMaterializationSpec(
        experience_name=name,
        projection_key="identity",
        branches=(),
        views=(),
    )


def _context(
    *,
    profile_experience_name: str,
    profile_projection_names: tuple[str, ...],
    package_projection_names: tuple[str, ...],
) -> materialization_service._ActivationTopologyStepContext:
    profile = materialization_service.EnvironmentProfileMaterializationSpec(
        fqn_prefix="aware_actor",
        experience_name=profile_experience_name,
        key="actor.home",
        source_path="profiles.aware",
        process_configs=(
            materialization_service.EnvironmentProfileProcessMaterializationSpec(
                type="continuous",
                key="actor",
                process_key="actor",
                source_path="profiles.aware",
                thread_configs=(
                    materialization_service.EnvironmentProfileThreadMaterializationSpec(
                        key="actor.home",
                        thread_key="actor.home",
                        source_path="profiles.aware",
                        projection_experiences=tuple(
                            materialization_service.EnvironmentProfileThreadProjectionMaterializationSpec(
                                projection_experience_name=name,
                                projection_key="identity",
                                source_path="profiles.aware",
                            )
                            for name in profile_projection_names
                        ),
                    ),
                ),
            ),
        ),
    )
    return materialization_service._ActivationTopologyStepContext(
        environment_handle="kernel",
        profile_spec=profile,
        action_specs=(),
        connector_specs=(),
        activation_target_specs=(),
        projection_specs=tuple(
            _projection_spec(name) for name in package_projection_names
        ),
        environment_events={},
        endpoint_request_attributes={},
    )


def test_activation_topology_prefers_profile_owner_projection_for_multi_projection_profile() -> (
    None
):
    context = _context(
        profile_experience_name="aware_actor_roles",
        profile_projection_names=(
            "aware_actor_roles",
            "aware_actor_commits",
            "aware_actor_subscriptions",
        ),
        package_projection_names=(
            "aware_actor_roles",
            "aware_actor_commits",
            "aware_actor_subscriptions",
        ),
    )

    resolved = materialization_service._activation_projection_spec_for_profile(
        context=context,
    )

    assert resolved.experience_name == "aware_actor_roles"


def test_activation_topology_still_fails_when_multi_projection_profile_has_no_owner_projection() -> (
    None
):
    context = _context(
        profile_experience_name="aware_actor_missing",
        profile_projection_names=("aware_actor_commits", "aware_actor_subscriptions"),
        package_projection_names=("aware_actor_commits", "aware_actor_subscriptions"),
    )

    with pytest.raises(
        RuntimeError, match="requires exactly one projection experience"
    ):
        materialization_service._activation_projection_spec_for_profile(
            context=context,
        )


@pytest.mark.asyncio
async def test_activation_topology_resolves_profile_specs_with_committed_dependency_projection_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependency_branch_id = uuid4()
    captured: dict[str, object] = {}

    async def _load_projection_experience_catalog(**kwargs: object):
        captured["branch_ids"] = kwargs["branch_ids"]
        return {"projections_by_name": {}}

    def _resolve_environment_profile_materialization_specs(**kwargs: object):
        captured["external_projection_keys"] = kwargs[
            "external_projection_keys_by_experience_name"
        ]
        return ()

    monkeypatch.setattr(
        activation_topology_materialization,
        "_projection_keys_by_experience_name_from_catalog",
        lambda **_: {"aware_conversation_spaces": "conversation_spaces"},
    )
    dependencies = (
        activation_topology_materialization.ActivationTopologyMaterializationDependencies(
            load_projection_experience_catalog=_load_projection_experience_catalog,
            resolve_environment_profile_materialization_specs=(
                _resolve_environment_profile_materialization_specs
            ),
            resolve_action_materialization_specs=lambda **_: (),
            resolve_connector_config_materialization_specs=lambda **_: (),
            resolve_activation_target_materialization_specs=lambda **_: (),
            resolve_projection_materialization_specs=lambda **_: (),
            resolve_projection_opgi_id_for_projection_key=lambda **_: uuid4(),
            find_projection_graph_by_opgi_id=lambda **_: None,  # type: ignore[arg-type]
            connector_invocation_action_target_ids=lambda **_: (None, None, None),  # type: ignore[arg-type,return-value]
            normalize_symbol=lambda raw: raw,
        )
    )

    receipt = await activation_topology_materialization.materialize_experience_activation_topology_ontology(
        index=object(),  # type: ignore[arg-type]
        actor_id=None,
        lane=materialization_service.MaterializationLaneContext(
            branch_id=uuid4(), projection_hash="ProjectionExperience"
        ),
        compile_plan_payloads=(),
        projection_reference_branch_ids_by_name={
            "aware_conversation_spaces": dependency_branch_id
        },
        dependencies=dependencies,
    )

    assert receipt is None
    assert captured == {
        "branch_ids": (dependency_branch_id,),
        "external_projection_keys": {
            "aware_conversation_spaces": "conversation_spaces"
        },
    }
