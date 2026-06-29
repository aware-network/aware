from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_meta.handlers._generated import meta_handlers
from aware_meta.runtime import (
    build_meta_graph_runtime_for_aware_package_manifests,
    graph_identity_generated_handlers,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    MultiLaneProofCall,
    LaneIds,
    ProofCall,
    ROOT_OBJECT_ID,
    run_multi_lane_meta_runtime_proof,
)
import pytest
from aware_meta_ontology.stable_ids import (
    stable_function_call_id,
    stable_function_call_response_id,
    stable_object_config_graph_identity_id,
)
from _meta_runtime_test_paths import META_PACKAGE_MANIFEST_PATHS, REPO_ROOT


OCGI_FQN = "aware_meta.graph.config." "ObjectConfigGraphIdentity"
OPGI_FQN = "aware_meta.graph.projection." "ObjectProjectionGraphIdentity"
FUNCTION_CALL_FQN = "aware_meta.default.function.FunctionCall"


def _meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return META_PACKAGE_MANIFEST_PATHS


def _build_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
    handler_modules: tuple[object, ...] = (meta_handlers,),
):
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=handler_modules,
        bootstrap_modules=handler_modules,
    )
    assert runtime.context is not None
    return runtime


def _function_config_id(
    *,
    idx,
    class_fqn: str,
    function_name: str,
) -> UUID:
    return next(
        edge.function_config.id
        for class_config in idx.class_configs_by_id.values()
        if class_config.class_fqn == class_fqn
        for edge in class_config.class_config_function_configs
        if edge.function_config.name == function_name
    )


def _class_instance_id_for_source(*, assertions, source_object_id: UUID) -> UUID:
    for class_instance in assertions.oig.class_instances:
        if class_instance.source_object_id == source_object_id:
            return class_instance.id
    raise AssertionError(
        f"Missing ClassInstance for source_object_id={source_object_id}"
    )


@pytest.mark.asyncio
async def test_meta_module_proof_projection_identity_observable(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    from aware_meta_ontology.stable_ids import (
        stable_object_projection_graph_identity_id,
        stable_object_projection_graph_observable_id,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
            handler_modules=(graph_identity_generated_handlers,),
        )
        idx = runtime.context.index
        identity_opg = next(
            opg
            for opg in idx.opg_by_hash.values()
            if (opg.name or "").strip() == "ObjectProjectionGraphIdentity"
        )

        ocgi_key = "kernel:identity"
        ocgi_id = stable_object_config_graph_identity_id(key=ocgi_key)
        opgi_id = stable_object_projection_graph_identity_id(
            object_config_graph_identity_id=ocgi_id,
            object_projection_graph_id=identity_opg.id,
        )
        lane = LaneIds(
            environment_id=uuid5(NAMESPACE_URL, "meta://tests/projection_identity/env"),
            process_id=uuid5(NAMESPACE_URL, "meta://tests/projection_identity/process"),
            thread_id=uuid5(NAMESPACE_URL, "meta://tests/projection_identity/thread"),
        )
        expected_observable_key = "onboarding.welcome"
        expected_observable_id = stable_object_projection_graph_observable_id(
            object_projection_graph_identity_id=opgi_id,
            observable_key=expected_observable_key,
        )

        results, assertions_by_opg = await run_multi_lane_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            calls=[
                MultiLaneProofCall(
                    opg_name="ObjectConfigGraphIdentity",
                    call=ProofCall(
                        target="constructor",
                        class_fqn=OCGI_FQN,
                        function_name="create",
                        args=[ocgi_key, "identity"],
                        expected_root_object_id=ocgi_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ObjectProjectionGraphIdentity",
                    call=ProofCall(
                        target="constructor",
                        class_fqn=OPGI_FQN,
                        function_name="create_via_object_config_graph_identity",
                        kwargs={
                            "object_config_graph_identity_id": ocgi_id,
                            "object_projection_graph_id": identity_opg.id,
                            "projection_name": identity_opg.name,
                            "label": "identity",
                        },
                        expected_root_object_id=opgi_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ObjectProjectionGraphIdentity",
                    call=ProofCall(
                        target="instance",
                        class_fqn=OPGI_FQN,
                        function_name="create_observable",
                        object_id=ROOT_OBJECT_ID,
                        kwargs={
                            "observable_key": expected_observable_key,
                            "key": f"{identity_opg.name}:{expected_observable_key}",
                            "kind": "construct",
                            "label": "Welcome",
                            "description": "Onboarding welcome step",
                            "position": 1,
                            "is_default": True,
                        },
                    ),
                ),
            ],
        )

        ocgi_result = results["ObjectConfigGraphIdentity"]
        ocgi_assertions = assertions_by_opg["ObjectConfigGraphIdentity"]
        opgi_result = results["ObjectProjectionGraphIdentity"]
        opgi_assertions = assertions_by_opg["ObjectProjectionGraphIdentity"]
        assert UUID(str(ocgi_result.root_object_id)) == ocgi_id
        assert UUID(str(opgi_result.root_object_id)) == opgi_id
        ocgi_root_ci_id = _class_instance_id_for_source(
            assertions=ocgi_assertions,
            source_object_id=ocgi_id,
        )
        opgi_root_ci_id = _class_instance_id_for_source(
            assertions=opgi_assertions,
            source_object_id=opgi_id,
        )
        observable_ci_id = _class_instance_id_for_source(
            assertions=opgi_assertions,
            source_object_id=expected_observable_id,
        )

        ocgi_assertions.expect_root(ocgi_root_ci_id)
        ocgi_assertions.expect_instance(ocgi_root_ci_id)
        assert ocgi_assertions.oig.root_class_instance.source_object_id == ocgi_id

        opgi_assertions.expect_root(opgi_root_ci_id)
        opgi_assertions.expect_instance(opgi_root_ci_id)
        opgi_assertions.expect_instance(observable_ci_id)
        assert opgi_assertions.oig.root_class_instance.source_object_id == opgi_id
        opgi_assertions.expect_edge(
            source_id=opgi_root_ci_id, target_id=observable_ci_id
        )
        opgi_assertions.expect_primitive(
            instance_id=observable_ci_id,
            field_name="observable_key",
            expected=expected_observable_key,
        )
        opgi_assertions.expect_primitive(
            instance_id=observable_ci_id,
            field_name="kind",
            expected="construct",
        )
        opgi_assertions.expect_primitive(
            instance_id=observable_ci_id,
            field_name="key",
            expected=f"{identity_opg.name}:{expected_observable_key}",
        )
        opgi_assertions.expect_primitive(
            instance_id=observable_ci_id, field_name="label", expected="Welcome"
        )
        opgi_assertions.expect_primitive(
            instance_id=observable_ci_id,
            field_name="description",
            expected="Onboarding welcome step",
        )
        opgi_assertions.expect_primitive(
            instance_id=observable_ci_id, field_name="position", expected=1
        )
        opgi_assertions.expect_primitive(
            instance_id=observable_ci_id, field_name="is_default", expected=True
        )


@pytest.mark.asyncio
async def test_meta_module_proof_function_call_projection(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        idx = runtime.context.index
        function_call_opg = next(
            opg
            for opg in idx.opg_by_hash.values()
            if (opg.name or "").strip() == "FunctionCall"
        )
        object_instance_graph_identity_opg = next(
            opg
            for opg in idx.opg_by_hash.values()
            if (opg.name or "").strip() == "ObjectInstanceGraphIdentity"
        )
        class_name_by_id = {
            class_config_id: cc.name
            for class_config_id, cc in idx.class_configs_by_id.items()
        }
        response_commit_portal = next(
            (
                portal
                for portal in function_call_opg.object_projection_graph_relationships
                if portal.target_object_projection_graph_id
                == object_instance_graph_identity_opg.id
                and (
                    idx.relationships_by_id.get(portal.class_config_relationship_id)
                    or portal.class_config_relationship
                ).relationship_key
                == "object_instance_graph_commit"
            ),
            None,
        )
        assert response_commit_portal is not None
        response_commit_relationship = (
            idx.relationships_by_id.get(
                response_commit_portal.class_config_relationship_id
            )
            or response_commit_portal.class_config_relationship
        )
        assert response_commit_relationship is not None
        assert (
            class_name_by_id[response_commit_relationship.class_config_id]
            == "FunctionCallResponseCommit"
        )
        assert (
            class_name_by_id[response_commit_relationship.target_class_config_id]
            == "ObjectInstanceGraphCommit"
        )
        assert (
            idx.portal_index.foreign_key_field_name_by_relationship_id[
                response_commit_relationship.id
            ]
            == "object_instance_graph_commit_id"
        )

        object_instance_graph_lane_id = uuid5(
            NAMESPACE_URL,
            "meta://tests/function_call_projection/oig_lane",
        )
        function_config_id = _function_config_id(
            idx=idx,
            class_fqn=FUNCTION_CALL_FQN,
            function_name="create_response",
        )
        call_key = uuid5(NAMESPACE_URL, "meta://tests/function_call_projection/call")
        function_call_id = stable_function_call_id(
            object_instance_graph_lane_id=object_instance_graph_lane_id,
            function_config_id=function_config_id,
            call_key=call_key,
        )
        response_id = stable_function_call_response_id(
            function_call_id=function_call_id,
        )
        assert function_call_id
        assert response_id
