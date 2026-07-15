from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from aware_code.handlers._generated import meta_handlers as code_meta_handlers
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
from aware_node.handlers._generated import meta_handlers as node_meta_handlers

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "aware.repo.toml").is_file()
)

CODE_PACKAGE_CLASS_FQN = "aware_code.package.CodePackage"
NODE_CONFIG_CLASS_FQN = "aware_node.node.NodeConfig"
NODE_CONFIG_ENVIRONMENT_TARGET_CLASS_FQN = "aware_node.node.NodeConfigEnvironmentTarget"
NODE_PACKAGE_CLASS_FQN = "aware_node.node.NodePackage"


def _node_module_proof_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
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
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/economy/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/service/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/network/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/interface/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/node/ontology/structure/aware.toml",
    )


def _build_node_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_node_module_proof_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            code_meta_handlers,
            node_meta_handlers,
        ),
        bootstrap_modules=(
            code_meta_handlers,
            node_meta_handlers,
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


def test_node_module_proof_does_not_import_legacy_runtime() -> None:
    source = Path(__file__).read_text(encoding="utf-8")

    assert ("from " + "aware_" + "runtime") not in source
    assert ("import " + "aware_" + "runtime") not in source


@pytest.mark.asyncio
async def test_node_package_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_code_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_interface_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    import aware_node_ontology  # noqa: F401
    import aware_environment_ontology  # noqa: F401
    import aware_service_ontology  # noqa: F401
    from aware_code.stable_ids import (
        code_package_source_config_key,
        stable_code_package_config_id,
        stable_code_package_id,
    )
    from aware_code.types import JsonArray
    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_node_ontology.node.node_package import NodePackage
    from aware_node_ontology.stable_ids import (
        stable_node_config_environment_profile_mount_id,
        stable_node_config_environment_target_id,
        stable_node_config_id,
        stable_node_config_interface_target_id,
        stable_node_config_service_target_id,
        stable_node_package_id,
    )
    from aware_environment_ontology.stable_ids import (
        stable_environment_config_id,
        stable_environment_profile_package_id,
    )
    from aware_interface_ontology.stable_ids import stable_interface_config_id
    from aware_service_ontology.stable_ids import stable_service_config_id

    package_name = "kernel-node"
    fqn_prefix = "aware_kernel_node"
    package_title = "Kernel Node"
    package_description = "NodePackage manifest truth proof"
    config_description = "Canonical node package for package materialization tests"
    environment_handle = "kernel"
    profile_package_name = "aware-workspace-environment-profile"
    profile_key = "os.default"
    mount_key = f"{profile_package_name}:{profile_key}"
    service_name = "aware-home-service"
    interface_name = "aware-home-interface"

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
    node_config_id = stable_node_config_id(name=package_name)
    node_package_id = stable_node_package_id(name=package_name)
    environment_target_id = stable_node_config_environment_target_id(
        node_config_id=node_config_id,
        environment_handle=environment_handle,
    )
    environment_profile_mount_id = stable_node_config_environment_profile_mount_id(
        node_config_environment_target_id=environment_target_id,
        mount_key=mount_key,
    )
    service_target_id = stable_node_config_service_target_id(
        node_config_id=node_config_id,
        service_name=service_name,
    )
    interface_target_id = stable_node_config_interface_target_id(
        node_config_id=node_config_id,
        interface_name=interface_name,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_node_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        assert runtime.context is not None
        index = runtime.context.index
        opg_names = {(opg.name or "").strip() for opg in index.opg_by_hash.values()}
        assert "CodePackage" in opg_names
        assert "NodeConfig" in opg_names
        assert "NodePackage" in opg_names

        lane = LaneIds(
            actor_id=uuid4(),
            branch_id=uuid4(),
        )

        await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="CodePackage",
            root_class_fqn=CODE_PACKAGE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=CODE_PACKAGE_CLASS_FQN,
                    function_name="build_via_code_package_config",
                    kwargs={
                        "code_package_config_id": source_code_package_config_id,
                        "package_name": package_name,
                        "language": CodeLanguage.aware.value,
                        "manifest_relative_path": "aware.node.toml",
                        "package_root": ".",
                        "sources_root": "nodes",
                        "fqn_prefix": fqn_prefix,
                        "surface": "runtime",
                    },
                    expected_root_object_id=source_code_package_id,
                )
            ],
        )

        await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="NodeConfig",
            root_class_fqn=NODE_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=NODE_CONFIG_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": package_name,
                        "description": config_description,
                    },
                    expected_root_object_id=node_config_id,
                )
            ],
        )

        _, environment_target_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="NodeConfig",
            root_class_fqn=NODE_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=NODE_CONFIG_CLASS_FQN,
                    function_name="attach_environment_target",
                    kwargs={
                        "environment_handle": environment_handle,
                    },
                    object_id=node_config_id,
                    expected_root_object_id=node_config_id,
                )
            ],
        )
        environment_target_assertions.expect_instance(environment_target_id)
        environment_target_assertions.expect_primitive(
            instance_id=environment_target_id,
            field_name="environment_handle",
            expected=environment_handle,
        )
        environment_target_fk = environment_target_assertions.primitive(
            instance_id=environment_target_id,
            field_name="environment_config_id",
        )
        assert environment_target_fk in {
            stable_environment_config_id(handle=environment_handle),
            str(stable_environment_config_id(handle=environment_handle)),
        }

        _, profile_mount_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="NodeConfig",
            root_class_fqn=NODE_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=NODE_CONFIG_ENVIRONMENT_TARGET_CLASS_FQN,
                    function_name="add_profile_mount",
                    kwargs={
                        "profile_key": profile_key,
                        "package_name": profile_package_name,
                        "mount_key": mount_key,
                        "mode": "mounted",
                        "position": 0,
                    },
                    object_id=environment_target_id,
                )
            ],
        )
        profile_mount_assertions.expect_instance(environment_target_id)
        profile_mount_assertions.expect_instance(environment_profile_mount_id)
        profile_mount_assertions.expect_primitive(
            instance_id=environment_profile_mount_id,
            field_name="package_name",
            expected=profile_package_name,
        )
        profile_mount_assertions.expect_primitive(
            instance_id=environment_profile_mount_id,
            field_name="profile_key",
            expected=profile_key,
        )
        profile_mount_assertions.expect_primitive(
            instance_id=environment_profile_mount_id,
            field_name="mount_key",
            expected=mount_key,
        )
        profile_mount_assertions.expect_edge(
            source_id=environment_target_id,
            target_id=environment_profile_mount_id,
            relationship_name="profile_mounts",
        )
        environment_profile_package_fk = profile_mount_assertions.primitive(
            instance_id=environment_profile_mount_id,
            field_name="environment_profile_package_id",
        )
        assert environment_profile_package_fk in {
            stable_environment_profile_package_id(name=profile_package_name),
            str(stable_environment_profile_package_id(name=profile_package_name)),
        }

        _, service_target_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="NodeConfig",
            root_class_fqn=NODE_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=NODE_CONFIG_CLASS_FQN,
                    function_name="attach_service_config",
                    kwargs={
                        "service_name": service_name,
                    },
                    object_id=node_config_id,
                    expected_root_object_id=node_config_id,
                )
            ],
        )
        service_target_assertions.expect_instance(service_target_id)
        service_target_assertions.expect_primitive(
            instance_id=service_target_id,
            field_name="service_name",
            expected=service_name,
        )
        service_target_fk = service_target_assertions.primitive(
            instance_id=service_target_id,
            field_name="service_config_id",
        )
        assert service_target_fk in {
            stable_service_config_id(name=service_name),
            str(stable_service_config_id(name=service_name)),
        }

        _, interface_target_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="NodeConfig",
            root_class_fqn=NODE_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=NODE_CONFIG_CLASS_FQN,
                    function_name="attach_interface_config",
                    kwargs={
                        "interface_name": interface_name,
                    },
                    object_id=node_config_id,
                    expected_root_object_id=node_config_id,
                )
            ],
        )
        interface_target_assertions.expect_instance(interface_target_id)
        interface_target_assertions.expect_primitive(
            instance_id=interface_target_id,
            field_name="interface_name",
            expected=interface_name,
        )
        interface_target_fk = interface_target_assertions.primitive(
            instance_id=interface_target_id,
            field_name="interface_config_id",
        )
        assert interface_target_fk in {
            stable_interface_config_id(name=interface_name),
            str(stable_interface_config_id(name=interface_name)),
        }

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="NodePackage",
            root_class_fqn=NODE_PACKAGE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=NODE_PACKAGE_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": package_name,
                        "node_config_id": node_config_id,
                        "source_code_package_id": source_code_package_id,
                        "fqn_prefix": fqn_prefix,
                        "version_number": 11,
                        "title": package_title,
                        "description": package_description,
                        "aware_node_version": 1,
                        "manifest_relative_path": "aware.node.toml",
                        "package_root": ".",
                        "sources_root": "nodes",
                        "include_paths": JsonArray(["**/*.aware"]),
                        "exclude_paths": JsonArray(["**/*.draft.aware"]),
                        "force_fresh_scan": False,
                        "compilation_mode": "node_ontology",
                        "dependencies": JsonArray(
                            [
                                {
                                    "package_name": "kernel-environment",
                                    "version_number": 2,
                                    "kind": "environment_package",
                                },
                                {
                                    "package_name": "aware-workspace",
                                    "version_number": 3,
                                    "kind": "experience_package",
                                },
                            ]
                        ),
                    },
                    expected_root_object_id=node_package_id,
                )
            ],
        )

        assert result.root_object_id == node_package_id
        assertions.expect_root(node_package_id)
        assertions.expect_instance(node_package_id)
        assertions.expect_primitive(
            instance_id=node_package_id,
            field_name="name",
            expected=package_name,
        )
        assertions.expect_primitive(
            instance_id=node_package_id,
            field_name="manifest_relative_path",
            expected="aware.node.toml",
        )
        assertions.expect_primitive(
            instance_id=node_package_id,
            field_name="compilation_mode",
            expected="node_ontology",
        )

        node_config_fk_value = assertions.primitive(
            instance_id=node_package_id,
            field_name="node_config_id",
        )
        assert node_config_fk_value in {node_config_id, str(node_config_id)}

        source_code_package_fk_value = assertions.primitive(
            instance_id=node_package_id,
            field_name="source_code_package_id",
        )
        assert source_code_package_fk_value in {
            source_code_package_id,
            str(source_code_package_id),
        }

        created = NodePackage.model_validate(
            _response_value(result.responses[-1].payload),
        )
        assert created.id == node_package_id
        assert created.name == package_name
        assert created.node_config_id == node_config_id
        assert created.source_code_package_id == source_code_package_id
        assert created.fqn_prefix == fqn_prefix
        assert created.version_number == 11
        assert created.title == package_title
        assert created.description == package_description
        assert created.aware_node_version == 1
        assert created.manifest_relative_path == "aware.node.toml"
        assert created.package_root == "."
        assert created.sources_root == "nodes"
        assert list(created.include_paths) == ["**/*.aware"]
        assert list(created.exclude_paths) == ["**/*.draft.aware"]
        assert created.force_fresh_scan is False
        assert created.compilation_mode == "node_ontology"
        assert list(created.dependencies) == [
            {
                "package_name": "kernel-environment",
                "version_number": 2,
                "kind": "environment_package",
            },
            {
                "package_name": "aware-workspace",
                "version_number": 3,
                "kind": "experience_package",
            },
        ]
