from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, cast
from uuid import UUID, uuid4

import pytest
from aware_api_runtime.handlers._generated import meta_handlers as api_meta_handlers
from aware_api_runtime.snapshots.commit import (
    commit_api_package_manifest_snapshot,
)
from aware_code.types import JsonArray, JsonObject
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
    find_meta_graph_projection_hash_by_name,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot,
    MetaOIGAssertions,
)
from _api_runtime_test_paths import (
    API_META_PACKAGE_MANIFEST_PATHS,
    API_META_PYTHON_ROOTS,
    REPO_ROOT,
)


_API_META_HANDLERS_ANY: Any = api_meta_handlers
_API_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _API_META_HANDLERS_ANY,
)
_API_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _API_META_HANDLERS_ANY,
)


def _api_meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return API_META_PACKAGE_MANIFEST_PATHS


def _api_meta_python_roots(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return API_META_PYTHON_ROOTS


def _prepend_api_meta_python_roots(
    *,
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    syspath_prepend = cast(Callable[[str], None], monkeypatch.syspath_prepend)
    for python_root in _api_meta_python_roots(repo_root):
        if python_root.exists():
            syspath_prepend(str(python_root))


def _build_api_meta_runtime(*, repo_root: Path, aware_root: Path) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_api_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_API_META_HANDLER_MODULE,),
        bootstrap_modules=(_API_META_BOOTSTRAP_MODULE,),
    )
    assert runtime.context is not None
    return runtime


async def _assertions_for_committed_head(
    *,
    runtime_index,
    branch_id: UUID,
    projection_hash: str,
) -> MetaOIGAssertions:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head is not None
    assert head.get("commit_id")
    assert head.get("object_instance_graph_id")
    opg = runtime_index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=runtime_index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        oig_id=UUID(str(head["object_instance_graph_id"])),
        attribute_configs_by_id=runtime_index.attribute_configs_by_id,
        class_configs_by_id=runtime_index.class_configs_by_id,
    )
    return MetaOIGAssertions(oig=oig, index=runtime_index)


@pytest.mark.asyncio
async def test_api_package_module_proof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = REPO_ROOT
    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_api_ontology  # noqa: F401
    import aware_code_ontology  # noqa: F401
    from aware_api_ontology.stable_ids import (
        stable_api_id,
        stable_api_package_id,
    )
    from aware_code.semantic_contract_config import source_code_package_config_ref
    from aware_code_ontology.stable_ids import stable_code_package_id

    api_name = "home-devices"
    source_package_name = "aware_api_test_source_package"
    source_code_package_config_id = source_code_package_config_ref(
        manifest_kind="aware_api_toml",
        surface="api",
    ).config_id
    source_code_package_id = stable_code_package_id(
        code_package_config_id=source_code_package_config_id,
        package_name=source_package_name,
        language="aware",
    )
    expected_api_id = stable_api_id(name=api_name)
    expected_api_package_id = stable_api_package_id(name=api_name)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_api_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        runtime_context = runtime.context
        assert runtime_context is not None
        runtime_index = runtime_context.index
        api_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="ApiPackage",
        )
        branch_id = uuid4()

        result = await commit_api_package_manifest_snapshot(
            index=runtime_index,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=api_package_projection_hash,
            package_name=api_name,
            api_id=expected_api_id,
            api_object_instance_graph_commit_id=None,
            source_code_package_id=source_code_package_id,
            fqn_prefix="aware_home_devices_api",
            version_number=6,
            title="Home Devices API",
            description="ApiPackage manifest truth proof",
            aware_api_version=1,
            manifest_relative_path="aware.api.toml",
            package_root=".",
            sources_root="apis",
            include_paths=JsonArray(["**/*.aware"]),
            exclude_paths=JsonArray(["**/*.draft.aware"]),
            force_fresh_scan=True,
            compilation_mode="api_ontology",
            dependencies=JsonArray(
                [
                    {
                        "package_name": "aware-home-ontology",
                        "version_number": 2,
                    }
                ]
            ),
            targets=JsonObject(
                {
                    "python": {
                        "root_dir": "apis/home/python",
                        "public_package": {
                            "package_dir": "aware_home_devices_api",
                            "root_dir": "apis/home/python/public",
                        },
                        "service_protocol": {
                            "package_dir": ("aware_home_devices_api_service_protocol"),
                            "root_dir": "apis/home/python/service_protocol",
                        },
                    }
                }
            ),
        )

        assert result.api_package.id == expected_api_package_id
        assert result.commit_id == result.head_commit_id
        assert result.object_count == 1
        assert result.change_count > 0

        assertions = await _assertions_for_committed_head(
            runtime_index=runtime_index,
            branch_id=branch_id,
            projection_hash=api_package_projection_hash,
        )
        assertions.expect_root(expected_api_package_id)
        assertions.expect_instance(expected_api_package_id)
        assertions.expect_primitive(
            instance_id=expected_api_package_id,
            field_name="name",
            expected=api_name,
        )
        assertions.expect_primitive(
            instance_id=expected_api_package_id,
            field_name="manifest_relative_path",
            expected="aware.api.toml",
        )
        assertions.expect_primitive(
            instance_id=expected_api_package_id,
            field_name="compilation_mode",
            expected="api_ontology",
        )
        api_fk_value = assertions.primitive(
            instance_id=expected_api_package_id,
            field_name="api_id",
        )
        assert api_fk_value in {expected_api_id, str(expected_api_id)}
        source_code_package_fk_value = assertions.primitive(
            instance_id=expected_api_package_id,
            field_name="source_code_package_id",
        )
        assert source_code_package_fk_value in {
            source_code_package_id,
            str(source_code_package_id),
        }

        created = result.api_package
        assert created.id == expected_api_package_id
        assert created.name == api_name
        assert created.api_id == expected_api_id
        assert created.source_code_package_id == source_code_package_id
        assert created.fqn_prefix == "aware_home_devices_api"
        assert created.version_number == 6
        assert created.title == "Home Devices API"
        assert created.description == "ApiPackage manifest truth proof"
        assert created.aware_api_version == 1
        assert created.manifest_relative_path == "aware.api.toml"
        assert created.package_root == "."
        assert created.sources_root == "apis"
        assert list(created.include_paths) == ["**/*.aware"]
        assert list(created.exclude_paths) == ["**/*.draft.aware"]
        assert created.force_fresh_scan is True
        assert created.compilation_mode == "api_ontology"
        assert list(created.dependencies) == [
            {"package_name": "aware-home-ontology", "version_number": 2}
        ]
        assert dict(created.targets) == {
            "python": {
                "root_dir": "apis/home/python",
                "public_package": {
                    "package_dir": "aware_home_devices_api",
                    "root_dir": "apis/home/python/public",
                },
                "service_protocol": {
                    "package_dir": "aware_home_devices_api_service_protocol",
                    "root_dir": "apis/home/python/service_protocol",
                },
            }
        }
