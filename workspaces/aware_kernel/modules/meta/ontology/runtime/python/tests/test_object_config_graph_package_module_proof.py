from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from aware_code.stable_ids import (
    code_package_generated_config_key,
    code_package_source_config_key,
)
from aware_meta.handlers._generated import meta_handlers
from aware_meta.runtime import build_meta_graph_runtime_for_aware_package_manifests
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    MultiLaneProofCall,
    ProofCall,
    run_multi_lane_meta_runtime_proof,
)
from _meta_runtime_test_paths import META_PACKAGE_MANIFEST_PATHS, REPO_ROOT


OBJECT_CONFIG_GRAPH_FQN = "aware_meta.graph.config.ObjectConfigGraph"
OBJECT_CONFIG_GRAPH_PACKAGE_FQN = "aware_meta.graph.config.ObjectConfigGraphPackage"


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


def test_aware_toml_language_materialization_accepts_stable_id_policy(
    tmp_path: Path,
) -> None:
    from aware_meta.manifest.loader import load_aware_toml_spec

    toml_path = tmp_path / "aware.toml"
    toml_path.write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-state"',
                'fqn_prefix = "aware_demo_state"',
                'kind = "state"',
                "",
                "[build]",
                'environment_slug = "demo_state"',
                "",
                "[[language_materializations]]",
                'role = "local_state_python"',
                'language = "python"',
                'output_dir = "python"',
                'import_root = "aware_demo_state"',
                'package_name = "demo-state"',
                'stable_ids_import_root = "aware_demo_state"',
                'stable_ids_resolution_policy = "class_strict"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    spec = load_aware_toml_spec(toml_path=toml_path)

    assert spec.language_materializations[0].stable_ids_resolution_policy == (
        "class_strict"
    )


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
async def test_object_config_graph_package_module_proof(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_code_ontology  # noqa: F401
    import aware_content_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    import aware_storage_ontology  # noqa: F401
    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_code_ontology.stable_ids import (
        stable_code_package_config_id,
        stable_code_package_id,
    )
    from aware_meta.materialization.service import (
        _build_object_config_graph_package_snapshot_root,
    )
    from aware_meta_ontology.graph.config.object_config_graph_package import (
        ObjectConfigGraphPackage,
    )
    from aware_meta_ontology.graph.config.object_config_graph_package_language_materialization import (
        ObjectConfigGraphPackageLanguageMaterialization,
    )
    from aware_meta_ontology.graph.config.object_config_graph_package_language_materialization_package import (
        ObjectConfigGraphPackageLanguageMaterializationPackage,
    )
    from aware_meta_ontology.stable_ids import (
        stable_object_config_graph_id,
        stable_object_config_graph_package_id,
        stable_object_config_graph_package_language_materialization_package_id,
    )

    source_package_name = "aware_meta_test_source_package"
    object_config_graph_name = "meta_test_package_graph"
    object_config_graph_hash = "meta_test_package_graph_hash"
    object_config_graph_fqn_prefix = "aware.meta.test.ocg_package"
    package_name = "aware_meta_test_ocg_package"
    title = "Meta Test OCG Package"
    description = "Meta package proof for source-code and graph portal truth"

    source_code_package_config_id = stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_toml",
            surface="structure",
        ),
    )
    source_code_package_id = stable_code_package_id(
        code_package_config_id=source_code_package_config_id,
        package_name=source_package_name,
        language="aware",
    )
    object_config_graph_id = stable_object_config_graph_id(
        fqn_prefix=object_config_graph_fqn_prefix,
        language="aware",
    )
    object_config_graph_package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=object_config_graph_fqn_prefix,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        idx = runtime.context.index
        opg_names = {(opg.name or "").strip() for opg in idx.opg_by_hash.values()}
        assert "ObjectConfigGraph" in opg_names
        assert "ObjectConfigGraphPackage" in opg_names

        lane = LaneIds(environment_id=uuid4(), process_id=uuid4(), thread_id=uuid4())
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
                            "name": object_config_graph_name,
                            "hash": object_config_graph_hash,
                            "fqn_prefix": object_config_graph_fqn_prefix,
                            "language": "aware",
                            "object_config_graph_id": object_config_graph_id,
                            "description": "Meta OCG package proof graph",
                        },
                        expected_root_object_id=object_config_graph_id,
                    ),
                ),
                MultiLaneProofCall(
                    opg_name="ObjectConfigGraphPackage",
                    call=ProofCall(
                        target="constructor",
                        class_fqn=OBJECT_CONFIG_GRAPH_PACKAGE_FQN,
                        function_name="build",
                        kwargs={
                            "package_name": package_name,
                            "fqn_prefix": object_config_graph_fqn_prefix,
                            "source_code_package_id": source_code_package_id,
                            "object_config_graph_id": object_config_graph_id,
                            "object_config_graph_package_id": object_config_graph_package_id,
                            "title": title,
                            "description": description,
                        },
                        expected_root_object_id=object_config_graph_package_id,
                    ),
                ),
            ],
        )

        result = results["ObjectConfigGraphPackage"]
        assertions = assertions_by_opg["ObjectConfigGraphPackage"]
        assert result.root_object_id == object_config_graph_package_id
        assertions.expect_root(object_config_graph_package_id)
        assertions.expect_instance(object_config_graph_package_id)
        assertions.expect_primitive(
            instance_id=object_config_graph_package_id,
            field_name="package_name",
            expected=package_name,
        )
        assertions.expect_primitive(
            instance_id=object_config_graph_package_id,
            field_name="fqn_prefix",
            expected=object_config_graph_fqn_prefix,
        )
        assertions.expect_primitive(
            instance_id=object_config_graph_package_id,
            field_name="title",
            expected=title,
        )
        assertions.expect_primitive(
            instance_id=object_config_graph_package_id,
            field_name="description",
            expected=description,
        )

        ids_by_class = _ids_by_class_name(assertions)
        assert ids_by_class.get("ObjectConfigGraphPackage", [])

        class_configs_by_name = {
            cc.name: cc
            for cc in assertions._class_configs_by_id.values()  # noqa: SLF001
            if cc.name is not None
        }
        assert "CodePackage" in class_configs_by_name
        assert "ObjectConfigGraph" in class_configs_by_name
        package_class_config = class_configs_by_name["ObjectConfigGraphPackage"]
        source_code_package_class_config = class_configs_by_name["CodePackage"]
        object_config_graph_class_config = class_configs_by_name["ObjectConfigGraph"]
        language_materialization_class_config = class_configs_by_name[
            "ObjectConfigGraphPackageLanguageMaterialization"
        ]
        language_materialization_package_class_config = class_configs_by_name[
            "ObjectConfigGraphPackageLanguageMaterializationPackage"
        ]
        assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=package_class_config.id,
            target_class_config_id=source_code_package_class_config.id,
            relationship_name="source_code_package",
        )
        assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=package_class_config.id,
            target_class_config_id=object_config_graph_class_config.id,
            relationship_name="object_config_graph",
        )
        assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=package_class_config.id,
            target_class_config_id=language_materialization_class_config.id,
            relationship_name="language_materializations",
        )
        assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=language_materialization_class_config.id,
            target_class_config_id=language_materialization_package_class_config.id,
            relationship_name="materialized_packages",
        )
        assertions._resolve_relationship_id_by_name(  # noqa: SLF001
            source_class_config_id=language_materialization_package_class_config.id,
            target_class_config_id=source_code_package_class_config.id,
            relationship_name="code_package",
        )

        payload = result.responses[-1].payload
        assert isinstance(payload, dict)
        if "value" in payload:
            payload = payload["value"]
        assert isinstance(payload, dict)
        created = ObjectConfigGraphPackage.model_validate(payload)
        assert created.id == object_config_graph_package_id
        assert created.package_name == package_name
        assert created.fqn_prefix == object_config_graph_fqn_prefix
        assert created.source_code_package_id == source_code_package_id
        assert created.object_config_graph_id == object_config_graph_id
        target = ObjectConfigGraphPackageLanguageMaterialization.model_validate(
            {
                "target_key": f"{package_name}:local_state_sqlite",
                "role": "local_state_sqlite",
                "language": "sql",
                "output_dir": "sqlite",
                "import_root": "aware_meta_test_sqlite",
                "package_name": "aware-meta-test-sqlite",
                "materialization_source": "ontology",
                "renderer_kind": "sqlite",
                "renderer_profile": "orm_models",
                "stable_ids_import_root": "aware_meta_test",
                "source_is_runtime": False,
                "object_config_graph_package_id": object_config_graph_package_id,
            }
        )
        assert target.language == CodeLanguage.sql
        assert target.renderer_kind == "sqlite"
        generated_code_package_config_id = stable_code_package_config_id(
            config_key=code_package_generated_config_key(
                materialization_source="ontology",
                renderer_kind="sqlite",
                language=CodeLanguage.sql,
                surface="structure",
                manifest_kind="generated_materialization",
            ),
        )
        generated_code_package_id = stable_code_package_id(
            code_package_config_id=generated_code_package_config_id,
            package_name="aware-meta-test-sqlite",
            language="sql",
        )
        materialized_package = ObjectConfigGraphPackageLanguageMaterializationPackage.model_validate(
            {
                "id": stable_object_config_graph_package_language_materialization_package_id(
                    code_package_id=generated_code_package_id,
                ),
                "object_config_graph_package_language_materialization_id": target.id,
                "code_package_id": generated_code_package_id,
                "package_output_key": "language_package",
                "package_name": "aware-meta-test-sqlite",
                "language": "sql",
                "output_dir": "sqlite",
                "package_root": "workspaces/aware_kernel/modules/meta/ontology/structure/sqlite",
                "sources_root": None,
                "import_root": "aware_meta_test_sqlite",
                "materialization_source": "ontology",
                "renderer_kind": "sqlite",
                "renderer_profile": "orm_models",
                "object_config_graph_object_instance_graph_commit_id": None,
                "code_package_object_instance_graph_commit_id": None,
                "status": "declared",
            }
        )
        assert materialized_package.code_package_id == generated_code_package_id
        assert materialized_package.language == CodeLanguage.sql

        generated_code_package_oig_commit_id = uuid4()
        realized_package_root, _ = _build_object_config_graph_package_snapshot_root(
            object_config_graph_package_id=object_config_graph_package_id,
            package_name=package_name,
            fqn_prefix=object_config_graph_fqn_prefix,
            source_code_package_id=source_code_package_id,
            object_config_graph_id=object_config_graph_id,
            object_config_graph_object_instance_graph_commit_id=uuid4(),
            function_impl_ownership="compiler",
            function_impl_parity_policy="error",
            implementation_policy_source="aware_toml",
            title=title,
            description=description,
            language_materialization_specs=(target,),
            package_root=Path("workspaces/aware_kernel/modules/meta/ontology/structure"),
            workspace_root=Path("."),
            language_materialization_package_realizations={
                generated_code_package_id: {
                    "schema": "aware.meta.language_materialization.code_package_ref.v1",
                    "object_config_graph_package_id": str(
                        object_config_graph_package_id
                    ),
                    "code_package_id": str(generated_code_package_id),
                    "code_package_object_instance_graph_commit_id": str(
                        generated_code_package_oig_commit_id
                    ),
                    "package_name": "aware-meta-test-sqlite",
                    "package_root": "workspaces/aware_kernel/modules/meta/ontology/structure/sqlite",
                    "sources_root": None,
                },
            },
        )
        realized_materialized_package = realized_package_root.language_materializations[
            0
        ].materialized_packages[0]
        assert realized_materialized_package.status == "materialized"
        assert (
            realized_materialized_package.code_package_object_instance_graph_commit_id
            == generated_code_package_oig_commit_id
        )


@pytest.mark.asyncio
async def test_language_materialization_output_commits_generated_code_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_code_ontology.code.code_plan import (
        CodePackageDelta,
        CodePackageDeltaKind,
        CodePackagePathRole,
    )
    from aware_code_ontology.stable_ids import (
        stable_code_package_config_id,
        stable_code_package_id,
    )
    from aware_meta.materialization import workspace_provider
    from aware_meta.materialization.workspace_provider import (
        _LanguageMaterializationTarget,
        _commit_language_materialization_code_packages,
    )

    workspace_root = tmp_path / "workspace"
    output_root = workspace_root / "sdks" / "workspace" / "db" / "sqlite"
    aware_root = output_root / "_aware"
    aware_root.mkdir(parents=True)
    schema_contract = aware_root / "sqlite_orm_schema_contract.json"
    schema_contract.write_text('{"schema":"test"}\n', encoding="utf-8")
    sql_file = output_root / "status" / "local_workspace_status_baseline.sql"
    sql_file.parent.mkdir(parents=True)
    sql_file.write_text(
        "create table local_workspace_status_baseline(id text);\n", encoding="utf-8"
    )

    captured: dict[str, object] = {}
    generated_code_package_config_id = stable_code_package_config_id(
        config_key=code_package_generated_config_key(
            materialization_source="ontology",
            renderer_kind="sqlite",
            language=CodeLanguage.sql,
            surface="runtime",
            manifest_kind="generated_materialization",
        ),
    )
    generated_code_package_id = stable_code_package_id(
        code_package_config_id=generated_code_package_config_id,
        package_name="workspace-sdk-db-sqlite",
        language="sql",
    )
    generated_commit_id = uuid4()
    generated_head_commit_id = uuid4()
    generated_oig_commit_id = uuid4()

    async def fake_commit_code_package_text_snapshot(**kwargs):  # noqa: ANN003, ANN202
        captured.update(kwargs)
        return SimpleNamespace(
            code_package=SimpleNamespace(id=generated_code_package_id),
            commit_id=generated_commit_id,
            head_commit_id=generated_head_commit_id,
            object_instance_graph_commit_id=generated_oig_commit_id,
            object_count=2,
            change_count=2,
        )

    monkeypatch.setattr(
        workspace_provider,
        "commit_code_package_text_snapshot",
        fake_commit_code_package_text_snapshot,
    )
    monkeypatch.setattr(
        workspace_provider,
        "find_meta_graph_projection_hash_by_name",
        lambda *, index, projection_name: "code-package-projection",
    )

    object_config_graph_package_id = uuid4()
    object_config_graph_oig_commit_id = uuid4()
    outputs = await _commit_language_materialization_code_packages(
        request=SimpleNamespace(
            index=object(),
            actor_id=uuid4(),
            workspace_root=workspace_root,
            context={},
        ),
        leaf_result=SimpleNamespace(
            object_config_graph_package=SimpleNamespace(
                id=object_config_graph_package_id
            ),
            object_config_graph_object_instance_graph_commit_id=object_config_graph_oig_commit_id,
        ),
        target=_LanguageMaterializationTarget(
            target_language_plugin_id=CodeLanguage.sql,
            output_root=output_root,
            import_root="aware_workspace_sdk_local",
            package_name="workspace-sdk-db-sqlite",
            materialization_source="ontology",
            code_package_surface="runtime",
            renderer_profile="orm_models",
            renderer_kind="sqlite",
        ),
        result=SimpleNamespace(
            package_outputs=(
                SimpleNamespace(
                    package_name="workspace-sdk-db-sqlite",
                    output_root=output_root,
                    import_root="aware_workspace_sdk_local",
                    generated_file_refs=(schema_contract, sql_file),
                    deleted_file_refs=(Path("status/stale_workspace_status.sql"),),
                ),
            )
        ),
    )
    refs = tuple(outputs)

    assert len(refs) == 1
    assert (
        refs[0]["schema"] == "aware.meta.language_materialization.code_package_ref.v1"
    )
    assert refs[0]["code_package_id"] == str(generated_code_package_id)
    assert refs[0]["code_package_commit_id"] == str(generated_commit_id)
    assert refs[0]["code_package_head_commit_id"] == str(generated_head_commit_id)
    assert refs[0]["code_package_object_instance_graph_commit_id"] == str(
        generated_oig_commit_id
    )
    assert refs[0]["manifest_kind"] == "generated_materialization"
    assert refs[0]["manifest_relative_path"] == (
        "sdks/workspace/db/sqlite/_aware/sqlite_orm_schema_contract.json"
    )
    assert refs[0]["path_count"] == 3
    assert refs[0]["delete_path_count"] == 1
    assert len(outputs.deltas) == 1
    delta = CodePackageDelta.model_validate(outputs.deltas[0])
    assert delta.package_name == "workspace-sdk-db-sqlite"
    assert delta.package_root == "sdks/workspace/db/sqlite"
    assert delta.manifest_relative_path == (
        "sdks/workspace/db/sqlite/_aware/sqlite_orm_schema_contract.json"
    )
    assert {path.relative_path for path in delta.paths} == {
        "_aware/sqlite_orm_schema_contract.json",
        "status/local_workspace_status_baseline.sql",
        "status/stale_workspace_status.sql",
    }
    assert {path.relative_path: path.kind for path in delta.paths} == {
        "_aware/sqlite_orm_schema_contract.json": CodePackageDeltaKind.update,
        "status/local_workspace_status_baseline.sql": CodePackageDeltaKind.update,
        "status/stale_workspace_status.sql": CodePackageDeltaKind.delete,
    }
    assert delta.production is not None
    assert delta.production.producer.provider_key == "aware_meta"
    assert delta.production.producer.provider_payload is not None
    assert delta.production.producer.provider_payload["output_key"] == (
        "generated_language_code_package_deltas"
    )

    assert captured["package_name"] == "workspace-sdk-db-sqlite"
    assert captured["language"] == CodeLanguage.sql
    assert captured["manifest_kind"] == "generated_materialization"
    assert captured["manifest_relative_path"] == (
        "sdks/workspace/db/sqlite/_aware/sqlite_orm_schema_contract.json"
    )
    assert captured["package_root"] == "sdks/workspace/db/sqlite"
    assert captured["sources_root"] is None
    assert captured["projection_hash"] == "code-package-projection"
    assert captured["source_texts_by_relative_path"] == {}
    assert captured["path_roles_by_relative_path"] == {
        "_aware/sqlite_orm_schema_contract.json": CodePackagePathRole.generated_metadata,
        "status/local_workspace_status_baseline.sql": CodePackagePathRole.generated_code,
    }


def test_generated_package_texts_include_package_inventory(
    tmp_path: Path,
) -> None:
    from aware_meta.materialization.workspace_provider import (
        _generated_package_texts_by_relative_path,
    )

    workspace_root = tmp_path / "workspace"
    output_root = workspace_root / "modules" / "storage" / "generated"
    package_root = output_root / "aware_storage_ontology"
    cache_root = package_root / "__pycache__"
    aware_root = package_root / "_aware"
    private_materialization_root = output_root / ".aware" / "materializations"
    package_root.mkdir(parents=True)
    cache_root.mkdir()
    aware_root.mkdir()
    private_materialization_root.mkdir(parents=True)

    pyproject = output_root / "pyproject.toml"
    init_file = package_root / "__init__.py"
    py_typed = package_root / "py.typed"
    generated = package_root / "bucket.py"
    metadata = aware_root / "python.bootstrap.json"
    private_materialization = private_materialization_root / "python.models.json"
    pycache = cache_root / "bucket.cpython-312.pyc"
    binary = output_root / "artifact.msgpack"

    pyproject.write_text(
        '[project]\nname = "aware-storage-ontology"\n', encoding="utf-8"
    )
    init_file.write_text("", encoding="utf-8")
    py_typed.write_text("", encoding="utf-8")
    generated.write_text("class StorageBucket: ...\n", encoding="utf-8")
    metadata.write_text("{}\n", encoding="utf-8")
    private_materialization.write_text("{}\n", encoding="utf-8")
    pycache.write_bytes(b"\x00\x01")
    binary.write_bytes(b"\x80\x81")

    texts = _generated_package_texts_by_relative_path(
        package_output=SimpleNamespace(
            generated_file_refs=(generated, private_materialization),
        ),
        output_root=output_root,
        workspace_root=workspace_root,
    )

    assert texts == {
        "aware_storage_ontology/__init__.py": "",
        "aware_storage_ontology/_aware/python.bootstrap.json": "{}\n",
        "aware_storage_ontology/bucket.py": "class StorageBucket: ...\n",
        "aware_storage_ontology/py.typed": "",
        "pyproject.toml": '[project]\nname = "aware-storage-ontology"\n',
    }
