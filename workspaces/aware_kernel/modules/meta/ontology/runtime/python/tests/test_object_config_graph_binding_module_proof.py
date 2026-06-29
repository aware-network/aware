from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.projection.branching import stable_portal_target_branch_id
from aware_meta.handlers._generated import meta_handlers
from aware_meta.handlers.impl.config import (
    object_config_graph_binding as object_config_graph_binding_handler,
)
from aware_meta.runtime import build_meta_graph_runtime_for_aware_package_manifests
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor.execution_context import (
    MetaGraphHandlerContext,
)
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.portal_invocation import (
    MetaPortalConstructorAuthorization,
    MetaPortalConstructorInvocationRequest,
    invoke_meta_portal_constructor,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    MultiLaneProofCall,
    ProofCall,
    ROOT_OBJECT_ID,
    SourceObjectId,
    run_multi_lane_meta_runtime_proof,
)
from _meta_runtime_test_paths import META_PACKAGE_MANIFEST_PATHS, REPO_ROOT


OBJECT_CONFIG_GRAPH_FQN = "aware_meta.graph.config.ObjectConfigGraph"
OBJECT_CONFIG_GRAPH_NODE_FQN = "aware_meta.graph.config.ObjectConfigGraphNode"
OBJECT_CONFIG_GRAPH_BINDING_FQN = "aware_meta.graph.config.ObjectConfigGraphBinding"


def _class_instance_id_for_source(*, assertions, source_object_id: UUID) -> UUID:
    for class_instance in assertions.oig.class_instances:
        if (
            class_instance.source_object_id == source_object_id
            and class_instance.id is not None
        ):
            return UUID(str(class_instance.id))
    raise AssertionError(
        f"Missing ClassInstance for source_object_id={source_object_id}"
    )


def _meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return META_PACKAGE_MANIFEST_PATHS


def _build_meta_runtime(*, repo_root: Path, aware_root: Path):
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(meta_handlers,),
        bootstrap_modules=(meta_handlers,),
    )
    assert runtime.context is not None
    return runtime


@pytest.mark.asyncio
async def test_object_config_graph_binding_module_proof(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = REPO_ROOT

    import aware_code_ontology  # noqa: F401
    import aware_content_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    import aware_storage_ontology  # noqa: F401
    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology.graph.config.object_config_graph_binding import (
        ObjectConfigGraphBinding,
    )

    from aware_meta_ontology.stable_ids import (
        stable_class_config_id,
        stable_object_config_graph_binding_class_id,
        stable_object_config_graph_binding_id,
        stable_object_config_graph_id,
        stable_object_instance_graph_branch_id,
        stable_object_instance_graph_id,
        stable_object_instance_graph_identity_id,
        stable_object_config_graph_node_id,
    )

    source_class_fqn = "aware.meta.test.runtime.default.default.TestEntity"
    target_graph_name = "meta_test_target_ocg_runtime"
    target_graph_hash = "meta_test_target_ocg_runtime_hash"
    target_graph_fqn_prefix = "aware.meta.test.target.runtime"
    target_graph_language = "aware"

    source_ocg_id = stable_object_config_graph_id(
        fqn_prefix="aware.meta.test.runtime",
        language="aware",
    )
    source_class_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=source_ocg_id,
        type="class",
        node_key=source_class_fqn,
    )
    source_class_id = stable_class_config_id(
        object_config_graph_node_id=source_class_node_id,
        class_fqn=source_class_fqn,
    )

    lane = LaneIds(
        environment_id=uuid5(NAMESPACE_URL, "aware://tests/meta/ocg_binding/env"),
        process_id=uuid5(NAMESPACE_URL, "aware://tests/meta/ocg_binding/process"),
        thread_id=uuid5(NAMESPACE_URL, "aware://tests/meta/ocg_binding/thread"),
    )

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        runtime = _build_meta_runtime(
            repo_root=repo_root,
            aware_root=tmp_path / "aware_root",
        )
        idx = runtime.context.index
        opg_names = {(opg.name or "").strip() for opg in idx.opg_by_hash.values()}
        assert "ObjectConfigGraph" in opg_names
        assert "ObjectConfigGraphBinding" in opg_names

        target_ocg_id = stable_object_config_graph_id(
            fqn_prefix=target_graph_fqn_prefix,
            language=target_graph_language,
        )
        target_graph = ObjectConfigGraph(
            id=target_ocg_id,
            name=target_graph_name,
            hash=target_graph_hash,
            fqn_prefix=target_graph_fqn_prefix,
            language=CodeLanguage.aware,
            object_config_graph_identity=None,
            object_config_graph_identity_id=None,
            description="Meta OCG target graph for binding portal proof",
            layout_hash=None,
        )
        target_graph_class_config = ObjectConfigGraph.get_class_config()
        assert target_graph_class_config is not None
        target_class_id = UUID(str(target_graph_class_config.id))
        target_class_attr = next(
            edge
            for edge in target_graph_class_config.class_config_attribute_configs
            if edge.attribute_config is not None
            and edge.attribute_config.name == "fqn_prefix"
        )
        target_class_attr_id = UUID(str(target_class_attr.id))
        binding_id = stable_object_config_graph_binding_id(
            object_config_graph_id=source_ocg_id,
            target_object_config_graph_id=target_ocg_id,
        )
        binding_class_id = stable_object_config_graph_binding_class_id(
            object_config_graph_binding_id=binding_id,
            source_class_id=source_class_id,
            target_class_id=target_class_id,
            target_attribute_id=target_class_attr_id,
        )

        original_current_handler_session = meta_handlers.current_handler_session

        def _binding_handler_session():
            session = original_current_handler_session()
            if session.imap_get(ObjectConfigGraph, target_ocg_id) is None:
                session.merge(target_graph)
            if (
                idx.ocg is not None
                and session.imap_get(ObjectConfigGraph, UUID(str(idx.ocg.id))) is None
            ):
                session.merge(idx.ocg)
            return session

        monkeypatch.setattr(
            meta_handlers,
            "current_handler_session",
            _binding_handler_session,
        )
        monkeypatch.setattr(
            object_config_graph_binding_handler,
            "current_handler_session",
            _binding_handler_session,
        )

        results, assertions_by_opg = await run_multi_lane_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            calls=[
                MultiLaneProofCall(
                    opg_name="ObjectConfigGraph",
                    call=ProofCall(
                        target="constructor",
                        class_fqn=OBJECT_CONFIG_GRAPH_FQN,
                        function_name="build",
                        kwargs={
                            "name": "meta_test_ocg_runtime",
                            "hash": "meta_test_ocg_runtime_hash",
                            "fqn_prefix": "aware.meta.test.runtime",
                            "language": "aware",
                            "object_config_graph_id": source_ocg_id,
                            "object_config_graph_identity_id": None,
                            "description": "Meta OCG source graph for binding proof",
                            "layout_hash": None,
                        },
                        expected_root_object_id=source_ocg_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ObjectConfigGraph",
                    call=ProofCall(
                        target="instance",
                        class_fqn=OBJECT_CONFIG_GRAPH_FQN,
                        function_name="create_node",
                        object_id=ROOT_OBJECT_ID,
                        kwargs={
                            "type": "class",
                            "node_key": source_class_fqn,
                        },
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ObjectConfigGraph",
                    call=ProofCall(
                        target="instance",
                        class_fqn=OBJECT_CONFIG_GRAPH_NODE_FQN,
                        function_name="create_class",
                        object_id=SourceObjectId(source_class_node_id),
                        kwargs={
                            "class_fqn": source_class_fqn,
                            "name": "TestEntity",
                            "is_base": True,
                            "is_edge": False,
                            "description": "Meta OCG source class",
                            "value_mode": "graph_ref",
                        },
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ObjectConfigGraphBinding",
                    call=ProofCall(
                        target="constructor",
                        class_fqn=OBJECT_CONFIG_GRAPH_BINDING_FQN,
                        function_name="build_via_object_config_graph",
                        kwargs={
                            "object_config_graph_id": source_ocg_id,
                            "target_object_config_graph_id": target_ocg_id,
                        },
                        expected_root_object_id=binding_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ObjectConfigGraphBinding",
                    call=ProofCall(
                        target="instance",
                        class_fqn=OBJECT_CONFIG_GRAPH_BINDING_FQN,
                        function_name="create_class",
                        object_id=ROOT_OBJECT_ID,
                        kwargs={
                            "name": "test_entity_to_target_fqn_prefix",
                            "source_class_id": source_class_id,
                            "target_class_id": target_class_id,
                            "target_attribute_id": target_class_attr_id,
                            "source_attr_id": None,
                        },
                    ),
                ),
            ],
        )

        source_result = results["ObjectConfigGraph"]
        source_assertions = assertions_by_opg["ObjectConfigGraph"]
        binding_result = results["ObjectConfigGraphBinding"]
        binding_assertions = assertions_by_opg["ObjectConfigGraphBinding"]

        assert UUID(str(source_result.root_object_id)) == source_ocg_id
        assert UUID(str(binding_result.root_object_id)) == binding_id
        assert source_result.branch_id == binding_result.branch_id

        source_source_ids = {
            UUID(str(class_instance.source_object_id))
            for class_instance in source_result.oig.class_instances
            if class_instance.source_object_id is not None
        }
        assert binding_id not in source_source_ids
        assert binding_class_id not in source_source_ids

        binding_root_ci_id = _class_instance_id_for_source(
            assertions=binding_assertions,
            source_object_id=binding_id,
        )
        binding_class_ci_id = _class_instance_id_for_source(
            assertions=binding_assertions,
            source_object_id=binding_class_id,
        )
        binding_assertions.expect_root(binding_root_ci_id)
        binding_assertions.expect_instance(binding_root_ci_id)
        binding_assertions.expect_instance(binding_class_ci_id)
        binding_assertions.expect_edge(
            source_id=binding_root_ci_id, target_id=binding_class_ci_id
        )
        assert (
            UUID(
                str(
                    binding_assertions.primitive(
                        instance_id=binding_root_ci_id,
                        field_name="object_config_graph_id",
                    )
                )
            )
            == source_ocg_id
        )
        assert (
            UUID(
                str(
                    binding_assertions.primitive(
                        instance_id=binding_root_ci_id,
                        field_name="target_object_config_graph_id",
                    )
                )
            )
            == target_ocg_id
        )
        source_root_ci_id = _class_instance_id_for_source(
            assertions=source_assertions,
            source_object_id=source_ocg_id,
        )
        source_assertions.expect_root(source_root_ci_id)
        source_assertions.expect_instance(source_root_ci_id)

        source_opg = idx.opg_by_hash[source_result.projection_hash]
        binding_opg = idx.opg_by_hash[binding_result.projection_hash]
        binding_portals = (
            idx.portal_index.portals_by_source_projection_hash.get(
                binding_result.projection_hash
            )
            or []
        )
        binding_portal = next(
            (
                portal
                for portal in binding_portals
                if portal.reference_field_name == "target_object_config_graph"
                and portal.target_projection_hash == source_result.projection_hash
            ),
            None,
        )
        assert binding_portal is not None

        binding_head = binding_result.head
        binding_oig_id = UUID(str(binding_head["object_instance_graph_id"]))
        _binding_ocgi, binding_opgi = resolve_meta_graph_ocgi_opgi(
            index=idx, projection_hash=binding_result.projection_hash
        )
        assert binding_opgi is not None
        binding_oigi_id = stable_object_instance_graph_identity_id(
            object_projection_graph_identity_id=binding_opgi.id,
            object_instance_graph_id=binding_oig_id,
        )
        binding_oigb_id = stable_object_instance_graph_branch_id(
            object_instance_graph_identity_id=binding_oigi_id,
            branch_id=binding_result.branch_id,
        )

        binding_session = reify_oig_session(
            index=idx,
            opg=binding_opg,
            oig=binding_result.oig,
            branch_id=binding_result.branch_id,
        )
        binding_root = binding_session.imap_get(ObjectConfigGraphBinding, binding_id)
        assert binding_root is not None

        target_opg_identity = resolve_meta_graph_ocgi_opgi(
            index=idx, projection_hash=source_result.projection_hash
        )[1]
        assert target_opg_identity is not None
        expected_target_branch_id = stable_portal_target_branch_id(
            object_instance_graph_id=binding_oig_id,
            object_projection_graph_identity_id=target_opg_identity.id,
            target_object_id=target_ocg_id,
        )

        actor_id = uuid5(NAMESPACE_URL, "aware://tests/meta/ocg_binding/actor")

        portal_ctor = await invoke_meta_portal_constructor(
            MetaPortalConstructorInvocationRequest(
                ctx=MetaGraphHandlerContext(
                    requester_id=actor_id,
                    environment_id=lane.environment_id,
                    process_id=lane.process_id,
                    thread_id=lane.thread_id,
                    domain_oigb_id=binding_oigb_id,
                    domain_object_instance_graph_id=binding_oig_id,
                    domain_object_instance_graph_identity_id=binding_oigi_id,
                    branch_id=binding_result.branch_id,
                    projection_hash=binding_result.projection_hash,
                    portal_index=idx.portal_index,
                ),
                index=idx,
                invoke_function=runtime.invoke_function,
                target_projection_hash=source_result.projection_hash,
                target_object_projection_graph_id=source_opg.id,
                target_class_config_id=target_graph_class_config.id,
                function_name="build",
                payload={
                    "name": target_graph_name,
                    "hash": target_graph_hash,
                    "fqn_prefix": target_graph_fqn_prefix,
                    "language": target_graph_language,
                    "object_config_graph_id": target_ocg_id,
                    "object_config_graph_identity_id": None,
                    "description": "Meta OCG target graph for binding portal proof",
                    "layout_hash": None,
                },
                target_branch_id=None,
                target_object_id=target_ocg_id,
                authorization=MetaPortalConstructorAuthorization(
                    source_class_config_id=ObjectConfigGraphBinding.get_class_config().id,  # type: ignore[union-attr]
                    source_instance_id=binding_root_ci_id,
                    source_object_id=binding_id,
                    source_branch_id=binding_result.branch_id,
                    source_projection_hash=binding_result.projection_hash,
                    class_config_relationship_id=binding_portal.class_config_relationship_id,
                    allowed_target_object_ids=frozenset({target_ocg_id}),
                ),
                commit=True,
            )
        )

        assert portal_ctor.status == "succeeded"
        assert portal_ctor.error is None
        assert portal_ctor.root_object_id == target_ocg_id
        assert isinstance(portal_ctor.branch_id, UUID)
        target_branch_id = portal_ctor.branch_id
        assert target_branch_id == expected_target_branch_id
        assert target_branch_id != source_result.branch_id
        assert target_branch_id != binding_result.branch_id

        store = FSCommitStore()
        target_head = await store.head(
            branch_id=target_branch_id,
            projection_hash=source_result.projection_hash,
        )
        assert (
            target_head
            and target_head.get("commit_id")
            and target_head.get("object_instance_graph_id")
        ), target_head

        expected_target_oig_id = stable_object_instance_graph_id(
            object_projection_graph_id=source_opg.id,
            key=str(target_branch_id),
        )
        target_oig_id = UUID(str(target_head["object_instance_graph_id"]))
        assert target_oig_id == expected_target_oig_id

        target_oig, _ = await OIGMaterializer().get(
            branch_id=target_branch_id,
            ocg=idx.ocg,
            opg=source_opg,
            commit_id=UUID(str(target_head["commit_id"])),
            oig_id=target_oig_id,
            attribute_configs_by_id=idx.attribute_configs_by_id,
            class_configs_by_id=idx.class_configs_by_id,
        )
        target_root_ci_id = None
        for class_instance in target_oig.class_instances:
            if class_instance.source_object_id == target_ocg_id:
                target_root_ci_id = class_instance.id
                break
        assert target_root_ci_id is not None
        assert target_oig.root_class_instance_id == target_root_ci_id
