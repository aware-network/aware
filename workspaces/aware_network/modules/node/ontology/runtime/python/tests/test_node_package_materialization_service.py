from __future__ import annotations

from pathlib import Path
import shutil
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from aware_code.semantic_materialization import (
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
    SemanticPackageMaterializationRequest,
)
from aware_code.semantic_contract_config import source_code_package_config_ref
from aware_code.stable_ids import stable_code_package_id
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_code_ontology.package.code_package import CodePackage
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime.graph_context import MetaGraphRuntimeIndexSnapshot
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.testing import IsolatedMetaAwareRoot
from aware_orm.session.session import Session

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "aware.repo.toml").is_file()
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _source_code_package_config_id() -> UUID:
    return source_code_package_config_ref(
        manifest_kind="aware_node_toml",
        surface="runtime",
    ).config_id


class _FailClosedSemanticRuntime:
    @property
    def invoker(self):
        raise AssertionError(
            "Node package materialization must not route through legacy runtime"
        )


def test_node_read_model_index_uses_meta_required_projection_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_node.ontology.materialization import node as node_materialization

    seen: dict[str, object] = {}
    expected_index = SimpleNamespace(kind="meta-node-read-model-index")

    def read_model(
        *,
        repo_root: Path,
        aware_root: Path,
        required_projection_names: tuple[str, ...],
        composite_name: str,
        **_kwargs: object,
    ) -> object:
        seen["repo_root"] = repo_root
        seen["aware_root"] = aware_root
        seen["required_projection_names"] = required_projection_names
        seen["composite_name"] = composite_name
        return SimpleNamespace(index=expected_index)

    monkeypatch.setattr(
        node_materialization,
        "read_workspace_meta_runtime_read_model",
        read_model,
    )
    (tmp_path / "modules").mkdir()

    index = node_materialization._resolve_node_read_model_index(root_dir=tmp_path)

    assert index is expected_index
    assert seen == {
        "repo_root": tmp_path.resolve(),
        "aware_root": tmp_path.resolve(),
        "required_projection_names": ("NodePackage", "NodeConfig"),
        "composite_name": "Aware Node Committed Read Model Context",
    }


def test_node_read_model_index_requires_explicit_repo_root_for_remote_state(
    tmp_path: Path,
) -> None:
    from aware_node.ontology.materialization import node as node_materialization

    with pytest.raises(RuntimeError, match="explicit repo_root"):
        node_materialization._resolve_node_read_model_index(
            root_dir=tmp_path / "remote_state",
        )


def test_node_materialization_service_uses_meta_runtime_read_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_node.materialization.service as node_materialization_service

    seen: dict[str, object] = {}
    expected_index = SimpleNamespace(kind="meta-node-materialization-index")

    def read_model(
        *,
        repo_root: Path,
        aware_root: Path,
        required_projection_names: tuple[str, ...],
        composite_name: str,
        **_kwargs: object,
    ) -> object:
        seen["repo_root"] = repo_root
        seen["aware_root"] = aware_root
        seen["required_projection_names"] = required_projection_names
        seen["composite_name"] = composite_name
        return SimpleNamespace(index=expected_index)

    monkeypatch.setattr(
        node_materialization_service,
        "read_workspace_meta_runtime_read_model",
        read_model,
    )
    (tmp_path / "modules").mkdir()

    read_model_result = (
        node_materialization_service._resolve_node_package_materialization_read_model(
            workspace_root=tmp_path,
        )
    )

    assert read_model_result.index is expected_index
    assert seen == {
        "repo_root": tmp_path.resolve(),
        "aware_root": tmp_path.resolve(),
        "required_projection_names": ("CodePackage", "NodeConfig", "NodePackage"),
        "composite_name": "Aware Node Package Materialization Context",
    }


def test_node_materialization_service_requires_explicit_repo_root_for_remote_workspace(
    tmp_path: Path,
) -> None:
    import aware_node.materialization.service as node_materialization_service

    with pytest.raises(RuntimeError, match="explicit read-model repo_root"):
        node_materialization_service._resolve_node_package_materialization_read_model(
            workspace_root=tmp_path / "remote_workspace",
        )


def test_node_materialization_service_uses_request_semantic_catalog(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_node.materialization.service as node_materialization_service

    seen: dict[str, object] = {}
    expected_index = SimpleNamespace(kind="meta-node-materialization-index")
    catalog = {
        "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
        "entries": [],
    }

    def read_model(
        *,
        repo_root: Path,
        aware_root: Path,
        required_projection_names: tuple[str, ...],
        semantic_ontology_package_catalog: object | None,
        composite_name: str,
        **_kwargs: object,
    ) -> object:
        seen["repo_root"] = repo_root
        seen["aware_root"] = aware_root
        seen["required_projection_names"] = required_projection_names
        seen["semantic_ontology_package_catalog"] = semantic_ontology_package_catalog
        seen["composite_name"] = composite_name
        return SimpleNamespace(index=expected_index)

    monkeypatch.setattr(
        node_materialization_service,
        "read_workspace_meta_runtime_read_model",
        read_model,
    )
    (tmp_path / "modules").mkdir()

    read_model_result = (
        node_materialization_service._resolve_node_package_materialization_read_model(
            workspace_root=tmp_path,
            semantic_ontology_package_catalog=catalog,
        )
    )

    assert read_model_result.index is expected_index
    assert seen == {
        "repo_root": tmp_path.resolve(),
        "aware_root": tmp_path.resolve(),
        "required_projection_names": ("CodePackage", "NodeConfig", "NodePackage"),
        "semantic_ontology_package_catalog": catalog,
        "composite_name": "Aware Node Package Materialization Context",
    }


def test_node_config_snapshot_builds_service_code_package_activation() -> None:
    from aware_node.materialization.snapshot_commit import (  # noqa: WPS433
        NodeConfigServiceCodePackageSnapshot,
        NodeConfigServiceTargetSnapshot,
        _build_node_config_manifest_snapshot_objects,
    )
    from aware_node_ontology.node.node_config_service_code_package import (  # noqa: WPS433
        NodeConfigServiceCodePackage,
    )
    from aware_node_ontology.stable_ids import (  # noqa: WPS433
        stable_node_config_id,
        stable_node_config_service_code_package_id,
        stable_node_config_service_target_id,
    )
    from aware_service_ontology.stable_ids import (  # noqa: WPS433
        stable_service_config_id,
    )

    node_config, objects_by_id = _build_node_config_manifest_snapshot_objects(
        name="kernel_services_host",
        description=None,
        environment_targets=(),
        ontology_package_names=(),
        service_targets=(
            NodeConfigServiceTargetSnapshot(
                service_name="aware_experience",
                code_packages=(
                    NodeConfigServiceCodePackageSnapshot(
                        slot_key="experience",
                        package_name="aware-workspace-experience",
                    ),
                ),
            ),
        ),
        interface_names=(),
    )

    node_config_id = stable_node_config_id(name="kernel_services_host")
    service_target_id = stable_node_config_service_target_id(
        node_config_id=node_config_id,
        service_name="aware_experience",
    )
    service_code_package_id = stable_node_config_service_code_package_id(
        node_config_service_target_id=service_target_id,
        slot_key="experience",
        package_name="aware-workspace-experience",
        language="aware",
    )

    assert node_config.id == node_config_id
    assert len(node_config.service_targets) == 1
    service_target = node_config.service_targets[0]
    assert service_target.id == service_target_id
    assert service_target.service_config_id == stable_service_config_id(
        name="aware_experience"
    )
    assert len(service_target.code_packages) == 1
    service_code_package = service_target.code_packages[0]
    assert isinstance(service_code_package, NodeConfigServiceCodePackage)
    assert service_code_package.id == service_code_package_id
    assert service_code_package.node_config_service_target_id == service_target_id
    assert service_code_package.slot_key == "experience"
    assert service_code_package.package_name == "aware-workspace-experience"
    assert getattr(
        service_code_package.language, "value", service_code_package.language
    ) == ("aware")
    assert objects_by_id[service_code_package_id] is service_code_package


@pytest.mark.asyncio
async def test_node_workspace_provider_passes_semantic_catalog(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_node.materialization.workspace_provider as workspace_provider

    captured: dict[str, object] = {}
    catalog = {
        "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
        "entries": [],
    }
    node_toml_path = tmp_path / "aware.node.toml"
    expected_source_code_package_id = uuid4()

    async def materialize_node_package_from_manifest(**kwargs: object) -> object:
        captured.update(kwargs)
        return SimpleNamespace(
            node_toml_path=node_toml_path,
            node_config=SimpleNamespace(id=uuid4(), name="kernel_host"),
            node_package=SimpleNamespace(id=uuid4(), name="kernel-node"),
            source_files=("aware.node.toml",),
            source_code_package_id=uuid4(),
            source_code_package_object_instance_graph_commit_id=uuid4(),
            node_config_commit_id=uuid4(),
            package_commit_id=uuid4(),
            package_head_commit_id=uuid4(),
            package_object_instance_graph_commit_id=uuid4(),
            node_config_projection_hash="sha256:test:NodeConfig",
            node_package_projection_hash="sha256:test:NodePackage",
            node_config_object_instance_graph_commit_id=uuid4(),
            phase_timings_s={},
        )

    monkeypatch.setattr(
        workspace_provider,
        "materialize_node_package_from_manifest",
        materialize_node_package_from_manifest,
    )

    await workspace_provider.materialize(
        SemanticPackageMaterializationRequest(
            runtime=object(),
            index=object(),
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=tmp_path,
            manifest_path=node_toml_path,
            source_code_package_id=expected_source_code_package_id,
            context={
                SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: catalog,
                workspace_provider.NODE_READ_MODEL_REPO_ROOT_CONTEXT_KEY: (
                    REPO_ROOT.as_posix()
                ),
            },
        )
    )

    assert captured["semantic_ontology_package_catalog"] is catalog
    assert captured["repo_root"] == REPO_ROOT
    assert captured["source_code_package_id"] == expected_source_code_package_id


def _write_node_package_fixture(*, workspace_root: Path) -> Path:
    node_toml_path = workspace_root / "aware.node.toml"
    _write(
        node_toml_path,
        "\n".join(
            [
                "aware_node = 1",
                "",
                "[node]",
                'package_name = "kernel-node"',
                'fqn_prefix = "aware_kernel_node"',
                "version_number = 11",
                'title = "Kernel Node"',
                'description = "Canonical node package for package materialization tests"',
                "",
                "[build]",
                'sources_dir = "nodes"',
                'include_paths = ["**/*.aware"]',
                'exclude_paths = ["**/*.draft.aware"]',
                "force_fresh_scan = false",
                'compilation_mode = "node_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "kernel-environment"',
                "version_number = 2",
                'kind = "environment_package"',
                "",
                "[[dependencies]]",
                'package_name = "aware-attention-service"',
                "version_number = 4",
                'kind = "service_package"',
                "",
                "[[dependencies]]",
                'package_name = "aware-workspace-interface"',
                "version_number = 5",
                'kind = "interface_package"',
                "",
                "[[dependencies]]",
                'package_name = "storage-ontology"',
                "version_number = 6",
                'kind = "ontology_package"',
            ]
        )
        + "\n",
    )
    _write(
        workspace_root / "nodes" / "kernel_node.aware",
        "\n".join(
            [
                "node kernel_host {",
                "    include aware.local_agent_kernel;",
                "    environment kernel {",
                "        profile os.default package aware-workspace-environment-profile",
                "    }",
                "    ontology storage-ontology;",
                "    service aware_attention {",
                "        package experience aware-attention-package;",
                "    }",
                "    interface aware_workspace;",
                "}",
                "",
            ]
        ),
    )
    return node_toml_path


@pytest.mark.asyncio
async def test_materialize_node_package_from_manifest_rejects_source_id_mismatch(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "node_package_source_id_mismatch"
    workspace_root.mkdir(parents=True, exist_ok=True)
    node_toml_path = _write_node_package_fixture(workspace_root=workspace_root)
    expected_source_code_package_id = stable_code_package_id(
        code_package_config_id=_source_code_package_config_id(),
        package_name="kernel-node",
        language="aware",
    )
    mismatched_source_code_package_id = uuid4()
    assert mismatched_source_code_package_id != expected_source_code_package_id

    from aware_node.materialization import (  # noqa: WPS433
        materialize_node_package_from_manifest,
    )

    with pytest.raises(RuntimeError, match="aware_node_toml source package config"):
        await materialize_node_package_from_manifest(
            runtime=_FailClosedSemanticRuntime(),
            index=None,
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=workspace_root,
            node_toml_path=node_toml_path,
            repo_root=REPO_ROOT,
            source_code_package_id=mismatched_source_code_package_id,
        )


async def _hydrate_projection_session(
    *,
    branch_id: UUID,
    projection_hash: str,
    index: MetaGraphRuntimeIndexSnapshot,
) -> Session:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head is not None
    assert head.get("commit_id") is not None
    assert head.get("object_instance_graph_id") is not None
    opg = index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        oig_id=UUID(str(head["object_instance_graph_id"])),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )


@pytest.mark.asyncio
async def test_materialize_node_package_from_manifest_commits_canonical_package_root(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "node_package_materialization"
    workspace_root.mkdir(parents=True, exist_ok=True)
    node_toml_path = _write_node_package_fixture(workspace_root=workspace_root)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_node_package_materialization", persistence_backend="fs"
    ):
        from aware_interface_ontology.stable_ids import (
            stable_interface_config_id,
        )  # noqa: WPS433
        from aware_node.ontology_package_identity import (  # noqa: WPS433
            ontology_package_id_for_name,
        )
        from aware_node_ontology.node.node_package import NodePackage  # noqa: WPS433
        from aware_node_ontology.stable_ids import (  # noqa: WPS433
            stable_node_config_environment_profile_mount_id,
            stable_node_config_environment_target_id,
            stable_node_config_id,
            stable_node_config_interface_target_id,
            stable_node_config_ontology_target_id,
            stable_node_config_service_code_package_id,
            stable_node_config_service_target_id,
            stable_node_package_included_node_package_id,
            stable_node_package_id,
        )
        from aware_environment_ontology.stable_ids import (  # noqa: WPS433
            stable_environment_profile_package_id,
        )
        from aware_service_ontology.stable_ids import (
            stable_service_config_id,
        )  # noqa: WPS433
        from aware_environment_ontology.stable_ids import (
            stable_environment_config_id,
        )  # noqa: WPS433

        from aware_node.materialization import (  # noqa: WPS433
            materialize_node_package_from_manifest,
            resolve_node_package_materialization_spec,
        )
        from aware_node.materialization.service import (  # noqa: WPS433
            _resolve_node_package_materialization_read_model,
        )

        spec = resolve_node_package_materialization_spec(
            node_toml_path=node_toml_path,
            workspace_root=workspace_root,
        )
        assert spec.package_name == "kernel-node"
        assert spec.package_fqn_prefix == "aware_kernel_node"
        assert spec.config_name == "kernel_host"
        assert (
            spec.config_description
            == "Canonical node package for package materialization tests"
        )
        assert tuple(
            item.included_package_name for item in spec.included_node_packages
        ) == ("aware.local_agent_kernel",)
        assert tuple(item.environment_handle for item in spec.environment_targets) == (
            "kernel",
        )
        assert tuple(
            mount.package_name
            for item in spec.environment_targets
            for mount in item.profile_mounts
        ) == ("aware-workspace-environment-profile",)
        assert tuple(
            mount.profile_key
            for item in spec.environment_targets
            for mount in item.profile_mounts
        ) == ("os.default",)
        assert spec.service_names == ("aware_attention",)
        assert len(spec.service_targets) == 1
        assert tuple(
            (
                package.slot_key,
                package.package_name,
                package.language,
            )
            for target in spec.service_targets
            for package in target.code_packages
        ) == (("experience", "aware-attention-package", "aware"),)
        assert spec.ontology_package_names == ("storage-ontology",)
        assert spec.interface_names == ("aware_workspace",)
        assert spec.source_files == ("nodes/kernel_node.aware",)

        branch_id = uuid4()

        read_model = _resolve_node_package_materialization_read_model(
            workspace_root=workspace_root,
            repo_root=repo_root,
        )
        code_package_projection_hash = read_model.projection_hash_for_name(
            "CodePackage"
        )
        assert code_package_projection_hash

        expected_source_code_package_id = stable_code_package_id(
            code_package_config_id=_source_code_package_config_id(),
            package_name="kernel-node",
            language="aware",
        )
        result = await materialize_node_package_from_manifest(
            runtime=_FailClosedSemanticRuntime(),
            index=None,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            node_toml_path=node_toml_path,
            repo_root=repo_root,
            source_code_package_id=expected_source_code_package_id,
        )

        expected_node_config_id = stable_node_config_id(name="kernel_host")
        expected_node_package_id = stable_node_package_id(name="kernel-node")

        assert result.node_toml_path == node_toml_path.resolve()
        assert result.workspace_root == workspace_root.resolve()
        assert result.manifest_spec.node.package_name == "kernel-node"
        assert result.node_config.id == expected_node_config_id
        assert result.node_package.id == expected_node_package_id
        assert result.node_package.node_config_id == expected_node_config_id
        assert result.node_package.fqn_prefix == "aware_kernel_node"
        assert result.node_package.version_number == 11
        assert result.node_package.title == "Kernel Node"
        assert (
            result.node_package.description
            == "Canonical node package for package materialization tests"
        )
        assert result.node_package.aware_node_version == 1
        assert result.node_package.manifest_relative_path == "aware.node.toml"
        assert result.node_package.package_root == "."
        assert result.node_package.sources_root == "nodes"
        assert list(result.node_package.include_paths) == ["**/*.aware"]
        assert list(result.node_package.exclude_paths) == ["**/*.draft.aware"]
        assert result.node_package.force_fresh_scan is False
        assert result.node_package.compilation_mode == "node_ontology"
        assert list(result.node_package.dependencies) == [
            {
                "package_name": "kernel-environment",
                "version_number": 2,
                "kind": "environment_package",
            },
            {
                "package_name": "aware-attention-service",
                "version_number": 4,
                "kind": "service_package",
            },
            {
                "package_name": "aware-workspace-interface",
                "version_number": 5,
                "kind": "interface_package",
            },
            {
                "package_name": "storage-ontology",
                "version_number": 6,
                "kind": "ontology_package",
            },
        ]
        assert tuple(
            include.included_package_name
            for include in result.node_package.included_node_packages
        ) == ("aware.local_agent_kernel",)
        assert result.source_files == ("nodes/kernel_node.aware",)
        assert result.source_code_package_id == expected_source_code_package_id
        assert result.node_config_commit_id is not None
        assert result.node_config_head_commit_id is not None
        assert result.package_commit_id is not None
        assert result.package_head_commit_id is not None
        assert result.phase_timings_s["total"] > 0
        assert "upsert_code_package_sources" in result.phase_timings_s
        assert "upsert_node_config_targets" in result.phase_timings_s

        assert len(result.node_config_environment_targets) == 1
        assert len(result.node_config_ontology_targets) == 1
        assert len(result.node_config_service_targets) == 1
        assert len(result.node_config_service_code_packages) == 1
        assert len(result.node_config_interface_targets) == 1
        assert len(result.node_package_included_node_packages) == 1

        included_node_package = result.node_package_included_node_packages[0]
        assert included_node_package.id == stable_node_package_included_node_package_id(
            node_package_id=expected_node_package_id,
            included_package_name="aware.local_agent_kernel",
        )
        assert included_node_package.included_node_package_id == stable_node_package_id(
            name="aware.local_agent_kernel"
        )
        assert included_node_package.included_package_name == "aware.local_agent_kernel"
        assert included_node_package.include_key == "aware.local_agent_kernel"

        environment_target = result.node_config_environment_targets[0]
        assert environment_target.id == stable_node_config_environment_target_id(
            node_config_id=expected_node_config_id,
            environment_handle="kernel",
        )
        assert environment_target.environment_config_id == stable_environment_config_id(
            handle="kernel"
        )
        assert len(environment_target.profile_mounts) == 1
        environment_mount = environment_target.profile_mounts[0]
        assert environment_mount.id == stable_node_config_environment_profile_mount_id(
            node_config_environment_target_id=environment_target.id,
            mount_key="aware-workspace-environment-profile:os.default",
        )
        assert (
            environment_mount.environment_profile_package_id
            == stable_environment_profile_package_id(
                name="aware-workspace-environment-profile"
            )
        )
        assert environment_target.environment_handle == "kernel"
        assert environment_mount.package_name == "aware-workspace-environment-profile"
        assert environment_mount.profile_key == "os.default"
        assert (
            environment_mount.mount_key
            == "aware-workspace-environment-profile:os.default"
        )
        assert environment_mount.mode == "mounted"
        assert environment_mount.position == 0

        ontology_target = result.node_config_ontology_targets[0]
        assert ontology_target.id == stable_node_config_ontology_target_id(
            node_config_id=expected_node_config_id,
            package_name="storage-ontology",
        )
        assert ontology_target.ontology_package_id == ontology_package_id_for_name(
            "storage-ontology"
        )
        assert ontology_target.package_name == "storage-ontology"

        service_target = result.node_config_service_targets[0]
        assert service_target.id == stable_node_config_service_target_id(
            node_config_id=expected_node_config_id,
            service_name="aware_attention",
        )
        assert service_target.service_config_id == stable_service_config_id(
            name="aware_attention"
        )
        assert service_target.service_name == "aware_attention"
        assert len(service_target.code_packages) == 1
        service_code_package = service_target.code_packages[0]
        assert service_code_package.id == stable_node_config_service_code_package_id(
            node_config_service_target_id=service_target.id,
            slot_key="experience",
            package_name="aware-attention-package",
            language="aware",
        )
        assert service_code_package in result.node_config_service_code_packages
        assert service_code_package.node_config_service_target_id == service_target.id
        assert service_code_package.slot_key == "experience"
        assert service_code_package.package_name == "aware-attention-package"
        assert (
            getattr(
                service_code_package.language, "value", service_code_package.language
            )
            == "aware"
        )

        interface_target = result.node_config_interface_targets[0]
        assert interface_target.id == stable_node_config_interface_target_id(
            node_config_id=expected_node_config_id,
            interface_name="aware_workspace",
        )
        assert interface_target.interface_config_id == stable_interface_config_id(
            name="aware_workspace"
        )
        assert interface_target.interface_name == "aware_workspace"

        code_package_session = await _hydrate_projection_session(
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
            index=read_model.index,
        )
        code_package = code_package_session.imap_get(
            CodePackage, expected_source_code_package_id
        )
        assert code_package is not None
        assert code_package.package_name == "kernel-node"
        assert code_package.code_package_config_id == _source_code_package_config_id()
        assert getattr(code_package.language, "value", code_package.language) == "aware"
        assert code_package.surface == "runtime"
        assert code_package.manifest_relative_path == "aware.node.toml"
        assert code_package.package_root == "."
        assert code_package.sources_root == "nodes"
        assert code_package.fqn_prefix == "aware_kernel_node"
        assert {edge.relative_path for edge in code_package.code_package_codes} == {
            "aware.node.toml",
            "nodes/kernel_node.aware",
        }

        node_package_session = await _hydrate_projection_session(
            branch_id=branch_id,
            projection_hash=result.node_package_projection_hash,
            index=read_model.index,
        )
        node_package = node_package_session.imap_get(
            NodePackage, expected_node_package_id
        )
        assert node_package is not None
        assert node_package.name == "kernel-node"
        assert node_package.node_config_id == expected_node_config_id
        assert node_package.source_code_package_id == expected_source_code_package_id
        assert node_package.fqn_prefix == "aware_kernel_node"
        assert node_package.version_number == 11
        assert node_package.manifest_relative_path == "aware.node.toml"
        assert node_package.package_root == "."
        assert node_package.sources_root == "nodes"
        assert tuple(
            include.included_package_name
            for include in node_package.included_node_packages
        ) == ("aware.local_agent_kernel",)
        assert list(node_package.dependencies) == list(result.node_package.dependencies)


@pytest.mark.asyncio
async def test_workspace_materialization_provider_returns_portable_node_refs(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "node_workspace_semantic_ref"
    workspace_root.mkdir(parents=True, exist_ok=True)
    node_toml_path = _write_node_package_fixture(workspace_root=workspace_root)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_node_workspace_semantic_ref",
        persistence_backend="fs",
    ):
        branch_id = uuid4()
        expected_source_code_package_id = stable_code_package_id(
            code_package_config_id=_source_code_package_config_id(),
            package_name="kernel-node",
            language="aware",
        )

        from aware_node.materialization.workspace_provider import (  # noqa: WPS433
            NODE_READ_MODEL_REPO_ROOT_CONTEXT_KEY,
            materialize,
        )
        from aware_node.deployment_closure import (  # noqa: WPS433
            NODE_RUNTIME_CLOSURE_CONTEXT_KEY,
        )
        from aware_environment_ontology.stable_ids import (  # noqa: WPS433
            stable_environment_config_id,
        )
        from aware_interface_ontology.stable_ids import (  # noqa: WPS433
            stable_interface_config_id,
        )
        from aware_service_ontology.stable_ids import (  # noqa: WPS433
            stable_service_config_id,
        )

        result = await materialize(
            SemanticPackageMaterializationRequest(
                runtime=_FailClosedSemanticRuntime(),
                index=None,
                actor_id=None,
                branch_id=branch_id,
                workspace_root=workspace_root,
                manifest_path=node_toml_path,
                source_code_package_id=expected_source_code_package_id,
                code_package_delta=CodePackageDelta(
                    package_name="kernel-node",
                    package_root=".",
                    sources_root="nodes",
                    manifest_relative_path="aware.node.toml",
                    paths=[
                        CodePackageDeltaPath(
                            relative_path="nodes/kernel_node.aware",
                            kind=CodePackageDeltaKind.update,
                        ),
                    ],
                ),
                change_preview={
                    "affected_semantic_keys": ("node_package:kernel-node",),
                },
                context={
                    NODE_READ_MODEL_REPO_ROOT_CONTEXT_KEY: repo_root.as_posix(),
                    NODE_RUNTIME_CLOSURE_CONTEXT_KEY: (
                        {
                            "package_kind": "environment",
                            "package_key": "kernel-environment",
                            "semantic_package_family": "environment",
                            "semantic_package_id": str(uuid4()),
                            "semantic_root_kind": "environment_config",
                            "semantic_root_id": str(
                                stable_environment_config_id(handle="kernel")
                            ),
                            "manifest_path": "environments/kernel/aware.environment.toml",
                        },
                        {
                            "package_kind": "environment_profile",
                            "package_key": "aware-workspace-environment-profile",
                            "semantic_package_family": "environment",
                            "semantic_package_id": str(uuid4()),
                            "semantic_root_kind": "environment_profile_package",
                            "semantic_root_id": str(uuid4()),
                            "manifest_path": "workspaces/aware_network/modules/interface/experiences/aware_control/aware.experience.toml",
                        },
                        {
                            "package_kind": "ontology",
                            "package_key": "storage-ontology",
                            "semantic_package_family": "ontology",
                            "semantic_package_id": str(uuid4()),
                            "semantic_root_kind": "OntologyPackage",
                            "semantic_root_id": str(uuid4()),
                            "manifest_path": "modules/storage/ontology/aware.ontology.toml",
                        },
                        {
                            "package_kind": "service",
                            "package_key": "aware-attention-service",
                            "semantic_package_family": "service",
                            "semantic_package_id": str(uuid4()),
                            "semantic_root_kind": "service_config",
                            "semantic_root_id": str(
                                stable_service_config_id(name="aware_attention")
                            ),
                            "manifest_path": "services/attention/aware.service.toml",
                        },
                        {
                            "package_kind": "interface",
                            "package_key": "aware-workspace-interface",
                            "semantic_package_family": "interface",
                            "semantic_package_id": str(uuid4()),
                            "semantic_root_kind": "interface_config",
                            "semantic_root_id": str(
                                stable_interface_config_id(name="aware_workspace")
                            ),
                            "manifest_path": "interfaces/workspace/aware.interface.toml",
                        },
                    ),
                },
            )
        )

        assert result.mode == "full_rebuild"
        assert result.affected_semantic_keys == ("node_package:kernel-node",)
        assert result.applied_semantic_keys == ("node_package:kernel-node",)
        assert result.fallback_reason is not None
        assert "full Node package manifest" in result.fallback_reason
        assert result.commit_id is not None
        assert result.head_commit_id is not None

        assert result.details["node_package_name"] == "kernel-node"
        assert result.details["node_config_name"] == "kernel_host"
        assert result.details["semantic_branch_id"] == str(branch_id)
        assert (
            result.details["source_code_package_object_instance_graph_commit_id"]
            is not None
        )
        assert (
            result.details["node_package_object_instance_graph_commit_id"] is not None
        )
        assert result.details["node_config_projection_hash"] is not None
        assert result.details["node_package_projection_hash"] is not None
        assert result.details["node_config_object_instance_graph_commit_id"] is not None
        closure = result.details["node_runtime_closure"]
        assert closure["required_python_packages"] == (
            "aware-environment-service",
            "aware-interface-service",
            "aware-node-service",
            "aware-service-service",
        )
        service_inputs = [
            item
            for item in closure["runtime_inputs"]
            if item["runtime_kind"] == "service"
        ]
        assert service_inputs[0]["target_name"] == "aware_attention"
        assert service_inputs[0]["code_packages"] == [
            {
                "slot_key": "experience",
                "package_name": "aware-attention-package",
                "language": "aware",
            }
        ]
        artifact_receipts = result.details["artifact_ownership_receipts"]
        assert artifact_receipts[0]["artifact_family"] == "node_runtime_closure"
        assert (workspace_root / artifact_receipts[0]["path"]).is_file()

        assert len(result.bundle_packages) == 1
        bundle = result.bundle_packages[0]
        assert bundle.package_key == "kernel-node"
        assert bundle.manifest_toml_path == node_toml_path.resolve()
        assert bundle.semantic_branch_id == branch_id
        assert bundle.semantic_head_commit_id == result.head_commit_id
        assert bundle.semantic_object_instance_graph_commit_id is not None
        assert bundle.semantic_root_kind == "node_config"
        assert bundle.semantic_projection_name == "NodePackage"
        assert (
            bundle.semantic_projection_hash
            == result.details["node_package_projection_hash"]
        )
        assert bundle.semantic_root_object_instance_graph_commit_id is not None
        assert bundle.source_code_package_id == expected_source_code_package_id
        assert bundle.source_object_instance_graph_commit_id is not None

        _write(
            workspace_root
            / ".aware"
            / "workspace"
            / "revision-filesystem.manifest.json",
            "{}",
        )
        shutil.copytree(
            tmp_path / "aware_root_node_workspace_semantic_ref" / ".aware" / "oig",
            workspace_root / ".aware" / "oig",
            dirs_exist_ok=True,
        )
        from aware_node.package_ref_resolution import (  # noqa: WPS433
            NodeRuntimePackageRef,
            resolve_committed_node_runtime_package_ref,
        )

        resolved = await resolve_committed_node_runtime_package_ref(
            package_ref=NodeRuntimePackageRef(
                family_key="aware_node",
                package_kind="node_package",
                package_name=bundle.package_key,
                manifest_path="aware.node.toml",
                semantic_package_id=str(bundle.semantic_package_id),
                semantic_projection_hash=bundle.semantic_projection_hash,
                semantic_object_instance_graph_commit_id=str(
                    bundle.semantic_object_instance_graph_commit_id
                ),
                semantic_root_kind=bundle.semantic_root_kind,
                semantic_root_id=str(bundle.semantic_root_id),
                semantic_root_object_instance_graph_commit_id=str(
                    bundle.semantic_root_object_instance_graph_commit_id
                ),
                source_code_package_id=str(bundle.source_code_package_id),
            ),
            materialized_workspace_root=workspace_root,
            repo_root=repo_root,
        )

        assert resolved.semantic_branch_id == str(branch_id)
        assert str(resolved.node_package_id) == result.details["node_package_id"]
        assert str(resolved.node_config_id) == result.details["node_config_id"]
        assert resolved.service_names == ("aware_attention",)
        assert tuple(
            include.included_package_name for include in resolved.included_node_packages
        ) == ("aware.local_agent_kernel",)
        assert tuple(
            target.environment_handle for target in resolved.environment_targets
        ) == ("kernel",)
        assert tuple(
            mount.package_name
            for target in resolved.environment_targets
            for mount in target.profile_mounts
        ) == ("aware-workspace-environment-profile",)
        assert tuple(
            target.interface_name for target in resolved.interface_targets
        ) == ("aware_workspace",)


@pytest.mark.asyncio
async def test_materialize_node_package_from_manifest_replaces_stale_node_config_targets(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "node_package_target_replacement"
    workspace_root.mkdir(parents=True, exist_ok=True)
    node_toml_path = _write_node_package_fixture(workspace_root=workspace_root)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_node_package_target_replacement",
        persistence_backend="fs",
    ):
        from aware_node.materialization import (  # noqa: WPS433
            materialize_node_package_from_manifest,
        )
        from aware_node.materialization.service import (  # noqa: WPS433
            _resolve_node_package_materialization_read_model,
        )
        from aware_node_ontology.node.node_config import NodeConfig  # noqa: WPS433
        from aware_node_ontology.stable_ids import stable_node_config_id  # noqa: WPS433

        read_model = _resolve_node_package_materialization_read_model(
            workspace_root=workspace_root,
            repo_root=repo_root,
        )
        branch_id = uuid4()

        await materialize_node_package_from_manifest(
            runtime=_FailClosedSemanticRuntime(),
            index=None,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            node_toml_path=node_toml_path,
            repo_root=repo_root,
        )
        _write(
            workspace_root / "nodes" / "kernel_node.aware",
            "\n".join(
                [
                    "node kernel_host {",
                    "    include aware.local_agent_kernel;",
                    "    environment aware-kernel-runtime {",
                    "        profile os.default package aware-control-environment-profile",
                    "    }",
                    "    ontology storage-ontology;",
                    "    service aware_attention;",
                    "    interface aware_workspace;",
                    "}",
                    "",
                ]
            ),
        )

        result = await materialize_node_package_from_manifest(
            runtime=_FailClosedSemanticRuntime(),
            index=None,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            node_toml_path=node_toml_path,
            repo_root=repo_root,
        )

        assert tuple(
            target.environment_handle
            for target in result.node_config_environment_targets
        ) == ("aware-kernel-runtime",)
        assert tuple(
            mount.package_name
            for target in result.node_config_environment_targets
            for mount in target.profile_mounts
        ) == ("aware-control-environment-profile",)

        node_config_session = await _hydrate_projection_session(
            branch_id=branch_id,
            projection_hash=result.node_config_projection_hash,
            index=read_model.index,
        )
        node_config = node_config_session.imap_get(
            NodeConfig,
            stable_node_config_id(name="kernel_host"),
        )

        assert node_config is not None
        assert tuple(
            target.environment_handle for target in node_config.environment_targets
        ) == ("aware-kernel-runtime",)
        assert tuple(
            mount.package_name
            for target in node_config.environment_targets
            for mount in target.profile_mounts
        ) == ("aware-control-environment-profile",)
        assert tuple(
            target.package_name for target in node_config.ontology_targets
        ) == ("storage-ontology",)


@pytest.mark.asyncio
async def test_read_committed_node_package_hydrates_targets_from_lane_head(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "node_package_read_model"
    workspace_root.mkdir(parents=True, exist_ok=True)
    node_toml_path = _write_node_package_fixture(workspace_root=workspace_root)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_node_package_read_model", persistence_backend="fs"
    ):
        from aware_node.materialization import (
            materialize_node_package_from_manifest,
        )  # noqa: WPS433
        from aware_node.ontology.materialization import (
            read_committed_node_package,
        )  # noqa: WPS433
        from aware_node_ontology.stable_ids import (
            stable_node_package_id,
        )  # noqa: WPS433

        branch_id = uuid4()

        result = await materialize_node_package_from_manifest(
            runtime=_FailClosedSemanticRuntime(),
            index=None,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            node_toml_path=node_toml_path,
            repo_root=repo_root,
        )
        read_result = await read_committed_node_package(
            branch_id=branch_id,
            node_package_id=stable_node_package_id(name="kernel-node"),
            repo_root=repo_root,
        )

        assert read_result.branch_id == branch_id
        assert read_result.head_commit_id
        assert result.package_head_commit_id is not None
        assert read_result.node_package.id == result.node_package.id
        assert read_result.node_package.name == "kernel-node"
        assert read_result.node_package.node_config is not None
        assert read_result.node_package.node_config.name == "kernel_host"
        assert tuple(
            item.environment_handle
            for item in read_result.node_package.node_config.environment_targets
        ) == ("kernel",)
        assert tuple(
            mount.package_name
            for item in read_result.node_package.node_config.environment_targets
            for mount in item.profile_mounts
        ) == ("aware-workspace-environment-profile",)
        assert tuple(
            mount.profile_key
            for item in read_result.node_package.node_config.environment_targets
            for mount in item.profile_mounts
        ) == ("os.default",)
        assert tuple(
            item.service_name
            for item in read_result.node_package.node_config.service_targets
        ) == ("aware_attention",)
        assert tuple(
            item.package_name
            for item in read_result.node_package.node_config.ontology_targets
        ) == ("storage-ontology",)
        assert tuple(
            item.included_package_name
            for item in read_result.node_package.included_node_packages
        ) == ("aware.local_agent_kernel",)
        assert tuple(
            item.interface_name
            for item in read_result.node_package.node_config.interface_targets
        ) == ("aware_workspace",)
