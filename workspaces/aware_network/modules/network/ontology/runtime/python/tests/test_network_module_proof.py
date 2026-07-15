from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_code.handlers._generated import meta_handlers as code_meta_handlers
from aware_meta.handlers._generated import meta_handlers as meta_meta_handlers
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    MetaOIGAssertions,
    ProofCall,
    SourceObjectId,
    run_meta_runtime_proof,
)
from aware_network.handlers._generated import meta_handlers as network_meta_handlers
from aware_environment.handlers._generated import (
    meta_handlers as environment_meta_handlers,
)
from aware_service_runtime.handlers._generated import (
    meta_handlers as service_meta_handlers,
)


ENVIRONMENT_CLASS_FQN = "aware_environment.environment.Environment"
NETWORK_NODE_CLASS_FQN = "aware_network.network.NetworkNode"
NETWORK_NODE_PEER_CLASS_FQN = "aware_network.network.NetworkNodePeer"
SERVICE_CLASS_FQN = "aware_service.service.Service"
SERVICE_CONFIG_CLASS_FQN = "aware_service.service.ServiceConfig"
SERVICE_PACKAGE_CLASS_FQN = "aware_service.service.ServicePackage"
_REPO_ROOT = Path(__file__).resolve().parents[8]


def _network_module_proof_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/economy/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/service/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/network/ontology/structure/aware.toml",
    )


def _build_network_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    package_manifest_paths = _network_module_proof_package_manifest_paths(repo_root)
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=package_manifest_paths,
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            code_meta_handlers,
            meta_meta_handlers,
            environment_meta_handlers,
            service_meta_handlers,
            network_meta_handlers,
        ),
        bootstrap_modules=(
            code_meta_handlers,
            meta_meta_handlers,
            environment_meta_handlers,
            service_meta_handlers,
            network_meta_handlers,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
        ),
    )
    assert runtime.context is not None
    return runtime


def _expect_uuid_primitive(
    assertions: MetaOIGAssertions,
    *,
    instance_id: UUID,
    field_name: str,
    expected: UUID,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


@pytest.mark.asyncio
async def test_network_node_and_peer_module_proof(tmp_path: Path) -> None:
    repo_root = _REPO_ROOT

    # Bootstrap ontologies required by the composed environment (cross-package refs).
    import aware_code_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    import aware_network_ontology  # noqa: F401
    import aware_environment_ontology  # noqa: F401
    import aware_service_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_network_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        assert runtime.context is not None

        # Commit-first invariant: when the composed environment includes the OS `environment` OPG,
        # we must initialize the boot lane before any domain commits can register into it.
        #
        # Production does this via `ensure_ready` at node boot. For module proofs, we perform the
        # OS genesis write explicitly by invoking `Environment.build`.
        from aware_history.stable_ids import stable_branch_id
        from aware_network_ontology.stable_ids import (
            stable_network_node_environment_id,
            stable_network_node_id,
            stable_network_node_peer_id,
            stable_network_node_service_id,
        )
        from aware_environment.stable_ids import (
            stable_boot_thread_id,
        )
        from aware_environment_ontology.stable_ids import stable_environment_id
        from aware_service_ontology.stable_ids import (
            stable_service_config_id,
            stable_service_id,
            stable_service_package_id,
        )

        environment_key = "tests.network.environment"
        env_id = stable_environment_id(key=environment_key)
        boot_thread_id = stable_boot_thread_id(environment_id=env_id)
        boot_branch_id = stable_branch_id(
            environment_id=env_id, thread_id=boot_thread_id
        )

        await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(
                actor_id=uuid4(),
                branch_id=boot_branch_id,
            ),
            opg_name="Environment",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ENVIRONMENT_CLASS_FQN,
                    function_name="build",
                    args=[],
                    kwargs={
                        "key": environment_key,
                        "title": "Network Test Environment",
                        "description": None,
                    },
                    expected_root_object_id=env_id,
                )
            ],
        )

        # Node A
        node_a_key_hex = "44" * 32
        node_a_public_key = f"ed25519:{node_a_key_hex}"
        expected_node_a_id = stable_network_node_id(public_key=node_a_public_key)
        node_a_system_actor_id = uuid4()

        lane_a = LaneIds(
            actor_id=node_a_system_actor_id,
            branch_id=expected_node_a_id,
        )
        _, node_a_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_a,
            opg_name="NetworkNode",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=NETWORK_NODE_CLASS_FQN,
                    function_name="register",
                    args=[node_a_public_key, "node-a.local", 8000],
                    kwargs={
                        "system_actor_id": str(node_a_system_actor_id),
                    },
                    expected_root_object_id=expected_node_a_id,
                ),
            ],
        )
        _expect_uuid_primitive(
            node_a_assertions,
            instance_id=expected_node_a_id,
            field_name="system_actor_id",
            expected=node_a_system_actor_id,
        )

        # Node B
        node_b_key_hex = "55" * 32
        node_b_public_key = f"ed25519:{node_b_key_hex}"
        expected_node_b_id = stable_network_node_id(public_key=node_b_public_key)

        lane_b = LaneIds(
            actor_id=uuid4(),
            branch_id=expected_node_b_id,
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_b,
            opg_name="NetworkNode",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=NETWORK_NODE_CLASS_FQN,
                    function_name="register",
                    args=[node_b_public_key, "node-b.local", 8001],
                    expected_root_object_id=expected_node_b_id,
                ),
            ],
        )

        # Node A environment association (commit-backed, portal reference)
        expected_node_env_id = stable_network_node_environment_id(
            network_node_id=expected_node_a_id,
            environment_id=env_id,
        )
        service_config_name = "interface_service_catalog"
        service_package_name = "aware-interface-service"
        service_name = "interface_service"
        expected_service_config_id = stable_service_config_id(name=service_config_name)
        expected_service_package_id = stable_service_package_id(
            name=service_package_name,
        )
        expected_service_id = stable_service_id(
            service_config_id=expected_service_config_id,
            name=service_name,
        )
        expected_node_service_id = stable_network_node_service_id(
            network_node_id=expected_node_a_id,
            service_package_id=expected_service_package_id,
        )

        lane_node_a = LaneIds(
            actor_id=uuid4(),
            branch_id=expected_node_a_id,
        )
        _, env_assoc_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_node_a,
            opg_name="NetworkNode",
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=NETWORK_NODE_CLASS_FQN,
                    function_name="upsert_environment",
                    kwargs={
                        "environment_id": str(env_id),
                        "role": "owner",
                        "is_active": True,
                        "priority": 10,
                    },
                    object_id=SourceObjectId(expected_node_a_id),
                    expected_root_object_id=expected_node_a_id,
                )
            ],
        )
        env_assoc_assertions.expect_instance(expected_node_env_id)
        _expect_uuid_primitive(
            env_assoc_assertions,
            instance_id=expected_node_env_id,
            field_name="environment_id",
            expected=env_id,
        )
        env_assoc_assertions.expect_primitive(
            instance_id=expected_node_env_id,
            field_name="role",
            expected="owner",
        )
        env_assoc_assertions.expect_primitive(
            instance_id=expected_node_env_id,
            field_name="is_active",
            expected=True,
        )
        env_assoc_assertions.expect_primitive(
            instance_id=expected_node_env_id,
            field_name="priority",
            expected=10,
        )
        env_assoc_assertions.expect_edge(
            source_id=expected_node_a_id,
            target_id=expected_node_env_id,
            relationship_name="environments",
        )

        lane_service_config = LaneIds(
            actor_id=uuid4(),
            branch_id=expected_service_config_id,
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_service_config,
            opg_name="ServiceConfig",
            root_class_fqn=SERVICE_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=SERVICE_CONFIG_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": service_config_name,
                        "description": "Interface host service catalog",
                    },
                    expected_root_object_id=expected_service_config_id,
                ),
            ],
        )

        lane_service_package = LaneIds(
            actor_id=uuid4(),
            branch_id=expected_service_package_id,
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_service_package,
            opg_name="ServicePackage",
            root_class_fqn=SERVICE_PACKAGE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=SERVICE_PACKAGE_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": service_package_name,
                        "service_config_id": str(expected_service_config_id),
                        "fqn_prefix": "aware_interface_service",
                        "title": "Interface Service",
                        "description": "Public interface host service package",
                        "manifest_relative_path": "services/interface/aware.service.toml",
                        "package_root": "services/interface",
                    },
                    expected_root_object_id=expected_service_package_id,
                ),
            ],
        )

        lane_service = LaneIds(
            actor_id=uuid4(),
            branch_id=expected_service_id,
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_service,
            opg_name="Service",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=SERVICE_CLASS_FQN,
                    function_name="build_via_service_config",
                    kwargs={
                        "service_config_id": str(expected_service_config_id),
                        "name": service_name,
                        "description": "Public interface host service",
                    },
                    expected_root_object_id=expected_service_id,
                ),
            ],
        )

        _, service_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_node_a,
            opg_name="NetworkNode",
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=NETWORK_NODE_CLASS_FQN,
                    function_name="attach_service",
                    kwargs={
                        "service_package_id": str(expected_service_package_id),
                        "service_id": str(expected_service_id),
                        "endpoint_refs": [
                            "interface.get_runtime_mount",
                            "interface.subscribe_runtime",
                        ],
                        "host_id": "interface-service-host",
                        "host_version": "1.0.0",
                        "protocol_version": "product-a-b",
                        "service_name": service_name,
                        "supports_stream_events": True,
                    },
                    object_id=SourceObjectId(expected_node_a_id),
                    expected_root_object_id=expected_node_a_id,
                )
            ],
        )
        service_assertions.expect_instance(expected_node_service_id)
        _expect_uuid_primitive(
            service_assertions,
            instance_id=expected_node_service_id,
            field_name="service_id",
            expected=expected_service_id,
        )
        _expect_uuid_primitive(
            service_assertions,
            instance_id=expected_node_service_id,
            field_name="service_package_id",
            expected=expected_service_package_id,
        )
        service_assertions.expect_primitive(
            instance_id=expected_node_service_id,
            field_name="endpoint_refs",
            expected=[
                "interface.get_runtime_mount",
                "interface.subscribe_runtime",
            ],
        )
        service_assertions.expect_primitive(
            instance_id=expected_node_service_id,
            field_name="stream_endpoint_refs",
            expected=[],
        )
        service_assertions.expect_primitive(
            instance_id=expected_node_service_id,
            field_name="host_id",
            expected="interface-service-host",
        )
        service_assertions.expect_primitive(
            instance_id=expected_node_service_id,
            field_name="host_version",
            expected="1.0.0",
        )
        service_assertions.expect_primitive(
            instance_id=expected_node_service_id,
            field_name="protocol_version",
            expected="product-a-b",
        )
        service_assertions.expect_primitive(
            instance_id=expected_node_service_id,
            field_name="service_name",
            expected=service_name,
        )
        service_assertions.expect_primitive(
            instance_id=expected_node_service_id,
            field_name="supports_stream_events",
            expected=True,
        )
        service_assertions.expect_edge(
            source_id=expected_node_a_id,
            target_id=expected_node_service_id,
            relationship_name="services",
        )

        # Node A -> Node B peer link (separate lane, similar to IdentityConnection)
        expected_peer_link_id = stable_network_node_peer_id(
            source_peer_node_id=expected_node_a_id,
            target_peer_node_id=expected_node_b_id,
        )

        lane_link = LaneIds(
            actor_id=uuid4(),
            branch_id=expected_peer_link_id,
        )
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_link,
            opg_name="NetworkNodePeer",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=NETWORK_NODE_PEER_CLASS_FQN,
                    function_name="create",
                    kwargs={
                        "network_node_id": str(expected_node_a_id),
                        "peer_node_id": str(expected_node_b_id),
                        "peer_http_base_url": "http://node-b.local:8001",
                    },
                    expected_root_object_id=expected_peer_link_id,
                ),
            ],
        )

        assertions.expect_root(expected_peer_link_id)
        assertions.expect_instance(expected_peer_link_id)

        # Connection-style contract: endpoints are stable ids referenced by FK fields.
        # The portal targets themselves live in separate `network_node` lanes.
        _expect_uuid_primitive(
            assertions,
            instance_id=expected_peer_link_id,
            field_name="source_peer_node_id",
            expected=expected_node_a_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=expected_peer_link_id,
            field_name="target_peer_node_id",
            expected=expected_node_b_id,
        )
        assertions.expect_primitive(
            instance_id=expected_peer_link_id,
            field_name="peer_http_base_url",
            expected="http://node-b.local:8001",
        )
        assertions.expect_primitive(
            instance_id=expected_peer_link_id,
            field_name="status",
            expected="accepted",
        )

        assert result.root_object_id == expected_peer_link_id

        # Node B -> Node A peer request (pending)
        expected_peer_request_id = stable_network_node_peer_id(
            source_peer_node_id=expected_node_b_id,
            target_peer_node_id=expected_node_a_id,
        )
        lane_request = LaneIds(
            actor_id=uuid4(),
            branch_id=expected_peer_request_id,
        )

        _, request_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane_request,
            opg_name="NetworkNodePeer",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=NETWORK_NODE_PEER_CLASS_FQN,
                    function_name="request",
                    kwargs={
                        "network_node_id": str(expected_node_b_id),
                        "peer_node_id": str(expected_node_a_id),
                        "peer_http_base_url": "http://node-a.local:8000",
                    },
                    expected_root_object_id=expected_peer_request_id,
                ),
            ],
        )
        request_assertions.expect_root(expected_peer_request_id)
        request_assertions.expect_instance(expected_peer_request_id)
        request_assertions.expect_primitive(
            instance_id=expected_peer_request_id,
            field_name="status",
            expected="pending",
        )
