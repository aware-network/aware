from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID, uuid4

from aware_history_ontology.change.change_enums import ChangeType
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kinds,
)

from aware_orm.projection.plan import (
    ProjectionColumnPlan,
    ProjectionPlan,
    ProjectionTablePlan,
)
from aware_meta.graph.instance.orm_projector import stage_lane_projection_writes
from aware_orm.session.session import Session


def test_required_scalar_fallback_fk_orders_created_parent_before_child() -> None:
    fk_attr_cfg_id = uuid4()
    parent_id = uuid4()
    child_id = uuid4()

    # Force the child class to sort before the parent in the deterministic fallback order.
    # Without the FK dependency edge, the queued inserts would put the child row first.
    parent_cc_id = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    child_cc_id = UUID("00000000-0000-0000-0000-000000000001")

    plan = ProjectionPlan(
        projection_hash="sha256:test:fk-fallback-create-order",
        opg_name="test",
        dialect="postgres",
        tables=(
            ProjectionTablePlan(
                table_key="api.api",
                class_config_id=parent_cc_id,
                primary_key=("branch_id", "projection_hash", "id"),
                columns=(
                    ProjectionColumnPlan(
                        column_name="branch_id", source="branch_id", nullable=False
                    ),
                    ProjectionColumnPlan(
                        column_name="projection_hash",
                        source="projection_hash",
                        nullable=False,
                    ),
                    ProjectionColumnPlan(column_name="id", source="id", nullable=False),
                ),
            ),
            ProjectionTablePlan(
                table_key="api.api_capability",
                class_config_id=child_cc_id,
                primary_key=("branch_id", "projection_hash", "id"),
                columns=(
                    ProjectionColumnPlan(
                        column_name="branch_id", source="branch_id", nullable=False
                    ),
                    ProjectionColumnPlan(
                        column_name="projection_hash",
                        source="projection_hash",
                        nullable=False,
                    ),
                    ProjectionColumnPlan(column_name="id", source="id", nullable=False),
                    ProjectionColumnPlan(
                        column_name="api_id",
                        source="fk_attribute",
                        attribute_config_id=fk_attr_cfg_id,
                        nullable=False,
                    ),
                ),
            ),
        ),
        associations=tuple(),
    )

    fk_attribute = SimpleNamespace(
        attribute_config_id=fk_attr_cfg_id,
        value_root=SimpleNamespace(
            type_descriptor=SimpleNamespace(kind=Kinds.class_),
            class_instance_id=parent_id,
            enum_option_id=None,
            child_links=[],
        ),
    )

    before_oig = SimpleNamespace(class_instances=[], class_instance_relationships=[])
    after_oig = SimpleNamespace(
        class_instances=[
            SimpleNamespace(
                id=child_id,
                class_config_id=child_cc_id,
                attributes=[fk_attribute],
            ),
            SimpleNamespace(
                id=parent_id,
                class_config_id=parent_cc_id,
                attributes=[],
            ),
        ],
        class_instance_relationships=[],
    )
    changes = [
        SimpleNamespace(
            class_instance_changes=[
                SimpleNamespace(
                    class_instance_id=child_id,
                    change=SimpleNamespace(type=ChangeType.create),
                ),
                SimpleNamespace(
                    class_instance_id=parent_id,
                    change=SimpleNamespace(type=ChangeType.create),
                ),
            ],
            class_instance_relationship_changes=[],
        )
    ]

    branch_id = uuid4()
    session = Session(branch_id=branch_id, skip_db=False)

    write_plan = stage_lane_projection_writes(
        session=session,
        plan=plan,
        branch_id=branch_id,
        projection_hash=plan.projection_hash,
        before_oig=before_oig,  # type: ignore[arg-type]
        after_oig=after_oig,  # type: ignore[arg-type]
        changes=changes,  # type: ignore[arg-type]
        enum_option_value_by_id={},
    )

    assert write_plan.create_count == 2
    assert [params[2] for _sql, params in session._pending_inserts] == [
        parent_id,
        child_id,
    ]
    assert session._pending_inserts[1][1][3] == parent_id


def test_required_scalar_fallback_fk_orders_updated_parent_before_created_child() -> (
    None
):
    fk_attr_cfg_id = uuid4()
    parent_id = uuid4()
    child_id = uuid4()

    parent_cc_id = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    child_cc_id = UUID("00000000-0000-0000-0000-000000000001")

    plan = ProjectionPlan(
        projection_hash="sha256:test:fk-fallback-update-parent-order",
        opg_name="test",
        dialect="postgres",
        tables=(
            ProjectionTablePlan(
                table_key="api.api",
                class_config_id=parent_cc_id,
                primary_key=("branch_id", "projection_hash", "id"),
                columns=(
                    ProjectionColumnPlan(
                        column_name="branch_id", source="branch_id", nullable=False
                    ),
                    ProjectionColumnPlan(
                        column_name="projection_hash",
                        source="projection_hash",
                        nullable=False,
                    ),
                    ProjectionColumnPlan(column_name="id", source="id", nullable=False),
                ),
            ),
            ProjectionTablePlan(
                table_key="api.api_capability",
                class_config_id=child_cc_id,
                primary_key=("branch_id", "projection_hash", "id"),
                columns=(
                    ProjectionColumnPlan(
                        column_name="branch_id", source="branch_id", nullable=False
                    ),
                    ProjectionColumnPlan(
                        column_name="projection_hash",
                        source="projection_hash",
                        nullable=False,
                    ),
                    ProjectionColumnPlan(column_name="id", source="id", nullable=False),
                    ProjectionColumnPlan(
                        column_name="api_id",
                        source="fk_attribute",
                        attribute_config_id=fk_attr_cfg_id,
                        nullable=False,
                    ),
                ),
            ),
        ),
        associations=tuple(),
    )

    fk_attribute = SimpleNamespace(
        attribute_config_id=fk_attr_cfg_id,
        value_root=SimpleNamespace(
            type_descriptor=SimpleNamespace(kind=Kinds.class_),
            class_instance_id=parent_id,
            enum_option_id=None,
            child_links=[],
        ),
    )

    parent = SimpleNamespace(
        id=parent_id,
        class_config_id=parent_cc_id,
        attributes=[],
    )
    before_oig = SimpleNamespace(
        class_instances=[parent],
        class_instance_relationships=[],
    )
    after_oig = SimpleNamespace(
        class_instances=[
            SimpleNamespace(
                id=child_id,
                class_config_id=child_cc_id,
                attributes=[fk_attribute],
            ),
            parent,
        ],
        class_instance_relationships=[],
    )
    changes = [
        SimpleNamespace(
            class_instance_changes=[
                SimpleNamespace(
                    class_instance_id=child_id,
                    change=SimpleNamespace(type=ChangeType.create),
                ),
                SimpleNamespace(
                    class_instance_id=parent_id,
                    change=SimpleNamespace(type=ChangeType.update),
                ),
            ],
            class_instance_relationship_changes=[],
        )
    ]

    branch_id = uuid4()
    session = Session(branch_id=branch_id, skip_db=False)

    write_plan = stage_lane_projection_writes(
        session=session,
        plan=plan,
        branch_id=branch_id,
        projection_hash=plan.projection_hash,
        before_oig=before_oig,  # type: ignore[arg-type]
        after_oig=after_oig,  # type: ignore[arg-type]
        changes=changes,  # type: ignore[arg-type]
        enum_option_value_by_id={},
    )

    assert write_plan.create_count == 1
    assert write_plan.update_count == 1
    assert [params[2] for _sql, params in session._pending_inserts] == [
        parent_id,
        child_id,
    ]
    assert session._pending_inserts[1][1][3] == parent_id


def test_fk_attribute_falls_back_to_scalar_attribute_when_relationship_edge_missing() -> (
    None
):
    cc_id = uuid4()
    fk_attr_cfg_id = uuid4()
    rel_id = uuid4()
    instance_id = uuid4()
    fk_target_id = uuid4()

    plan = ProjectionPlan(
        projection_hash="sha256:test:fk-fallback",
        opg_name="test",
        dialect="postgres",
        tables=(
            ProjectionTablePlan(
                table_key="actor.actor_subscription",
                class_config_id=cc_id,
                primary_key=("branch_id", "projection_hash", "id"),
                columns=(
                    ProjectionColumnPlan(
                        column_name="branch_id", source="branch_id", nullable=False
                    ),
                    ProjectionColumnPlan(
                        column_name="projection_hash",
                        source="projection_hash",
                        nullable=False,
                    ),
                    ProjectionColumnPlan(column_name="id", source="id", nullable=False),
                    ProjectionColumnPlan(
                        column_name="actor_id",
                        source="fk_attribute",
                        attribute_config_id=fk_attr_cfg_id,
                        relationship_id=rel_id,
                        direction="forward",
                        nullable=True,
                    ),
                ),
            ),
        ),
        associations=tuple(),
    )

    fk_attribute = SimpleNamespace(
        attribute_config_id=fk_attr_cfg_id,
        value_root=SimpleNamespace(
            type_descriptor=SimpleNamespace(kind=Kinds.primitive),
            primitive_value={"value": fk_target_id},
            enum_option_id=None,
            child_links=[],
        ),
    )

    before_oig = SimpleNamespace(class_instances=[], class_instance_relationships=[])
    after_oig = SimpleNamespace(
        class_instances=[
            SimpleNamespace(
                id=instance_id,
                class_config_id=cc_id,
                attributes=[fk_attribute],
            )
        ],
        class_instance_relationships=[],
    )
    changes = [
        SimpleNamespace(
            class_instance_changes=[
                SimpleNamespace(
                    class_instance_id=instance_id,
                    change=SimpleNamespace(type=ChangeType.create),
                )
            ],
            class_instance_relationship_changes=[],
        )
    ]

    branch_id = uuid4()
    session = Session(branch_id=branch_id, skip_db=False)

    stage_lane_projection_writes(
        session=session,
        plan=plan,
        branch_id=branch_id,
        projection_hash=plan.projection_hash,
        before_oig=before_oig,  # type: ignore[arg-type]
        after_oig=after_oig,  # type: ignore[arg-type]
        changes=changes,  # type: ignore[arg-type]
        enum_option_value_by_id={},
    )

    assert len(session._pending_inserts) == 1
    _sql, params = session._pending_inserts[0]
    assert params[3] == fk_target_id


def test_fk_attribute_required_fallback_is_resolved_from_scalar_value() -> None:
    cc_id = uuid4()
    fk_attr_cfg_id = uuid4()
    rel_id = uuid4()
    instance_id = uuid4()
    fk_target_id = uuid4()

    plan = ProjectionPlan(
        projection_hash="sha256:test:fk-fallback-required",
        opg_name="test",
        dialect="postgres",
        tables=(
            ProjectionTablePlan(
                table_key="actor.actor_subscription",
                class_config_id=cc_id,
                primary_key=("branch_id", "projection_hash", "id"),
                columns=(
                    ProjectionColumnPlan(
                        column_name="branch_id", source="branch_id", nullable=False
                    ),
                    ProjectionColumnPlan(
                        column_name="projection_hash",
                        source="projection_hash",
                        nullable=False,
                    ),
                    ProjectionColumnPlan(column_name="id", source="id", nullable=False),
                    ProjectionColumnPlan(
                        column_name="actor_id",
                        source="fk_attribute",
                        attribute_config_id=fk_attr_cfg_id,
                        relationship_id=rel_id,
                        direction="forward",
                        nullable=False,
                    ),
                ),
            ),
        ),
        associations=tuple(),
    )

    fk_attribute = SimpleNamespace(
        attribute_config_id=fk_attr_cfg_id,
        value_root=SimpleNamespace(
            type_descriptor=SimpleNamespace(kind=Kinds.class_),
            class_instance_id=fk_target_id,
            enum_option_id=None,
            child_links=[],
        ),
    )

    before_oig = SimpleNamespace(class_instances=[], class_instance_relationships=[])
    after_oig = SimpleNamespace(
        class_instances=[
            SimpleNamespace(
                id=instance_id,
                class_config_id=cc_id,
                attributes=[fk_attribute],
            )
        ],
        class_instance_relationships=[],
    )
    changes = [
        SimpleNamespace(
            class_instance_changes=[
                SimpleNamespace(
                    class_instance_id=instance_id,
                    change=SimpleNamespace(type=ChangeType.create),
                )
            ],
            class_instance_relationship_changes=[],
        )
    ]

    branch_id = uuid4()
    session = Session(branch_id=branch_id, skip_db=False)

    stage_lane_projection_writes(
        session=session,
        plan=plan,
        branch_id=branch_id,
        projection_hash=plan.projection_hash,
        before_oig=before_oig,  # type: ignore[arg-type]
        after_oig=after_oig,  # type: ignore[arg-type]
        changes=changes,  # type: ignore[arg-type]
        enum_option_value_by_id={},
    )

    assert len(session._pending_inserts) == 1
    _sql, params = session._pending_inserts[0]
    assert params[3] == fk_target_id
