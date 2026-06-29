from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
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
from aware_ontology.handlers._generated import meta_handlers as ontology_meta_handlers


ONTOLOGY_PACKAGE_CLASS_FQN = "aware_ontology.default.ontology.OntologyPackage"
ONTOLOGY_CONFIG_CLASS_FQN = "aware_ontology.default.ontology.OntologyConfig"
_TEST_FILE = Path(__file__).resolve()
_REPO_ROOT = _TEST_FILE.parents[8]

_ONTOLOGY_META_HANDLERS_ANY: Any = ontology_meta_handlers
_ONTOLOGY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _ONTOLOGY_META_HANDLERS_ANY,
)
_ONTOLOGY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _ONTOLOGY_META_HANDLERS_ANY,
)


def _ontology_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
    )


def _build_ontology_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_ontology_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_ONTOLOGY_META_HANDLER_MODULE,),
        bootstrap_modules=(_ONTOLOGY_META_BOOTSTRAP_MODULE,),
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
async def test_ontology_config_handlers_module_proof(
    tmp_path: Path,
) -> None:
    import aware_meta_ontology  # noqa: F401
    import aware_ontology_ontology  # noqa: F401
    from aware_ontology_ontology.ontology.ontology_config import OntologyConfig
    from aware_ontology_ontology.stable_ids import (
        stable_ontology_config_id,
        stable_ontology_id,
    )

    config_name = "ontology-config-proof"
    fqn_prefix = "aware.ontology.test.config"
    ontology_key = "default"
    ontology_config_id = stable_ontology_config_id(
        name=config_name,
        fqn_prefix=fqn_prefix,
    )
    ontology_id = stable_ontology_id(
        ontology_config_id=ontology_config_id,
        key=ontology_key,
    )
    object_config_graph_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/ontology/config/object-config-graph",
    )
    object_config_graph_commit_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/ontology/config/ocg-commit",
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_ontology_meta_runtime(
            repo_root=_REPO_ROOT,
            aware_root=aware_root,
        )
        lane = LaneIds(
            environment_id=uuid5(
                NAMESPACE_URL,
                "aware://tests/ontology/config/env",
            ),
            process_id=uuid5(
                NAMESPACE_URL,
                "aware://tests/ontology/config/process",
            ),
            thread_id=uuid5(
                NAMESPACE_URL,
                "aware://tests/ontology/config/thread",
            ),
        )

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="OntologyConfig",
            root_class_fqn=ONTOLOGY_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ONTOLOGY_CONFIG_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": config_name,
                        "fqn_prefix": fqn_prefix,
                        "object_config_graph_id": object_config_graph_id,
                        "object_config_graph_object_instance_graph_commit_id": (
                            object_config_graph_commit_id
                        ),
                        "version_number": 1,
                        "title": "Ontology config proof",
                        "description": "Ontology config handler proof.",
                        "schema_hash": "b" * 64,
                    },
                    expected_root_object_id=ontology_config_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ONTOLOGY_CONFIG_CLASS_FQN,
                    function_name="create_ontology",
                    object_id=SourceObjectId(ontology_config_id),
                    kwargs={
                        "key": ontology_key,
                        "title": "Default ontology",
                        "description": "Default concrete ontology authority.",
                        "status": "active",
                    },
                ),
            ],
        )

        assert result.root_object_id == ontology_config_id
        assertions.expect_root(ontology_config_id)
        assertions.expect_instance(ontology_config_id)
        assertions.expect_instance(ontology_id)
        assertions.expect_edge(
            source_id=ontology_config_id,
            target_id=ontology_id,
            relationship_name="ontologies",
        )
        assertions.expect_primitive(
            instance_id=ontology_config_id,
            field_name="schema_hash",
            expected="b" * 64,
        )
        assertions.expect_primitive(
            instance_id=ontology_id,
            field_name="key",
            expected=ontology_key,
        )
        assertions.expect_primitive(
            instance_id=ontology_id,
            field_name="status",
            expected="active",
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=ontology_config_id,
            field_name="object_config_graph_id",
            expected=object_config_graph_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=ontology_config_id,
            field_name="object_config_graph_object_instance_graph_commit_id",
            expected=object_config_graph_commit_id,
        )

        payload = result.responses[0].payload
        assert isinstance(payload, dict)
        created_payload = payload.get("value", payload)
        assert isinstance(created_payload, dict)
        created = OntologyConfig.model_validate(created_payload)
        assert created.id == ontology_config_id
        assert created.fqn_prefix == fqn_prefix


@pytest.mark.asyncio
async def test_ontology_package_handlers_module_proof(
    tmp_path: Path,
) -> None:
    import aware_meta_ontology  # noqa: F401
    import aware_ontology_ontology  # noqa: F401
    from aware_code.types import JsonArray
    from aware_code.stable_ids import stable_code_package_id
    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_meta_ontology.stable_ids import stable_object_config_graph_package_id
    from aware_ontology_ontology.ontology.ontology_package import OntologyPackage
    from aware_ontology_ontology.stable_ids import (
        stable_ontology_config_id,
        stable_ontology_package_dependency_id,
        stable_ontology_package_id,
        stable_ontology_package_runtime_code_package_id,
    )

    package_name = "ontology-runtime-proof"
    fqn_prefix = "aware.ontology.test.proof"
    ontology_package_id = stable_ontology_package_id(
        name=package_name,
        fqn_prefix=fqn_prefix,
    )
    ontology_config_id = stable_ontology_config_id(
        name=package_name,
        fqn_prefix=fqn_prefix,
    )
    source_code_package_id = stable_code_package_id(
        package_name="ontology-runtime-proof-source",
        language="aware",
    )
    runtime_code_package_id = stable_code_package_id(
        package_name="aware-ontology-runtime-proof",
        language="python",
    )
    object_config_graph_package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    target_ontology_package_id = stable_ontology_package_id(
        name="meta-ontology",
        fqn_prefix="aware_meta",
    )
    runtime_package_edge_id = stable_ontology_package_runtime_code_package_id(
        ontology_package_id=ontology_package_id,
        code_package_id=runtime_code_package_id,
    )
    dependency_edge_id = stable_ontology_package_dependency_id(
        ontology_package_id=ontology_package_id,
        target_ontology_package_id=target_ontology_package_id,
    )
    object_config_graph_package_commit_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/ontology/package/ocg-package-commit",
    )
    object_config_graph_commit_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/ontology/package/ocg-commit",
    )
    ontology_config_commit_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/ontology/package/ontology-config-commit",
    )
    runtime_code_commit_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/ontology/package/runtime-code-commit",
    )
    target_ontology_commit_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/ontology/package/target-ontology-commit",
    )
    expected_hash = "a" * 64

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_ontology_meta_runtime(
            repo_root=_REPO_ROOT,
            aware_root=aware_root,
        )
        lane = LaneIds(
            environment_id=uuid5(NAMESPACE_URL, "aware://tests/ontology/env"),
            process_id=uuid5(NAMESPACE_URL, "aware://tests/ontology/process"),
            thread_id=uuid5(NAMESPACE_URL, "aware://tests/ontology/thread"),
        )

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="OntologyPackage",
            root_class_fqn=ONTOLOGY_PACKAGE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ONTOLOGY_PACKAGE_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": package_name,
                        "fqn_prefix": fqn_prefix,
                        "ontology_config_id": ontology_config_id,
                        "ontology_config_object_instance_graph_commit_id": (
                            ontology_config_commit_id
                        ),
                        "source_code_package_id": source_code_package_id,
                        "object_config_graph_package_id": object_config_graph_package_id,
                        "object_config_graph_package_object_instance_graph_commit_id": (
                            object_config_graph_package_commit_id
                        ),
                        "object_config_graph_object_instance_graph_commit_id": (
                            object_config_graph_commit_id
                        ),
                        "version_number": 1,
                        "title": "Ontology runtime proof",
                        "description": "Ontology package handler proof.",
                        "manifest_relative_path": (
                            "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml"
                        ),
                        "package_root": "modules/ontology",
                        "sources_root": "structure/ontology/aware",
                    },
                    expected_root_object_id=ontology_package_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ONTOLOGY_PACKAGE_CLASS_FQN,
                    function_name="attach_runtime_code_package",
                    object_id=SourceObjectId(ontology_package_id),
                    kwargs={
                        "code_package_id": runtime_code_package_id,
                        "package_name": "aware-ontology-runtime-proof",
                        "language": CodeLanguage.python.value,
                        "import_root": "aware_ontology",
                        "manifest_relative_path": (
                            "workspaces/aware_kernel/modules/ontology/ontology/runtime/python/pyproject.toml"
                        ),
                        "package_root": "workspaces/aware_kernel/modules/ontology/ontology/runtime/python",
                        "role": "runtime",
                        "object_instance_graph_commit_id": runtime_code_commit_id,
                        "include_paths": JsonArray(["aware_ontology/**"]),
                        "exclude_paths": JsonArray(["**/__pycache__/**"]),
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ONTOLOGY_PACKAGE_CLASS_FQN,
                    function_name="attach_dependency",
                    object_id=SourceObjectId(ontology_package_id),
                    kwargs={
                        "target_ontology_package_id": target_ontology_package_id,
                        "target_package_name": "meta-ontology",
                        "target_ontology_package_object_instance_graph_commit_id": (
                            target_ontology_commit_id
                        ),
                        "target_version_number": 1,
                        "expected_hash_sha256": expected_hash,
                        "description": "Meta OCG representation dependency.",
                    },
                ),
            ],
        )

        assert result.root_object_id == ontology_package_id
        assertions.expect_root(ontology_package_id)
        assertions.expect_instance(ontology_package_id)
        assertions.expect_instance(runtime_package_edge_id)
        assertions.expect_instance(dependency_edge_id)
        assertions.expect_edge(
            source_id=ontology_package_id,
            target_id=runtime_package_edge_id,
            relationship_name="runtime_code_packages",
        )
        assertions.expect_edge(
            source_id=ontology_package_id,
            target_id=dependency_edge_id,
            relationship_name="dependencies",
        )
        assertions.expect_primitive(
            instance_id=ontology_package_id,
            field_name="manifest_relative_path",
            expected="workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        )
        assertions.expect_primitive(
            instance_id=ontology_package_id,
            field_name="package_root",
            expected="modules/ontology",
        )
        assertions.expect_primitive(
            instance_id=runtime_package_edge_id,
            field_name="import_root",
            expected="aware_ontology",
        )
        assertions.expect_primitive(
            instance_id=runtime_package_edge_id,
            field_name="include_paths",
            expected=["aware_ontology/**"],
        )
        assertions.expect_primitive(
            instance_id=dependency_edge_id,
            field_name="target_package_name",
            expected="meta-ontology",
        )
        assertions.expect_primitive(
            instance_id=dependency_edge_id,
            field_name="expected_hash_sha256",
            expected=expected_hash,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=ontology_package_id,
            field_name="ontology_config_id",
            expected=ontology_config_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=ontology_package_id,
            field_name="ontology_config_object_instance_graph_commit_id",
            expected=ontology_config_commit_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=ontology_package_id,
            field_name="source_code_package_id",
            expected=source_code_package_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=ontology_package_id,
            field_name="object_config_graph_package_id",
            expected=object_config_graph_package_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=ontology_package_id,
            field_name="object_config_graph_package_object_instance_graph_commit_id",
            expected=object_config_graph_package_commit_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=ontology_package_id,
            field_name="object_config_graph_object_instance_graph_commit_id",
            expected=object_config_graph_commit_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=runtime_package_edge_id,
            field_name="code_package_id",
            expected=runtime_code_package_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=runtime_package_edge_id,
            field_name="object_instance_graph_commit_id",
            expected=runtime_code_commit_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=dependency_edge_id,
            field_name="target_ontology_package_id",
            expected=target_ontology_package_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=dependency_edge_id,
            field_name="target_ontology_package_object_instance_graph_commit_id",
            expected=target_ontology_commit_id,
        )

        payload = result.responses[0].payload
        assert isinstance(payload, dict)
        created_payload = payload.get("value", payload)
        assert isinstance(created_payload, dict)
        created = OntologyPackage.model_validate(created_payload)
        assert created.id == ontology_package_id
        assert created.fqn_prefix == fqn_prefix
