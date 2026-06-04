from __future__ import annotations

import json
from pathlib import Path

import msgpack
import pytest
from datetime import datetime, timezone
from uuid import uuid4

# Kernel Graph Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)

# Kernel Structure
from aware_structure.environment_config.manifest.schema.environment_manifest import (
    EnvironmentDescriptor,
    EnvironmentManifest,
    ManifestArtifact,
)
from aware_structure.environment_config.manifest.schema.ocg_manifest import (
    OCGSnapshotManifest,
)
from aware_structure.environment_config.manifest.schema.opg_manifest import (
    OPGIndexManifest,
)
from aware_structure.environment_config.bundle import EnvironmentBundle

# ORM
from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry
from aware_orm.runtime.bundle_binding import install_bindings_from_bundle
from aware_orm.runtime.graph_artifacts import OrmGraphBindingSnapshot
from aware_orm.runtime.graph_binding import dump_orm_graph_binding_snapshot_msgpack
from aware_meta.orm_artifacts.binding import (
    dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph,
)
from aware_structure.environment_config.orm_runtime_install import install_environment_bundle


def _build_graph() -> ObjectConfigGraph:
    # Ensure ontology models are rebuilt so forward refs (e.g. ClassConfigChange) are resolved.
    import aware_meta_ontology as ontology_pkg

    bootstrap = getattr(ontology_pkg, "_bootstrap_models", None)
    if callable(bootstrap):
        bootstrap()

    ocg_id = uuid4()
    user = ClassConfig(name="User", class_fqn="pkg.User")
    node = ObjectConfigGraphNode(
        type=ObjectConfigGraphNodeType.class_,
        node_key=user.class_fqn,
        class_config=user,
        object_config_graph_id=ocg_id,
        class_config_id=user.id,
    )
    return ObjectConfigGraph(
        id=ocg_id,
        name="g",
        description="g",
        hash="sha256:test",
        fqn_prefix="pkg",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[node],
    )


@pytest.mark.parametrize(
    "identity_key",
    ("canonical_entity_id", "canonical_class_config_id"),
)
def test_install_bindings_from_bundle_binds_canonical_class_config(
    tmp_path: Path,
    identity_key: str,
) -> None:
    graph = _build_graph()
    user_cls = next(
        n.class_config for n in graph.object_config_graph_nodes if n.class_config and n.class_config.name == "User"
    )
    assert user_cls is not None and user_cls.id is not None

    class UserModel(ORMModel):
        name: str

    fqn = f"{UserModel.__module__}.{UserModel.__name__}"
    ORMModelRegistry.register_class_stub(UserModel)

    bindings = {
        "version": "1.0.0",
        "planner_version": "test",
        "bindings": [
            {
                "class_fqn": fqn,
                identity_key: str(user_cls.id),
                "sql_mapping": [],
            }
        ],
    }

    # Build a minimal bundle with canonical ocg_bytes.
    manifest = EnvironmentManifest(
        version="1.0",
        built_at=datetime.now(timezone.utc),
        environment=EnvironmentDescriptor(
            id="00000000-0000-0000-0000-000000000000",
            title=None,
            canonical_language="aware",
        ),
        ocg=OCGSnapshotManifest(
            canonical_id="00000000-0000-0000-0000-000000000000",
            hash="sha256:x",
            snapshot="ocg.snapshot.msgpack",
        ),
        ocg_binding_snapshot=ManifestArtifact(file="orm.graph.binding.msgpack", hash="sha256:x"),
        overlays={},
        opg_index=OPGIndexManifest(file="opg.index.json", entries=[]),
        graphsql=None,
        bindings=None,
    )
    bundle = EnvironmentBundle(
        manifest=manifest,
        base_path=tmp_path,
        ocg_bytes=msgpack.packb(graph.model_dump(mode="json", exclude_none=True), use_bin_type=True) or b"",
        orm_graph_binding_snapshot_bytes=(
            dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph(object_config_graph=graph)
        ),
        overlays={},
        opgs={},
        graphsql=None,
        bindings=json.dumps(bindings).encode("utf-8"),
    )

    with ORMModelRegistry.temporary_clear():
        ORMModelRegistry.register_class_stub(UserModel)
        res = install_bindings_from_bundle(bundle, strict=True)
        assert res.bound_count == 1
        cc = UserModel.get_class_config()
        assert cc is not None
        assert str(cc.id) == str(user_cls.id)


def test_install_bindings_from_bundle_uses_orm_graph_artifact_metadata(
    tmp_path: Path,
) -> None:
    graph = _build_graph()
    user_cls = next(
        n.class_config
        for n in graph.object_config_graph_nodes
        if n.class_config and n.class_config.name == "User"
    )
    assert user_cls is not None and user_cls.id is not None

    class UserModel(ORMModel):
        name: str

    fqn = f"{UserModel.__module__}.{UserModel.__name__}"
    rich_user_cls = user_cls.model_copy(deep=True)
    reference_attribute = AttributeConfig.model_construct(
        id=uuid4(),
        owner_key="pkg.User",
        name="best_friend",
    )
    rich_user_cls.class_config_attribute_configs = [
        ClassConfigAttributeConfig(
            class_config_id=rich_user_cls.id,
            attribute_config=reference_attribute,
            attribute_config_id=reference_attribute.id,
            name=reference_attribute.name,
            position=0,
        )
    ]
    relationship = ClassConfigRelationship.model_construct(
        id=uuid4(),
        class_config_id=rich_user_cls.id,
        target_class_config_id=rich_user_cls.id,
        relationship_key="best_friend",
        class_config_relationship_attributes=[],
    )
    relationship.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=relationship.id,
            attribute_config_id=reference_attribute.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]
    rich_user_cls.class_config_relationships = [relationship]
    rich_graph = graph.model_copy(deep=True)
    for node in rich_graph.object_config_graph_nodes:
        if node.class_config and node.class_config.id == rich_user_cls.id:
            node.class_config = rich_user_cls
            break

    bindings = {
        "version": "1.0.0",
        "planner_version": "test",
        "bindings": [
            {
                "class_fqn": fqn,
                "canonical_entity_id": str(user_cls.id),
                "sql_mapping": [],
            }
        ],
    }
    manifest = EnvironmentManifest(
        version="1.0",
        built_at=datetime.now(timezone.utc),
        environment=EnvironmentDescriptor(
            id="00000000-0000-0000-0000-000000000000",
            title=None,
            canonical_language="aware",
        ),
        ocg=OCGSnapshotManifest(
            canonical_id="00000000-0000-0000-0000-000000000000",
            hash="sha256:x",
            snapshot="ocg.snapshot.msgpack",
        ),
        ocg_binding_snapshot=ManifestArtifact(
            file="orm.graph.binding.msgpack",
            hash="sha256:x",
        ),
        overlays={},
        opg_index=OPGIndexManifest(file="opg.index.json", entries=[]),
        graphsql=None,
        bindings=None,
    )
    bundle = EnvironmentBundle(
        manifest=manifest,
        base_path=tmp_path,
        ocg_bytes=msgpack.packb(
            rich_graph.model_dump(mode="json", exclude_none=True),
            use_bin_type=True,
        )
        or b"",
        orm_graph_binding_snapshot_bytes=dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph(
            object_config_graph=rich_graph
        ),
        overlays={},
        opgs={},
        graphsql=None,
        bindings=json.dumps(bindings).encode("utf-8"),
    )

    with ORMModelRegistry.temporary_clear():
        ORMModelRegistry.register_class_stub(UserModel)
        res = install_bindings_from_bundle(bundle, strict=True)

    assert res.bound_count == 1
    rebound = UserModel.get_class_config()
    assert rebound is not None
    assert {link.attribute_config_id for link in rebound.class_config_attribute_configs} == {
        reference_attribute.id
    }
    assert {rel.id for rel in rebound.class_config_relationships} == {
        relationship.id
    }


@pytest.mark.parametrize("load_graph_artifacts", (True, False))
def test_install_environment_bundle_derives_binding_snapshot_from_ocg_when_embedded_snapshot_is_empty(
    tmp_path: Path,
    load_graph_artifacts: bool,
) -> None:
    graph = _build_graph()
    user_cls = next(
        n.class_config
        for n in graph.object_config_graph_nodes
        if n.class_config and n.class_config.name == "User"
    )
    assert user_cls is not None and user_cls.id is not None

    class UserModel(ORMModel):
        name: str

    fqn = f"{UserModel.__module__}.{UserModel.__name__}"
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "ocg.snapshot.msgpack").write_bytes(
        msgpack.packb(
            graph.model_dump(mode="json", exclude_none=True),
            use_bin_type=True,
        )
        or b""
    )
    (bundle_dir / "orm.graph.binding.msgpack").write_bytes(
        dump_orm_graph_binding_snapshot_msgpack(
            snapshot=OrmGraphBindingSnapshot(
                graph_id=graph.id,
                entities=[],
            )
        )
    )
    bindings = {
        "version": "1.0.0",
        "planner_version": "test",
        "bindings": [
            {
                "class_fqn": fqn,
                "canonical_class_config_id": str(user_cls.id),
                "sql_mapping": [
                    {
                        "attribute_name": "id",
                        "persisted": True,
                        "table_schema": "public",
                        "table_name": "user",
                        "column_name": "id",
                        "fk_owner": None,
                        "fk_columns": [],
                        "join_chain": [],
                    }
                ],
            }
        ],
    }
    (bundle_dir / "bindings.json").write_text(
        json.dumps(bindings),
        encoding="utf-8",
    )
    manifest = EnvironmentManifest(
        version="1.0",
        built_at=datetime.now(timezone.utc),
        environment=EnvironmentDescriptor(
            id="00000000-0000-0000-0000-000000000000",
            title=None,
            canonical_language="aware",
        ),
        ocg=OCGSnapshotManifest(
            canonical_id="00000000-0000-0000-0000-000000000000",
            hash="sha256:x",
            snapshot="ocg.snapshot.msgpack",
        ),
        ocg_binding_snapshot=ManifestArtifact(
            file="orm.graph.binding.msgpack",
            hash="sha256:x",
        ),
        overlays={},
        opg_index=OPGIndexManifest(file="opg.index.json", entries=[]),
        graphsql=None,
        bindings=ManifestArtifact(file="bindings.json", hash="sha256:x"),
    )
    manifest_path = bundle_dir / "environment.manifest.json"
    manifest_path.write_text(manifest.model_dump_json(), encoding="utf-8")

    with ORMModelRegistry.temporary_clear():
        ORMModelRegistry.register_class_stub(UserModel)
        _bundle, binding_result, _rel = install_environment_bundle(
            manifest_path=manifest_path,
            canonical_only=True,
            strict=True,
            load_graph_artifacts=load_graph_artifacts,
        )
        assert binding_result is not None
        assert binding_result.bound_count == 1
        cc = UserModel.get_class_config()
        assert cc is not None
        assert str(cc.id) == str(user_cls.id)


def test_install_environment_bundle_bootstraps_loader_modules(tmp_path: Path, monkeypatch) -> None:
    graph = _build_graph()
    counter_cls = ClassConfig(name="Counter", class_fqn="bundle_loader_pkg.models.Counter")
    counter_node = ObjectConfigGraphNode(
        type=ObjectConfigGraphNodeType.class_,
        node_key=counter_cls.class_fqn,
        class_config=counter_cls,
        object_config_graph_id=graph.id,
        class_config_id=counter_cls.id,
    )
    graph.object_config_graph_nodes.append(counter_node)

    pkg_dir = tmp_path / "bundle_loader_pkg"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
    (pkg_dir / "models.py").write_text(
        "from __future__ import annotations\n"
        "from aware_orm.models.orm_model import ORMModel\n\n"
        "class Counter(ORMModel):\n"
        "    value: int\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    (bundle_dir / "ocg.snapshot.msgpack").write_bytes(
        msgpack.packb(graph.model_dump(mode="json", exclude_none=True), use_bin_type=True) or b""
    )
    (bundle_dir / "orm.graph.binding.msgpack").write_bytes(
        dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph(object_config_graph=graph)
    )

    bindings = {
        "version": "1.0.0",
        "planner_version": "test",
        "bindings": [
            {
                "class_fqn": "bundle_loader_pkg.models.Counter",
                "canonical_entity_id": str(counter_cls.id),
                "sql_mapping": [
                    {
                        "attribute_name": "value",
                        "table_schema": "public",
                        "table_name": "counter",
                        "column_name": "value",
                        "persisted": True,
                    }
                ],
            }
        ],
    }
    (bundle_dir / "bindings.json").write_text(json.dumps(bindings), encoding="utf-8")

    manifest = EnvironmentManifest(
        version="1.0",
        built_at=datetime.now(timezone.utc),
        environment=EnvironmentDescriptor(
            id="00000000-0000-0000-0000-000000000000",
            title=None,
            canonical_language="aware",
        ),
        ocg=OCGSnapshotManifest(
            canonical_id="00000000-0000-0000-0000-000000000000",
            hash="sha256:x",
            snapshot="ocg.snapshot.msgpack",
        ),
        ocg_binding_snapshot=ManifestArtifact(file="orm.graph.binding.msgpack", hash="sha256:x"),
        overlays={},
        opg_index=OPGIndexManifest(file="opg.index.json", entries=[]),
        graphsql=None,
        bindings=ManifestArtifact(file="bindings.json", hash="sha256:x"),
        loader={"python_modules": ["bundle_loader_pkg.models"]},
    )
    manifest_path = bundle_dir / "environment.manifest.json"
    manifest_path.write_text(manifest.model_dump_json(), encoding="utf-8")

    with ORMModelRegistry.temporary_clear():
        _bundle, binding_result, _rel = install_environment_bundle(
            manifest_path=manifest_path,
            canonical_only=True,
            strict=True,
        )
        assert binding_result is not None
        assert binding_result.bound_count == 1

        from bundle_loader_pkg.models import Counter

        cc = Counter.get_class_config()
        assert cc is not None
        assert str(cc.id) == str(counter_cls.id)
