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
    ProofCall,
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
NETWORK_NODE_CONFIG_CLASS_FQN = "aware_network.network.NetworkNodeConfig"
NETWORK_NODE_PACKAGE_CLASS_FQN = "aware_network.network.NetworkNodePackage"
_REPO_ROOT = Path(__file__).resolve().parents[8]


def _network_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
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
    package_manifest_paths = _network_package_manifest_paths(repo_root)
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


def _response_value(payload: object) -> dict[str, object]:
    assert isinstance(payload, dict)
    value = payload.get("value", payload)
    assert isinstance(value, dict)
    return value


async def _bootstrap_environment_lane(
    *,
    runtime: MetaGraphRuntime,
    environment_id: UUID,
    environment_key: str,
) -> tuple[UUID, UUID]:
    from aware_history.stable_ids import stable_branch_id  # noqa: WPS433
    from aware_environment.stable_ids import (  # noqa: WPS433
        stable_boot_process_id,
        stable_boot_thread_id,
    )

    boot_process_id = stable_boot_process_id(environment_id=environment_id)
    boot_thread_id = stable_boot_thread_id(environment_id=environment_id)
    boot_branch_id = stable_branch_id(
        environment_id=environment_id, thread_id=boot_thread_id
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
                kwargs={
                    "key": environment_key,
                    "title": "Network Node Package Test Environment",
                    "description": None,
                },
                expected_root_object_id=environment_id,
            )
        ],
    )
    return boot_process_id, boot_thread_id


@pytest.mark.asyncio
async def test_network_node_package_module_proof(
    tmp_path: Path,
) -> None:
    repo_root = _REPO_ROOT

    import aware_code_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    import aware_network_ontology  # noqa: F401
    import aware_environment_ontology  # noqa: F401
    import aware_service_ontology  # noqa: F401
    from aware_code.stable_ids import (
        code_package_source_config_key,
        stable_code_package_config_id,
        stable_code_package_id,
    )
    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_network_ontology.network.network_node_package import NetworkNodePackage
    from aware_network_ontology.stable_ids import (
        stable_network_node_config_id,
        stable_network_node_package_id,
    )

    package_name = "kernel-node"
    config_description = "Canonical node package for package materialization tests"

    source_code_package_config_id = stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_toml",
            surface="runtime",
        ),
    )
    source_code_package_id = stable_code_package_id(
        code_package_config_id=source_code_package_config_id,
        package_name=package_name,
        language=CodeLanguage.aware,
    )
    network_node_config_id = stable_network_node_config_id(name=package_name)
    network_node_package_id = stable_network_node_package_id(name=package_name)

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_network_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        assert runtime.context is not None
        index = runtime.context.index
        opg_names = {(opg.name or "").strip() for opg in index.opg_by_hash.values()}
        assert "CodePackage" in opg_names
        assert "NetworkNodeConfig" in opg_names
        assert "NetworkNodePackage" in opg_names

        from aware_environment_ontology.stable_ids import stable_environment_id

        environment_key = "tests.network-node-package.environment"
        environment_id = stable_environment_id(key=environment_key)
        process_id, thread_id = await _bootstrap_environment_lane(
            runtime=runtime,
            environment_id=environment_id,
            environment_key=environment_key,
        )
        lane = LaneIds(
            actor_id=uuid4(),
            branch_id=uuid4(),
        )

        await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="NetworkNodeConfig",
            root_class_fqn=NETWORK_NODE_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=NETWORK_NODE_CONFIG_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": package_name,
                        "description": config_description,
                    },
                    expected_root_object_id=network_node_config_id,
                )
            ],
        )

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="NetworkNodePackage",
            root_class_fqn=NETWORK_NODE_PACKAGE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=NETWORK_NODE_PACKAGE_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": package_name,
                        "network_node_config_id": network_node_config_id,
                        "source_code_package_id": source_code_package_id,
                    },
                    expected_root_object_id=network_node_package_id,
                )
            ],
        )

        assert result.root_object_id == network_node_package_id
        assertions.expect_root(network_node_package_id)
        assertions.expect_instance(network_node_package_id)
        assertions.expect_primitive(
            instance_id=network_node_package_id,
            field_name="name",
            expected=package_name,
        )

        network_node_config_fk_value = assertions.primitive(
            instance_id=network_node_package_id,
            field_name="network_node_config_id",
        )
        assert network_node_config_fk_value in {
            network_node_config_id,
            str(network_node_config_id),
        }

        source_code_package_fk_value = assertions.primitive(
            instance_id=network_node_package_id,
            field_name="source_code_package_id",
        )
        assert source_code_package_fk_value in {
            source_code_package_id,
            str(source_code_package_id),
        }

        created = NetworkNodePackage.model_validate(
            _response_value(result.responses[-1].payload)
        )
        assert created.id == network_node_package_id
        assert created.name == package_name
        assert created.network_node_config_id == network_node_config_id
        assert created.source_code_package_id == source_code_package_id
