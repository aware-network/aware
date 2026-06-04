from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import msgpack
import pytest
from uuid import uuid4

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_code_ontology.code.code_enums import CodeLanguage

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

from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry
from aware_orm.runtime.sql_metadata import (
    SQLRuntimeMetadata,
    clear_sql_metadata_registry,
    register_sql_metadata,
)
from aware_orm.runtime.bundle_binding import install_bindings_from_bundle
from aware_meta.orm_artifacts.binding import (
    dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph,
)
from aware_orm.session.current_session_ctx import set_session
from aware_orm.session.session import Session


def _build_graph() -> ObjectConfigGraph:
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


@pytest.mark.asyncio
async def test_push_requires_sql_metadata_when_skip_db_false(tmp_path: Path) -> None:
    graph = _build_graph()
    user_cls = next(
        n.class_config for n in graph.object_config_graph_nodes if n.class_config and n.class_config.name == "User"
    )
    assert user_cls is not None and user_cls.id is not None

    class UserModel(ORMModel):
        name: str

    fqn = f"{UserModel.__module__}.{UserModel.__name__}"

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

    clear_sql_metadata_registry()
    with ORMModelRegistry.temporary_clear():
        ORMModelRegistry.register_class_stub(UserModel)
        install_bindings_from_bundle(bundle, strict=True)

        session = Session(skip_db=False)
        with set_session(session):
            model = UserModel(name="alice")
            with pytest.raises(ValueError, match=r"Missing SQL metadata for UserModel"):
                await model.push()


@pytest.mark.asyncio
async def test_push_prefers_sql_metadata_over_default_schema_class_config() -> None:
    clear_sql_metadata_registry()

    class ServiceModel(ORMModel):
        name: str

    class_fqn = f"{ServiceModel.__module__}.{ServiceModel.__name__}"
    register_sql_metadata(
        SQLRuntimeMetadata(
            class_config_id=uuid4(),
            table_schema="service",
            table_name="service",
            column_by_attribute={"id": "id", "name": "name"},
            persisted_attributes=frozenset({"id", "name"}),
            fk_owner_by_attribute={},
            fk_columns_by_attribute={},
            join_chain_by_attribute={},
        ),
        class_fqn=class_fqn,
    )

    original_class_config = ServiceModel._class_config
    ServiceModel._class_config = SimpleNamespace(
        id=uuid4(),
        table_schema="default",
        table_name="service",
        class_config_attribute_configs=[],
    )
    try:
        session = Session(skip_db=False, backend_name="noop")
        with set_session(session):
            model = ServiceModel(name="ontology")
            await model.push()
    finally:
        ServiceModel._class_config = original_class_config
        clear_sql_metadata_registry()

    assert session._pending_inserts
    sql, _params = session._pending_inserts[0]
    assert sql.startswith("INSERT INTO service.service")
    assert not sql.startswith("INSERT INTO default.service")


@pytest.mark.asyncio
async def test_upsert_requires_class_fqn_sql_metadata_and_does_not_guess_by_table_name() -> None:
    clear_sql_metadata_registry()

    class ServiceModel(ORMModel):
        name: str

    register_sql_metadata(
        SQLRuntimeMetadata(
            class_config_id=uuid4(),
            table_schema="service",
            table_name="service",
            column_by_attribute={"id": "id", "name": "name"},
            persisted_attributes=frozenset({"id", "name"}),
            fk_owner_by_attribute={},
            fk_columns_by_attribute={},
            join_chain_by_attribute={},
        ),
        class_fqn="runtime.binding.Service",
    )

    original_class_config = ServiceModel._class_config
    ServiceModel._class_config = SimpleNamespace(
        id=uuid4(),
        table_schema="default",
        table_name="service",
        class_config_attribute_configs=[],
    )
    try:
        session = Session(skip_db=False, backend_name="noop")
        with set_session(session):
            model = ServiceModel(name="ontology")
            with pytest.raises(ValueError, match=r"Missing SQL metadata for ServiceModel"):
                await model.upsert()
    finally:
        ServiceModel._class_config = original_class_config
        clear_sql_metadata_registry()

    assert session._pending_inserts == []


@pytest.mark.asyncio
async def test_delete_via_session_uses_class_fqn_sql_metadata() -> None:
    clear_sql_metadata_registry()

    class ServiceModel(ORMModel):
        name: str

    class_fqn = f"{ServiceModel.__module__}.{ServiceModel.__name__}"
    register_sql_metadata(
        SQLRuntimeMetadata(
            class_config_id=uuid4(),
            table_schema="service",
            table_name="service",
            column_by_attribute={"id": "id", "name": "name"},
            persisted_attributes=frozenset({"id", "name"}),
            fk_owner_by_attribute={},
            fk_columns_by_attribute={},
            join_chain_by_attribute={},
        ),
        class_fqn=class_fqn,
    )

    original_class_config = ServiceModel._class_config
    ServiceModel._class_config = SimpleNamespace(
        id=uuid4(),
        class_config_attribute_configs=[],
    )
    try:
        session = Session(skip_db=False, backend_name="noop")
        with set_session(session):
            model = ServiceModel(name="ontology")
            await model.delete_via_session()
    finally:
        ServiceModel._class_config = original_class_config
        clear_sql_metadata_registry()

    assert session._pending_deletes
    sql, params = session._pending_deletes[0]
    assert sql == "DELETE FROM service.service WHERE id = $1"
    assert params == (model.id,)
