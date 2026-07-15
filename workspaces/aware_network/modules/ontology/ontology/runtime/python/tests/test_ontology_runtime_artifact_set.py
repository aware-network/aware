from __future__ import annotations

import inspect
import json
from pathlib import Path
from uuid import uuid4

from aware_ontology.semantic_contract import (
    AWARE_ONTOLOGY_SEMANTIC_CONTRACT,
)
from aware_ontology.semantic_runtime_catalog import (
    ONTOLOGY_RUNTIME_ARTIFACT_SET_ACTIVATION_POLICY,
    ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY,
    ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE,
    ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION,
    ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY,
    ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_KEY,
    ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_PROVIDER_KEY,
    ONTOLOGY_RUNTIME_ARTIFACT_SET_REQUIRED_FOR,
    ONTOLOGY_RUNTIME_ARTIFACT_SET_SEMANTIC_OWNER,
    ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_ARTIFACT_ROLE,
    ONTOLOGY_RUNTIME_DB_SCHEMA_REGISTRY_ARTIFACT_ROLE,
    ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_ARTIFACT_ROLE,
    build_ontology_runtime_artifact_set_ownership_receipt,
    build_ontology_runtime_artifact_set_from_materialization_details,
    find_ontology_runtime_artifact_ref,
    ontology_runtime_artifact_ref_path,
    resolve_local_ontology_runtime_artifact_set_payload,
    resolve_ontology_runtime_artifact_set_payload,
)


def _materialization_details() -> dict[str, object]:
    return {
        "schema": "aware_ontology.workspace_materialize.ontology_package.v1",
        "provider_key": "aware_ontology",
        "semantic_owner": "aware_ontology.provider",
        "manifest_path": "modules/ontology/aware.ontology.toml",
        "source_manifest_path": "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        "runtime_bundle_manifest_path": (
            "workspaces/aware_kernel/modules/ontology/ontology/structure/.aware/ontology/runtime/"
            "ontology.runtime.manifest.json"
        ),
        "runtime_bundle_manifest_workspace_relative_path": (
            "workspaces/aware_kernel/modules/ontology/ontology/structure/.aware/ontology/runtime/"
            "ontology.runtime.manifest.json"
        ),
        "runtime_bundle_manifest_status": "available",
        "runtime_bundle_manifest_digest": "sha256:runtime-bundle",
        "runtime_bundle_manifest_size_bytes": 1234,
        "runtime_bundle_db_schema_registry_path": (
            "workspaces/aware_kernel/modules/ontology/ontology/structure/.aware/ontology/runtime/"
            "db.schema.registry.json"
        ),
        "runtime_bundle_db_schema_registry_workspace_relative_path": (
            "workspaces/aware_kernel/modules/ontology/ontology/structure/.aware/ontology/runtime/"
            "db.schema.registry.json"
        ),
        "runtime_bundle_db_schema_registry_digest": "sha256:db-schema-registry",
        "runtime_bundle_db_schema_registry_sql_roots": (
            "workspaces/aware_kernel/modules/ontology/ontology/structure/sql",
        ),
        "python_models_manifest_path": (
            "workspaces/aware_kernel/modules/ontology/ontology/structure/python/orm_runtime/"
            ".aware/materializations/python.models.json"
        ),
        "python_models_manifest_workspace_relative_path": (
            "workspaces/aware_kernel/modules/ontology/ontology/structure/python/orm_runtime/"
            ".aware/materializations/python.models.json"
        ),
        "python_models_manifest_status": "available",
        "python_models_manifest_digest": "sha256:python-models",
        "python_models_manifest_size_bytes": 4321,
        "package_name": "ontology-ontology",
        "fqn_prefix": "aware_ontology",
        "ontology_config_id": "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa",
        "ontology_config_commit_id": "aaaaaaaa-2222-4222-8222-aaaaaaaaaaaa",
        "ontology_config_head_commit_id": "aaaaaaaa-4444-4444-8444-aaaaaaaaaaaa",
        "ontology_config_object_instance_graph_commit_id": (
            "aaaaaaaa-3333-4333-8333-aaaaaaaaaaaa"
        ),
        "ontology_package_id": "11111111-1111-4111-8111-111111111111",
        "ontology_package_commit_id": "22222222-2222-4222-8222-222222222222",
        "ontology_package_head_commit_id": "22222222-4444-4444-8444-222222222222",
        "ontology_package_object_instance_graph_commit_id": (
            "22222222-3333-4333-8333-222222222222"
        ),
        "materialized_semantic_roots": [
            {
                "semantic_root_kind": "OntologyConfig",
                "semantic_projection_name": "OntologyConfig",
                "semantic_projection_hash": "ontology-config.projection",
                "semantic_package_id": "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa",
                "semantic_root_id": "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa",
                "semantic_head_commit_id": "aaaaaaaa-4444-4444-8444-aaaaaaaaaaaa",
                "semantic_object_instance_graph_commit_id": (
                    "aaaaaaaa-3333-4333-8333-aaaaaaaaaaaa"
                ),
                "semantic_root_object_instance_graph_commit_id": (
                    "aaaaaaaa-3333-4333-8333-aaaaaaaaaaaa"
                ),
            },
            {
                "semantic_root_kind": "OntologyPackage",
                "semantic_projection_name": "OntologyPackage",
                "semantic_projection_hash": "ontology-package.projection",
                "semantic_package_id": "11111111-1111-4111-8111-111111111111",
                "semantic_root_id": "11111111-1111-4111-8111-111111111111",
                "semantic_head_commit_id": "22222222-4444-4444-8444-222222222222",
                "semantic_object_instance_graph_commit_id": (
                    "22222222-3333-4333-8333-222222222222"
                ),
                "semantic_root_object_instance_graph_commit_id": (
                    "22222222-3333-4333-8333-222222222222"
                ),
            },
        ],
        "object_config_graph_id": "33333333-3333-4333-8333-333333333333",
        "object_config_graph_hash": "sha256:ocg",
        "object_config_graph_commit_id": "44444444-4444-4444-8444-444444444444",
        "object_config_graph_package_id": "55555555-5555-4555-8555-555555555555",
        "runtime_projection_descriptors": [
            {
                "projection_name": "Environment",
                "projection_hash": "environment.projection",
                "object_projection_graph_id": ("99999999-9999-4999-8999-999999999999"),
                "constructor_function_id": ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
                "object_config_graph_id": "33333333-3333-4333-8333-333333333333",
                "opg_hashes": ["environment.projection"],
                "required_for": ["runtime_index", "service_boot"],
            }
        ],
        "source_code_package_id": "66666666-6666-4666-8666-666666666666",
        "source_code_package_commit_id": "77777777-7777-4777-8777-777777777777",
        "semantic_commit_strategy": "seed",
        "meta_language_materialization_bridge": {
            "provider_key": "aware_meta",
            "status": "completed",
        },
        "artifact_ownership_receipts": [
            {
                "artifact_key": "python:package:aware_ontology_service_dto",
                "artifact_role": "package",
                "artifact_family": "api_product_runtime",
                "producer_provider_key": "aware_api",
                "producer_key": "aware_api.product_runtime",
                "status": "available",
                "digest": "sha256:package",
                "required_for": ["workspace_revision", "runtime_index"],
                "runtime_contract_version": "aware.api.product_runtime.v1",
                "workspace_relative_path": (
                    "modules/ontology/apis/ontology/python/aware_ontology_service_dto"
                ),
            }
        ],
        "materialized_language_packages": [
            {
                "artifact_key": "aware_ontology_service_dto",
                "status": "available",
                "code_package_id": "88888888-8888-4888-8888-888888888888",
            }
        ],
    }


def test_ontology_runtime_artifact_set_semantic_contract_output_declared() -> None:
    descriptor = next(
        item
        for item in AWARE_ONTOLOGY_SEMANTIC_CONTRACT.materialization_artifact_outputs
        if item.output_key == ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY
    )

    assert descriptor.artifact_family == ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY
    assert descriptor.artifact_role == ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE
    assert descriptor.runtime_contract_version == (
        ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION
    )
    assert descriptor.output_kind == "materialization_detail"
    assert descriptor.provider_payload is not None
    assert descriptor.provider_payload["activation_allowed"] is False
    assert "workspace_revision" in descriptor.required_for
    assert "service_boot" in descriptor.required_for


def test_ontology_runtime_artifact_set_payload_is_non_activation_descriptor() -> None:
    payload = build_ontology_runtime_artifact_set_from_materialization_details(
        details=_materialization_details(),
    )

    assert payload["artifact_set_id"].startswith("ontology-runtime-artifact-set:")
    assert payload["package_name"] == "ontology-ontology"
    assert payload["fqn_prefix"] == "aware_ontology"
    assert payload["runtime_contract_version"] == (
        ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION
    )
    assert payload["activation_allowed"] is False
    assert (
        payload["activation_policy"] == ONTOLOGY_RUNTIME_ARTIFACT_SET_ACTIVATION_POLICY
    )
    assert payload["provenance"]["source_kind"] == "ontology_materialization"
    assert payload["provenance"]["ontology_manifest_path"] == (
        "modules/ontology/aware.ontology.toml"
    )
    assert payload["provenance"]["ontology_config_id"] == (
        "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa"
    )
    assert payload["provenance"]["ontology_config_commit_id"] == (
        "aaaaaaaa-2222-4222-8222-aaaaaaaaaaaa"
    )
    assert payload["provenance"]["ontology_config_head_commit_id"] == (
        "aaaaaaaa-4444-4444-8444-aaaaaaaaaaaa"
    )
    assert (
        payload["provenance"]["ontology_config_object_instance_graph_commit_id"]
        == "aaaaaaaa-3333-4333-8333-aaaaaaaaaaaa"
    )
    assert payload["provenance"]["ontology_package_head_commit_id"] == (
        "22222222-4444-4444-8444-222222222222"
    )

    artifact_roles = {item["artifact_role"] for item in payload["artifacts"]}
    assert "ontology_manifest" in artifact_roles
    assert "source_manifest" in artifact_roles
    assert "ontology_config" in artifact_roles
    assert ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_ARTIFACT_ROLE in artifact_roles
    assert ONTOLOGY_RUNTIME_DB_SCHEMA_REGISTRY_ARTIFACT_ROLE in artifact_roles
    assert ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_ARTIFACT_ROLE in artifact_roles
    assert "object_config_graph" in artifact_roles
    assert "language_package" in artifact_roles
    assert (
        ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_ARTIFACT_ROLE
        in payload["required_artifact_roles"]
    )
    runtime_bundle = next(
        item
        for item in payload["artifacts"]
        if item["artifact_role"] == ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_ARTIFACT_ROLE
    )
    assert runtime_bundle["status"] == "available"
    assert runtime_bundle["output_key"] == "runtime_bundle_manifest"
    assert runtime_bundle["output_kind"] == "runtime_manifest"
    assert runtime_bundle["manifest_path"] == (
        "workspaces/aware_kernel/modules/ontology/ontology/structure/.aware/ontology/runtime/"
        "ontology.runtime.manifest.json"
    )
    assert runtime_bundle["provider_payload"]["manifest_role"] == (
        "ontology_runtime_bundle_manifest"
    )
    assert runtime_bundle["provider_payload"]["contains"] == [
        "object_config_graph",
        "graphsql_plans",
        "projection_plans",
        "orm_binding_snapshot",
        "db_schema_registry",
    ]
    db_schema_registry = next(
        item
        for item in payload["artifacts"]
        if item["artifact_role"] == ONTOLOGY_RUNTIME_DB_SCHEMA_REGISTRY_ARTIFACT_ROLE
    )
    assert db_schema_registry["status"] == "available"
    assert db_schema_registry["output_key"] == "db_schema_registry"
    assert db_schema_registry["digest"] == "sha256:db-schema-registry"
    assert db_schema_registry["provider_payload"] == {
        "package_kind": "ontology",
        "backend_targets": ["postgres"],
        "sql_roots": [
            "workspaces/aware_kernel/modules/ontology/ontology/structure/sql"
        ],
    }
    assert "object_config_graph" in payload["required_artifact_roles"]
    assert "ontology_config" in payload["required_artifact_roles"]
    assert (
        ONTOLOGY_RUNTIME_DB_SCHEMA_REGISTRY_ARTIFACT_ROLE
        in payload["required_artifact_roles"]
    )
    assert (
        ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_ARTIFACT_ROLE
        in payload["required_artifact_roles"]
    )
    python_models = next(
        item
        for item in payload["artifacts"]
        if item["artifact_role"]
        == ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_ARTIFACT_ROLE
    )
    assert python_models["status"] == "available"
    assert python_models["output_key"] == "python_models_manifest"
    assert python_models["output_kind"] == "model_bootstrap_manifest"
    assert python_models["digest"] == "sha256:python-models"
    assert python_models["provider_payload"]["manifest_role"] == (
        "ontology_python_models_manifest"
    )
    assert payload["metadata"]["object_config_graph_hash"] == "sha256:ocg"
    assert [
        root["semantic_projection_name"]
        for root in payload["metadata"]["materialized_semantic_roots"]
    ] == ["OntologyConfig", "OntologyPackage"]
    assert [
        root["semantic_projection_name"]
        for root in payload["materialized_semantic_roots"]
    ] == ["OntologyConfig", "OntologyPackage"]
    config_root = payload["materialized_semantic_roots"][0]
    assert config_root == {
        "semantic_root_kind": "OntologyConfig",
        "semantic_projection_name": "OntologyConfig",
        "semantic_projection_hash": "ontology-config.projection",
        "semantic_package_id": "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa",
        "semantic_root_id": "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa",
        "semantic_head_commit_id": "aaaaaaaa-4444-4444-8444-aaaaaaaaaaaa",
        "semantic_object_instance_graph_commit_id": (
            "aaaaaaaa-3333-4333-8333-aaaaaaaaaaaa"
        ),
        "semantic_root_object_instance_graph_commit_id": (
            "aaaaaaaa-3333-4333-8333-aaaaaaaaaaaa"
        ),
    }
    assert payload["runtime_projection_descriptors"] == [
        {
            "projection_name": "Environment",
            "projection_hash": "environment.projection",
            "object_projection_graph_id": "99999999-9999-4999-8999-999999999999",
            "constructor_function_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "object_config_graph_id": "33333333-3333-4333-8333-333333333333",
            "opg_hashes": ["environment.projection"],
            "required_for": ["runtime_index", "service_boot"],
            "metadata": {},
        }
    ]

    resolved = resolve_ontology_runtime_artifact_set_payload(
        source_payload={ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY: payload},
        package_name="ontology-ontology",
        fqn_prefix="aware_ontology",
        include_artifacts=False,
    )
    assert resolved["artifacts"] == []


def test_ontology_runtime_artifact_set_marks_missing_runtime_bundle_manifest() -> None:
    details = dict(_materialization_details())
    details["runtime_bundle_manifest_status"] = "missing"
    details["runtime_bundle_manifest_error"] = "runtime bundle manifest missing"
    details.pop("runtime_bundle_manifest_digest", None)
    details.pop("runtime_bundle_manifest_size_bytes", None)

    payload = build_ontology_runtime_artifact_set_from_materialization_details(
        details=details,
    )

    runtime_bundle = next(
        item
        for item in payload["artifacts"]
        if item["artifact_role"] == ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_ARTIFACT_ROLE
    )
    assert runtime_bundle["status"] == "missing"
    assert runtime_bundle["error"] == "runtime bundle manifest missing"
    assert (
        ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_ARTIFACT_ROLE
        in payload["required_artifact_roles"]
    )


def test_ontology_runtime_artifact_set_builds_workspace_revision_receipt() -> None:
    payload = build_ontology_runtime_artifact_set_from_materialization_details(
        details=_materialization_details(),
    )

    receipt = build_ontology_runtime_artifact_set_ownership_receipt(
        artifact_set=payload,
    )

    assert receipt["producer_provider_key"] == (
        ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_PROVIDER_KEY
    )
    assert receipt["semantic_owner"] == ONTOLOGY_RUNTIME_ARTIFACT_SET_SEMANTIC_OWNER
    assert receipt["producer_key"] == ONTOLOGY_RUNTIME_ARTIFACT_SET_PRODUCER_KEY
    assert receipt["output_key"] == ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY
    assert receipt["output_kind"] == "materialization_detail"
    assert receipt["artifact_family"] == ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY
    assert receipt["artifact_role"] == ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE
    assert receipt["artifact_key"] == payload["artifact_set_id"]
    assert receipt["package_name"] == "ontology-ontology"
    assert receipt["fqn_prefix"] == "aware_ontology"
    assert receipt["status"] == "available"
    assert receipt["required_for"] == list(ONTOLOGY_RUNTIME_ARTIFACT_SET_REQUIRED_FOR)
    assert receipt["media_type"] == "application/json"
    assert receipt["runtime_contract_version"] == (
        ONTOLOGY_RUNTIME_ARTIFACT_SET_CONTRACT_VERSION
    )
    assert receipt["digest_algorithm"] == "sha256"
    assert isinstance(receipt["digest"], str)
    assert receipt["provider_payload"] == {
        "package_name": "ontology-ontology",
        "fqn_prefix": "aware_ontology",
        "artifact_set_id": payload["artifact_set_id"],
        "lifecycle_state": "produced",
        "activation_allowed": False,
        "activation_policy": ONTOLOGY_RUNTIME_ARTIFACT_SET_ACTIVATION_POLICY,
        "artifact_count": len(payload["artifacts"]),
        "required_artifact_roles": payload["required_artifact_roles"],
        "runtime_projection_descriptor_count": 1,
    }
    assert receipt[ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY] == payload


def test_local_ontology_runtime_artifact_set_resolves_model_bootstrap_role(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    source_root = workspace_root / "modules" / "demo" / "ontology" / "structure"
    runtime_root = source_root / ".aware" / "ontology" / "runtime"
    models_path = (
        source_root
        / "python"
        / "orm_runtime"
        / ".aware"
        / "materializations"
        / "python.models.json"
    )
    runtime_root.mkdir(parents=True)
    models_path.parent.mkdir(parents=True)
    source_manifest = source_root / "aware.toml"
    source_manifest.write_text(
        "\n".join(
            [
                "aware = 1",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
            ]
        ),
        encoding="utf-8",
    )
    (runtime_root / "ontology.runtime.manifest.json").write_text(
        json.dumps({"ocg": {"snapshot": "ocg.snapshot.msgpack"}}),
        encoding="utf-8",
    )
    models_path.write_text(json.dumps({"classes": []}), encoding="utf-8")

    artifact_set = resolve_local_ontology_runtime_artifact_set_payload(
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        source_manifest_path=source_manifest,
        workspace_root=workspace_root,
    )

    runtime_manifest_ref = find_ontology_runtime_artifact_ref(
        artifact_set=artifact_set,
        artifact_role=ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_ARTIFACT_ROLE,
        output_key="runtime_bundle_manifest",
    )
    python_models_ref = find_ontology_runtime_artifact_ref(
        artifact_set=artifact_set,
        artifact_role=ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_ARTIFACT_ROLE,
        output_key="python_models_manifest",
    )
    assert runtime_manifest_ref is not None
    assert python_models_ref is not None
    assert (
        ontology_runtime_artifact_ref_path(
            artifact_ref=runtime_manifest_ref,
            workspace_root=workspace_root,
        )
        == (runtime_root / "ontology.runtime.manifest.json").resolve()
    )
    assert (
        ontology_runtime_artifact_ref_path(
            artifact_ref=python_models_ref,
            workspace_root=workspace_root,
        )
        == models_path.resolve()
    )


def test_ontology_runtime_bundle_writer_is_physical_artifact_producer(
    tmp_path: Path,
) -> None:
    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_meta_ontology.graph.config.object_config_graph import (
        ObjectConfigGraph,
    )
    from aware_ontology import runtime_bundle

    aware_root = tmp_path / "modules" / "demo" / "structure" / "ontology"
    (aware_root / "sql").mkdir(parents=True)
    (aware_root / ".aware" / "materializations").mkdir(parents=True)
    (aware_root / ".aware" / "materializations" / "python.models.json").write_text(
        json.dumps(
            {
                "classes": [
                    {
                        "class_config_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                        "module": "aware_demo.demo",
                        "name": "Demo",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    graph = ObjectConfigGraph(
        id=uuid4(),
        name="Demo",
        description=None,
        hash="sha256:demo",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
    )

    result = runtime_bundle.write_ontology_runtime_bundle(
        output_dir=aware_root / ".aware" / "ontology" / "runtime",
        env_id=graph.id,
        env_title="Demo",
        env_canonical_language=CodeLanguage.aware,
        aware_root=aware_root,
        canonical_graph=graph,
        environment_service_provider_modules=(
            "aware_demo.handlers._generated.meta_handlers",
        ),
    )

    assert (
        result.manifest_path
        == (
            aware_root
            / ".aware"
            / "ontology"
            / "runtime"
            / "ontology.runtime.manifest.json"
        ).resolve()
    )
    assert result.contract_path.is_file()
    assert result.db_schema_registry_path is not None
    assert result.db_schema_registry_path.is_file()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["ocg"]["snapshot"] == "ocg.snapshot.msgpack"
    assert manifest["ocg_binding_snapshot"]["file"] == "orm.graph.binding.msgpack"
    assert manifest["graphsql"]["file"] == "graphsql/graphsql.plans.msgpack"
    assert manifest["projection_plans"]["file"] == "projection/projection.plans.msgpack"
    assert manifest["bindings"]["file"] == "bindings.manifest.json"
    assert manifest["db_schema_registry"]["file"] == "db.schema.registry.json"
    assert manifest["db_schema_registry"]["hash"].startswith("sha256:")
    assert manifest["db_schema_registry"]["status"] == "ready"
    assert manifest["loader"]["python_modules"] == ["aware_demo"]
    assert manifest["environment_service_provider_modules"] == [
        "aware_demo.handlers._generated.meta_handlers"
    ]
    assert (result.manifest_path.parent / "ocg.snapshot.msgpack").is_file()
    assert (result.manifest_path.parent / "orm.graph.binding.msgpack").is_file()
    assert (
        result.manifest_path.parent / "graphsql" / "graphsql.plans.msgpack"
    ).is_file()
    assert (
        result.manifest_path.parent / "projection" / "projection.plans.msgpack"
    ).is_file()
    assert "aware_structure" not in inspect.getsource(runtime_bundle)


def test_ontology_runtime_bundle_bindings_include_only_sql_backed_classes(
    tmp_path: Path,
) -> None:
    from aware_ontology.runtime_bundle import _export_bindings_manifest

    persisted_id = uuid4()
    non_persisted_id = uuid4()

    artifact = _export_bindings_manifest(
        destination=tmp_path,
        class_config_ids=(persisted_id, non_persisted_id),
        class_fqn_by_class_config_id={
            str(persisted_id): "aware_demo.demo.Persisted",
            str(non_persisted_id): "aware_demo.demo.NonPersisted",
        },
        sql_mapping_by_class_config_id={
            str(persisted_id): [
                {
                    "attribute_name": "id",
                    "persisted": True,
                    "table_schema": "demo",
                    "table_name": "persisted",
                    "column_name": "id",
                    "fk_owner": None,
                    "fk_columns": [],
                    "join_chain": [],
                }
            ]
        },
    )

    payload = json.loads(artifact.path.read_text(encoding="utf-8"))

    assert [entry["class_fqn"] for entry in payload["bindings"]] == [
        "aware_demo.demo.Persisted"
    ]
