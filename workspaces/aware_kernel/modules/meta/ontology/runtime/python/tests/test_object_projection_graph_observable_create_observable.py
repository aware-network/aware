from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from aware_code.types import JsonObject
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    build_meta_graph_runtime_for_aware_package_manifests,
    graph_identity_generated_handlers,
)
from aware_meta.runtime.author import META_SYSTEM_ACTOR_ID
from aware_meta.runtime.graph_runtime import MetaGraphRuntime
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphInvokeFunctionInput,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    MultiLaneProofCall,
    ProofCall,
    ROOT_OBJECT_ID,
    run_multi_lane_meta_runtime_proof,
)
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_identity_id,
    stable_object_projection_graph_identity_id,
    stable_object_projection_graph_observable_id,
)
from _meta_runtime_test_paths import META_PACKAGE_MANIFEST_PATHS, REPO_ROOT


OCGI_FQN = "aware_meta.graph.config.ObjectConfigGraphIdentity"
OPGI_FQN = "aware_meta.graph.projection.ObjectProjectionGraphIdentity"


def _meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return META_PACKAGE_MANIFEST_PATHS


def _build_meta_runtime(*, repo_root: Path, aware_root: Path) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(graph_identity_generated_handlers,),
        bootstrap_modules=(graph_identity_generated_handlers,),
    )
    assert runtime.context is not None
    return runtime


def _function_config_id(
    *,
    idx: MetaGraphRuntimeIndex,
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


def _class_instance_id_for_source(
    *, oig, source_object_id: UUID
) -> UUID:  # noqa: ANN001
    for class_instance in oig.class_instances:
        if class_instance.source_object_id == source_object_id:
            assert class_instance.id is not None
            return UUID(str(class_instance.id))
    raise AssertionError(
        f"Missing ClassInstance for source_object_id={source_object_id}"
    )


async def _ensure_projection_identity_root(
    *,
    runtime: MetaGraphRuntime,
    lane: LaneIds,
    ocgi_id: UUID,
    ocgi_key: str,
    opgi_projection_id: UUID,
    opgi_projection_name: str,
) -> tuple[UUID, UUID, UUID]:
    identity_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=ocgi_id,
        object_projection_graph_id=opgi_projection_id,
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
                        "object_projection_graph_id": opgi_projection_id,
                        "projection_name": opgi_projection_name,
                        "label": "identity",
                    },
                    expected_root_object_id=identity_id,
                ),
            ),
        ],
    )
    result = results["ObjectProjectionGraphIdentity"]
    assertions = assertions_by_opg["ObjectProjectionGraphIdentity"]
    root_ci_id = _class_instance_id_for_source(
        oig=assertions.oig,
        source_object_id=identity_id,
    )
    return result.branch_id, root_ci_id, identity_id


async def _invoke_create_observable(
    *,
    runtime: MetaGraphRuntime,
    lane: LaneIds,
    branch_id: UUID,
    projection_hash: str,
    identity_root_ci_id: UUID,
    kwargs: dict[str, object],
):
    idx = runtime.context.index
    return await runtime.invoke_function(
        MetaGraphInvokeFunctionInput(
            index=idx,
            actor_id=META_SYSTEM_ACTOR_ID,
            function_id=_function_config_id(
                idx=idx,
                class_fqn=OPGI_FQN,
                function_name="create_observable",
            ),
            domain_branch_id=branch_id,
            domain_projection_hash=projection_hash,
            call_target=MetaGraphCallTarget.instance,
            target_object_id=identity_root_ci_id,
            kwargs=JsonObject(kwargs),
            commit=True,
        )
    )


@pytest.mark.asyncio
async def test_create_observable_is_deterministic_and_computes_key(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    lane = LaneIds(
        branch_id=uuid5(NAMESPACE_URL, "aware://tests/meta/branch"),
    )
    ocgi_key = "kernel:identity"
    ocgi_id = stable_object_config_graph_identity_id(key=ocgi_key)

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        idx = runtime.context.index
        identity_opg = next(
            opg
            for opg in idx.opg_by_hash.values()
            if opg.name == "ObjectProjectionGraphIdentity"
        )
        identity_id = stable_object_projection_graph_identity_id(
            object_config_graph_identity_id=ocgi_id,
            object_projection_graph_id=identity_opg.id,
        )
        expected_observable_key = "onboarding.welcome"
        expected_observable_id = stable_object_projection_graph_observable_id(
            object_projection_graph_identity_id=identity_id,
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
                        expected_root_object_id=identity_id,
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

        opgi_result = results["ObjectProjectionGraphIdentity"]
        assertions = assertions_by_opg["ObjectProjectionGraphIdentity"]
        assert UUID(str(opgi_result.root_object_id)) == identity_id
        opgi_root_ci_id = _class_instance_id_for_source(
            oig=assertions.oig,
            source_object_id=identity_id,
        )
        observable_ci_id = _class_instance_id_for_source(
            oig=assertions.oig,
            source_object_id=expected_observable_id,
        )

        assertions.expect_root(opgi_root_ci_id)
        assertions.expect_instance(opgi_root_ci_id)
        assertions.expect_instance(observable_ci_id)
        assert assertions.oig.root_class_instance.source_object_id == identity_id
        assertions.expect_edge(source_id=opgi_root_ci_id, target_id=observable_ci_id)
        assertions.expect_primitive(
            instance_id=observable_ci_id,
            field_name="observable_key",
            expected=expected_observable_key,
        )
        assertions.expect_primitive(
            instance_id=observable_ci_id,
            field_name="kind",
            expected="construct",
        )
        assertions.expect_primitive(
            instance_id=observable_ci_id,
            field_name="key",
            expected=f"{identity_opg.name}:{expected_observable_key}",
        )
        assertions.expect_primitive(
            instance_id=observable_ci_id,
            field_name="label",
            expected="Welcome",
        )
        assertions.expect_primitive(
            instance_id=observable_ci_id,
            field_name="description",
            expected="Onboarding welcome step",
        )
        assertions.expect_primitive(
            instance_id=observable_ci_id,
            field_name="position",
            expected=1,
        )
        assertions.expect_primitive(
            instance_id=observable_ci_id,
            field_name="is_default",
            expected=True,
        )


@pytest.mark.asyncio
async def test_create_observable_rejects_blank_observable_key(
    tmp_path: Path,
) -> None:
    from aware_meta.handlers.impl.projection.object_projection_graph_observable import (
        create_via_object_projection_graph_identity,
    )

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        with pytest.raises(ValueError, match="requires observable_key"):
            await create_via_object_projection_graph_identity(
                object_projection_graph_identity_id=uuid4(),
                observable_key="  ",
                key="ObjectProjectionGraphIdentity:blank",
            )


@pytest.mark.asyncio
async def test_create_observable_is_idempotent_and_does_not_duplicate(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    lane = LaneIds(
        branch_id=uuid5(
            NAMESPACE_URL, "aware://tests/meta/branch/idempotent-observable"
        ),
    )
    ocgi_key = "kernel:identity"
    ocgi_id = stable_object_config_graph_identity_id(key=ocgi_key)
    observable_key = "onboarding.welcome"

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        idx = runtime.context.index
        opg = next(
            opg
            for opg in idx.opg_by_hash.values()
            if opg.name == "ObjectProjectionGraphIdentity"
        )
        branch_id, identity_root_ci_id, identity_id = (
            await _ensure_projection_identity_root(
                runtime=runtime,
                lane=lane,
                ocgi_id=ocgi_id,
                ocgi_key=ocgi_key,
                opgi_projection_id=opg.id,
                opgi_projection_name=opg.name,
            )
        )
        expected_observable_id = stable_object_projection_graph_observable_id(
            object_projection_graph_identity_id=identity_id,
            observable_key=observable_key,
        )
        observable_kwargs = {
            "observable_key": observable_key,
            "key": f"{opg.name}:{observable_key}",
            "kind": "construct",
            "label": "Welcome",
            "description": None,
            "position": 1,
            "is_default": True,
        }
        res1 = await _invoke_create_observable(
            runtime=runtime,
            lane=lane,
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            identity_root_ci_id=identity_root_ci_id,
            kwargs=observable_kwargs,
        )
        assert res1.status == "succeeded", res1.error
        assert res1.commit_id is not None

        res2 = await _invoke_create_observable(
            runtime=runtime,
            lane=lane,
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            identity_root_ci_id=identity_root_ci_id,
            kwargs=observable_kwargs,
        )
        assert res2.status == "succeeded", res2.error

        head = await FSCommitStore().head(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
        )
        assert head and head.get("commit_id") == str(res1.commit_id)
        oig, _ = await OIGMaterializer().get(
            branch_id=branch_id,
            ocg=idx.ocg,
            opg=opg,
            commit_id=UUID(str(head["commit_id"])),
            oig_id=UUID(str(head["object_instance_graph_id"])),
            attribute_configs_by_id=idx.attribute_configs_by_id,
            class_configs_by_id=idx.class_configs_by_id,
        )

        observable_ci_id = _class_instance_id_for_source(
            oig=oig,
            source_object_id=expected_observable_id,
        )
        view_instances = [ci for ci in oig.class_instances if ci.id == observable_ci_id]
        assert len(view_instances) == 1

        rel_edges = [
            rel
            for rel in oig.class_instance_relationships
            if rel.source_class_instance_id == identity_root_ci_id
            and rel.target_class_instance_id == observable_ci_id
        ]
        assert len(rel_edges) == 1
