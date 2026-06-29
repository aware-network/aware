from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_history_ontology.change.change_enums import ChangeType
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)

from aware_orm.projection.plan import (
    ProjectionColumnPlan,
    ProjectionPlan,
    ProjectionTablePlan,
)
from aware_meta.graph.instance.orm_projector import stage_lane_projection_writes
from aware_orm.session.session import Session


def test_datetime_primitive_is_coerced_for_postgres_projection() -> None:
    """Regression: asyncpg TIMESTAMPTZ expects datetime, not ISO strings."""

    cc_id = uuid4()
    attr_cfg_id = uuid4()
    instance_id = uuid4()

    plan = ProjectionPlan(
        projection_hash="sha256:test:proj",
        opg_name="test",
        dialect="postgres",
        tables=(
            ProjectionTablePlan(
                table_key="test.datetime_table",
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
                        column_name="last_seen_at",
                        source="attribute",
                        attribute_config_id=attr_cfg_id,
                        nullable=False,
                    ),
                ),
            ),
        ),
        associations=tuple(),
    )

    value_root = SimpleNamespace(
        type_descriptor=SimpleNamespace(
            kind=AttributeTypeDescriptorKind.primitive,
            primitive_config=SimpleNamespace(
                primitive_type=SimpleNamespace(
                    base_type=CodePrimitiveBaseType.datetime
                ),
            ),
        ),
        primitive_value={"value": "2026-02-04T23:29:21.095045"},
        enum_option_id=None,
        child_links=[],
        class_instance_id=None,
    )

    before_oig = SimpleNamespace(class_instances=[], class_instance_relationships=[])
    after_oig = SimpleNamespace(
        class_instances=[
            SimpleNamespace(
                id=instance_id,
                class_config_id=cc_id,
                attributes=[
                    SimpleNamespace(
                        attribute_config_id=attr_cfg_id, value_root=value_root
                    ),
                ],
            ),
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
        attribute_configs_by_id=None,
    )

    assert len(session._pending_inserts) == 1
    _sql, params = session._pending_inserts[0]
    assert isinstance(params[3], datetime)
    assert params[3].tzinfo is not None
