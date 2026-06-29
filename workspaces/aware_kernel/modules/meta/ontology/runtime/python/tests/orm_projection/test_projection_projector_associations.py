# @code-under-test: ../../../modules/meta/runtime/aware_meta/graph/instance/orm_projector.py

from __future__ import annotations

from uuid import uuid4

import pytest

from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph

from aware_orm.projection.plan import ProjectionAssociationPlan, ProjectionPlan
from aware_meta.graph.instance.orm_projector import stage_lane_projection_writes
from aware_orm.session.session import Session


def _oig(*, rels: list[ClassInstanceRelationship]) -> ObjectInstanceGraph:
    oig_id = uuid4()
    root = ClassInstance(
        id=uuid4(),
        source_object_id=uuid4(),
        object_instance_graph_id=oig_id,
        class_config_id=uuid4(),
    )
    return ObjectInstanceGraph(
        id=oig_id,
        key=str(oig_id),
        name="oig",
        description="",
        hash="sha256:test",
        object_projection_graph_id=uuid4(),
        object_config_graph_id=uuid4(),
        object_instance_graph_identity_id=oig_id,
        root_class_instance=root,
        class_instances=[],
        class_instance_relationships=rels,
    )


@pytest.mark.parametrize("backend_name", ["db"])
def test_projector_stages_association_upserts(monkeypatch, backend_name: str) -> None:
    monkeypatch.setenv("AWARE_PERSISTENCE_BACKEND", backend_name)

    rel_id = uuid4()
    edge_id = uuid4()
    src_id = uuid4()
    tgt_id = uuid4()

    plan = ProjectionPlan(
        projection_hash="sha256:test:proj",
        opg_name="test",
        dialect="postgres",
        tables=(),
        associations=(
            ProjectionAssociationPlan(
                association_table_key="default.left_right_join",
                relationship_id=rel_id,
                source_fk_column="left_id",
                target_fk_column="right_id",
            ),
        ),
    )

    before = _oig(rels=[])
    after = _oig(
        rels=[
            ClassInstanceRelationship(
                id=edge_id,
                object_instance_graph_id=uuid4(),
                class_config_relationship_id=rel_id,
                source_class_instance_id=src_id,
                target_class_instance_id=tgt_id,
            )
        ]
    )

    branch_id = uuid4()
    session = Session(branch_id=branch_id, skip_db=False)

    stage_lane_projection_writes(
        session=session,
        plan=plan,
        branch_id=branch_id,
        projection_hash=plan.projection_hash,
        before_oig=before,
        after_oig=after,
        changes=[],
        enum_option_value_by_id={},
    )

    assert len(session._pending_deletes) == 0
    assert len(session._pending_inserts) == 1

    sql, params = session._pending_inserts[0]
    assert 'INSERT INTO "default"."left_right_join"' in sql
    assert "ON CONFLICT" in sql
    assert params == (branch_id, plan.projection_hash, edge_id, src_id, tgt_id)


@pytest.mark.parametrize("backend_name", ["db"])
def test_projector_stages_association_deletes(monkeypatch, backend_name: str) -> None:
    monkeypatch.setenv("AWARE_PERSISTENCE_BACKEND", backend_name)

    rel_id = uuid4()
    edge_id = uuid4()
    src_id = uuid4()
    tgt_id = uuid4()

    plan = ProjectionPlan(
        projection_hash="sha256:test:proj",
        opg_name="test",
        dialect="postgres",
        tables=(),
        associations=(
            ProjectionAssociationPlan(
                association_table_key="default.left_right_join",
                relationship_id=rel_id,
                source_fk_column="left_id",
                target_fk_column="right_id",
            ),
        ),
    )

    before = _oig(
        rels=[
            ClassInstanceRelationship(
                id=edge_id,
                object_instance_graph_id=uuid4(),
                class_config_relationship_id=rel_id,
                source_class_instance_id=src_id,
                target_class_instance_id=tgt_id,
            )
        ]
    )
    after = _oig(rels=[])

    branch_id = uuid4()
    session = Session(branch_id=branch_id, skip_db=False)

    stage_lane_projection_writes(
        session=session,
        plan=plan,
        branch_id=branch_id,
        projection_hash=plan.projection_hash,
        before_oig=before,
        after_oig=after,
        changes=[],
        enum_option_value_by_id={},
    )

    assert len(session._pending_inserts) == 0
    assert len(session._pending_deletes) == 1

    sql, params = session._pending_deletes[0]
    assert 'DELETE FROM "default"."left_right_join"' in sql
    assert params == (branch_id, plan.projection_hash, edge_id)
