# @code-under-test: ../../aware_orm/projection/plan.py
# @code-under-test: ../../aware_orm/projection/serialization.py

from __future__ import annotations

from uuid import UUID, uuid4

from aware_orm.projection.plan import (
    ProjectionAssociationPlan,
    ProjectionColumnPlan,
    ProjectionPlan,
    ProjectionTablePlan,
)
from aware_orm.projection.serialization import (
    deserialize_projection_plans,
    serialize_projection_plans,
)


def test_projection_plan_serialization_roundtrip() -> None:
    rel_id = uuid4()
    attr_id = uuid4()
    cc_id = uuid4()

    plan = ProjectionPlan(
        projection_hash="sha256:test",
        opg_name="Identity",
        dialect="sqlite",
        tables=(
            ProjectionTablePlan(
                table_key="identity.actor",
                class_config_id=cc_id,
                primary_key=("branch_id", "projection_hash", "id"),
                columns=(
                    ProjectionColumnPlan(
                        column_name="id",
                        source="id",
                        sql_type_hint="TEXT",
                        nullable=False,
                    ),
                    ProjectionColumnPlan(
                        column_name="display_name",
                        source="attribute",
                        attribute_config_id=attr_id,
                        sql_type_hint="TEXT",
                        nullable=False,
                    ),
                    ProjectionColumnPlan(
                        column_name="identity_id",
                        source="fk_attribute",
                        attribute_config_id=UUID(int=0),
                        relationship_id=rel_id,
                        direction="forward",
                        sql_type_hint="TEXT",
                        nullable=False,
                    ),
                ),
            ),
        ),
        associations=(
            ProjectionAssociationPlan(
                association_table_key="identity.actor_role",
                relationship_id=rel_id,
                source_fk_column="actor_id",
                target_fk_column="role_id",
            ),
        ),
    )

    payload = serialize_projection_plans([plan])
    recovered = deserialize_projection_plans(payload)
    assert len(recovered) == 1
    assert recovered[0] == plan
