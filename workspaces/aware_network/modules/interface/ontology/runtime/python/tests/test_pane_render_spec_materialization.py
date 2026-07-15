from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from _meta_runtime_support import (
    build_interface_meta_runtime,
    isolated_meta_aware_root,
)
from _interface_runtime_test_paths import REPO_ROOT


def _write_materialization_artifact(*, path: Path) -> dict[str, object]:
    from aware_interface.builder import (
        _PANE_RENDER_SPEC_MATERIALIZATION_KIND,
        _PANE_RENDER_SPEC_MATERIALIZATION_SCHEMA_VERSION,
        _canonical_json_sha256,
        _pane_render_spec_semantic_object_ids,
        _stable_pane_render_spec_materialization_commit_id,
    )
    from aware_experience.stable_ids import (
        stable_projection_experience_view_invocation_action_config_id,
    )
    from aware_interface_ontology.stable_ids import stable_pane_render_spec_id

    namespace = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface/pane-render-spec-materialization",
    )
    pane_config_id = uuid5(
        namespace,
        "pane-config-projection-experience-view:identity-admission",
    )
    projection_experience_view_id = uuid5(
        namespace,
        "projection-experience-view:identity-admission",
    )
    state_model_id = uuid5(namespace, "state-model:identity-admission")
    state_attribute_config_id = uuid5(
        namespace,
        "state-attribute:identity-admission.status",
    )
    status_tone_attribute_config_id = uuid5(
        namespace,
        "state-attribute:identity-admission.status_tone",
    )
    avatar_media_attribute_config_id = uuid5(
        namespace,
        "state-attribute:identity-admission.avatar_media",
    )
    api_view_capability_endpoint_id = uuid5(
        namespace,
        "api-view-capability-endpoint:identity-admission.admit_identity",
    )
    view_action_id = stable_projection_experience_view_invocation_action_config_id(
        projection_experience_view_id=projection_experience_view_id,
        api_view_capability_endpoint_id=api_view_capability_endpoint_id,
    )
    render_spec_id = stable_pane_render_spec_id(
        pane_config_id=pane_config_id,
        name="identity_admission_default",
        spec_version="0.1.0",
    )
    payload: dict[str, object] = {
        "spec_id": str(render_spec_id),
        "name": "identity_admission_default",
        "spec_version": "0.1.0",
        "pane_name": "identity_admission",
        "pane_kind": "identity_admission",
        "view_ref": "aware_control_identity.identity.admission.v1",
        "projection_view_key": "identity.admission.v1",
        "pane_config_id": str(pane_config_id),
        "projection_experience_view_id": str(projection_experience_view_id),
        "state_model_id": str(state_model_id),
        "root_node_key": "root",
        "nodes": [
            {
                "node_key": "root",
                "node_kind": "column",
                "semantic_role": "pane",
                "order": 0,
                "style_tokens": [
                    {
                        "token_key": "density",
                        "token_value": "compact",
                    }
                ],
            },
            {
                "node_key": "status",
                "node_kind": "status",
                "parent_node_key": "root",
                "semantic_role": "status",
                "order": 1,
                "state_bindings": [
                    {
                        "binding_key": "status_text",
                        "target_property": "text",
                        "json_path": "$.status",
                        "state_model_id": str(state_model_id),
                        "state_attribute_config_id": str(state_attribute_config_id),
                        "transform": "text",
                        "fallback_value": "unknown",
                    },
                    {
                        "binding_key": "status_tone",
                        "target_property": "tone",
                        "json_path": "$.status_tone",
                        "state_model_id": str(state_model_id),
                        "state_attribute_config_id": str(status_tone_attribute_config_id),
                        "transform": "text",
                    },
                ],
            },
            {
                "node_key": "avatar_media",
                "node_kind": "component",
                "parent_node_key": "root",
                "semantic_role": "metadata",
                "order": 2,
                "component_ref": "aware.storage.media.image",
                "state_bindings": [
                    {
                        "binding_key": "avatar_media_ref",
                        "target_property": "media_ref",
                        "json_path": "$.avatar_media",
                        "state_model_id": str(state_model_id),
                        "state_attribute_config_id": str(avatar_media_attribute_config_id),
                        "transform": "raw",
                    }
                ],
            },
            {
                "node_key": "submit",
                "node_kind": "button",
                "parent_node_key": "root",
                "semantic_role": "action",
                "order": 3,
                "label": "Admit",
                "action_bindings": [
                    {
                        "binding_key": "admit_identity",
                        "event": "activate",
                        "action_key": "admit_identity",
                        "projection_experience_view_invocation_action_id": str(view_action_id),
                        "label": "Admit",
                        "receipt_policy": "show_receipt",
                        "input_bindings": [
                            {
                                "payload_path": "profile.display_name",
                                "source_node_key": "display_name_input",
                            }
                        ],
                    }
                ],
            },
        ],
        "renderer_requirements": [
            {
                "capability_kind": "node_kind",
                "capability_key": "column",
                "is_required": True,
            },
            {
                "capability_kind": "action_binding",
                "capability_key": "view_action",
                "is_required": True,
            },
        ],
    }
    row: dict[str, object] = {
        "source_path": (
            "workspaces/aware_network/modules/identity/interfaces/panes/"
            "identity_admission/identity_admission.aware#render:default"
        ),
        "source_kind": "authored_aware",
        "pane_name": "identity_admission",
        "pane_kind": "identity_admission",
        "view_ref": "aware_control_identity.identity.admission.v1",
        "projection_view_key": "identity.admission.v1",
        "render_spec_id": str(render_spec_id),
        "render_spec_content_hash_sha256": _canonical_json_sha256(payload),
        "semantic_object_ids": _pane_render_spec_semantic_object_ids(
            payload=payload,
        ),
        "payload": payload,
    }
    package_name = "aware-control-interface"
    fqn_prefix = "aware_control_interface"
    commit_seed: dict[str, object] = {
        "schema_version": _PANE_RENDER_SPEC_MATERIALIZATION_SCHEMA_VERSION,
        "materialization_kind": _PANE_RENDER_SPEC_MATERIALIZATION_KIND,
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "render_spec_count": 1,
        "render_specs": [row],
    }
    materialization_content_hash = _canonical_json_sha256(commit_seed)
    artifact: dict[str, object] = {
        "schema_version": _PANE_RENDER_SPEC_MATERIALIZATION_SCHEMA_VERSION,
        "materialization_kind": _PANE_RENDER_SPEC_MATERIALIZATION_KIND,
        "materialization_commit_id": str(
            _stable_pane_render_spec_materialization_commit_id(
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                content_hash_sha256=materialization_content_hash,
            )
        ),
        "materialization_content_hash_sha256": materialization_content_hash,
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "render_spec_count": 1,
        "render_specs": [row],
    }
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def _write_multi_materialization_artifact(*, path: Path) -> dict[str, object]:
    from aware_interface.builder import (
        _canonical_json_sha256,
        _pane_render_spec_semantic_object_ids,
        _stable_pane_render_spec_materialization_commit_id,
    )
    from aware_interface_ontology.stable_ids import stable_pane_render_spec_id

    artifact = json.loads(json.dumps(_write_materialization_artifact(path=path)))
    rows = cast(list[dict[str, object]], artifact["render_specs"])
    second_row = json.loads(json.dumps(rows[0]))
    second_payload = cast(dict[str, object], second_row["payload"])
    namespace = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface/pane-render-spec-materialization:secondary",
    )
    second_binding_id = uuid5(
        namespace,
        "pane-config-projection-experience-view:identity-audit",
    )
    second_view_id = uuid5(
        namespace,
        "projection-experience-view:identity-audit",
    )
    second_spec_id = stable_pane_render_spec_id(
        pane_config_id=second_binding_id,
        name="identity_audit_default",
        spec_version="0.1.0",
    )
    second_payload["spec_id"] = str(second_spec_id)
    second_payload["name"] = "identity_audit_default"
    second_payload["pane_name"] = "identity_audit"
    second_payload["pane_kind"] = "identity_audit"
    second_payload["view_ref"] = "aware_control_identity.identity.audit.v1"
    second_payload["projection_view_key"] = "identity.audit.v1"
    second_payload["pane_config_id"] = str(second_binding_id)
    second_payload["projection_experience_view_id"] = str(second_view_id)
    second_row["source_path"] = "panes/identity_audit/identity_audit.aware#render:default"
    second_row["pane_name"] = "identity_audit"
    second_row["pane_kind"] = "identity_audit"
    second_row["view_ref"] = "aware_control_identity.identity.audit.v1"
    second_row["projection_view_key"] = "identity.audit.v1"
    second_row["render_spec_id"] = str(second_spec_id)
    second_row["render_spec_content_hash_sha256"] = _canonical_json_sha256(second_payload)
    second_row["semantic_object_ids"] = _pane_render_spec_semantic_object_ids(
        payload=second_payload,
    )
    rows.append(second_row)
    artifact["render_spec_count"] = len(rows)
    artifact["render_specs"] = rows

    commit_seed: dict[str, object] = {
        "schema_version": artifact["schema_version"],
        "materialization_kind": artifact["materialization_kind"],
        "package_name": artifact["package_name"],
        "fqn_prefix": artifact["fqn_prefix"],
        "render_spec_count": artifact["render_spec_count"],
        "render_specs": rows,
    }
    materialization_content_hash = _canonical_json_sha256(commit_seed)
    artifact["materialization_content_hash_sha256"] = materialization_content_hash
    artifact["materialization_commit_id"] = str(
        _stable_pane_render_spec_materialization_commit_id(
            package_name=cast(str, artifact["package_name"]),
            fqn_prefix=cast(str, artifact["fqn_prefix"]),
            content_hash_sha256=materialization_content_hash,
        )
    )
    path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return artifact


@pytest.mark.asyncio
async def test_pane_render_spec_materialization_commits_schema_v2_artifact(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_interface_ontology  # noqa: F401

    from aware_interface_ontology.render.pane_render_enums import (
        PaneStateBindingTargetProperty,
    )
    from aware_interface.ontology.materialization import (
        load_pane_render_spec_runtime_payloads_from_oig_head,
        load_pane_render_spec_runtime_states_from_materialization_artifact_oig,
        materialize_pane_render_specs_from_materialization_artifact,
    )

    materialization_path = tmp_path / "pane_render_specs.materialization.json"
    artifact = _write_materialization_artifact(path=materialization_path)
    semantic_object_ids = cast(
        Mapping[str, object],
        cast(list[object], artifact["render_specs"])[0],
    )["semantic_object_ids"]
    semantic_object_ids = cast(Mapping[str, object], semantic_object_ids)
    render_payload = cast(
        Mapping[str, object],
        cast(Mapping[str, object], cast(list[object], artifact["render_specs"])[0])["payload"],
    )
    render_nodes = cast(list[Mapping[str, object]], render_payload["nodes"])
    submit_node = next(node for node in render_nodes if node["node_key"] == "submit")
    submit_actions = cast(list[Mapping[str, object]], submit_node["action_bindings"])
    view_action_id = UUID(cast(str, submit_actions[0]["projection_experience_view_invocation_action_id"]))

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        index = cast(Any, context.index)
        environment_id = uuid4()
        process_id = uuid4()
        thread_id = uuid4()

        result = await materialize_pane_render_specs_from_materialization_artifact(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            materialization_path=materialization_path,
        )

        assert result.materialization_path == materialization_path.resolve()
        assert result.materialization_commit_id == UUID(cast(str, artifact["materialization_commit_id"]))
        assert result.branch_id == result.materialization_commit_id
        assert result.last_commit_id is not None
        assert result.last_head_commit_id == result.last_commit_id
        assert result.object_instance_graph_commit_id is not None
        assert len(result.pane_render_specs) == 1
        assert len(result.runtime_payloads) == 1

        materialized = result.pane_render_specs[0]
        pane_render_spec = materialized.pane_render_spec
        assert pane_render_spec.id == UUID(cast(str, semantic_object_ids["pane_render_spec_id"]))
        assert pane_render_spec.name == "identity_admission_default"
        assert pane_render_spec.view_ref == "aware_control_identity.identity.admission.v1"
        assert pane_render_spec.projection_view_key == "identity.admission.v1"
        assert pane_render_spec.root_node_key == "root"
        materialized_runtime_payload = result.runtime_payloads[0]
        assert materialized_runtime_payload.source_kind == "materialized_oig"
        assert materialized_runtime_payload.pane_render_spec_id == pane_render_spec.id
        assert materialized_runtime_payload.payload["spec_id"] == str(pane_render_spec.id)
        assert materialized_runtime_payload.payload["pane_name"] == "identity_admission"
        assert materialized_runtime_payload.payload["pane_kind"] == "identity_admission"
        assert materialized_runtime_payload.payload["root_node_key"] == "root"

        node_ids = cast(
            Mapping[str, str],
            semantic_object_ids["pane_render_node_ids_by_key"],
        )
        nodes_by_key = {node.node_key: node for node in pane_render_spec.nodes}
        assert sorted(nodes_by_key) == ["avatar_media", "root", "status", "submit"]
        assert nodes_by_key["root"].id == UUID(node_ids["root"])
        assert nodes_by_key["status"].id == UUID(node_ids["status"])
        assert nodes_by_key["avatar_media"].id == UUID(node_ids["avatar_media"])
        assert nodes_by_key["submit"].id == UUID(node_ids["submit"])

        state_binding_ids = cast(
            Mapping[str, str],
            semantic_object_ids["pane_state_binding_ids_by_ref"],
        )
        status_bindings = nodes_by_key["status"].state_bindings
        assert [binding.binding_key for binding in status_bindings] == [
            "status_text",
            "status_tone",
        ]
        assert status_bindings[0].id == UUID(state_binding_ids["status.status_text"])
        assert status_bindings[1].id == UUID(state_binding_ids["status.status_tone"])
        assert status_bindings[0].state_attribute_config_id is not None
        assert status_bindings[1].state_attribute_config_id is not None
        avatar_media_bindings = nodes_by_key["avatar_media"].state_bindings
        assert [binding.binding_key for binding in avatar_media_bindings] == ["avatar_media_ref"]
        assert avatar_media_bindings[0].id == UUID(state_binding_ids["avatar_media.avatar_media_ref"])
        assert avatar_media_bindings[0].target_property is PaneStateBindingTargetProperty.media_ref
        assert avatar_media_bindings[0].state_attribute_config_id is not None

        action_binding_ids = cast(
            Mapping[str, str],
            semantic_object_ids["pane_action_binding_ids_by_ref"],
        )
        input_binding_ids = cast(
            Mapping[str, str],
            semantic_object_ids["pane_input_binding_ids_by_ref"],
        )
        action_bindings = nodes_by_key["submit"].action_bindings
        assert [binding.binding_key for binding in action_bindings] == ["admit_identity"]
        assert action_bindings[0].id == UUID(action_binding_ids["submit.admit_identity"])
        assert action_bindings[0].projection_experience_view_invocation_action_id == view_action_id
        assert "pane_config_api_capability_endpoint_id" not in type(action_bindings[0]).model_fields
        assert [binding.payload_path for binding in action_bindings[0].input_bindings] == ["profile.display_name"]
        assert action_bindings[0].input_bindings[0].id == UUID(
            input_binding_ids["submit.admit_identity.profile.display_name"]
        )

        style_token_ids = cast(
            Mapping[str, str],
            semantic_object_ids["pane_style_token_ref_ids_by_ref"],
        )
        assert [token.token_key for token in nodes_by_key["root"].style_tokens] == ["density"]
        assert nodes_by_key["root"].style_tokens[0].id == UUID(style_token_ids["root.density"])

        requirement_ids = cast(
            Mapping[str, str],
            semantic_object_ids["pane_renderer_capability_requirement_ids_by_ref"],
        )
        requirements = {
            f"{requirement.capability_kind.value}:{requirement.capability_key}": requirement
            for requirement in pane_render_spec.renderer_requirements
        }
        assert sorted(requirements) == [
            "action_binding:view_action",
            "node_kind:column",
        ]
        assert requirements["node_kind:column"].id == UUID(requirement_ids["node_kind:column"])

        oig_runtime_payloads = await load_pane_render_spec_runtime_payloads_from_oig_head(
            index=index,
            branch_id=result.branch_id,
            pane_render_spec_ids=(pane_render_spec.id,),
            pane_name_by_pane_config_id={
                pane_render_spec.pane_config_id: "identity_admission",
            },
            pane_kind_by_pane_config_id={
                pane_render_spec.pane_config_id: "identity_admission",
            },
        )
        assert len(oig_runtime_payloads) == 1
        oig_runtime_payload = oig_runtime_payloads[0]
        assert oig_runtime_payload.source_kind == "committed_oig"
        assert oig_runtime_payload.pane_render_spec_id == pane_render_spec.id
        assert oig_runtime_payload.pane_config_id == (pane_render_spec.pane_config_id)
        assert oig_runtime_payload.payload["spec_id"] == str(pane_render_spec.id)
        assert oig_runtime_payload.payload["pane_name"] == "identity_admission"
        assert oig_runtime_payload.payload["pane_kind"] == "identity_admission"
        assert oig_runtime_payload.payload["view_ref"] == "aware_control_identity.identity.admission.v1"
        assert oig_runtime_payload.payload["projection_view_key"] == "identity.admission.v1"
        assert oig_runtime_payload.payload["root_node_key"] == "root"
        oig_nodes = cast(list[Mapping[str, object]], oig_runtime_payload.payload["nodes"])
        assert [node["node_key"] for node in oig_nodes] == [
            "root",
            "status",
            "avatar_media",
            "submit",
        ]
        oig_status = oig_nodes[1]
        oig_status_bindings = cast(list[Mapping[str, object]], oig_status["state_bindings"])
        assert oig_status_bindings[0]["state_attribute_config_id"] == (
            str(status_bindings[0].state_attribute_config_id)
        )
        assert oig_status_bindings[1]["target_property"] == "tone"
        assert oig_status_bindings[1]["state_attribute_config_id"] == (
            str(status_bindings[1].state_attribute_config_id)
        )
        oig_avatar_media = oig_nodes[2]
        oig_avatar_media_bindings = cast(
            list[Mapping[str, object]],
            oig_avatar_media["state_bindings"],
        )
        assert oig_avatar_media_bindings[0]["target_property"] == "media_ref"
        assert oig_avatar_media_bindings[0]["state_attribute_config_id"] == (
            str(avatar_media_bindings[0].state_attribute_config_id)
        )
        oig_submit = oig_nodes[3]
        oig_actions = cast(list[Mapping[str, object]], oig_submit["action_bindings"])
        assert oig_actions[0]["action_key"] == "admit_identity"
        assert oig_actions[0]["action_kind"] == "view_action"
        assert oig_actions[0]["view_action_key"] == "admit_identity"
        assert oig_actions[0]["projection_experience_view_invocation_action_id"] == (str(view_action_id))

        oig_runtime_states = await load_pane_render_spec_runtime_states_from_materialization_artifact_oig(
            index=index,
            materialization_path=materialization_path,
            pane_name_by_pane_config_id={
                pane_render_spec.pane_config_id: "identity_admission",
            },
            pane_kind_by_pane_config_id={
                pane_render_spec.pane_config_id: "identity_admission",
            },
        )
        assert len(oig_runtime_states) == 1
        oig_runtime_state = oig_runtime_states[0]
        assert oig_runtime_state.source_kind == "committed_oig"
        assert oig_runtime_state.branch_id == result.branch_id
        assert oig_runtime_state.projection_hash is not None
        assert oig_runtime_state.last_commit_id == result.last_commit_id
        assert oig_runtime_state.object_instance_graph_commit_id == result.object_instance_graph_commit_id
        assert oig_runtime_state.pane_render_spec_id == pane_render_spec.id
        assert oig_runtime_state.pane_config_id == (pane_render_spec.pane_config_id)
        assert oig_runtime_state.render_spec_content_hash_sha256 == (
            oig_runtime_payload.render_spec_content_hash_sha256
        )
        assert oig_runtime_state.payload["spec_id"] == str(pane_render_spec.id)

        with pytest.raises(RuntimeError, match="requires pane kind"):
            await load_pane_render_spec_runtime_payloads_from_oig_head(
                index=index,
                branch_id=result.branch_id,
                pane_render_spec_ids=(pane_render_spec.id,),
                pane_kind_by_pane_config_id={},
            )

        rerun = await materialize_pane_render_specs_from_materialization_artifact(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            materialization_path=materialization_path,
        )

        assert rerun.branch_id == result.branch_id
        assert len(rerun.pane_render_specs) == 1
        rerun_spec = rerun.pane_render_specs[0].pane_render_spec
        assert rerun_spec.id == pane_render_spec.id
        assert sorted(node.node_key for node in rerun_spec.nodes) == [
            "avatar_media",
            "root",
            "status",
            "submit",
        ]
        assert len(rerun_spec.renderer_requirements) == 2


@pytest.mark.asyncio
async def test_pane_render_spec_materialization_rebuilds_without_hydrating_stale_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_interface.ontology.materialization.render as render_mod

    from aware_interface.ontology.materialization import (
        materialize_pane_render_specs_from_materialization_artifact,
    )

    materialization_path = tmp_path / "pane_render_specs.materialization.json"
    artifact = _write_materialization_artifact(path=materialization_path)

    async def _raise_on_stale_head_hydration(**_kwargs: object) -> object:
        raise AssertionError("PaneRenderSpec snapshot materialization must not hydrate stale lane head")

    monkeypatch.setattr(
        render_mod,
        "_hydrate_lane_root_from_head",
        _raise_on_stale_head_hydration,
    )

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_runtime(
            REPO_ROOT,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None

        result = await materialize_pane_render_specs_from_materialization_artifact(
            runtime=runtime,
            index=cast(Any, context.index),
            actor_id=None,
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            materialization_path=materialization_path,
        )

    semantic_object_ids = cast(
        Mapping[str, object],
        cast(Mapping[str, object], cast(list[object], artifact["render_specs"])[0])["semantic_object_ids"],
    )
    assert result.pane_render_specs[0].pane_render_spec.id == UUID(
        cast(str, semantic_object_ids["pane_render_spec_id"])
    )


@pytest.mark.asyncio
async def test_pane_render_spec_materialization_rebuilds_stale_child_graph(
    tmp_path: Path,
) -> None:
    from aware_interface.ontology.materialization.render import (
        _materialize_nodes,
        _materialize_renderer_requirements,
    )
    from aware_interface_ontology.render.pane_render_enums import (
        PaneRenderCapabilityKind,
        PaneRenderNodeKind,
    )
    from aware_interface_ontology.render.pane_render_node import PaneRenderNode
    from aware_interface_ontology.render.pane_render_spec import PaneRenderSpec
    from aware_interface_ontology.render.pane_renderer_capability_requirement import (
        PaneRendererCapabilityRequirement,
    )
    from aware_interface_ontology.render.pane_style_token_ref import PaneStyleTokenRef
    from aware_meta.runtime import find_meta_graph_projection_hash_by_name

    materialization_path = tmp_path / "pane_render_specs.materialization.json"
    artifact = _write_materialization_artifact(path=materialization_path)
    row = cast(Mapping[str, object], cast(list[object], artifact["render_specs"])[0])
    render_payload = cast(Mapping[str, object], row["payload"])
    semantic_object_ids = cast(Mapping[str, object], row["semantic_object_ids"])

    pane_render_spec_id = UUID(cast(str, semantic_object_ids["pane_render_spec_id"]))
    node_ids = cast(
        Mapping[str, str],
        semantic_object_ids["pane_render_node_ids_by_key"],
    )
    style_token_ids = cast(
        Mapping[str, str],
        semantic_object_ids["pane_style_token_ref_ids_by_ref"],
    )
    requirement_ids = cast(
        Mapping[str, str],
        semantic_object_ids["pane_renderer_capability_requirement_ids_by_ref"],
    )
    pane_config_id = UUID(
        cast(str, render_payload["pane_config_id"])
    )

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_runtime(
            REPO_ROOT,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        projection_hash = find_meta_graph_projection_hash_by_name(
            index=cast(Any, context.index),
            projection_name="PaneRenderSpec",
        )
        lane = runtime.bind(
            projection=projection_hash,
            branch_id=uuid4(),
            context=context,
        )
        with lane.activate(commit=False):
            pane_render_spec = await PaneRenderSpec.create(
                pane_config_id=(pane_config_id),
                name=cast(str, render_payload["name"]),
                spec_version=cast(str, render_payload["spec_version"]),
                root_node_key=cast(str, render_payload["root_node_key"]),
            )
            assert pane_render_spec.id == pane_render_spec_id
            pane_render_spec.nodes = [
                PaneRenderNode.model_construct(
                    id=UUID(node_ids["root"]),
                    node_key="root",
                    node_kind=PaneRenderNodeKind.column,
                    style_tokens=[
                        PaneStyleTokenRef.model_construct(
                            id=UUID(style_token_ids["root.density"]),
                            token_key="density",
                            token_value="stale",
                        )
                    ],
                )
            ]
            pane_render_spec.renderer_requirements = [
                PaneRendererCapabilityRequirement.model_construct(
                    id=UUID(requirement_ids["node_kind:column"]),
                    capability_kind=PaneRenderCapabilityKind.node_kind,
                    capability_key="column",
                )
            ]
            await _materialize_nodes(
                pane_render_spec=pane_render_spec,
                render_payload=render_payload,
                semantic_object_ids=semantic_object_ids,
            )
            await _materialize_renderer_requirements(
                pane_render_spec=pane_render_spec,
                render_payload=render_payload,
                semantic_object_ids=semantic_object_ids,
            )

        nodes_by_key = {node.node_key: node for node in pane_render_spec.nodes}
    assert nodes_by_key["root"].pane_render_spec_id == pane_render_spec.id
    assert nodes_by_key["root"].style_tokens[0].pane_render_node_id == (nodes_by_key["root"].id)
    assert nodes_by_key["root"].style_tokens[0].token_value == "compact"
    assert nodes_by_key["avatar_media"].component_ref == "aware.storage.media.image"
    requirements = {
        f"{requirement.capability_kind.value}:{requirement.capability_key}": requirement
        for requirement in pane_render_spec.renderer_requirements
    }
    assert requirements["node_kind:column"].pane_render_spec_id == pane_render_spec.id


@pytest.mark.asyncio
async def test_pane_render_spec_materialization_commits_multiple_render_specs_to_row_branches(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_interface_ontology  # noqa: F401

    from aware_interface.ontology.materialization import (
        load_pane_render_spec_runtime_states_from_materialization_artifact_oig,
        materialize_pane_render_specs_from_materialization_artifact,
    )

    materialization_path = tmp_path / "pane_render_specs.materialization.json"
    artifact = _write_multi_materialization_artifact(path=materialization_path)

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        index = cast(Any, context.index)
        environment_id = uuid4()
        process_id = uuid4()
        thread_id = uuid4()

        result = await materialize_pane_render_specs_from_materialization_artifact(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            materialization_path=materialization_path,
        )

        assert result.branch_id == UUID(cast(str, artifact["materialization_commit_id"]))
        assert len(result.pane_render_specs) == 2
        assert len(result.runtime_payloads) == 2
        row_branch_ids = {materialized.branch_id for materialized in result.pane_render_specs}
        assert len(row_branch_ids) == 2
        assert result.branch_id not in row_branch_ids
        assert all(
            materialized.last_commit_id is not None and materialized.object_instance_graph_commit_id is not None
            for materialized in result.pane_render_specs
        )
        assert sorted(payload.payload["name"] for payload in result.runtime_payloads) == [
            "identity_admission_default",
            "identity_audit_default",
        ]

        pane_kind_by_binding_id = {
            materialized.pane_render_spec.pane_config_id: (materialized.pane_render_spec.name.removesuffix("_default"))
            for materialized in result.pane_render_specs
        }
        states = await load_pane_render_spec_runtime_states_from_materialization_artifact_oig(
            index=index,
            materialization_path=materialization_path,
            pane_name_by_pane_config_id=(pane_kind_by_binding_id),
            pane_kind_by_pane_config_id=(pane_kind_by_binding_id),
        )
        assert len(states) == 2
        assert {state.branch_id for state in states} == row_branch_ids
        assert sorted(state.payload["name"] for state in states) == [
            "identity_admission_default",
            "identity_audit_default",
        ]

        rerun = await materialize_pane_render_specs_from_materialization_artifact(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            materialization_path=materialization_path,
        )
        assert len(rerun.pane_render_specs) == 2
        assert {materialized.branch_id for materialized in rerun.pane_render_specs} == row_branch_ids
