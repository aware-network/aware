from __future__ import annotations

# pyright: reportMissingTypeStubs=false

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_code.stable_ids import stable_code_package_id
from aware_content.handlers._generated import meta_handlers as content_meta_handlers
from aware_code.handlers._generated import meta_handlers as code_meta_handlers
from aware_code.package.test_inventory import (
    build_code_package_test_inventory_from_files,
)
from aware_code.semantic_contract_config import source_code_package_config_descriptor
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.projection.branching import stable_portal_target_branch_id
from aware_meta.handlers._generated import meta_handlers as meta_meta_handlers
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.graph_commit_invocation_backend import (
    resolve_meta_graph_object_projection_graph_identity_id,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot,
    LaneIds,
    MetaOIGAssertions,
    ProofCall,
    ROOT_OBJECT_ID,
    run_meta_runtime_proof,
)
from _code_runtime_test_paths import CODE_PACKAGE_MANIFEST_PATHS, REPO_ROOT


PYPROJECT_TEXT = (
    '[project]\nname = "demo-python"\nversion = "0.0.0"\ndependencies = ["pytest>=8"]\n'
)
TEST_FILE_TEXT = "def test_demo():\n    assert True\n"
CODE_PACKAGE_CONFIG_CLASS_FQN = "aware_code.package.CodePackageConfig"
CODE_PACKAGE_CLASS_FQN = "aware_code.package.CodePackage"


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
            content_meta_handlers,
            meta_meta_handlers,
        ),
        bootstrap_modules=(
            code_meta_handlers,
            content_meta_handlers,
            meta_meta_handlers,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
        ),
    )
    assert runtime.context is not None
    return runtime


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


def _opg_by_name(runtime: MetaGraphRuntime, name: str):
    assert runtime.context is not None
    matches = [
        opg
        for opg in runtime.context.index.opg_by_hash.values()
        if (opg.name or "") == name
    ]
    assert len(matches) == 1
    return matches[0]


@pytest.mark.asyncio
async def test_code_package_config_create_package_uses_package_projection_portal(
    tmp_path: Path,
) -> None:
    descriptor = source_code_package_config_descriptor(
        manifest_kind="pyproject_toml",
        surface="runtime",
    )
    package_name = "demo-python"
    code_package_id = stable_code_package_id(
        code_package_config_id=descriptor.ref.config_id,
        package_name=package_name,
        language=CodeLanguage.python,
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_code_package_config_portal",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=REPO_ROOT, aware_root=aware_root)
        assert runtime.context is not None
        idx = runtime.context.index
        config_opg = _opg_by_name(runtime, "CodePackageConfig")
        package_opg = _opg_by_name(runtime, "CodePackage")
        portal = next(
            (
                item
                for item in idx.portal_index.portals_by_source_projection_hash.get(
                    config_opg.projection_hash,
                    [],
                )
                if item.reference_field_name == "packages"
                and item.target_projection_hash == package_opg.projection_hash
            ),
            None,
        )
        assert portal is not None

        lane = LaneIds(branch_id=uuid4(), actor_id=uuid4())
        source_result, source_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="CodePackageConfig",
            root_class_fqn=CODE_PACKAGE_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=CODE_PACKAGE_CONFIG_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "config_key": descriptor.ref.config_key,
                        "provider_key": descriptor.provider_key,
                        "semantic_owner": descriptor.semantic_owner,
                        "contract": descriptor.contract,
                        "manifest_kind": descriptor.ref.manifest_kind,
                        "manifest_filename": descriptor.manifest_filename,
                        "package_role": descriptor.package_role,
                        "semantic_package_family": descriptor.semantic_package_family,
                        "semantic_package_kind": descriptor.semantic_package_kind,
                        "semantic_projection_name": descriptor.semantic_projection_name,
                        "semantic_root_kind": descriptor.semantic_root_kind,
                        "default_surface": descriptor.ref.surface,
                        "materialization_capability": descriptor.materialization_capability,
                    },
                    expected_root_object_id=descriptor.ref.config_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=CODE_PACKAGE_CONFIG_CLASS_FQN,
                    function_name="create_package",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "package_name": package_name,
                        "language": CodeLanguage.python.value,
                        "manifest_relative_path": "pyproject.toml",
                        "package_root": ".",
                        "sources_root": ".",
                        "fqn_prefix": "demo_python",
                        "surface": "runtime",
                    },
                    allow_noop_commit=True,
                ),
            ],
        )

        source_assertions.expect_root(descriptor.ref.config_id)
        source_oig_id = UUID(str(source_result.head["object_instance_graph_id"]))
        target_opgi_id = resolve_meta_graph_object_projection_graph_identity_id(
            index=idx,
            opg=package_opg,
        )
        target_branch_id = stable_portal_target_branch_id(
            object_instance_graph_id=source_oig_id,
            object_projection_graph_identity_id=target_opgi_id,
            target_object_id=code_package_id,
        )
        assert target_branch_id != source_result.branch_id

        target_head = await FSCommitStore().head(
            branch_id=target_branch_id,
            projection_hash=package_opg.projection_hash,
        )
        assert target_head and target_head.get("commit_id")
        target_oig, _ = await OIGMaterializer().get(
            branch_id=target_branch_id,
            ocg=idx.ocg,
            opg=package_opg,
            commit_id=UUID(str(target_head["commit_id"])),
            oig_id=UUID(str(target_head["object_instance_graph_id"])),
            attribute_configs_by_id=idx.attribute_configs_by_id,
            class_configs_by_id=idx.class_configs_by_id,
        )
        target_assertions = MetaOIGAssertions(oig=target_oig, index=idx)
        target_assertions.expect_root(code_package_id)
        target_assertions.expect_primitive(
            instance_id=code_package_id,
            field_name="package_name",
            expected=package_name,
        )
        target_assertions.expect_primitive(
            instance_id=code_package_id,
            field_name="manifest_relative_path",
            expected="pyproject.toml",
        )
        target_assertions.expect_primitive(
            instance_id=code_package_id,
            field_name="package_root",
            expected=".",
        )


@pytest.mark.asyncio
async def test_code_package_sync_tests_materializes_pytest_inventory_via_meta_runtime(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    setup_code_plugins()

    descriptor = source_code_package_config_descriptor(
        manifest_kind="pyproject_toml",
        surface="runtime",
    )
    inventory = build_code_package_test_inventory_from_files(
        package_name="demo-python",
        language=CodeLanguage.python,
        manifest_kind="pyproject_toml",
        manifest_relative_path="pyproject.toml",
        package_root=".",
        sources_root=".",
        manifest_text=PYPROJECT_TEXT,
        files={"tests/test_demo.py": TEST_FILE_TEXT},
    )
    assert len(inventory.frameworks) == 1
    assert len(inventory.units) == 1
    framework = inventory.frameworks[0]
    unit = inventory.units[0]
    code_package_id = inventory.code_package_id

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_code_package_sync_tests_runtime",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        lane = LaneIds(branch_id=uuid4(), actor_id=uuid4())
        _result, assertions = await run_meta_runtime_proof(
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
                        "code_package_config_id": descriptor.ref.config_id,
                        "package_name": "demo-python",
                        "language": CodeLanguage.python.value,
                        "manifest_relative_path": "pyproject.toml",
                        "package_root": ".",
                        "sources_root": ".",
                        "fqn_prefix": "demo_python",
                        "surface": "runtime",
                    },
                    expected_root_object_id=code_package_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=CODE_PACKAGE_CLASS_FQN,
                    function_name="upsert_code_from_text",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "relative_path": "tests/test_demo.py",
                        "content_text": TEST_FILE_TEXT,
                        "language": None,
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=CODE_PACKAGE_CLASS_FQN,
                    function_name="sync_tests",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={"manifest_text": PYPROJECT_TEXT},
                ),
            ],
        )

    ids_by_class = _ids_by_class_name(assertions)
    assert len(ids_by_class.get("CodePackage", [])) == 1
    assert len(ids_by_class.get("CodePackageCode", [])) == 1
    assert len(ids_by_class.get("CodePackageTestFramework", [])) == 1
    assert len(ids_by_class.get("CodePackageTest", [])) == 1
    assert len(ids_by_class.get("CodeTest", [])) == 1
    assert len(ids_by_class.get("CodeTestUnit", [])) == 1

    for expected_id in (
        code_package_id,
        unit.code_package_code_id,
        unit.code_id,
        unit.code_section_id,
        framework.code_package_test_framework_id,
        unit.code_test_id,
        unit.code_package_test_id,
        unit.code_test_unit_id,
    ):
        assertions.expect_instance(expected_id)

    assertions.expect_primitive(
        instance_id=code_package_id,
        field_name="package_name",
        expected="demo-python",
    )
    assertions.expect_primitive(
        instance_id=framework.code_package_test_framework_id,
        field_name="declaration_kind",
        expected=framework.declaration_kind,
    )
    assertions.expect_primitive(
        instance_id=framework.code_package_test_framework_id,
        field_name="declaration_ref",
        expected=framework.declaration_ref,
    )
    assertions.expect_primitive(
        instance_id=unit.code_package_test_id,
        field_name="relative_path",
        expected="tests/test_demo.py",
    )
    assertions.expect_primitive(
        instance_id=unit.code_test_id,
        field_name="selector_prefix",
        expected="tests/test_demo.py",
    )
    assertions.expect_primitive(
        instance_id=unit.code_test_unit_id,
        field_name="selector",
        expected="tests/test_demo.py::test_demo",
    )
    assertions.expect_primitive(
        instance_id=unit.code_test_unit_id,
        field_name="unit_key",
        expected="pytest:tests/test_demo.py:test_demo",
    )
