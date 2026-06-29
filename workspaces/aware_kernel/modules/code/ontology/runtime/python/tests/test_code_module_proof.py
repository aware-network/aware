from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_code.handlers._generated import meta_handlers as code_meta_handlers
from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_code_ontology.package.code_package_artifact import CodePackageArtifactRef
from aware_meta.handlers._generated import meta_handlers as meta_meta_handlers
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    ProofCall,
    ROOT_OBJECT_ID,
    run_meta_runtime_proof,
)
from _code_runtime_test_paths import CODE_PACKAGE_MANIFEST_PATHS, REPO_ROOT, source_text


def _code_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return CODE_PACKAGE_MANIFEST_PATHS


def _build_code_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_code_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            code_meta_handlers,
            meta_meta_handlers,
        ),
        bootstrap_modules=(
            code_meta_handlers,
            meta_meta_handlers,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
        ),
    )
    assert runtime.context is not None
    return runtime


def _single_projection_hash_by_name(idx: MetaGraphRuntimeIndex, name: str) -> str:
    matches = [
        opg.projection_hash for opg in idx.opg_by_hash.values() if opg.name == name
    ]
    assert matches, f"Projection not found: {name}"
    assert len(matches) == 1, f"Projection name is not unique: {name}"
    return matches[0]


def _runtime_function_names_by_class_name(
    idx: MetaGraphRuntimeIndex,
    class_name: str,
) -> set[str]:
    for node in idx.ocg.object_config_graph_nodes:
        class_config = node.class_config
        if class_config is None or class_config.name != class_name:
            continue
        return {
            link.function_config.name
            for link in class_config.class_config_function_configs
        }
    raise AssertionError(f"Class not found: {class_name}")


def _source_code_package_config_id(*, manifest_kind: object, surface: object) -> UUID:
    return stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind=manifest_kind,
            surface=surface,
        ),
    )


@pytest.mark.asyncio
async def test_code_package_text_snapshot_builds_package_artifacts() -> None:
    from aware_code.package import snapshot_commit  # noqa: WPS433
    from aware_code_ontology.code.code_enums import CodeLanguage  # noqa: WPS433

    code_package_config_id = _source_code_package_config_id(
        manifest_kind="pyproject_toml",
        surface="runtime",
    )
    code_package_id = stable_code_package_id(
        code_package_config_id=code_package_config_id,
        package_name="aware-demo-runtime",
        language=CodeLanguage.python,
    )

    code_package, objects_by_id = (
        await snapshot_commit._build_code_package_text_snapshot_objects(  # noqa: SLF001
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name="aware-demo-runtime",
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="modules/demo/runtime/pyproject.toml",
            package_root="modules/demo/runtime",
            sources_root="modules/demo/runtime/aware_demo_runtime",
            fqn_prefix="aware_demo_runtime",
            source_texts_by_relative_path={},
            source_plans_by_relative_path={},
            unparsed_texts_by_relative_path={
                "aware_demo_runtime/client.py": "def value() -> int:\n    return 1\n",
            },
            path_roles_by_relative_path={},
            code_package_artifact_refs=(
                CodePackageArtifactRef(
                    code_package_id=code_package_id,
                    output_key="api.product_runtime_file",
                    artifact_key="runtime/client.py",
                    artifact_family="api_product_runtime",
                    artifact_role="runtime_file",
                    required_for=["workspace_revision"],
                    producer_key="aware_api.product_runtime",
                    relative_path="aware_demo_runtime/client.py",
                    digest="sha256:client",
                ),
            ),
        )
    )

    assert len(code_package.artifacts) == 1
    artifact = code_package.artifacts[0]
    assert artifact.code_package_id == code_package_id
    assert artifact.output_key == "api.product_runtime_file"
    assert artifact.artifact_key == "runtime/client.py"
    assert artifact.digest == "sha256:client"
    assert artifact.id in objects_by_id


def test_code_module_projection_portals_through_package_slot_edge() -> None:
    source = source_text(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/"
        "code_module_projection.aware"
    )

    assert "aware_code.module.CodeModule::packages CodePackage" not in source
    assert "aware_code.module.CodeModule::packages" in source
    assert "aware_code.module.CodeModuleCodePackage::code_package CodePackage" in source


def _ids_by_class_name(assertions) -> dict[str, list[UUID]]:  # noqa: ANN001
    class_name_by_id = {
        cc_id: cc.name for cc_id, cc in assertions._class_configs_by_id.items()
    }
    ids_by_class_name: dict[str, list[UUID]] = {}
    for ci in assertions.oig.class_instances:
        if ci.id is None:
            continue
        class_name = class_name_by_id.get(ci.class_config_id)
        if class_name is None:
            continue
        ids_by_class_name.setdefault(class_name, []).append(UUID(str(ci.id)))
    return ids_by_class_name


@pytest.mark.asyncio
async def test_code_module_has_no_direct_code_portal(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        assert runtime.context is not None
        idx = runtime.context.index

        opg_by_name = {str(opg.name): opg for opg in idx.ocg.object_projection_graphs}
        assert "code" not in opg_by_name
        assert "CodeModule" in opg_by_name
        assert "CodePrimitiveType" in opg_by_name

        code_module_projection_hash = _single_projection_hash_by_name(idx, "CodeModule")
        code_module_portals = (
            idx.portal_index.portals_by_source_projection_hash.get(
                code_module_projection_hash
            )
            or []
        )

        assert not any(
            portal.reference_field_name == "code" for portal in code_module_portals
        )


@pytest.mark.asyncio
async def test_code_module_portal_to_code_package_registered(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        assert runtime.context is not None
        idx = runtime.context.index

        code_module_projection_hash = _single_projection_hash_by_name(idx, "CodeModule")
        code_package_projection_hash = _single_projection_hash_by_name(
            idx, "CodePackage"
        )
        code_module_portals = (
            idx.portal_index.portals_by_source_projection_hash.get(
                code_module_projection_hash
            )
            or []
        )

        assert any(
            portal.reference_field_name == "code_package"
            and portal.target_projection_hash == code_package_projection_hash
            for portal in code_module_portals
        )


@pytest.mark.asyncio
async def test_code_package_edge_constructor_lowers_to_code_via_constructor(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        assert runtime.context is not None
        idx = runtime.context.index

        code_package_code_functions = _runtime_function_names_by_class_name(
            idx,
            "CodePackageCode",
        )
        code_functions = _runtime_function_names_by_class_name(idx, "Code")

        assert "create_via_code_package" in code_package_code_functions
        assert "create" not in code_package_code_functions
        assert "create_via_code_package_code" in code_functions
        assert "create" not in code_functions


def test_code_package_artifact_delta_plan_is_code_owned() -> None:
    from aware_code.package.artifact_delta_plan import (
        CODE_PACKAGE_ARTIFACT_DELTA_PLAN_SCHEMA,
        CodePackageArtifactAuthoritativeScope,
        CodePackageArtifactCurrentStateIndex,
        CodePackageArtifactCurrentStateRow,
        CodePackageArtifactDeltaPlan,
        code_package_artifact_delta_plan_from_refs,
    )

    code_package_id = uuid4()
    kept_ref = CodePackageArtifactRef(
        code_package_id=code_package_id,
        output_key="python.orm_runtime",
        artifact_key="models.py",
        artifact_family="python",
        artifact_role="orm_runtime",
        required_for=["workspace_revision"],
        producer_key="aware_python.orm_runtime",
        relative_path="aware_demo/models.py",
        digest="sha256:kept",
    )
    stale_ref = kept_ref.model_copy(
        update={
            "artifact_key": "stale.py",
            "relative_path": "aware_demo/stale.py",
            "digest": "sha256:stale",
        }
    )
    kept_operation = code_package_artifact_delta_plan_from_refs(
        code_package_artifact_refs=(kept_ref,),
    ).operations[0]
    stale_operation = code_package_artifact_delta_plan_from_refs(
        code_package_artifact_refs=(stale_ref,),
    ).operations[0]
    current_state = CodePackageArtifactCurrentStateIndex(
        status="hydrated_from_code_package_text_snapshot_index",
        code_package_id=str(code_package_id),
        artifacts=(
            CodePackageArtifactCurrentStateRow(
                output_key=kept_operation.output_key,
                artifact_key=kept_operation.artifact_key,
                identity_key=kept_operation.identity_key,
                signature_hash=kept_operation.signature_hash,
                artifact_family="python",
                artifact_role="orm_runtime",
                producer_key="aware_python.orm_runtime",
            ),
            CodePackageArtifactCurrentStateRow(
                output_key=stale_operation.output_key,
                artifact_key=stale_operation.artifact_key,
                identity_key=stale_operation.identity_key,
                signature_hash=stale_operation.signature_hash,
                artifact_family="python",
                artifact_role="orm_runtime",
                producer_key="aware_python.orm_runtime",
            ),
        ),
    )

    partial_plan = code_package_artifact_delta_plan_from_refs(
        code_package_artifact_refs=(kept_ref,),
        current_artifact_state=current_state,
    )
    scoped_plan = code_package_artifact_delta_plan_from_refs(
        code_package_artifact_refs=(kept_ref,),
        current_artifact_state=current_state,
        authoritative_scopes=(
            CodePackageArtifactAuthoritativeScope(
                code_package_id=str(code_package_id),
                output_key="python.orm_runtime",
                producer_key="aware_python.orm_runtime",
            ),
        ),
    )

    assert CODE_PACKAGE_ARTIFACT_DELTA_PLAN_SCHEMA == (
        "aware.code.package.artifact_delta_plan.v1"
    )
    assert partial_plan.operation_counts.delete == 0
    assert scoped_plan.operation_counts.to_payload() == {
        "create": 0,
        "refresh": 0,
        "upsert": 0,
        "noop_existing": 1,
        "delete": 1,
    }
    assert [operation.operation for operation in scoped_plan.operations] == [
        "noop_existing",
        "delete",
    ]
    assert CodePackageArtifactDeltaPlan.from_payload(scoped_plan.to_payload()) == (
        scoped_plan
    )


@pytest.mark.asyncio
async def test_code_package_text_snapshot_uses_lane_index_for_identical_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT

    from aware_code.package import snapshot_commit
    from aware_code.package.artifact_delta_plan import (
        CODE_PACKAGE_ARTIFACT_DELTA_PLAN_SCHEMA,
        artifact_identity_key,
        code_package_artifact_ref_signature_hash,
    )
    from aware_code_ontology.code.code_enums import CodeLanguage

    code_package_config_id = _source_code_package_config_id(
        manifest_kind="pyproject_toml",
        surface="runtime",
    )
    package_name = "aware_demo_runtime"
    code_package_id = stable_code_package_id(
        code_package_config_id=code_package_config_id,
        package_name=package_name,
        language=CodeLanguage.python,
    )
    artifact_ref = CodePackageArtifactRef(
        code_package_id=code_package_id,
        output_key="python.orm_runtime",
        artifact_key="runtime/client.py",
        artifact_family="python",
        artifact_role="orm_runtime",
        required_for=["workspace_revision"],
        producer_key="aware_python.orm_runtime",
        relative_path="aware_demo_runtime/client.py",
        digest="sha256:client-v1",
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        assert runtime.context is not None
        idx = runtime.context.index
        projection_hash = _single_projection_hash_by_name(idx, "CodePackage")
        branch_id = uuid4()

        first = await snapshot_commit.commit_code_package_text_snapshot(
            index=idx,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_config_id=code_package_config_id,
            package_name=package_name,
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="modules/demo/runtime/pyproject.toml",
            package_root="modules/demo/runtime/aware_demo_runtime",
            sources_root="modules/demo/runtime/aware_demo_runtime",
            fqn_prefix="aware_demo_runtime",
            source_texts_by_relative_path={},
            unparsed_texts_by_relative_path={
                "aware_demo_runtime/__init__.py": "",
                "aware_demo_runtime/client.py": "def value() -> int:\n    return 1\n",
            },
            code_package_artifact_refs=(artifact_ref,),
        )

        class _UnexpectedMaterializer:
            async def get(self, **_: object) -> object:
                raise AssertionError("identical snapshot should not hydrate HEAD OIG")

        monkeypatch.setattr(
            snapshot_commit,
            "OIGMaterializer",
            _UnexpectedMaterializer,
        )

        second = await snapshot_commit.commit_code_package_text_snapshot(
            index=idx,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_config_id=code_package_config_id,
            package_name=package_name,
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="modules/demo/runtime/pyproject.toml",
            package_root="modules/demo/runtime/aware_demo_runtime",
            sources_root="modules/demo/runtime/aware_demo_runtime",
            fqn_prefix="aware_demo_runtime",
            source_texts_by_relative_path={},
            unparsed_texts_by_relative_path={
                "aware_demo_runtime/__init__.py": "",
                "aware_demo_runtime/client.py": "def value() -> int:\n    return 1\n",
            },
            code_package_artifact_refs=(artifact_ref,),
        )
        artifact_state = (
            await snapshot_commit.load_code_package_text_snapshot_artifact_state_index(
                branch_id=branch_id,
                projection_hash=projection_hash,
                code_package_id=code_package_id,
            )
        )

    assert second.commit_id == first.commit_id
    assert second.head_commit_id == first.head_commit_id
    assert (
        second.object_instance_graph_commit_id == first.object_instance_graph_commit_id
    )
    assert second.change_count == 0
    assert second.object_count == first.object_count
    assert artifact_state is not None
    assert artifact_state["current_state_status"] == (
        "hydrated_from_code_package_text_snapshot_index"
    )
    assert artifact_state["artifact_count"] == 1
    assert artifact_state["source_snapshot_fingerprint"]
    assert artifact_state["snapshot_fingerprint"]
    assert artifact_state["head_commit_id"] == str(first.head_commit_id)
    assert artifact_state["object_instance_graph_commit_id"] == str(
        first.object_instance_graph_commit_id
    )
    artifacts = artifact_state["artifacts"]
    assert isinstance(artifacts, list)
    assert artifacts[0]["artifact_key"] == "runtime/client.py"
    assert artifacts[0]["identity_key"] == artifact_identity_key(
        output_key="python.orm_runtime",
        artifact_key="runtime/client.py",
    )
    assert artifacts[0]["signature_hash"] == (
        code_package_artifact_ref_signature_hash(artifact_ref=artifact_ref)
    )
    assert CODE_PACKAGE_ARTIFACT_DELTA_PLAN_SCHEMA == (
        "aware.code.package.artifact_delta_plan.v1"
    )


@pytest.mark.asyncio
async def test_code_package_text_snapshot_deletes_omitted_snapshot_paths(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    from aware_code.package import snapshot_commit
    from aware_code.stable_ids import (
        stable_code_id,
        stable_code_package_code_id,
        stable_code_package_id,
    )
    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_meta.graph.instance.commit.materializer import OIGMaterializer

    package_name = "aware_demo_runtime"
    code_package_config_id = _source_code_package_config_id(
        manifest_kind="pyproject_toml",
        surface="runtime",
    )
    package_id = stable_code_package_id(
        code_package_config_id=code_package_config_id,
        package_name=package_name,
        language=CodeLanguage.python,
    )
    stale_relative_path = ".aware/materializations/python.models.json"
    stale_package_code_id = stable_code_package_code_id(
        code_package_id=package_id,
        relative_path=stale_relative_path,
    )
    stale_code_id = stable_code_id(
        code_package_code_id=stale_package_code_id,
        relative_path=stale_relative_path,
    )
    kept_relative_path = "aware_demo_runtime/__init__.py"
    kept_package_code_id = stable_code_package_code_id(
        code_package_id=package_id,
        relative_path=kept_relative_path,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        assert runtime.context is not None
        idx = runtime.context.index
        projection_hash = _single_projection_hash_by_name(idx, "CodePackage")
        branch_id = uuid4()

        await snapshot_commit.commit_code_package_text_snapshot(
            index=idx,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_config_id=code_package_config_id,
            package_name=package_name,
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="modules/demo/runtime/pyproject.toml",
            package_root="modules/demo/runtime",
            sources_root="modules/demo/runtime/aware_demo_runtime",
            fqn_prefix="aware_demo_runtime",
            source_texts_by_relative_path={},
            unparsed_texts_by_relative_path={
                kept_relative_path: "",
                stale_relative_path: "{}\n",
            },
        )

        second = await snapshot_commit.commit_code_package_text_snapshot(
            index=idx,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_config_id=code_package_config_id,
            package_name=package_name,
            language=CodeLanguage.python,
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="modules/demo/runtime/pyproject.toml",
            package_root="modules/demo/runtime",
            sources_root="modules/demo/runtime/aware_demo_runtime",
            fqn_prefix="aware_demo_runtime",
            source_texts_by_relative_path={},
            unparsed_texts_by_relative_path={kept_relative_path: ""},
        )

        oig, _ = await OIGMaterializer().get(
            branch_id=branch_id,
            ocg=idx.ocg,
            opg=idx.opg_by_hash[projection_hash],
            commit_id=None,
            attribute_configs_by_id=idx.attribute_configs_by_id,
            class_configs_by_id=idx.class_configs_by_id,
        )

    source_object_ids = {
        class_instance.source_object_id
        for class_instance in oig.class_instances
        if class_instance.source_object_id is not None
    }
    assert second.change_count > 0
    assert kept_package_code_id in source_object_ids
    assert stale_package_code_id not in source_object_ids
    assert stale_code_id not in source_object_ids


@pytest.mark.asyncio
async def test_code_package_text_snapshot_resets_when_package_root_changes(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    from aware_code.package import snapshot_commit
    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_meta.graph.instance.commit.fs_store import FSCommitStore

    legacy_config_id = _source_code_package_config_id(
        manifest_kind="aware_toml",
        surface="runtime",
    )
    node_config_id = _source_code_package_config_id(
        manifest_kind="aware_node_toml",
        surface="runtime",
    )
    expected_node_package_id = stable_code_package_id(
        code_package_config_id=node_config_id,
        package_name="aware-network-ontology-authority-node",
        language=CodeLanguage.aware,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        assert runtime.context is not None
        idx = runtime.context.index
        projection_hash = _single_projection_hash_by_name(idx, "CodePackage")
        branch_id = uuid4()

        legacy = await snapshot_commit.commit_code_package_text_snapshot(
            index=idx,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_config_id=legacy_config_id,
            package_name="legacy-node-source",
            language=CodeLanguage.aware,
            surface="runtime",
            manifest_kind="aware_toml",
            manifest_relative_path="nodes/legacy/aware.node.toml",
            package_root="nodes/legacy",
            sources_root="nodes",
            fqn_prefix="legacy_node",
            source_texts_by_relative_path={
                "aware.node.toml": "aware_node = 1\n",
            },
        )
        current = await snapshot_commit.commit_code_package_text_snapshot(
            index=idx,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_config_id=node_config_id,
            package_name="aware-network-ontology-authority-node",
            language=CodeLanguage.aware,
            surface="runtime",
            manifest_kind="aware_node_toml",
            manifest_relative_path=(
                "modules/node/nodes/aware_network_ontology_authority/aware.node.toml"
            ),
            package_root="modules/node/nodes/aware_network_ontology_authority",
            sources_root="modules/node/nodes/aware_network_ontology_authority/nodes",
            fqn_prefix="aware_network_ontology_authority_node",
            source_texts_by_relative_path={
                "aware.node.toml": "aware_node = 1\n",
            },
        )

        head = await FSCommitStore().head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        assert head is not None
        assert head.get("root_object_id") == str(expected_node_package_id)

    assert legacy.code_package.id != current.code_package.id
    assert current.code_package.id == expected_node_package_id
    assert current.commit_id != legacy.commit_id


@pytest.mark.asyncio
async def test_code_package_text_snapshot_revisits_prior_graph_state_with_new_parent(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    from aware_code.package import snapshot_commit
    from aware_code_ontology.code.code_enums import CodeLanguage

    code_package_config_id = _source_code_package_config_id(
        manifest_kind="pyproject_toml",
        surface="runtime",
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        assert runtime.context is not None
        idx = runtime.context.index
        projection_hash = _single_projection_hash_by_name(idx, "CodePackage")
        branch_id = uuid4()
        common_kwargs = {
            "index": idx,
            "actor_id": None,
            "branch_id": branch_id,
            "projection_hash": projection_hash,
            "code_package_config_id": code_package_config_id,
            "package_name": "aware_demo_runtime",
            "language": CodeLanguage.python,
            "surface": "runtime",
            "manifest_kind": "pyproject_toml",
            "manifest_relative_path": "modules/demo/runtime/pyproject.toml",
            "package_root": "modules/demo/runtime",
            "sources_root": "modules/demo/runtime/aware_demo_runtime",
            "fqn_prefix": "aware_demo_runtime",
            "source_texts_by_relative_path": {},
        }

        first = await snapshot_commit.commit_code_package_text_snapshot(
            **common_kwargs,
            unparsed_texts_by_relative_path={
                "aware_demo_runtime/client.py": "def value() -> int:\n    return 1\n",
            },
        )
        second = await snapshot_commit.commit_code_package_text_snapshot(
            **common_kwargs,
            unparsed_texts_by_relative_path={
                "aware_demo_runtime/client.py": "def value() -> int:\n    return 2\n",
            },
        )
        third = await snapshot_commit.commit_code_package_text_snapshot(
            **common_kwargs,
            unparsed_texts_by_relative_path={
                "aware_demo_runtime/client.py": "def value() -> int:\n    return 1\n",
            },
        )

    assert second.commit_id != first.commit_id
    assert third.commit_id != first.commit_id
    assert third.head_commit_id == third.commit_id
    assert third.change_count > 0


@pytest.mark.asyncio
async def test_code_module_build_and_dependency_stays_group_only(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    from aware_code.stable_ids import (
        stable_code_module_dependence_id,
        stable_code_module_id,
    )

    module_name = "workspace_module"
    expected_module_id = stable_code_module_id(name=module_name)
    dependency_name = "shared_util"
    expected_dependency_id = stable_code_module_dependence_id(
        code_module_id=expected_module_id,
        name=dependency_name,
    )
    expected_target_module_id = stable_code_module_id(name=dependency_name)

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        lane = LaneIds(branch_id=uuid4(), actor_id=uuid4())
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="CodeModule",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn="aware_code.module.CodeModule",
                    function_name="build",
                    kwargs={
                        "name": module_name,
                        "languages": ["aware"],
                        "aware_module_version": 1,
                        "manifest_relative_path": "aware.module.toml",
                        "manifest_hash": "sha256:module",
                    },
                    expected_root_object_id=expected_module_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn="aware_code.module.CodeModule",
                    function_name="create_dependency",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={"name": dependency_name},
                ),
            ],
        )

        assert result.root_object_id == expected_module_id
        assertions.expect_root(expected_module_id)
        assertions.expect_instance(expected_module_id)
        assertions.expect_primitive(
            instance_id=expected_module_id,
            field_name="name",
            expected=module_name,
        )
        assertions.expect_primitive(
            instance_id=expected_module_id,
            field_name="aware_module_version",
            expected=1,
        )
        assertions.expect_primitive(
            instance_id=expected_module_id,
            field_name="manifest_relative_path",
            expected="aware.module.toml",
        )
        assertions.expect_primitive(
            instance_id=expected_module_id,
            field_name="manifest_hash",
            expected="sha256:module",
        )

        ids_by_class = _ids_by_class_name(assertions)
        assert not ids_by_class.get("Code", [])
        assert not ids_by_class.get("CodeModuleCode", [])
        assert not ids_by_class.get("CodePackage", [])
        assertions.expect_instance(expected_dependency_id)
        assertions.expect_edge(
            source_id=expected_module_id,
            target_id=expected_dependency_id,
            relationship_name="dependences",
        )
        assertions.expect_primitive(
            instance_id=expected_dependency_id,
            field_name="dependence_id",
            expected=expected_target_module_id,
        )


def test_code_package_config_create_package_uses_config_scoped_identity() -> None:
    from aware_code.stable_ids import (
        stable_code_package_id,
    )

    manifest_relative_path = "structure/ontology/aware.toml"
    package_name = "aware_workspace_package_ontology"
    config_key = code_package_source_config_key(
        manifest_kind="aware_toml",
        surface="structure",
    )
    expected_config_id = stable_code_package_config_id(config_key=config_key)
    expected_package_id = stable_code_package_id(
        code_package_config_id=expected_config_id,
        package_name=package_name,
        language="aware",
    )
    legacy_package_id = stable_code_package_id(
        package_name=package_name,
        language="aware",
    )
    handler_keys = {
        (key.owner_class_fqn, key.function_name, key.is_constructor)
        for key in code_meta_handlers.AWARE_META_GRAPH_HANDLERS
    }

    assert expected_package_id != legacy_package_id
    assert expected_config_id == _source_code_package_config_id(
        manifest_kind="aware_toml",
        surface="structure",
    )
    assert manifest_relative_path == "structure/ontology/aware.toml"
    assert (
        "aware_code.package.CodePackageConfig",
        "build",
        True,
    ) in handler_keys
    assert (
        "aware_code.package.CodePackageConfig",
        "create_package",
        False,
    ) in handler_keys
    assert (
        "aware_code.package.CodePackage",
        "build_via_code_package_config",
        True,
    ) in handler_keys


def test_code_package_config_resolution_does_not_infer_manifest_kind_from_filename(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_code.handlers.impl.package import code_package as code_package_handler
    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_code_ontology.package.code_package import CodePackage

    class _MissingConfigSession:
        def imap_get(self, *_: object) -> object | None:
            return None

    code_package = CodePackage(
        id=uuid4(),
        code_package_config_id=uuid4(),
        package_name="aware_demo_runtime",
        language=CodeLanguage.python,
        manifest_relative_path="modules/demo/runtime/pyproject.toml",
        package_root="modules/demo/runtime",
        sources_root="modules/demo/runtime/aware_demo_runtime",
        fqn_prefix="aware_demo_runtime",
    )
    monkeypatch.setattr(
        code_package_handler,
        "current_handler_session",
        lambda: _MissingConfigSession(),
    )

    with pytest.raises(RuntimeError, match="must not be inferred"):
        code_package_handler._resolve_code_package_config(code_package)

    source = Path(code_package_handler.__file__).read_text(encoding="utf-8")
    assert "_infer_manifest_kind_from_filename" not in source
    assert "pyproject_toml" not in source


def test_code_package_instance_function_surface_stays_package_owned() -> None:
    handler_keys = {
        (key.owner_class_fqn, key.function_name, key.is_constructor)
        for key in code_meta_handlers.AWARE_META_GRAPH_HANDLERS
    }

    assert (
        "aware_code.package.CodePackage",
        "build",
        True,
    ) not in handler_keys
    assert (
        "aware_code.package.CodePackage",
        "build_via_code_package_config",
        True,
    ) in handler_keys
    assert (
        "aware_code.package.CodePackage",
        "read_code_text",
        False,
    ) not in handler_keys
    for function_name in (
        "create_code",
        "create_code_from_text",
        "delete_code",
    ):
        assert (
            "aware_code.package.CodePackage",
            function_name,
            False,
        ) in handler_keys
